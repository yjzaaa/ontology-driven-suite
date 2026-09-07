# M3 Rule 与 M5 Actor/Permission 契约（T03.3 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.3 产出。
> 前置：T03.1、T01.2（model-boundary-matrix）。

## 1. M3 Rule 契约要点

- 表达可复用判断/派生约束；**不直接执行**状态修改（`AGENTS.md`）。
- 字段：`applies_to`（对象/行为）、`condition`（语义描述）、`result`、`severity`（`INFO`/`WARNING`/`BLOCK`）、`explanation`、`evidence_refs`。
- 纯 UI 格式校验（`DuplicateValidatorInfo`/`VarifyLists`）若不满足跨行为复用 + 业务不变量，不建模为 M3（T01.4 §3.2，TERM-007）。

## 2. M5 Actor/Permission 契约要点

- 表达角色、权限、数据范围；**不得**包含凭据、token 或绕过 DPA 授权的声明。
- 字段：`actors[]`、`permissions[]`、`data_scope`、`applies_to`（M2/M7 引用）、`authority_source`（`DPA`/`platform-policy`）。
- 权限来源不明的样例保持 `REVIEW_REQUIRED`，不发布为确定权限（边界 8）。

## 3. 样例

- `models/examples/masterdata/m3-rule.yaml`：`allow-update-rule`（禁止更新列表 → 该类型不允许更新，BLOCK）。
- `models/examples/masterdata/m5-actor-permission.yaml`：在线审批角色 + 更新行为权限（来源 DPA，待确认）。

## 4. 验证记录

- 有效样例通过对应 Schema；纯 UI 格式校验不会被错误建模为 M3。
- M5 样例不得包含凭据、token 或绕过 DPA 授权的声明。
- 权限来源不明的样例保持候选或审核状态。
- 命令：`git diff --check` 应通过。
