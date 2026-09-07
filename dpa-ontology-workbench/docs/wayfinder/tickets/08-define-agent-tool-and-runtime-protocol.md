---
title: 定义 Agent Tool 与运行时事件协议
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 03-define-ontology-contracts-and-lifecycle.md
  - 06-define-governed-query-and-data-scope.md
  - 07-define-hitl-and-action-execution.md
---

## 工作包目标

定义独立 Agent Runtime 与 Gateway 之间小而深、稳定且只表达业务语义的 Tool 集与运行时协议。Agent 只能发现和选择已发布对象、查询与行为，并提交结构化语义参数；Gateway 独占技术映射、授权、数据范围、审批与执行。协议必须覆盖 Schema、行为发现、上下文历史、运行时事件、错误、取消和可完整重放的端到端 transcript。

## 必需 Task

### [ ] T08.1 设计最小深 Tool 集与职责边界

- **达成目标**：用最少的稳定 Tool 覆盖发现、读取、查询、提案、审批后执行状态查询和取消，不为每个 DPA 端点创建 Tool。
- **输入**：工作包 03 的发布模型、工作包 06 的查询契约、工作包 07 的提案与执行契约。
- **执行步骤**：
  1. 按用户意图而非技术端点归并 Tool，形成候选清单。
  2. 为每个 Tool 定义单一职责、允许输入、返回语义和禁止能力。
  3. 评估新增对象、查询或 Behavior 是否无需新增 Tool 即可暴露。
  4. 明确 Gateway 内部能力与 Agent 可见能力的边界。
- **产出物**：`docs/specification/agent-tools/minimal-toolset.md`；`docs/specification/agent-tools/tool-capability-matrix.yaml`。
- **验证方式**：用 MasterData 的对象发现、集合查询、详情读取、创建修改提案、状态跟踪和取消场景逐项映射；每个场景有且仅有明确 Tool 组合，任何 Tool 都不接受 URL、HTTP Method、凭据、Header 或 SQL。
- **边界**：不暴露 MI、路由表、数据库结构、内部 DTO 或授权实现细节。

### [ ] T08.2 定义 Tool Schema 与版本兼容规则

- **达成目标**：为最小 Tool 集建立机器可校验、面向语义 ID 的输入输出 Schema。
- **输入**：T08.1、工作包 03 的稳定 ID 和发布版本规则。
- **执行步骤**：
  1. 定义每个 Tool 的名称、描述、输入、输出、分页、排序、过滤、引用和 artifact 字段。
  2. 区分 Agent 提供字段、Gateway 注入字段和只读返回字段。
  3. 规定未知字段、未知 ID、Schema 版本不匹配和弃用版本的处理。
  4. 为每个 Tool 编制有效样例和安全反例。
- **产出物**：`models/schemas/tools/`；`docs/specification/agent-tools/tool-schema-contract.md`；`docs/specification/agent-tools/examples/tool-calls/`。
- **验证方式**：运行仓库 Schema 校验命令，断言正例全部通过、反例全部失败；反例覆盖技术参数注入、越权字段、任意 SQL 和未发布 ID。
- **前置 Task**：T08.1。

### [ ] T08.3 定义对象、查询与行为发现协议

- **达成目标**：让 Agent 在不读取完整内部模型的前提下发现当前用户可见、可用且已发布的语义能力。
- **输入**：T08.2、Registry 投影、用户身份与数据范围上下文。
- **执行步骤**：
  1. 定义按领域、对象类型、意图关键词和能力类型发现的请求。
  2. 定义返回的稳定 ID、名称、用途、参数摘要、风险、执行模式和版本。
  3. 规定基于当前用户权限、租户、发布状态和功能开关的过滤顺序。
  4. 规定无匹配、多匹配、能力撤回和会话中版本变化时的行为。
  5. 规定发现匹配机制的实现边界：第一阶段使用词法与结构化匹配（如 BM25、PostgreSQL 全文检索）；引入向量检索前必须证明词法匹配无法满足召回要求，且嵌入索引不得携带敏感业务数据。
- **产出物**：`docs/specification/agent-tools/capability-discovery.md`；`models/schemas/tools/capability-discovery.schema.json`；`docs/specification/agent-tools/examples/discovery-cases.yaml`。
- **验证方式**：以不同用户和发布版本运行固定发现用例；断言不可见能力不泄露、撤回能力不可继续选择、相同上下文返回稳定排序。
- **前置 Task**：T08.2。

### [ ] T08.4 定义上下文、历史与 artifact 边界

