# M6 Flow 与 M7 Query 契约（T03.4 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.4 产出。
> 前置：T03.1–T03.3、T01.2。

## 1. M6 Flow 契约要点

- 表达跨行为编排、状态迁移与终止状态；**不**表达单次页面刷新/按钮导航（T01.4，TERM-005）。
- 字段：`states[]`、`transitions[]`、`trigger_behaviors[]`（M2 引用）、`guard_rules[]`（M3/M5 引用）、`terminals[]`。
- 每个迁移必须引用存在的状态、M2、M3/M5；不可达引用校验失败。

## 2. M7 Query 契约要点

- 表达查询语义、语义参数、返回形状、过滤/排序/分页、数据范围与限制；**不得**包含任意 SQL、数据库凭据或物理 DTO 映射。
- 字段：`target_object`（M1 引用）、`semantic_parameters[]`、`return_shape`、`filters[]`、`ordering`、`pagination`（必填上限）、`row_scope`、`limits`。
- 无分页/上限的集合查询或越过声明数据范围的查询不能通过发布级校验。

## 3. 样例

- `models/examples/masterdata/m6-flow.yaml`：`subtable-approval-flow`（待审 → 通过/驳回）。
- `models/examples/masterdata/m7-query.yaml`：`list-subtable-data`（按 `subtableType` 列出子表数据，分页上限）。

## 4. 验证记录

- M6 样例的每个迁移都引用存在的状态、M2、M3/M5；不可达引用校验失败。
- M7 样例不包含任意 SQL、数据库凭据或物理 DTO 映射。
- 无分页/上限的集合查询或越过声明数据范围的查询不能通过发布级校验。
- 命令：`git diff --check` 应通过。
