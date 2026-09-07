---
title: 定义 HITL 与行为执行语义
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 05-define-mi-integration-contract.md
  - 06-define-governed-query-and-data-scope.md
---

## 工作包目标

形成可直接指导实现与测试的 HITL 和行为执行规格：以统一风险分级决定行为是否只生成草稿、必须人工审批或允许受控执行；以稳定的 `ActionProposal`、`ApprovalToken`、状态机和不可变收据串联校验、影响预览、审批、执行、补偿与人工处置。规格必须坚持 DPA 是最终授权与持久化裁决者，模型不得接触 URL、HTTP Method、凭据、Header、任意 SQL 或内部 DTO 映射。

## 必需 Task

### [ ] T07.1 定义行为风险分级与执行模式判定

- **达成目标**：建立可机械判定的风险矩阵，将每个已发布 Behavior 分配为 `READ_ONLY`、`DRAFT_ONLY`、`APPROVAL_REQUIRED`、`PROHIBITED`，并明确无法证明纯读时按 `MIXED/HIGH` 处理；同时规定写表单呈现的机械路由：读取走 Agent UI 投影，简单写走自渲染表单或 HITL 受控执行，复杂表单走 Legacy View 草稿回填。
- **输入**：`docs/wayfinder/tickets/05-define-mi-integration-contract.md`、`docs/wayfinder/tickets/06-define-governed-query-and-data-scope.md`、已发布 Behavior 与 MI Schema。
- **执行步骤**：
  1. 按数据敏感度、副作用、可逆性、影响范围、授权强度和执行通道定义分级维度。
  2. 给出确定性的判定顺序、升级规则和禁止降级规则。
  3. 为 MasterData 的新增、修改、停用、批量操作和混合读写接口各给出判定案例。
  4. 规定风险级别、执行模式和审批要求在发布时固化，运行时只能收紧。
  5. 定义写表单机械路由与三项证据门槛：简单写行为只有同时满足“保存端点服务端校验闭包完整（T05.8）、无未处理客户端计算字段、M1/M2 字段闭包覆盖全部必填项”且存在已发布 MI，才允许进入 HITL 受控执行与自渲染表单；任一门槛不满足即机械落入草稿回填路径。
- **产出物**：`docs/specification/hitl/action-risk-classification.md`；`docs/specification/hitl/examples/masterdata-risk-cases.yaml`。
- **验证方式**：对样例 YAML 运行 `tools/validation/validate-action-risk-cases.*` 中定义的可重复校验命令；同一输入必须得到唯一风险级别，所有 `MIXED` 或证据不足案例必须落入 `APPROVAL_REQUIRED` 或 `PROHIBITED`；路由判定必须由证据门槛结论机械推导，缺失闭包证据即落回 `DRAFT_ONLY`。
- **边界**：不重新定义 DPA 业务权限，不允许用模型置信度降低风险等级。

### [ ] T07.2 定义 Action Proposal 契约

- **达成目标**：定义可版本化、可审计、与技术端点解耦的 `ActionProposal` Schema。
- **输入**：T07.1、工作包 03 的本体标识与版本规则、工作包 05 的 MI 映射契约。
- **执行步骤**：
  1. 定义 `proposal_id`、`behavior_id`、`subject`、`arguments`、`ontology_version`、`mi_version`、`risk_level`、`execution_mode`、`requested_by`、`created_at`、`expires_at` 等字段。
  2. 区分模型可提供字段、Gateway 派生字段和禁止由客户端覆盖字段。
  3. 规定敏感字段的遮蔽、摘要、引用和落盘规则。
  4. 定义 JSON Schema、版本兼容策略及至少一组有效与无效样例。
- **产出物**：`docs/specification/hitl/action-proposal-contract.md`；`models/schemas/runtime/action-proposal.schema.json`；`docs/specification/hitl/examples/action-proposals/`。
- **验证方式**：使用仓库既定 Schema 校验器验证全部正例通过、全部反例失败；反例必须覆盖伪造风险等级、未知 Behavior、过期版本和注入技术参数。
- **前置 Task**：T07.1。

### [ ] T07.3 规定校验顺序与影响预览