- **达成目标**：规定运行时哪些信息进入模型上下文、会话历史、服务端状态或外部 artifact，避免敏感数据和大型结果无界复制。
- **输入**：T08.2、T08.3、工作包 04 的身份边界、工作包 06 的数据投影规则。
- **执行步骤**：
  1. 分类系统指令、用户消息、Tool 调用、Tool 结果、对象引用、提案引用和 artifact 元数据。
  2. 定义最大大小、截断、摘要、分页、过期、脱敏和重新获取规则。
  3. 规定历史重放时身份、权限、对象版本和能力版本必须重新校验的内容。
  4. 禁止凭据、会话 Token、内部端点、原始敏感字段和完整大型结果进入模型历史。
- **产出物**：`docs/specification/agent-runtime/context-history-and-artifacts.md`；`models/schemas/runtime/artifact-reference.schema.json`；`docs/specification/agent-runtime/examples/context-boundary-cases.yaml`。
- **验证方式**：对超大结果、敏感字段、过期 artifact、权限变化和会话恢复执行固定用例；检查 transcript 中不存在禁止内容且引用可按规则重新解析。
- **前置 Task**：T08.2。

### [ ] T08.5 定义运行时事件与执行状态更新

- **达成目标**：定义传输无关的事件模型及 Socket.IO 映射，使 UI 可可靠呈现消息、Tool、artifact、提案与执行进度。
- **输入**：T08.4、工作包 07 的状态机。
- **执行步骤**：
  1. 定义统一事件信封：`event_id`、`conversation_id`、`turn_id`、`correlation_id`、`sequence`、`type`、`occurred_at`、`payload`、`schema_version`。
  2. 定义消息增量、Tool 开始/完成、artifact 可用、提案更新、审批更新、执行更新和终止事件。
  3. 规定顺序、重复投递、断线续传、缺口检测、心跳和快照恢复。
  4. 给出领域事件到 Socket.IO event name 的映射，同时保持核心协议不依赖 Socket.IO。
- **产出物**：`docs/specification/agent-runtime/runtime-event-protocol.md`；`models/schemas/runtime/events/`；`docs/specification/agent-runtime/socketio-event-mapping.yaml`。
- **验证方式**：重放包含重复、乱序、断线和恢复的事件夹具；最终 UI 状态必须确定且与服务端快照一致。
- **前置 Task**：T08.4。

### [ ] T08.6 定义错误、超时与取消协议

- **达成目标**：建立跨 Tool 和运行时的一致错误分类、可重试提示与取消语义。
- **输入**：T08.2、T08.5、工作包 07 的失败状态。
- **执行步骤**：
  1. 定义校验、认证、授权、未找到、冲突、限流、超时、依赖失败、结果不确定和内部错误代码。
  2. 为每类错误定义用户可见消息、模型可见详情、可重试标志、关联 ID 和敏感信息过滤。
  3. 规定 turn、Tool 调用、提案等待和执行请求各自可取消的阶段与不可取消边界。
  4. 规定取消竞争、迟到结果、取消失败和 Gateway Execution 已产生副作用时的状态。
- **产出物**：`docs/specification/agent-runtime/errors-timeouts-and-cancellation.md`；`models/schemas/runtime/runtime-error.schema.json`；`docs/specification/agent-runtime/examples/error-cancellation-cases.yaml`。
- **验证方式**：运行错误映射与取消竞争测试；每个依赖错误映射到唯一稳定代码，取消不得把已产生副作用的执行误报为未执行。
- **前置 Task**：T08.5。

### [ ] T08.7 定义运行时安全与协议一致性检查

- **达成目标**：把“模型只选择业务语义、Gateway 掌握技术执行”转化为可自动检查的协议约束。
- **输入**：T08.1 至 T08.6、工作包 05 至 07 的安全边界。
- **执行步骤**：
  1. 建立 Tool 输入与事件 payload 的禁止字段清单和嵌套字段检测规则。
  2. 定义仅允许已发布稳定 ID、枚举和 Schema 字段的 allowlist 校验。
  3. 规定 prompt injection、越权引用、伪造审批、版本降级和 artifact 猜测的拒绝行为。
  4. 编制可持续加入 CI 的协议一致性测试清单。
- **产出物**：`docs/specification/agent-runtime/protocol-security-invariants.md`；`tools/validation/fixtures/agent-protocol-negative-cases/`；`docs/specification/agent-runtime/protocol-conformance-suite.md`。
- **验证方式**：对负面夹具运行一致性测试；全部攻击输入必须在进入 Registry、Query 或 Execution 适配器前被拒绝并产生稳定审计事件。
- **前置 Task**：T08.6。

### [ ] T08.8 制作端到端 transcript 与可重放验收夹具

- **达成目标**：用完整 transcript 证明 Tool、上下文、事件、HITL、错误和取消协议可以协同工作。
- **输入**：T08.2 至 T08.7、MasterData 参考场景。
- **执行步骤**：
  1. 制作对象查询、Draft Application、Gateway Execution、审批拒绝、执行超时和用户取消六类 transcript。
  2. 每条记录包含用户消息、模型 Tool 选择、Tool 输入输出、事件序列、artifact、状态变化和最终用户呈现。
  3. 对敏感值脱敏，并保留稳定 ID、sequence、correlation_id 和 Schema 版本。
  4. 定义 transcript 重放器所需输入、期望状态和断言。
