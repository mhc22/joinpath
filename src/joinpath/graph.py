from __future__ import annotations

from collections import defaultdict, deque

from .schema import ForeignKey, Schema, norm


class JoinGraph:
    def __init__(self, schema: Schema):
        self.schema = schema
        self.adj: dict[str, list[tuple[str, ForeignKey]]] = defaultdict(list)
        for fk in schema.foreign_keys:
            left = norm(fk.from_table)
            right = norm(fk.to_table)
            self.adj[left].append((right, fk))
            self.adj[right].append((left, fk.reverse()))

    def shortest_path(self, src: str, dst: str) -> list[ForeignKey] | None:
        src, dst = norm(src), norm(dst)
        if src == dst:
            return []
        prev: dict[str, tuple[str, ForeignKey]] = {}
        seen = {src}
        q: deque[str] = deque([src])
        while q:
            node = q.popleft()
            for nxt, edge in self.adj.get(node, []):
                if nxt in seen:
                    continue
                seen.add(nxt)
                prev[nxt] = (node, edge)
                if nxt == dst:
                    return _rebuild(prev, src, dst)
                q.append(nxt)
        return None

    def connect(self, tables: list[str]) -> tuple[list[str], list[ForeignKey]]:
        """Greedy Steiner: attach each next table via shortest path."""
        if not tables:
            return [], []
        ordered = [norm(t) for t in tables]
        included = {ordered[0]}
        edges: list[ForeignKey] = []
        for target in ordered[1:]:
            if target in included:
                continue
            best: tuple[int, list[ForeignKey], str] | None = None
            for src in included:
                path = self.shortest_path(src, target)
                if path is None:
                    continue
                cand = (len(path), path, src)
                if best is None or cand[0] < best[0]:
                    best = cand
            if best is None:
                continue
            for edge in best[1]:
                included.add(norm(edge.from_table))
                included.add(norm(edge.to_table))
                edges.append(edge)
        # keep original names
        names = []
        seen: set[str] = set()
        for key in list(ordered) + [norm(e.from_table) for e in edges] + [norm(e.to_table) for e in edges]:
            if key in seen or key not in self.schema.tables:
                continue
            seen.add(key)
            names.append(self.schema.tables[key].name)
        return names, _dedupe_edges(edges)


def _rebuild(prev: dict[str, tuple[str, ForeignKey]], src: str, dst: str) -> list[ForeignKey]:
    path: list[ForeignKey] = []
    cur = dst
    while cur != src:
        parent, edge = prev[cur]
        path.append(edge)
        cur = parent
    path.reverse()
    return path


def _dedupe_edges(edges: list[ForeignKey]) -> list[ForeignKey]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[ForeignKey] = []
    for edge in edges:
        key = tuple(
            sorted(
                [
                    (norm(edge.from_table), norm(edge.from_column)),
                    (norm(edge.to_table), norm(edge.to_column)),
                ]
            )
        )
        flat = (key[0][0], key[0][1], key[1][0], key[1][1])
        if flat in seen:
            continue
        seen.add(flat)
        out.append(edge)
    return out
