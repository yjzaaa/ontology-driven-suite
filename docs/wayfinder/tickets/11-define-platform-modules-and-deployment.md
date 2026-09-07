---
title: 定义平台模块、仓库边界与部署
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 04-define-identity-session-and-authorization.md
  - 05-define-mi-integration-contract.md
  - 08-define-agent-tool-and-runtime-protocol.md
---

## 工作包目标

把 Scanner、Candidate Generator、Validator、Registry、Gateway、独立 Agent Runtime、Agent UI、Studio 和 Explorer 划分为职责清晰的深模块，确定模块接口、持久化责任、仓库构建边界、同源试点部署、配置与秘密、高可用故障域以及运维发布责任。最终方案必须保持各模块通过稳定协议协作，并确保所有业务写入仍由 DPA 原 HTTP/业务层路径完成。

## 必需 Task

### [ ] T11.1 定义深模块职责与不变量

**达成目标**

为每个模块建立单一、稳定且可测试的职责边界，避免界面层、治理层、运行时和 DPA 集成相互泄漏实现细节。

**输入**

- `README.md` 的规划目录与项目边界
- 工作包 04、05、08 的身份、MI 和运行时协议结论
- Scanner、Candidate Generator、Validator、Registry、Gateway、独立 Agent Runtime、Agent UI、Studio 和 Explorer 模块清单

**执行步骤**

1. 为每个模块定义主要职责、拥有的数据、允许的依赖和禁止承担的职责。
2. 标出编译期、发布期和运行期模块，并定义各阶段不变量。
3. 明确 `models/<domain>/` 已发布 YAML 是运行时唯一语义来源。
4. 明确 Scanner 证据和候选模型不授予执行权，Studio 与 Explorer 不直接访问 DPA 数据库。
5. 用至少三个跨边界反例验证职责是否足以拒绝错误设计。

**产出物**

- `docs/architecture/platform/module-responsibilities.md`
- `docs/architecture/platform/module-invariants.yaml`

**验证方式**

对每个模块执行“职责归属”表格检查；任一能力只能有一个最终责任模块，所有跨边界反例都能由明确不变量拒绝，且不存在 Agent UI 持有本体发布或执行策略的设计。

### [ ] T11.2 定义模块接口与依赖方向

**前置 Task**

- T11.1

**达成目标**

定义模块之间的稳定接口、调用方向、错误语义和版本兼容规则，使内部实现可以独立替换。

**输入**

- `docs/architecture/platform/module-responsibilities.md`
- 工作包 05、08 定义的 MI、Tool 和运行时事件协议

**执行步骤**

1. 列出模块提供和消费的 API、命令、事件、文件契约及批处理入口。
2. 为每个接口定义调用方、提供方、同步或异步模式、认证上下文、幂等要求和错误分类。
3. 区分公开稳定协议、仓库内部接口和构建期文件交换。
4. 定义版本协商、向后兼容窗口和不兼容变更处理方式。
5. 绘制依赖方向图并检查是否存在循环依赖。

**产出物**

- `docs/architecture/platform/module-interfaces.md`
- `docs/architecture/platform/module-dependencies.mmd`
- `docs/architecture/platform/interface-catalog.yaml`

**验证方式**

使用 `interface-catalog.yaml` 逐项检查调用双方和版本策略；依赖图无循环，且独立 Agent Runtime 与 Agent UI 只依赖稳定语义 Tool/API，不依赖 Registry、模型存储或治理内部接口。

### [ ] T11.3 分配持久化责任与数据生命周期

**前置 Task**

- T11.1
- T11.2

**达成目标**

明确证据、候选模型、已发布模型、运行时索引、提案、审批、审计和界面偏好的存储归属、保留规则和恢复责任。

**输入**

- 模块职责与接口目录
- 工作包 03、07 的模型生命周期和 HITL 状态
- `README.md` 中 `evidence/`、`models/`、`gateway/` 等边界

**执行步骤**

1. 建立数据资产到唯一写入责任模块的映射。
2. 定义事实源、派生数据、缓存和可重建索引，禁止多个事实源并存。
3. 记录事务边界、一致性要求、备份恢复点目标和数据迁移责任。
4. 明确 Database MCP 只读，业务数据写入只经 DPA 原路径。
5. 定义模型发布、回滚和运行时索引重建之间的一致性规则。

**产出物**

- `docs/architecture/platform/persistence-ownership.md`
- `docs/architecture/platform/data-lifecycle.yaml`

**验证方式**

