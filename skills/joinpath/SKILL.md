---
name: joinpath
description: Before writing SQL for a data question, retrieve the schema subgraph (tables, join path, hinted columns). Use when doing NL2SQL or reviewing warehouse queries.
---

# joinpath

Never dump the full warehouse DDL into context. Never invent join keys.

1. Load the project's `schema.json` (tables + foreign_keys + aliases).
2. Run:

```bash
python -m joinpath.cli --schema schema.json --prompt "今年黄金会员的成交额"
```

3. Write SQL using ONLY the tables and columns in that prompt block.
4. If `disconnected_tables` is non-empty, stop and ask which join is correct. Do not invent one.
5. If the plan is empty, ask the user which business term maps to which column, then add an alias to schema.json.
