# joinpath

**给 NL2SQL Agent 一张「该走哪几张表」的地图，而不是整仓 DDL。**

生产里 Text-to-SQL 挂掉，通常不是模型不会写 `SELECT`，而是 200 张表、700 个字段时：

1. 选错表
2. 走错 join / 丢掉桥表
3. 把整份 schema 塞进上下文，模型在噪声里编一个「看起来合理」的字段

`joinpath` 做且只做这件事：人话 + schema（表、字段、外键、业务别名）→ 子图。Agent **只允许在这张子图上写 SQL**。

零第三方依赖。Python 3.10+。

## 30 秒

```bash
PYTHONPATH=src python3 -m joinpath.cli \
  --schema examples/schema.json \
  "今年黄金会员的成交额"
```

输出类似：

```text
[plan] tables: customers, orders  confidence=0.86
  join  orders.customer_id = customers.id
  col   orders.gmv_amt  ← 成交额
  col   customers.tier  ← 黄金会员
  col   orders.booked_at ← 成交时间
```

以及一段可以直接塞进模型的 compact prompt：只列出这几张表、这几条边、这几个被问句命中的字段。`employees` 不会出现。

品类销量会自动把桥表拉进来：

```bash
PYTHONPATH=src python3 -m joinpath.cli --schema examples/schema.json "每个品类的销量"
# skus + order_items + orders，沿着 FK 补全
```

## 它在 Agent 里的位置

```
用户提问
  → joinpath 检索子图 + join 路径     ← 本仓库
  → 模型只看 compact prompt 写 SQL
  → 执行
```

别名写在 schema 里，不写在 prompt 里。现场交付第一周收的「成交额 = gmv_amt、成交时间 = booked_at」就是这份 JSON。

## Schema

见 [`examples/schema.json`](examples/schema.json)。关键字段：

- `tables[].aliases` / `columns[].aliases`：业务叫法
- `foreign_keys`：`{"from": "orders.customer_id", "to": "customers.id"}`

没有外键的表如果被问句命中，会出现在 `disconnected_tables`。Agent 的约定是：**不要发明 join，去问人。**

## Python

```python
from joinpath import Schema, plan_question

schema = Schema.from_path("examples/schema.json")
plan = plan_question("今年黄金会员的成交额", schema)
print(plan.tables)
print(plan.joins)
print(plan.compact_prompt())
```

## MCP / Skill

```bash
python -m joinpath.mcp
```

工具名：`plan_sql_subgraph`。Skill 在 [`skills/joinpath/SKILL.md`](skills/joinpath/SKILL.md)。

## 不是什么

- 不是完整 Text-to-SQL：不生成最终 SQL，不执行，不算钱
- 不是 embedding 检索：第一版用别名 + 中英文 n-gram 重叠，零模型，可复现
- 不是语义层：指标公式、权限、RLS 不在范围内

别名质量决定效果上限。没有别名的脏字段名（`tbl_ema_nrm`）检索会弱——这是有意暴露的，方便你把现场口径补进 schema。

## 路线图

1. 可选 `sqlglot` / embedding 后端
2. 指标锁：`metrics.yaml` → 子图必须覆盖指标用到的列
3. 从信息_schema + 慢查询日志半自动挖 FK 和别名

## License

MIT