对每类数据执行唯一写入者检查和恢复演练桌面推演；任一资产均可回答“谁写入、谁读取、事实源在哪、如何恢复”，且不存在平台直接写 DPA 数据库的路径。

### [ ] T11.4 确定仓库与构建边界

**前置 Task**

- T11.2
- T11.3

**达成目标**

确认独立平台仓库的目录、可独立构建单元、共享契约发布方式和质量门禁，避免通过源码引用把 Agent Runtime、Agent UI 或 DPA 与治理模块耦合。

**输入**

- `README.md` 的规划目录
- 模块依赖与持久化责任
- 工作包 08 的协议产物

**执行步骤**

1. 将模块映射到仓库目录、项目或包，并标出独立构建和部署单元。
2. 定义共享 Schema、生成客户端和测试夹具的存放与版本发布方式。
3. 规定禁止的跨目录源码引用和允许的依赖形式。
4. 定义构建顺序、契约兼容检查、模型校验和制品命名规则。
5. 记录 DPA、Agent Runtime、Agent UI 与治理服务仅通过版本化协议或部署路由集成的约束。

**产出物**

- `docs/architecture/platform/repository-boundaries.md`
- `docs/architecture/platform/build-units.yaml`

**验证方式**

从空工作区按文档顺序模拟构建依赖解析；每个部署单元的输入、输出和版本均明确，且删除任一 UI 源码目录不会阻止核心 Validator 或 Registry 的独立构建。

### [ ] T11.5 设计同源试点部署拓扑与网络边界

**前置 Task**

- T11.2
- T11.4

**达成目标**

定义满足现有 Entra ID/OIDC 与 `UserToken` 试点约束的同源路由、服务部署和网络访问规则，同时保持 Agent Runtime、Agent UI 与治理服务可独立演进。

**输入**

- 工作包 04 的身份与会话转发结论
- 工作包 05 的 DPA MI 边界
- 模块接口目录与构建单元

**执行步骤**

1. 绘制浏览器、反向代理、独立 Agent UI、Agent Runtime、Studio、Explorer、Gateway、Registry、后台工具和 DPA 的部署节点。
2. 定义同源 URL 空间、反向代理路由、Cookie 或 token 转发边界及 CSRF 防护位置。
3. 列出每条网络跨越的来源、目标、协议、端口、认证方式和允许用途。
4. 区分面向用户、内部服务、管理和批处理网络面。
5. 定义 DPA、Gateway 或 Registry 不可用时的降级行为，禁止失败时绕过授权。

**产出物**

- `docs/architecture/deployment/pilot-topology.mmd`
- `docs/architecture/deployment/network-crossings.yaml`
- `docs/architecture/deployment/same-origin-routing.md`

**验证方式**

按 `network-crossings.yaml` 逐条进行最小权限审查；任一浏览器请求都可追踪到认证与授权裁决点，Agent Runtime、Agent UI 与本体治理后台不存在未声明的进程内耦合，失败路径均为拒绝或只读降级。

### [ ] T11.6 定义配置、秘密与环境差异管理

**前置 Task**

- T11.4
- T11.5

**达成目标**

建立开发、测试、预生产和生产环境的配置分类、秘密来源、轮换和校验规则，避免配置漂移和凭据进入源码或日志。

**输入**

- 构建单元、部署拓扑和网络跨越清单
- 身份、MI 与 Tool 协议要求

**执行步骤**

1. 列出每个部署单元的配置键、类型、默认策略、是否敏感和生效阶段。
2. 区分普通配置、环境绑定配置、秘密和运行时动态策略。
3. 定义秘密注入、轮换、撤销、最小权限和访问审计责任。
4. 定义启动时配置校验、缺失配置失败方式和环境差异报告。
5. 禁止文档、示例、日志和构建制品包含真实秘密值。

**产出物**

- `docs/architecture/deployment/configuration-catalog.yaml`
- `docs/architecture/deployment/secrets-management.md`

**验证方式**

使用无真实秘密的样例配置执行静态检查表；所有必需键均有所有者和校验规则，敏感项无默认明文值，缺失关键身份或授权配置时系统设计为启动失败而非不安全降级。

### [ ] T11.7 定义高可用、扩缩容与故障域

**前置 Task**

- T11.3
- T11.5
- T11.6

**达成目标**

确定各部署单元的可用性等级、水平扩展条件、状态放置和故障隔离方式，使局部故障不会造成重复执行、越权或不可解释状态。

**输入**

- 持久化责任与数据生命周期
- 试点部署拓扑
- 配置与秘密管理方案

**执行步骤**

