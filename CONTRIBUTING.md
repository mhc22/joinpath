# Contributing

最小的有用改动优于大重构。

## 本地

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m joinpath.cli --schema examples/schema.json "今年黄金会员的成交额"
```

不增加必选依赖。embedding / sqlglot 只能放 optional extra。

## 什么算好 Issue

- 一句真实业务问句 + 你期望的表/join + 实际 plan
- 一个业务叫法 → 物理字段的映射（用 Alias 模板）

## PR

- 新检索规则请带一个失败问句变成通过的测试
- 不要把真实客户库结构提交上来
