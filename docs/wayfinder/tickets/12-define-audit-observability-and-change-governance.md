---
title: 定义审计、可观测性与变更治理
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 02-specify-reverse-engineering-evidence-pipeline.md
  - 03-define-ontology-contracts-and-lifecycle.md
  - 05-define-mi-integration-contract.md
  - 07-define-hitl-and-action-execution.md
---

## 工作包目标

建立可解释、可关联、可查询且可执行阻断的审计与可观测性规范，使每次扫描、模型发布、查询、行为提案、审批、执行和 DPA 交接都能追踪到主体、来源证据、模型版本、策略裁决和结果。规范同时覆盖日志、Trace、指标、脱敏保留、源码与模型变更治理、`REVIEW_REQUIRED` 强制阻断、审计查询和事故响应。

## 必需 Task

### [ ] T12.1 定义全链路关联 ID

**达成目标**

定义跨 Scanner、Validator、Registry、Gateway、独立 Agent Runtime、Agent UI、MI 和 DPA 的关联标识，使一次用户意图及其派生活动能够可靠串联。

**输入**

- 工作包 02、03、05、07 定义的证据、模型、MI、提案和执行实体
- 工作包 08 的 Tool 与运行时事件协议
- 各实体已有稳定 ID 和版本字段

**执行步骤**

1. 盘点 `request_id`、`trace_id`、`session_id`、`actor_id`、模型稳定 ID、模型版本、`proposal_id`、`approval_id`、`execution_id`、证据 ID 和 DPA 业务对象 ID。
2. 定义每个 ID 的生成方、格式、作用域、生命周期、可否跨信任边界传播和禁止复用条件。
3. 定义父子关系、因果关系及批处理中的多对多关联表达。
4. 明确哪些 ID 可进入日志、审计事件、Trace baggage、用户界面和 DPA 请求。
5. 给出查询链路、草稿应用链路和 Gateway 执行链路的完整示例。

**产出物**

- `docs/architecture/governance/correlation-identifiers.md`
- `docs/architecture/governance/correlation-examples.yaml`

**验证方式**

从三个示例链路的任一 `request_id` 或 `execution_id` 出发，均能反向定位主体、模型版本、提案或查询、策略裁决、MI 调用和最终结果；不存在把敏感 token 当作关联 ID 的设计。

### [ ] T12.2 定义审计事件契约与不可变回执

**前置 Task**

- T12.1

**达成目标**

定义覆盖关键决策和状态变化的审计事件，确保查询与行为可解释、审批与执行不可抵赖，并能生成不可变回执。

**输入**

- 关联 ID 规范
- 模型发布、查询、Action Proposal、HITL 和执行状态机
- DPA 草稿应用与 Gateway 执行两类路径

**执行步骤**

1. 建立扫描、候选生成、校验、审核、发布、查询、策略裁决、提案、审批、执行、草稿应用和 DPA 响应事件目录。
2. 为每类事件定义稳定事件名、版本、发生时间、主体、对象、关联 ID、输入摘要、裁决、结果和错误字段。
3. 区分业务审计事件、系统运行事件和不可变执行回执。
4. 定义事件顺序、重复投递、幂等记录、时钟偏差和 Schema 演进规则。
5. 明确失败、拒绝、取消、过期和未知结果必须记录，不得只记录成功事件。

**产出物**

- `docs/architecture/governance/audit-event-catalog.yaml`
- `docs/architecture/governance/audit-receipt-schema.yaml`
- `docs/architecture/governance/audit-event-rules.md`

**验证方式**

用正常查询、被拒查询、草稿应用、批准后执行、重复执行阻断和未知 DPA 结果六个场景生成事件序列；序列均满足 Schema，能够解释“谁在何时依据哪个模型和策略做了什么以及结果如何”。

### [ ] T12.3 定义日志、Trace 与指标规范

**前置 Task**

- T12.1
- T12.2

**达成目标**

建立统一的结构化日志、分布式 Trace 和指标目录，使运行故障、性能退化和治理异常可检测且可定位。

**输入**

- 关联 ID 与审计事件契约
- 平台模块接口和预期运行链路

**执行步骤**