1. 为每个部署单元定义可用性目标、容量指标和是否允许多副本。
2. 标出进程、节点、可用区、依赖服务和 DPA 的故障域。
3. 定义 Gateway 幂等、审批单次消费、任务租约和重试在多副本下的约束。
4. 定义 Registry 缓存、模型版本固定和故障恢复规则。
5. 对 DPA、身份提供方、模型存储和审计存储故障执行桌面推演。

**产出物**

- `docs/architecture/deployment/availability-and-failure-domains.md`
- `docs/architecture/deployment/failure-scenarios.yaml`

**验证方式**

逐一推演 `failure-scenarios.yaml`；每个故障均有检测、隔离、恢复和数据一致性结论，任何重试或故障转移都不会重复消费批准或绕过 DPA 最终授权。

### [ ] T11.8 明确运维、发布与回滚责任

**前置 Task**

- T11.4
- T11.5
- T11.6
- T11.7

**达成目标**

定义代码、模型、配置、数据库迁移和路由变更的发布责任、审批门禁、回滚顺序及值班归属。

**输入**

- 构建单元、部署拓扑、配置目录和故障场景
- 工作包 03 的模型发布生命周期

**执行步骤**

1. 建立开发、审核、发布、运维、值班和安全责任矩阵。
2. 区分应用制品发布、模型发布、配置变更、Schema 迁移和反向代理路由变更。
3. 定义每类变更的前置检查、批准人、发布顺序、健康验证和回滚触发条件。
4. 定义跨模块版本不兼容时的阻断和协同发布规则。
5. 用一次模型回滚和一次 Gateway 制品回滚进行桌面演练。

**产出物**

- `docs/operations/platform-ownership-raci.md`
- `docs/operations/release-and-rollback.md`
- `docs/operations/release-checklist.md`

**验证方式**

使用发布检查表模拟正常发布、模型回滚和应用回滚；每一步均有唯一责任角色、可观察健康信号和停止条件，且回滚不会恢复已撤销的秘密或重新启用过期模型。

### [ ] T11.9 完成平台技术栈与基础设施选型

**前置 Task**

- T11.1
- T11.2
- T11.3
- T11.5
- T11.7

**达成目标**

为反向工程、Registry、Gateway、状态持久化、事件传输、审计存储和部署运行选择明确的技术方案，形成可实施的首选栈、备选栈和替换边界。

**输入**

- 模块职责、接口、数据生命周期和部署拓扑。
- DPA 的 .NET 技术事实，以及独立 Agent Runtime、Agent UI 和治理平台的能力要求。
- 已确认语言基线：codebase-memory MCP + Python Evidence Adapter 为源码分析主路径；C#/.NET + Roslyn 仅用于定向补证；Python + LangGraph + FastAPI/Pydantic、TypeScript + React、YAML + JSON Schema。
- [技术选型基线](../../architecture/technology-selection/baseline.md) 中的推荐、条件采用和暂缓引入项。
- 企业现有数据库、消息系统、缓存、容器平台、监控和秘密管理能力。

**执行步骤**

1. 在已确认语言基线内固化版本与运行时：源码分析以 codebase-memory MCP 为主、Evidence Adapter 使用 Python、缺口 extractor 使用 C#/.NET + Roslyn；Agent Runtime、Candidate Generator、Validator、Registry、Gateway 和集成适配器使用 Python；Agent UI、Studio、Explorer 使用 TypeScript/React；模型使用 YAML/JSON Schema。
2. 比较 Registry 索引、Proposal/Approval/Execution 状态、不可变审计和 Artifact 元数据的存储方案，明确哪些数据可共库、哪些必须隔离。
3. 比较 HTTP、SSE、Socket.IO、消息队列等同步与异步通信方案，并按实际事件可靠性需求选择，不为尚不存在的规模提前引入复杂中间件。
4. 比较 JSON Schema/OpenAPI/Pydantic 等契约工具在生成、校验、版本兼容和多语言客户端上的职责，避免重复事实源。
5. 确定反向代理、容器、任务调度、配置、秘密、日志、Trace 和指标的技术实现边界。
6. 为每个关键选型记录评价标准、候选方案、首选方案、淘汰理由、风险、PoC 或基准证据、版本策略和可替换接口。
7. 对难以撤销且存在真实权衡的选择分别创建 ADR；可轻易替换的库只记录选型说明，不滥用 ADR。

**产出物**