- **产出物**：`docs/specification/agent-runtime/transcripts/`；`docs/specification/agent-runtime/end-to-end-transcript-guide.md`；`tools/validation/fixtures/runtime-transcripts/`。
- **验证方式**：按指南重放全部 transcript；断言事件顺序、最终状态、错误代码、artifact 引用和安全不变量均与期望一致。
- **前置 Task**：T08.7。

### [ ] T08.9 验证并固化 Agent 编排框架

- **达成目标**：以“自主实现 Agent Runtime 与 Agent UI、LangGraph 作为 Agent 编排层、FastAPI/Pydantic 作为语义 Tool Gateway”为首选基线，通过最小 PoC 验证后形成正式选型结论，并同步固化 LLM 模型与供应商矩阵。
- **输入**：T08.1 至 T08.8 的 Tool、上下文、事件、错误和 transcript 契约；[技术选型基线](../../architecture/technology-selection/baseline.md)；独立 Agent Runtime 对模型接入、会话、流式输出、人工中断和恢复的要求；LangGraph、Semantic Kernel、AutoGen、PydanticAI 等候选框架的官方资料。
- **执行步骤**：
  1. 建立独立 Python Agent Runtime PoC，验证 LangGraph 与自研 Agent UI、Gateway 和模型供应商适配层的集成方式。
  2. 使用同一组对象查询、行为提案、审批等待、断线恢复和取消场景比较候选框架。
  3. 重点验证结构化 Tool 调用、持久化 checkpoint、人工中断与恢复、流式事件、可观测性、测试隔离、模型供应商解耦和许可证。
  4. 明确 LangGraph 只负责任务编排和 Tool 调用顺序，不拥有业务权限、MI 解析、审批 Token、执行状态或业务事务。
  5. 将 Proposal、Approval、Execution 和审计状态保存在平台权威服务中；不得只保存在 LangGraph 内存或会话 checkpoint。
  6. 记录首选、备选、淘汰理由、版本锁定、升级策略和框架替换接口；框架专有对象不得泄漏到 Tool、事件和持久化领域契约。
  7. 固化 LLM 模型与供应商矩阵：分别确定对话主模型、构建期候选起草模型（OAG 查询生成与 MU 起草）和多模态辅助模型，验证 Tool 调用的结构化输出（JSON Schema 约束 / function calling）在主候选模型上稳定，并记录内网部署、国产化与成本约束下的供应商切换边界；供应商替换不得改变 Tool 协议与 Tool Schema。
  8. 将框架与模型选型结论形成 ADR。
- **产出物**：`docs/architecture/technology-selection/agent-framework-options.md`；`docs/architecture/technology-selection/agent-framework-poc.md`；`docs/architecture/technology-selection/llm-provider-matrix.md`；`docs/adr/ADR-agent-orchestration-framework.md`；可重放 PoC transcript。
- **验证方式**：首选方案必须完整重放 T08.8 的关键 transcript，并证明进程重启后能从平台权威状态恢复；替换模型供应商不改变 Tool 协议；关闭 LangGraph checkpoint 不会丢失 Proposal、Approval、Execution 或审计事实；主候选模型对全部 Tool Schema 的结构化输出调用通过规定阈值测试。
- **前置 Task**：T08.8。
- **边界**：不采用 AutoGen/CrewAI 式自治多 Agent 作为默认架构；不依赖或复用 InsightBot；不允许 Agent 框架直接调用 DPA 技术端点、持有 DPA 凭据或替代 Policy/HITL 状态机。

## 工作包验收

- T08.1 至 T08.9 的产出物全部存在并通过可重复验证。
- 新增已发布对象、查询或 Behavior 时，在不新增专用 Tool 的情况下可通过发现协议使用。
- 所有 Tool Schema、运行时事件、错误和 artifact 引用均有版本规则、正例与反例。
- 断线、重复、乱序、超时和取消场景可确定性恢复，不会误报执行结果。
- 至少六条 MasterData transcript 可从用户意图重放到最终 UI 状态和审计关联。
- 自动检查证明 Agent 无法提交 URL、HTTP Method、凭据、Header、任意 SQL、内部 DTO 映射或伪造审批信息。
- Agent 编排框架有可重放 PoC 和正式 ADR，且框架状态不成为业务提案、审批、执行或审计的唯一事实源。

## 解决记录

完成工作包时填写：

- **关闭日期**：
- **负责人**：
- **关键决策**：
- **产出物索引**：
- **验证命令与结果**：
- **遗留风险与后续工作包**：
