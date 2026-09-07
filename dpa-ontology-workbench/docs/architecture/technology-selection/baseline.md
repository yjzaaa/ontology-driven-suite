# 技术选型基线

## 状态

本文件记录进入 PoC 的推荐技术基线。它不是对具体版本、部署规格和供应商产品的最终确认；工作包 08、09、11 必须通过统一样例验证后，才能在“解决记录”中将对应选择定为正式决策。

## 选型原则

- 优先建立深模块，以小接口隐藏框架、存储、协议和第三方工具复杂度。
- 第一阶段采用模块化单体，不为尚未出现的团队、容量或安全隔离需求提前拆分微服务。
- 只在存在两个真实 Adapter 时建立可替换 Seam，不为空想的未来变化增加抽象层。
- 业务状态、权限和审计不依赖 Agent 框架、前端框架或图数据库。
- 已发布 YAML 是本体事实源；数据库、内存索引和关系图都是可重建投影。
- 新增基础设施必须证明其删除了自有复杂代码或满足可测量的可靠性要求。

## 推荐技术矩阵

| 领域 | 推荐基线 | 状态 | 说明 |
|---|---|---|---|
| 源码图谱 | codebase-memory MCP | 推荐进入 PoC | 负责索引、符号搜索、调用图、数据流和变化影响 |
| 证据转换 | Python Evidence Adapter | 推荐进入 PoC | 负责噪声过滤、分页、稳定 ID、revision、证据等级和快照 |
| 专有语义补证 | C#/.NET + Roslyn | 按缺口启用 | 仅补充 fixture 证明的 ASP.NET/DPA 专有语义缺口 |
| Agent 编排 | Python + LangGraph | 推荐进入 PoC | 只负责任务编排、Tool 顺序、中断恢复和对话 checkpoint |
| HTTP 后端 | FastAPI + Pydantic | 推荐进入 PoC | 承载认证上下文、协议边界和模块装配 |
| 业务状态 | PostgreSQL | 推荐进入 PoC | 保存模型索引、Proposal、Approval、Execution 和审计元数据 |
| Agent UI | TypeScript + React + Vite | 推荐进入 PoC | 自主实现，不依赖 InsightBot |
| 企业界面 | Ant Design | 候选首选 | 重点验证表格、审核、可访问性和主题适配 |
| 服务器状态 | TanStack Query | 候选首选 | 查询、缓存和失效；不承载权威业务状态 |
| 局部界面状态 | Zustand | 条件采用 | 仅用于选中项、面板和非权威交互状态 |
| Schema 校验 | JSON Schema 2020-12 + Ajv | 推荐进入 PoC | 校验本体、Tool、事件和 Renderer 投影 |
| 本体图 | Cytoscape.js | 候选首选 | 适合只读关系图和较大规模图 |
| 自动布局 | ELK.js | 候选首选 | 负责分层、复杂关系和可重建布局 |
| 统计图表 | ECharts | 候选首选 | 负责聚合指标和业务统计 |
| 浏览器流式协议 | HTTP + SSE | 推荐进入 PoC | 命令走 HTTP，Token 和状态事件走 SSE |
| 观测标准 | OpenTelemetry | 推荐进入 PoC | 统一 Trace、日志关联和指标语义 |
| 指标与看板 | Prometheus + Grafana | 候选首选 | 与企业现有观测平台冲突时允许替换 Adapter |
| 打包部署 | Docker + 同源反向代理 | 推荐进入 PoC | 新平台独立部署，试点期与 DPA 同源 |
| LLM 模型与供应商 | 分层：对话主模型 + 构建期起草模型 + 多模态辅助 | 待 T08.9 PoC | 结构化输出（JSON Schema 约束/function calling）是 OAG 与 MU 起草的安全前提；记录内网/国产化/成本切换边界 |
| 只读 SQL 防护 | sqlglot（AST 级 SELECT 校验与表列闭包） | 候选首选 | 服务于受治理查询“禁止任意 SQL”的强制执行，不替代 Database MCP capability 边界 |
| UI 证据提取 | Python HTML/Razor 解析（lxml/BeautifulSoup4 候选）+ Playwright DOM 抽样 | 候选首选 | LLM 仅构建期起草候选 MU；产物进 Evidence Adapter 契约 |
| Approval Token 实现 | opaque 随机 Token + PostgreSQL 原子单次消费 | 推荐进入 PoC | 撤销与单次消费语义比自包含签名 Token 可控；详见 WP07 T07.4 |

## 平台形态

第一阶段采用 Python 模块化单体。模块通过内部 Interface 协作，不通过进程内 HTTP 自调用。

```text
backend/
  agent_runtime/
  ontology/
  queries/
  planning/
  policy/
  approval/
  execution/
  audit/
  evidence/
  shared/
```

允许同一代码库形成不同运行进程：