1. 定义结构化日志公共字段、级别、错误码和禁止记录内容。
2. 为查询、模型加载、策略裁决、MI 调用、HITL 和 DPA 交接定义 Span 边界与属性。
3. 定义吞吐、延迟、错误率、拒绝率、过期提案、重复消费阻断、模型版本滞后和扫描覆盖率指标。
4. 为关键指标定义单位、标签基数限制、聚合窗口、告警条件和责任人。
5. 明确审计事件不能仅由普通日志替代，指标不得携带业务对象明细或个人信息。

**产出物**

- `docs/architecture/observability/logging-standard.md`
- `docs/architecture/observability/trace-conventions.yaml`
- `docs/architecture/observability/metric-catalog.yaml`

**验证方式**

使用固定的查询与执行场景生成示例日志、Trace 和指标；三类信号可通过 `trace_id` 或稳定 ID 交叉定位，指标标签基数有上限，日志中不出现凭据、完整请求体或未脱敏业务数据。

### [ ] T12.4 制定脱敏、访问控制与保留策略

**前置 Task**

- T12.2
- T12.3

**达成目标**

按数据敏感度定义采集最小化、字段脱敏、访问授权、保留期限、归档和删除规则，使审计可用性与隐私、安全要求兼容。

**输入**

- 审计事件、日志、Trace、指标和不可变回执字段
- 身份、业务对象、提案和 DPA 响应中的敏感数据分类

**执行步骤**

1. 对所有可观测与审计字段进行公开、内部、敏感和禁止采集分类。
2. 为敏感字段定义删除、掩码、哈希、令牌化或受控明文策略。
3. 定义按数据类别和环境区分的在线保留、归档保留与删除期限。
4. 定义审计查询权限、紧急访问、访问留痕和导出限制。
5. 设计删除与法律保留冲突、主体 ID 失效和不可变回执最小保留的处理方式。

**产出物**

- `docs/architecture/governance/data-redaction-matrix.yaml`
- `docs/architecture/governance/retention-and-access-policy.md`

**验证方式**

使用包含 token、Header、个人标识、业务字段和错误堆栈的合成样例执行字段级审查；禁止字段全部不落库，敏感字段按矩阵处理，每类数据均有可执行的保留期限和访问角色。

### [ ] T12.5 定义源码与证据变更治理

**前置 Task**

- T12.1
- T12.2

**达成目标**

将 DPA 源码变化、扫描覆盖变化和证据差异转换为可归属、可评审的治理信号，及时识别可能失效的本体与集成映射。

**输入**

- 工作包 02 的扫描、增量变更和覆盖率规则
- 已发布模型中的源码证据引用
- MI 映射与所有者信息

**执行步骤**

1. 定义源码 revision、扫描批次、证据 ID、覆盖率和模型稳定 ID 的关联方式。
2. 分类新增、修改、删除、无法解析和覆盖率下降等变更信号。
3. 建立从变更信号到受影响模型、查询、行为、MI 映射和责任人的影响分析。
4. 定义误报确认、重新扫描、补证和升级评审流程。
5. 明确源码变化不得直接修改或发布本体，只能产生候选与治理状态变化。

**产出物**

- `docs/architecture/governance/source-change-governance.md`
- `docs/architecture/governance/source-change-cases.yaml`

**验证方式**

对控制器删除、DTO 字段变更、授权过滤器变化、扫描失败和覆盖率下降五个固定案例执行影响分析；每个案例均能定位受影响资产、责任人和下一步动作，且不会自动发布模型。

### [ ] T12.6 定义模型变更评审与 `REVIEW_REQUIRED` 强制阻断

**前置 Task**

- T12.2
- T12.5

**达成目标**

定义模型差异的风险分级、评审状态和运行时阻断机制，确保过期、失配或高风险变更在重新审核前不能执行。

**输入**

- 工作包 03 的模型版本与发布生命周期
- 工作包 05、07 的 MI、风险和执行规则
- 源码变更影响分析

**执行步骤**

1. 定义触发 `REVIEW_REQUIRED` 的条件，包括证据失效、MI 失配、授权语义变化、风险升级和不可兼容模型变更。
2. 定义状态写入责任、传播路径、缓存失效和运行时读取一致性要求。
3. 规定 Registry、Gateway 和 Agent Tool 在 `REVIEW_REQUIRED` 下允许的只读能力和禁止的执行能力。
4. 定义人工解除阻断所需的补证、校验、批准、模型版本和审计事件。
5. 设计缓存旧模型、并发请求、阻断传播延迟和解除后重试场景。

