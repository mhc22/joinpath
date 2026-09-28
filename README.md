<p align="center">
  <h1 align="center">joinpath</h1>
  <p align="center">Give an NL2SQL agent a <em>map</em>, not the whole warehouse.</p>
  <p align="center">
    <a href="https://github.com/mhc22/joinpath/actions"><img src="https://github.com/mhc22/joinpath/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
    <img src="https://img.shields.io/badge/deps-zero-lightgrey" alt="no deps">
  </p>
</p>

**中文** | [Launch copy](docs/launch.md) | [English below](#english)

生产里 Text-to-SQL 挂掉，通常不是模型不会写 `SELECT`，而是仓库有 200 张表时：

1. 选错表
2. 走错 join，丢掉桥表
3. 整份 DDL 塞进上下文，模型编一个「看起来合理」的字段

`joinpath` 只做一件事：

```
人话 + schema.json（表 / 字段 / 外键 / 业务别名）
        ↓
   子图 + join 路径 + 命中字段
        ↓
   Agent 只能在这张图上写 SQL
```

零依赖。Python 3.10+。CLI / 库 / MCP / Agent Skill。

## 30 秒

```bash
git clone https://github.com/mhc22/joinpath.git
cd joinpath
PYTHONPATH=src python3 -m joinpath.cli \
  --schema examples/schema.json \
  "今年黄金会员的成交额"
```

```text
[plan] tables: orders, customers  confidence=1.00
  join  orders.customer_id = customers.id
  col   orders.gmv_amt   ← 成交额
  col   customers.tier   ← 黄金
  col   orders.booked_at ← 今年
```

模型实际看到的是这段 **compact prompt**，不是 200 张表：

```text
# schema subgraph — write SQL using ONLY these objects
# question: 今年黄金会员的成交额
tables:
  - orders: gmv_amt:numeric=成交额, booked_at:timestamptz=今年
  - customers: tier:text=黄金
joins:
  - orders.customer_id = customers.id
```

`employees` 不会出现。问「每个品类的销量」时，会沿外键把桥表 `order_items` 补进来。

```bash
PYTHONPATH=src python3 -m joinpath.cli --schema examples/schema.json "每个品类的销量"
```

## 为什么不是又一个 Text-to-SQL

| 做法 | 结果 |
| --- | --- |
| 把整仓 DDL 丢进 prompt | 贵、慢、选错表 |
| 只做事后 lint（字段在不在） | 拦不住「字段在，但用错了」 |
| embedding 整库检索 | 要模型、要索引、难复现 |
| **joinpath** | 别名 + 图。现场第一周收的口径，写成 JSON |

别名写在 schema 里，不写在 prompt 里。交付时那句「成交额是 `gmv_amt`，入账看 `booked_at`」就是这份文件。

## 接入 Agent

```
用户提问
  → joinpath.plan_question(...)     ← 本库
  → 只把 compact_prompt() 给模型
  → 模型写 SQL
  → 执行
```

Python：

```python
from joinpath import Schema, plan_question

schema = Schema.from_path("examples/schema.json")
plan = plan_question("今年黄金会员的成交额", schema)
assert "employees" not in plan.tables
print(plan.compact_prompt())
```

MCP（Claude Code / Cursor / 任意 MCP host）：

```bash
python -m joinpath.mcp
```

```json
{
  "mcpServers": {
    "joinpath": {
      "command": "python",
      "args": ["-m", "joinpath.mcp"]
    }
  }
}
```

工具名：`plan_sql_subgraph`。Skill：[`skills/joinpath/SKILL.md`](skills/joinpath/SKILL.md)。

约定：

- `disconnected_tables` 非空 → **不要发明 join**，问人
- plan 为空 → 缺别名，把业务词补进 `schema.json`

## Schema

完整示例：[`examples/schema.json`](examples/schema.json)。

```json
{
  "tables": [
    {
      "name": "orders",
      "aliases": ["订单", "成交"],
      "columns": [
        {
          "name": "gmv_amt",
          "type": "numeric",
          "aliases": ["成交额", "GMV", "销售额"]
        }
      ]
    }
  ],
  "foreign_keys": [
    {"from": "orders.customer_id", "to": "customers.id"}
  ]
}
```

效果上限 = 别名质量。字段叫 `tbl_ema_nrm` 且没有别名，检索就会弱。这是有意的：逼你把现场口径沉淀成文件。

## 不是什么

- 不生成最终 SQL，不连仓库，不算查询费用
- 第一版不用 embedding，可复现
- 不是语义层 / 权限 / RLS（见路线图）

## 路线图

- [ ] 可选 sqlglot / embedding 后端
- [ ] `metrics.yaml` 口径锁：子图必须覆盖指标用到的列
- [ ] 从 `information_schema` + 慢查询日志半自动挖 FK 和别名

## 开发

```bash
PYTHONPATH=src python3 -m pytest -q
```

欢迎直接开 Issue：选错表、缺别名、真实仓库里的叫法。模板在 `.github/ISSUE_TEMPLATE/`。

## License

MIT

---

<a id="english"></a>

## English

`joinpath` retrieves the **schema subgraph** an NL2SQL agent is allowed to see.

Production text-to-SQL usually dies on schema linking, not on `SELECT` syntax. Dumping 200 tables into the prompt is how models invent plausible column names. `joinpath` takes a question plus a declared schema (tables, columns, foreign keys, business aliases) and returns the small join graph the model should use — nothing else.

No third-party dependencies. MIT.

```bash
PYTHONPATH=src python3 -m joinpath.cli \
  --schema examples/schema.json \
  "gold member GMV this year"
```

Plug `plan.compact_prompt()` into any agent loop before SQL generation. If `disconnected_tables` is set, the agent must ask a human instead of inventing a join.
