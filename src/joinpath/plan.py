from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .graph import JoinGraph
from .retrieve import Hit, retrieve
from .schema import ForeignKey, Schema, norm


@dataclass
class ColumnHint:
    table: str
    column: str
    score: float
    matched: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    type: str = ""


@dataclass
class JoinPlan:
    question: str
    tables: list[str]
    joins: list[str]
    columns: list[ColumnHint]
    disconnected: list[str]
    confidence: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload

    def compact_prompt(self) -> str:
        """The only context the SQL agent should see."""
        lines = ["# schema subgraph — write SQL using ONLY these objects", f"# question: {self.question}"]
        if not self.tables:
            lines.append("# no tables retrieved. ask the user to clarify.")
            return "\n".join(lines)
        lines.append("tables:")
        by_table: dict[str, list[ColumnHint]] = {}
        for col in self.columns:
            by_table.setdefault(col.table, []).append(col)
        for table in self.tables:
            hints = by_table.get(table) or []
            if hints:
                parts = []
                for h in hints:
                    piece = h.column
                    if h.type:
                        piece += f":{h.type}"
                    if h.matched:
                        piece += f"={h.matched}"
                    parts.append(piece)
                cols = ", ".join(parts)
            else:
                cols = "(use listed joins only; no column hint)"
            lines.append(f"  - {table}: {cols}")
        if self.joins:
            lines.append("joins:")
            for join in self.joins:
                lines.append(f"  - {join}")
        if self.disconnected:
            lines.append("disconnected_tables: " + ", ".join(self.disconnected))
            lines.append("# these tables matched the question but have no FK path — do not invent a join")
        lines.append("rules:")
        lines.append("  - do not reference any table or column not listed above")
        lines.append("  - prefer hinted columns when an alias matches the question")
        lines.append("  - add LIMIT unless the user asked for a full export")
        return "\n".join(lines)

    def summary(self) -> str:
        if not self.tables:
            return f"[empty] no schema match for: {self.question}"
        lines = [
            f"[plan] tables: {', '.join(self.tables)}  confidence={self.confidence:.2f}",
        ]
        for join in self.joins:
            lines.append(f"  join  {join}")
        for col in self.columns[:12]:
            lines.append(f"  col   {col.table}.{col.column}  ← {col.matched} ({col.score:.1f})")
        if self.disconnected:
            lines.append(f"  gap   {', '.join(self.disconnected)} (no FK path)")
        return "\n".join(lines)


def plan_question(question: str, schema: Schema, top_k: int = 4, min_score: float = 1.5) -> JoinPlan:
    hits = [h for h in retrieve(question, schema, top_k=top_k) if h.score >= min_score]
    if not hits:
        hits = retrieve(question, schema, top_k=min(2, top_k))

    seed_tables = [h.table for h in hits]
    graph = JoinGraph(schema)
    connected, edges = graph.connect(seed_tables)
    connected_set = {norm(t) for t in connected}
    disconnected = [t for t in seed_tables if norm(t) not in connected_set]

    columns = _collect_columns(schema, hits, connected)
    reasons = []
    for hit in hits:
        reasons.extend(f"{hit.table}:{r}" for r in hit.reasons[:4])

    confidence = _confidence(hits, edges, disconnected)
    return JoinPlan(
        question=question,
        tables=connected or seed_tables,
        joins=[_named_eq(schema, e) for e in edges],
        columns=columns,
        disconnected=disconnected,
        confidence=confidence,
        reasons=reasons,
    )


def _collect_columns(schema: Schema, hits: list[Hit], tables: list[str]) -> list[ColumnHint]:
    wanted = {norm(t) for t in tables}
    out: list[ColumnHint] = []
    seen: set[tuple[str, str]] = set()
    for hit in hits:
        if norm(hit.table) not in wanted:
            continue
        table = schema.table(hit.table)
        if not table:
            continue
        for col_name, score, matched in hit.columns:
            key = (norm(hit.table), norm(col_name))
            if key in seen:
                continue
            seen.add(key)
            col = table.columns.get(norm(col_name))
            out.append(
                ColumnHint(
                    table=table.name,
                    column=col.name if col else col_name,
                    score=score,
                    matched=matched,
                    aliases=list(col.aliases) if col else [],
                    description=col.description if col else "",
                    type=col.type if col else "",
                )
            )
    out.sort(key=lambda c: c.score, reverse=True)
    return out


def _named_eq(schema: Schema, edge: ForeignKey) -> str:
    left = schema.table(edge.from_table)
    right = schema.table(edge.to_table)
    lt = left.name if left else edge.from_table
    rt = right.name if right else edge.to_table
    return f"{lt}.{edge.from_column} = {rt}.{edge.to_column}"


def _confidence(hits: list[Hit], edges: list[ForeignKey], disconnected: list[str]) -> float:
    if not hits:
        return 0.0
    top = min(1.0, hits[0].score / 8.0)
    coverage = min(1.0, sum(h.score for h in hits) / 16.0)
    penalty = 0.25 * len(disconnected)
    path_bonus = 0.1 if edges else 0.0
    return max(0.0, min(1.0, 0.5 * top + 0.5 * coverage + path_bonus - penalty))
