from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


def norm(name: str) -> str:
    return name.strip().strip("`\"[]").lower()


@dataclass(frozen=True)
class Column:
    name: str
    type: str = ""
    description: str = ""
    aliases: tuple[str, ...] = ()

    def terms(self) -> list[str]:
        return [self.name, *self.aliases, self.description]


@dataclass
class Table:
    name: str
    columns: dict[str, Column] = field(default_factory=dict)
    description: str = ""
    aliases: tuple[str, ...] = ()

    def terms(self) -> list[str]:
        return [self.name, *self.aliases, self.description]


@dataclass(frozen=True)
class ForeignKey:
    from_table: str
    from_column: str
    to_table: str
    to_column: str

    def as_eq(self) -> str:
        return f"{self.from_table}.{self.from_column} = {self.to_table}.{self.to_column}"

    def reverse(self) -> "ForeignKey":
        return ForeignKey(self.to_table, self.to_column, self.from_table, self.from_column)


@dataclass
class Schema:
    tables: dict[str, Table] = field(default_factory=dict)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    dialect: str = "generic"

    def table(self, name: str) -> Table | None:
        return self.tables.get(norm(name))

    def column(self, table: str, column: str) -> Column | None:
        t = self.table(table)
        if not t:
            return None
        return t.columns.get(norm(column))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Schema":
        tables: dict[str, Table] = {}
        raw_tables = payload.get("tables")
        if raw_tables is None:
            raise ValueError("schema.tables is required")
        if isinstance(raw_tables, dict):
            items: Iterable[Any] = [
                {"name": k, **(v if isinstance(v, dict) else {"columns": v})}
                for k, v in raw_tables.items()
            ]
        else:
            items = raw_tables

        for item in items:
            cols: dict[str, Column] = {}
            for col in item.get("columns") or []:
                if isinstance(col, str):
                    column = Column(name=col)
                else:
                    column = Column(
                        name=col["name"],
                        type=str(col.get("type") or ""),
                        description=str(col.get("description") or ""),
                        aliases=tuple(col.get("aliases") or ()),
                    )
                cols[norm(column.name)] = column
            table = Table(
                name=item["name"],
                columns=cols,
                description=str(item.get("description") or ""),
                aliases=tuple(item.get("aliases") or ()),
            )
            tables[norm(table.name)] = table

        fks: list[ForeignKey] = []
        for fk in payload.get("foreign_keys") or []:
            if "from" in fk and "to" in fk:
                ft, fc = _split_ident(fk["from"])
                tt, tc = _split_ident(fk["to"])
            else:
                ft, fc = fk["from_table"], fk["from_column"]
                tt, tc = fk["to_table"], fk["to_column"]
            fks.append(ForeignKey(ft, fc, tt, tc))

        return cls(tables=tables, foreign_keys=fks, dialect=str(payload.get("dialect") or "generic"))

    @classmethod
    def from_path(cls, path: str | Path) -> "Schema":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _split_ident(value: str) -> tuple[str, str]:
    if "." not in value:
        raise ValueError(f"expected table.column, got {value!r}")
    table, column = value.split(".", 1)
    return table, column
