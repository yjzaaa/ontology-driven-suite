# 自动提取与人工审核边界（T02.8 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.8 产出。
> 任务：明确哪些结论可自动接受、哪些必须人工确认、哪些证据不足时必须阻断，并形成可审计的审核队列契约。
> 前置：T02.3–T02.7。

## 1. 审核决策表

| 结论类型 | 证据等级 | 覆盖率 | 动态特征 | 副作用 | 判定 |
|---|---|---|---|---|---|
| 源码符号存在性 | FACT | — | 否 | — | 自动接受 |
| 调用边（静态可解析） | FACT/INFERENCE | 高 | 否 | — | 自动接受 |
| 路由映射 | FACT（Roslyn 补证） | 高 | 否 | — | 自动接受 |
| 分派结论 | INFERENCE | 中 | 工厂/字典 | — | 人工确认 |
| 读写分类 | INFERENCE | 中 | 否 | 纯写 | 人工确认（写） |
| 动态 SQL / 反射 | ASSUMPTION/GAP | 低 | 是 | — | 阻断 |
| 混合副作用 | MIXED/HIGH | — | — | 写+缓存/日志 | 阻断自动执行 |
| 权限归属 | INFERENCE | 低 | — | — | 人工确认 |
| 动态 UI 绑定 | GAP | 低 | 是 | — | 阻断 |

## 2. 审核项字段与状态机

- 审核项字段：`review_item_id`、`conclusion_type`、`evidence_ids`、`state`、`assigned_role`、`decision`、`decision_by`、`decision_at`、`basis_evidence_ids`。
- 状态机：`pending` → `accepted` / `corrected` / `rejected` → （重新打开 `reopened`）。
- 分派：按 `assigned_role`（DPA 技术负责人 / 领域本体审核员 / 安全与数据负责人 / 发布审批人）路由（T02.9）。

## 3. 人工裁决约束

- 人工裁决**不得覆盖原始证据**：只能追加带身份和时间的决策记录（`decision_by` + `decision_at` + `basis_evidence_ids`），原始 `FACT` 不可被改写。
- 机器证据、审核结果和候选 YAML 均不授予运行执行权。

## 4. 五类高风险样例

| 高风险类型 | 样例 | 路由 |
|---|---|---|
| 动态 SQL | `MobileHaasJob` 的 `insert into ... select`（已解析为 FACT，但跨库） | 阻断自动执行 → 人工确认写副作用 |
| 反射调用 | 未发现；按规则反射一律阻断 | 阻断 |
| UI 动态绑定 | `gridwidget.cshtml` 运行时 push 列 | 阻断 → 人工补证 |
| 混合副作用 | `UpdateSubtableData`（写+缓存+日志） | 阻断自动执行（MIXED/HIGH） |
| 权限不明 | `GetUserByToken` 相关授权 | 人工确认权限归属 |

以上五类均稳定路由到人工审核或阻断，不会自动升级为已确认事实。

## 5. 审核队列契约（Schema 与样例）

- Schema：`schemas/evidence/review-item.schema.json`（见本工作包产出）。
- 样例：`evidence/examples/masterdata-review-queue.json`。
- 接受、修正和拒绝操作均保留操作者、理由、时间和所依据的证据 ID。

## 6. 验证记录

- 五类高风险样例均被稳定路由到人工审核或阻断，不会自动升级为已确认事实。
- 接受、修正和拒绝操作均保留操作者、理由、时间和所依据的证据 ID。
- 文档明确机器证据、审核结果和候选 YAML 均不授予运行执行权。
- 命令：`git diff --check` 应通过。