- `docs/architecture/technology-selection/platform-technology-stack.md`
- `docs/architecture/technology-selection/persistence-and-messaging-options.md`
- `docs/architecture/technology-selection/contract-tooling-options.md`
- `docs/architecture/technology-selection/deployment-and-observability-stack.md`
- 必要时新增 `docs/adr/` 下的技术选型 ADR。

**验证方式**

- 每个模块都能映射到明确语言、框架、部署单元、存储和通信方式，不存在“实现时再决定”的关键空白。
- 每项首选技术都有官方支持状态、许可证、版本、团队适配度和最小 PoC 或现有项目证据。
- 使用选定方案可以完整走通“扫描证据 → 候选模型 → 校验发布 → 查询/提案 → 审批执行 → 审计”的技术链路。
- 删除任一非必要中间件后重新审视方案，确认其复杂度确有业务或可靠性依据。

**边界**

- 本 Task 完成技术决策和必要 PoC，不实现生产服务。
- 不因语言偏好拆分服务，也不为了“微服务化”引入无业务边界的独立部署单元。

### [ ] T11.10 定义渐进式 DDD 采用与演进门禁

**前置 Task**

- T11.1
- 工作包 01
- 工作包 03

**达成目标**

根据本体模型揭示的业务语义和实际复杂度，为每个 Module 选择最低足够的 DDD 级别，并定义从简单实现升级到规则、Aggregate 和限界上下文的可验证条件。

**输入**

- [渐进式 DDD 采用规则](../../architecture/progressive-ddd.md)。
- `CONTEXT.md` 和 `CONTEXT-MAP.md`。
- 工作包 01 的统一语言和模型边界。
- 工作包 03 的 M1/M2/M3/M5/M6/M7/MU/MI 契约。
- MasterData 参考切片中的业务场景、不变量、状态和并发要求。

**执行步骤**

1. 为 Evidence、Ontology Governance、Semantic Query、Action Governance、DPA Integration、Agent Experience、Identity and Audit 分别评估 L0 至 L4。
2. 对每个采用 L2 以上的 Module 记录具体规则、不变量、生命周期或跨上下文问题。
3. 将 M1/M2/M3/M5/M6/M7/MU/MI 映射为候选代码表达，并明确不自动生成的战术模式。
4. 为 Proposal、Approval、Execution 和 Published Ontology Version 设计事务与并发场景，判断是否需要独立 Aggregate。
5. 为 Query、Evidence Adapter、Renderer 和协议转换验证保持 L0/L1 是否足够。
6. 定义升级触发器、禁止升级条件、评审问题和回归测试要求。
7. 将确认后的 DDD 级别写入各 Module README，不预先创建空目录和空类型。

**产出物**

- `docs/architecture/domain-design/ddd-adoption-matrix.md`
- `docs/architecture/domain-design/aggregate-decision-records.md`
- 更新后的各 Module README
- MasterData 领域测试场景清单

**验证方式**

- 每个 Module 都有当前级别和基于真实场景的理由。
- 每个 Aggregate 都能指出要保护的不变量、事务范围和并发策略。
- 简单 Query、Adapter 和 Renderer 不被强制包装成 Aggregate 或 Repository。
- 随机抽查本体模型，不能仅依据模型类型直接推导代码战术模式。
- DDD 升级前后行为测试保持一致，新增测试覆盖升级所解决的复杂度。

**边界**

- 不以 DDD 名义重写 DPA。
- 不为每张表创建 Entity/Repository。
- 不为了目录一致性预建未使用的 domain/application/ports/adapters。

## 工作包验收

- 八个核心模块均有明确职责、不变量、接口、依赖方向和唯一数据责任。
- 仓库目录、构建单元和共享契约边界可支持独立构建与版本化发布。
- 同源试点拓扑完整描述身份转发、网络跨越、授权裁决和失败降级。
- 配置与秘密均有分类、所有者、校验、轮换和审计规则，不记录真实值。
- 高可用设计覆盖多副本幂等、审批单次消费、模型版本固定和关键依赖故障。
- 发布、回滚、运维和值班责任可由检查表重复演练。
- 最终方案不依赖或复用 InsightBot，不允许 Agent UI 承担本体治理责任，也不允许平台直接写 DPA 数据库。
- 平台各模块、存储、通信、契约和可观测性技术均有经过对比和 PoC 支撑的明确选型。
- 每个 Module 的 DDD 级别由业务复杂度和本体语义决定，升级有明确触发器、测试和评审门禁。

## 解决记录

> 工作包关闭时填写，只记录最终结论、关键取舍、验证结果和资产链接。

- 最终结论：待完成。
- 关键取舍：待完成。
- 验证结果：待完成。
- 资产链接：待完成。