- **达成目标**：使每个提案在展示给审批人之前完成一致、可解释、无副作用的校验和影响预览。
- **输入**：T07.2、Behavior 参数约束、MI 契约、受治理查询与数据范围规则。
- **执行步骤**：
  1. 固定 Schema、引用版本、身份会话、候选对象范围、字段权限、业务前置条件、并发版本和执行通道的校验顺序。
  2. 定义 `ValidationIssue` 的稳定代码、严重度、字段路径和用户可读说明。
  3. 定义影响预览的受影响对象、字段差异、数量、不可逆影响、权限提示和数据新鲜度。
  4. 规定预览只使用受治理读取能力，任何预览失败不得回退为盲目执行。
- **产出物**：`docs/specification/hitl/proposal-validation-and-impact-preview.md`；`models/schemas/runtime/action-impact-preview.schema.json`；`docs/specification/hitl/examples/impact-previews/`。
- **验证方式**：以固定测试向量逐步重放校验；断言错误顺序、稳定错误码和预览摘要一致，并证明重放过程不产生 DPA 写入。
- **前置 Task**：T07.2。

### [ ] T07.4 定义 Approval Token 与审批约束

- **达成目标**：定义短期、单次消费、不可扩权并绑定具体提案快照的 `ApprovalToken`。
- **输入**：T07.2、T07.3、工作包 04 的身份与会话结论。
- **执行步骤**：
  1. 定义 `token_id`、`proposal_id`、提案内容摘要、审批人、审批范围、签发时间、过期时间、nonce、策略版本和签名信息。
  2. 规定审批人与请求人的职责分离、允许的自审批例外及高风险强制复核。
  3. 规定签发、校验、撤销、过期、单次原子消费和并发竞争行为。
  4. 定义提案变更、预览过期、权限变化和对象版本变化时 Token 失效规则。
  5. 规定实现机制基线：opaque 随机 Token + PostgreSQL 原子单次消费（服务端状态为唯一事实源）；如改用自包含签名 Token，必须证明撤销、单次消费和绑定校验语义不弱于该基线。
- **产出物**：`docs/specification/hitl/approval-token-contract.md`；`models/schemas/runtime/approval-token-claims.schema.json`；`docs/specification/hitl/examples/approval-token-cases.yaml`。
- **验证方式**：对有效、篡改、过期、重复消费、提案摘要不一致和并发双消费案例执行确定性测试；任何失败均不得进入执行适配器。
- **前置 Task**：T07.3。
- **边界**：Token 不携带 DPA 凭据，不替代 DPA 最终授权。

### [ ] T07.5 定义提案与执行状态机

- **达成目标**：建立无歧义的 `ProposalState` 与 `ExecutionState` 状态、事件、守卫条件和终态。
- **输入**：T07.2、T07.4。
- **执行步骤**：
  1. 定义提案从创建、校验、待审批、批准、拒绝、取消、过期到已消费的转换。
  2. 定义执行从排队、执行中、成功、失败、结果不确定、补偿中、已补偿、待人工处置到关闭的转换。
  3. 为每条转换指定触发者、前置条件、幂等键、持久化边界和审计事件。
  4. 规定重试、超时、进程重启、重复消息和乱序事件的处理方式。
- **产出物**：`docs/specification/hitl/action-state-machines.md`；`docs/specification/hitl/action-state-machines.mmd`；`docs/specification/hitl/examples/state-transition-cases.yaml`。
- **验证方式**：运行状态转换表测试，证明未列出的转换全部拒绝、终态不可回退、重复事件不产生第二次副作用。
- **前置 Task**：T07.4。

### [ ] T07.6 规定 Draft Application 流程（写入体验阶梯兑底路径 L1）

- **达成目标**：定义兑底写入路径（写入体验阶梯 L1）：生成并校验草稿，经 Agent UI 审核后应用到原 DPA 表单，由用户执行 DPA 原保存动作。该路径服务未通过 T07.1 三项证据门槛的写行为，不再是全部写行为的默认体验；通过门槛的简单写行为默认走 T07.5/T07.7 的 HITL 受控执行。
- **输入**：T07.1、T07.3、T07.5、工作包 05 的字段映射、DPA 目标页面预填能力证据。
- **执行步骤**：
  1. 实证 DPA 表单预填能力并固定结论：以源码/页面证据确认目标表单是否支持 URL 参数预填、暂存接口或受控回填；不可行时明确降级为“打开原页面 + 待填清单”，并写明该降级的影响评估方式。
  2. 定义 `DraftApplication` 的字段值、目标对象、来源提案、版本、校验结果和显示提示。
  3. 规定 Renderer 到 Legacy View 的安全传递方式、一次性引用、过期与重新校验。
  4. 规定字段映射失败、页面版本不兼容、用户无权限和原对象已变化时的阻断行为。
  5. 明确“应用草稿”不等于“已保存”，Gateway 不宣称业务写入成功。
