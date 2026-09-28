from __future__ import annotations

from dataclasses import dataclass

from .schema import Schema, Table
from .text import phrase_in, tokenize


@dataclass
class Hit:
    table: str
    score: float
    reasons: list[str]
    columns: list[tuple[str, float, str]]


def retrieve(question: str, schema: Schema, top_k: int = 4) -> list[Hit]:
    q_tokens = tokenize(question)
    hits: list[Hit] = []
    for table in schema.tables.values():
        score, reasons, columns = _score_table(question, q_tokens, table)
        if score <= 0:
            continue
        hits.append(Hit(table=table.name, score=score, reasons=reasons, columns=columns))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def _score_table(question: str, q_tokens: list[str], table: Table) -> tuple[float, list[str], list[tuple[str, float, str]]]:
    score = 0.0
    reasons: list[str] = []

    for alias in (table.name, *table.aliases):
        if phrase_in(question, alias) and len(alias) >= 2:
            bonus = 5.0 if alias.lower() != table.name.lower() else 3.5
            score += bonus
            reasons.append(f"table:{alias}")
            break
        overlap = _token_overlap(q_tokens, tokenize(alias))
        if overlap:
            score += 1.2 * overlap
            reasons.append(f"table-token:{alias}")

    columns: list[tuple[str, float, str]] = []
    for col in table.columns.values():
        col_score = 0.0
        why = ""
        for alias in (col.name, *col.aliases):
            if phrase_in(question, alias) and len(alias) >= 2:
                col_score = 4.0 if alias.lower() != col.name.lower() else 2.5
                why = alias
                break
            ov = _token_overlap(q_tokens, tokenize(alias + " " + col.description))
            if ov and ov > col_score:
                col_score = 1.0 * ov
                why = alias
        if col_score > 0:
            score += col_score
            columns.append((col.name, col_score, why))
            reasons.append(f"col:{col.name}={why}")

    columns.sort(key=lambda x: x[1], reverse=True)
    return score, reasons, columns[:8]


def _token_overlap(question_tokens: list[str], candidate_tokens: list[str]) -> float:
    if not question_tokens or not candidate_tokens:
        return 0.0
    q = set(question_tokens)
    c = set(candidate_tokens)
    inter = q & c
    if not inter:
        return 0.0
    return len(inter) / max(1, len(c))
