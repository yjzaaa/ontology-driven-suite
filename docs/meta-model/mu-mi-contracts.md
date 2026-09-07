# MU Presentation 与 MI Integration 契约（T03.5 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.5 产出。
> 前置：T03.1、T03.2、T03.4、T01.5（runtime-concept-boundaries）。

## 1. MU Presentation 契约要点

- 表达绑定对象/查询、视图结构、字段展示、交互意图与 Legacy View 回退；**不**成为新业务事实源（T01.5）。
- 字段：`binds`（M1/M2/M7 引用）、`view_structure`、`fields[]`、`intent`（`view`/`edit`/`import`/`legacy`）、`legacy_fallback`。
- MU 只能引用已声明的 M1/M2/M7 字段和意图。

## 2. MI Integration 契约要点

- 表达所绑定 M2/M7 与 DPA endpoint 或只读 Database MCP 能力的技术映射；**隐藏** URL、HTTP Method、Header、Cookie、DTO 技术细节（边界 3）。
- 字段：`binds`（M2/M7 语义引用）、`target_kind`（`dpa-http`/`database-mcp-readonly`）、`fixed_params`、`forbidden_params`、`side_effect_level`、`timeout`、`retry_policy`、`idempotent`、`error_map`、`credential_policy`（只描述来源/转发策略，不包含真实值）、`evidence_refs`。
- 凭据只描述来源或转发策略，不包含真实值；Database MCP 映射只能声明只读能力。
- `MIXED/HIGH` 或无法证明纯读的样例必须要求人工审核，不能声明自动执行。

## 3. 样例

- `models/examples/masterdata/mu-presentation.yaml`：`subtable-grid-view`（绑定 M7 列表查询，`view` 意图，Legacy 回退）。
- `models/examples/masterdata/mi-integration.yaml`：`mi-update-subtable`（绑定 M2 `update-subtable-data`，`dpa-http`，MIXED/HIGH，禁自动执行）。

## 4. 验证记录

- MU 只能引用已声明的 M1/M2/M7 字段和意图，不成为新的业务事实源。
- MI 中凭据只描述来源或转发策略，不包含真实值；Database MCP 映射只能声明只读能力。
- `MIXED/HIGH` 或无法证明纯读的样例必须要求人工审核，不能声明自动执行。
- 命令：`git diff --check` 应通过。
