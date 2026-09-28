from joinpath import Schema, plan_question

SCHEMA = Schema.from_path("examples/schema.json")


def test_gold_member_gmv_picks_orders_and_customers():
    plan = plan_question("今年黄金会员的成交额", SCHEMA)
    names = {t.lower() for t in plan.tables}
    assert "orders" in names
    assert "customers" in names
    assert "employees" not in names
    join_text = " ".join(plan.joins).lower()
    assert "customer_id" in join_text
    col_names = {f"{c.table}.{c.column}".lower() for c in plan.columns}
    assert any(name.endswith("gmv_amt") for name in col_names)
    assert any(name.endswith("tier") for name in col_names)


def test_sku_category_pulls_bridge_table():
    plan = plan_question("每个品类的销量", SCHEMA)
    names = {t.lower() for t in plan.tables}
    assert "skus" in names
    # fact path should come in via order_items
    assert "order_items" in names or any("order_items" in j for j in plan.joins)
    assert "employees" not in names


def test_compact_prompt_forbids_extra_tables():
    plan = plan_question("黄金会员成交额", SCHEMA)
    prompt = plan.compact_prompt()
    assert "write SQL using ONLY these objects" in prompt
    assert "employees" not in prompt


def test_unknown_question_is_low_confidence():
    plan = plan_question("今天天气怎么样", SCHEMA)
    assert plan.confidence < 0.4