- **产出物**：`docs/specification/hitl/draft-application-flow.md`；`models/schemas/runtime/draft-application.schema.json`；`docs/specification/hitl/examples/draft-application-cases.yaml`。
- **验证方式**：用 MasterData 样例重放“提案—审批—应用—用户保存/放弃”路径；断言应用前无业务写入，原 DPA 保存结果与平台状态明确区分；预填能力结论附证据引用，并覆盖“预填不可行”降级用例。
- **前置 Task**：T07.5。
- **边界**：不复制或替代复杂 DPA 表单，不绕过 DPA 原保存和授权机制。

### [ ] T07.7 规定 Gateway Execution、补偿与人工处置

- **达成目标**：为少量经批准的简单命令定义 Gateway 受控执行协议及失败闭环。
- **输入**：T07.1、T07.4、T07.5、工作包 05 的执行适配器契约。
- **执行步骤**：
  1. 定义准入条件、幂等键、并发控制、超时、重试预算和 DPA 响应归一化。
  2. 区分明确失败、明确成功和结果不确定，禁止对非幂等调用盲目重试。
  3. 为可补偿行为定义补偿命令、授权要求和补偿失败状态。
  4. 为不可补偿或结果不确定场景定义人工处置队列、所需证据、责任人和关闭条件。
- **产出物**：`docs/specification/hitl/gateway-execution-and-recovery.md`；`docs/specification/hitl/examples/gateway-execution-cases.yaml`；`docs/runbooks/action-manual-intervention.md`。
- **验证方式**：通过故障注入矩阵重放超时、重复请求、并发冲突、DPA 5xx、响应丢失和补偿失败；断言副作用次数、最终状态和人工处置入口符合规格。
- **前置 Task**：T07.5。
- **边界**：仅允许发布并评审通过的 Behavior/MI；不得由 Agent 构造端点、方法、Header 或凭据。

### [ ] T07.8 定义不可变执行收据与追踪闭环

- **达成目标**：定义从提案、审批、执行到补偿或人工关闭的不可变证据链。
- **输入**：T07.2 至 T07.7、工作包 12 的审计需求草案。
- **执行步骤**：
  1. 定义 `ActionReceipt` 的稳定标识、关联 ID、主体、版本、状态转换、时间戳、结果摘要和哈希链字段。
  2. 规定敏感值不进入收据正文，只保存脱敏摘要或受控引用。
  3. 规定追加写、禁止覆盖、保留期、查询权限和跨系统关联方式。
  4. 编制从 `proposal_id` 到 DPA 关联 ID、补偿记录和人工结论的追踪示例。
- **产出物**：`docs/specification/hitl/immutable-action-receipts.md`；`models/schemas/runtime/action-receipt.schema.json`；`docs/specification/hitl/examples/action-receipt-chain.jsonl`。
- **验证方式**：校验样例收据 Schema、哈希链连续性和必需关联；修改任一历史记录后完整性检查必须失败。
- **前置 Task**：T07.6、T07.7。

## 工作包验收

- T07.1 至 T07.8 的产出物均存在、互相引用且通过各自验证。
- 任一发布 Behavior 都能唯一确定风险等级、执行模式、审批要求及失败处置路径。
- `ActionProposal`、`ApprovalToken`、`DraftApplication`、`ActionReceipt` 的字段和版本关系不存在冲突。
- 状态机覆盖批准、拒绝、取消、过期、并发、幂等、重试、补偿和人工处置，非法转换有可重复的拒绝测试。
- MasterData 至少各有一条 Draft Application 与 Gateway Execution 完整追踪样例。
- 可证明 Agent 无法提供或覆盖 URL、HTTP Method、凭据、Header、任意 SQL、风险等级或授权结论。

## 解决记录

完成工作包时填写：

- **关闭日期**：
- **负责人**：
- **关键决策**：
- **产出物索引**：
- **验证命令与结果**：
- **遗留风险与后续工作包**：