```text
ontology-api       HTTP、SSE、Agent Runtime、查询和审批入口
ontology-worker    证据转换、候选生成、校验和后台任务
agent-ui           独立 Web 前端
```

只有在独立扩缩容、独立安全区、不同可用性目标或独立团队所有权真实出现时，才拆分部署模块。

## Agent Runtime

LangGraph 位于 Agent 编排 Seam 后面。外部模块只依赖平台自有的 Agent Runtime Interface，不依赖 LangGraph Graph、State 或 Checkpoint 类型。

LangGraph 可以负责：

- 对话步骤和 Tool 调用顺序；
- 流式输出；
- 人工中断与恢复；
- 可重放的对话 checkpoint；
- 模型供应商 Adapter 调用。

LangGraph 不得拥有：

- Policy 和权限结论；
- Proposal、Approval、Execution 权威状态；
- MI 技术目标和 DPA 凭据；
- 业务事务；
- 不可变审计收据。

这些状态由平台领域模块写入 PostgreSQL。删除或重建 LangGraph checkpoint 不得破坏审批与执行事实。

## 数据与存储

第一阶段不引入 Neo4j。PostgreSQL 保存：

- 已发布模型的运行时索引和版本元数据；
- 模型引用反向索引；
- Proposal、Approval、Execution；
- 审计事件和收据索引；
- Artifact 元数据；
- 后台任务租约和状态。

正式 YAML 通过版本控制和发布流程形成不可变模型包，Runtime Registry 加载发布包，而不是直接读取开发工作树。图投影可以从模型包和 PostgreSQL 索引重建。

只有在出现经过测量的超大规模多跳在线查询或图算法需求时，才重新评估 Neo4j。

## 浏览器协议

首选 HTTP + SSE：

- 查询、提案、批准、拒绝和取消使用显式 HTTP 命令；
- Token 增量、Tool 状态、审批状态和执行状态使用 SSE；
- 事件包含稳定 `event_id` 和顺序号；
- 客户端使用 `Last-Event-ID` 恢复；
- 终态始终从服务端查询或事件确认，不由按钮点击推断。

只有高频双向协同编辑成为真实需求时，才重新评估 WebSocket。第一阶段不引入 Socket.IO。

## 前端渲染

- React/TypeScript 负责 Agent UI、Studio、Workbench 和 Explorer。
- Renderer 使用判别联合和 JSON Schema 校验，不执行权限或业务规则。
- Cytoscape.js 用于第一阶段只读本体图。
- ELK.js 负责布局，布局结果不是模型事实。
- ECharts 负责指标和聚合图。
- React Flow 只在未来需要图形化模型编辑时重新评估。
- `visual-model` 只提供视觉语义、交互模式和可复用实现证据，不成为生产数据模型。

## 深模块与 Seam

| 深模块 | 外部 Interface | 隐藏的实现复杂度 |
|---|---|---|
| Evidence Source | `extract_snapshot(revision, scope)` | MCP 查询、分页、图标签、噪声过滤、Roslyn 补证 |
| Ontology Registry | `resolve(ref, version)` | YAML 加载、引用闭包、索引和缓存 |
| Semantic Query | `execute(queryRef, arguments, identity)` | MI、数据源、范围、字段和资源限制 |
| Action Planning | `propose(behaviorRef, arguments, identity)` | Schema、规则、风险和影响预览 |
| Approval | `approve(proposalId, identity)` | Token、单次消费、过期和并发 |
| Execution | `execute(approvalToken)` | MI、DPA HTTP、幂等、超时和错误标准化 |
| Agent Runtime | `run_turn(conversation, input)` | LangGraph、模型 Adapter、Tool 编排和 checkpoint |
| Renderer Projection | `render(projection)` | React 组件注册、图表和可访问性 |

## 暂缓引入

第一阶段不采用：

- 微服务拆分；
- Neo4j；
- Kafka；
- Temporal；
- Kubernetes；
- AutoGen/CrewAI 式自治多 Agent；
- 通用任意 HTTP Tool；
- 通用任意 SQL Tool；
- 每个 Controller 一个 Tool；
- 全量事件溯源；
- Socket.IO；
- 浏览器保存 DPA Token。

这些技术不是永久禁止。只有对应规模、可靠性或组织需求被实际测量并超过当前方案能力时，才建立新的 Wayfinder 工作包重新评估。

## PoC 必须回答的问题

- codebase-memory MCP 对 DPA 自定义 Filter、接口分派、EF/Dapper、存储过程和动态路由的准确率是多少。
- LangGraph 在进程重启、人工等待和模型供应商切换时是否保持 Tool 协议稳定。
- PostgreSQL 是否能满足模型引用、状态机、审计和后台任务的并发与恢复要求。
- SSE 是否能稳定完成断线续传、事件去重和终态恢复。
- Cytoscape.js + ELK.js 在千级节点下的布局和交互性能是否达到验收目标。
- Ant Design 是否满足 DPA 用户的表格密度、审核体验、主题和可访问性要求。