**产出物**

- `docs/architecture/governance/model-change-review.md`
- `docs/architecture/governance/review-required-cases.yaml`

**验证方式**

逐一运行 `review-required-cases.yaml` 的触发、传播、并发、缓存和解除场景；任何受影响行为在阻断解除前均返回稳定拒绝结果并产生审计事件，且不能通过旧缓存、重试或换入口绕过。

### [ ] T12.7 设计审计查询与治理视图

**前置 Task**

- T12.1
- T12.2
- T12.4
- T12.6

**达成目标**

定义安全、可重复的审计查询和治理视图，使授权用户能回答关键追责问题而不接触任意 SQL 或越权数据。

**输入**

- 关联 ID、审计事件、回执、脱敏和访问策略
- `REVIEW_REQUIRED` 状态与源码变更信号

**执行步骤**

1. 定义按时间、主体、模型版本、业务对象、`proposal_id`、`execution_id`、结果和治理状态筛选的查询契约。
2. 定义查询范围、分页、导出、超限、超时和权限裁剪行为。
3. 设计“解释一次查询”“解释一次行为”“查看模型变更影响”“查看阻断原因”四类固定视图。
4. 定义结果中的脱敏、证据链接、事件顺序和不可变回执校验信息。
5. 建立最小审计查询测试集，覆盖正常、无权限、已脱敏、数据已归档和关联链断裂。

**产出物**

- `docs/architecture/governance/audit-query-contract.yaml`
- `docs/architecture/governance/audit-query-cases.yaml`
- `docs/architecture/governance/audit-views.md`

**验证方式**

对测试集执行预期结果比对；授权用户可回答谁、何时、基于何版本、作出何裁决和结果如何，未授权用户无法通过筛选、导出或关联 ID 推断被保护数据。

### [ ] T12.8 制定事故响应与证据保全手册

**前置 Task**

- T12.3
- T12.4
- T12.6
- T12.7

**达成目标**

建立针对越权查询、错误执行、审计缺口、模型陈旧和敏感数据泄漏的检测、控制、调查、恢复和复盘流程。

**输入**

- 日志、Trace、指标和告警定义
- 审计查询与访问策略
- `REVIEW_REQUIRED` 阻断机制
- 模型与源码变更治理规则

**执行步骤**

1. 定义事故分级、触发条件、初始响应时限和升级路径。
2. 为五类事故编写检测、立即控制、证据保全、影响评估、恢复和通知步骤。
3. 定义冻结模型、撤销批准、阻断行为、轮换秘密和切换只读模式的授权责任。
4. 明确证据导出、哈希校验、访问留痕和保管链要求。
5. 执行一次“陈旧 MI 映射仍被调用”和一次“日志泄漏敏感字段”的桌面演练。

**产出物**

- `docs/operations/incident-response.md`
- `docs/operations/incident-playbooks/`
- `docs/operations/incident-exercise-report.md`

**验证方式**

两次桌面演练均能在规定时限内定位关联链、触发控制措施、保存证据并给出恢复条件；报告记录时间线、责任人、缺口和改进项，且事故处置不依赖任意数据库写入或关闭审计。

## 工作包验收

- 查询、提案、审批、执行、草稿应用、模型发布和源码变更均可通过关联 ID 串联。
- 审计事件覆盖成功、失败、拒绝、取消、过期、重复和未知结果，并具有版本化 Schema。
- 日志、Trace 和指标职责清晰、可交叉定位，且与不可变审计回执分离。
- 脱敏、访问和保留策略覆盖全部采集字段，不记录凭据或不必要的业务明细。
- 源码与模型变化能够触发影响分析、责任分配和可审计评审。
- `REVIEW_REQUIRED` 在 Registry、Gateway 和 Agent Tool 各入口均为强制阻断，无法通过缓存或重试绕过。
- 固定审计查询能够解释关键业务链路，事故手册已经过至少两次可重复桌面演练。

## 解决记录

> 工作包关闭时填写，只记录最终结论、关键取舍、验证结果和资产链接。

- 最终结论：待完成。
- 关键取舍：待完成。
- 验证结果：待完成。
- 资产链接：待完成。
