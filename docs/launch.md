# 发布文案

复制即用。先把仓库 About 填好，再发社区。

## GitHub About

- Description: `Schema subgraph + join path for NL2SQL agents. Map, not the whole warehouse.`
- Website: `https://github.com/mhc22/joinpath`
- Topics: `nl2sql` `text-to-sql` `schema-linking` `ai-agents` `mcp` `data-agent` `python`

仓库页右侧 ⚙️ 填写。

## 一句话

中文：给 NL2SQL Agent 一张该走哪几张表的地图，别把整仓 DDL 塞进上下文。

English: Don't dump your warehouse into the prompt. Retrieve the join path first.

## Show HN

**Title:** Show HN: joinpath – schema subgraph retrieval for NL2SQL agents

**Body:**

Production text-to-SQL mostly fails on schema linking: 200 tables, opaque column names, wrong join, or a hallucinated column that looks reasonable. Accuracy that is 80%+ on Spider-style schemas collapses on real warehouses.

joinpath is a tiny zero-dep library that takes a question + a declared schema (tables, FKs, business aliases) and returns the only subgraph the agent may use. The model never sees `employees` when you asked about gold-member GMV.

It does not generate SQL. It does not call a warehouse. It is the step before the LLM.

Repo: https://github.com/mhc22/joinpath

## X / 微博

给数据 Agent 用的小工具开源了：写 SQL 之前先检索「该碰哪几张表、怎么 join」。

整仓 DDL 塞进 prompt 是在邀请模型编字段。joinpath 用别名 + 外键图，输出一段 compact prompt，Agent 只能在这张子图上写。

零依赖，MIT。
https://github.com/mhc22/joinpath

## 掘金 / 知乎标题

NL2SQL 在生产挂掉，通常不是模型不会写 SELECT

副标题：一个只做 schema linking 的开源小库

开头可用 README 里「200 张表」那三段，结尾贴仓库和 `examples/schema.json`。强调：别名是交付第一周就要收的东西，不是又一个框架。

## V2EX

标题：`[开源] 写给数据 Agent 的 schema 路由器，不生成 SQL`

正文短一点：痛点（选错表 / 错 join / 幻觉列）→ 输入输出各一行 → clone 命令 → 求真实 schema 的别名 Issue。

## Reddit r/LocalLLaMA

Title: Tiny zero-dep schema linker for local SQL agents (no embeddings)

Most local SQL agents still stuff the whole DDL into context. This repo retrieves a join subgraph from aliases + FKs so a 7B/14B tool-caller only sees 2–3 tables. Looking for people with messy warehouse names to file alias issues.

## 小红书 / 朋友圈（短）

数据 Agent 别再把整库表结构扔给模型了。

开源了一个小工具：问「黄金会员成交额」，自动只给你 orders + customers 和那一条 join。

https://github.com/mhc22/joinpath

## 演示顺序（录屏 40 秒）

1. 打开 `examples/schema.json`，指一下 `employees` 也在库里
2. 跑「今年黄金会员的成交额」
3. 指出输出里没有 `employees`，有 `gmv_amt ← 成交额`
4. 再跑「每个品类的销量」，指出桥表 `order_items` 被补上
5. 结束画面停在 GitHub README
