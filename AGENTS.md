# DPA Ontology Studio & Runtime Workbench — Agent 开发规范

本项目建立 DPA 之上的独立本体治理与运行时语义平台。开始工作前先读 [README.md](README.md)、[CONTEXT.md](CONTEXT.md) 和 [Wayfinder 地图](docs/wayfinder/map.md)。修改 `docs/` 时同时遵循 [docs/AGENTS.md](docs/AGENTS.md)。

## 当前纪律：先完成地图，再实现产品

当前阶段以 Wayfinder 决策为唯一工作主线。除非地图的“已确认边界”或具体工作包明确授权实现，否则：

- 只解决一个已领取的当前可执行工作包；
- 当前 Copilot 主 Agent 是所有 Wayfinder 工作包和 Task 的默认执行者，负责调查、调用工具、编写产出、运行验证和记录解决结果；
- 主 Agent 应基于任务性质主动使用 codebase-memory MCP、专业 Skill、代码搜索、命令工具和可并行的子 Agent，不得把可自行完成的工作转交给用户；
- 子 Agent 只承担主 Agent 划分的独立子问题，主 Agent负责整合结果、处理冲突和最终验收；
- 用户、DPA 技术负责人、领域专家、安全负责人和发布审批人只承担必须由人作出的事实确认、业务裁决、风险接受和授权决定；
- 产出决策、调查结论或低保真原型，不实现生产代码；
- 不提前解决被阻塞工作包；
- 不把尚未决定的内容写成既定架构；
- 工作包必须拆分为可独立执行、可验证的 Task，不能只保留一个笼统问题；
- 工作包关闭后，将一行决策摘要和链接追加到地图的“已完成决策”；
- 新发现但尚不能精确描述的问题保留在“尚未明确”。

`assignee` 表示当前由哪个 Agent 会话领取工作包，不表示将工作移交给外部人员。领取时默认填写 `copilot-agent`；只有用户明确指定其他执行者时才使用其他值。

本地 tracker 规则见 [docs/wayfinder/README.md](docs/wayfinder/README.md)。

## 不可违反的产品边界

1. **DPA 是最终业务执行系统。** 复杂表单、业务校验、工作流、最终授权和持久化继续由 DPA 负责。
2. **所有业务写入通过 DPA 原 HTTP/业务层路径。** Database MCP 永远只读，不得成为写库后门。
3. **模型不能选择技术接口。** Agent 只能引用已发布的业务对象、行为和查询；URL、HTTP Method、凭据、Header、DTO 映射和重试策略只存在于 Gateway 内部 MI。
4. **写操作默认只生成提案。** Agent 不得直接调用内部 DPA Executor；执行必须经过服务端 Policy 和 HITL 状态机。
5. **不按 Controller 一对一生成 Tool。** Agent 只获得少量稳定语义 Tool，具体能力通过 `behaviorRef`、`queryRef` 和 Schema 表达。
6. **无法证明纯读即按写风险处理。** 混合副作用接口默认 `MIXED/HIGH`，禁止自动执行。
7. **本体必须可追溯。** 每个对象、行为、规则、权限、查询和 MI 都必须引用 DPA 源码、配置、UI、接口或数据库证据。
8. **候选模型没有执行权。** 只有经验证、审核和发布的不可变模型版本可以进入 Runtime Registry。
9. **不复制 DPA 复杂表单。** Runtime Workbench 使用对象卡、表格、图表、行为提案和 Legacy View；复杂编辑回到原 DPA 页面。
10. **凭据不进入模型上下文。** Cookie、Access Token、密码和连接串不得写入 Prompt、Tool 参数、聊天历史、审计正文或本体 YAML。

## 仓库布局

```text
docs/
  wayfinder/             本地 Markdown tracker
  meta-model/            codebase-reverse 规定的反向工程报告
  architecture/          架构、数据流、时序和部署视图
  adr/                   满足 ADR 门槛的长期决策
evidence/
  snapshots/<revision>/  按 DPA revision 固化的机器证据
models/
  schemas/               M1/M2/M3/M5/M6/M7/MU/MI Schema
  <domain>/              已发布领域模型唯一来源
tools/
  codebase-memory-adapter/ MCP 图谱到证据契约的适配与补证
  roslyn-extractors/     仅补充 MCP 缺失的 DPA 专有语义
  candidate-generator/   Evidence → DRAFT YAML
  model-validator/       Schema、引用、证据和兼容性校验
  change-detector/       DPA 变化 → REVIEW_REQUIRED
gateway/
  ontology/              Registry、Resolver、版本
  tools/                 Agent 可见语义 Tool
  planning/              意图解析与提案创建，不执行 HTTP
  policy/                权限、风险、规则、数据范围
  approval/              HITL 状态机和 Token
  execution/             DPA HTTP 与 Database MCP 内部适配器
  audit/                 审计收据和关联标识
agent-ui/                独立 Agent UI、会话协议与业务 Renderer
ontology-explorer/       本体治理和可视化
deploy/                  反向代理、容器和环境配置
tests/                   模型契约、集成和端到端验收
```

目录内出现更具体的 `AGENTS.md` 时，以更近的文件补充本规范；不得放宽根级安全边界。

## 权威来源和生成物

权威顺序：

1. 已关闭 Wayfinder 工作包“解决记录”中的决策；
2. `CONTEXT.md` 中的统一业务语言；
3. `docs/adr/` 中仍有效的架构决策；
4. `models/<domain>/` 中已发布的 YAML；
5. DPA revision 对应的 `evidence/snapshots/`；
6. 生成的报告、图和运行时索引。

不得同时维护两份正式本体。`.build/candidates/` 是临时候选区，禁止被 Runtime Registry 加载。

## 代码风格：通用

- 优先正确的模块边界、显式失败和可验证契约，不为短期演示加入静默降级。
- 一个模块应隐藏复杂实现并提供窄接口；跨模块依赖使用公开协议，不导入内部文件。
- 在解析、持久化、进程、HTTP、Tool JSON、模型 YAML 和 DPA 响应边界做运行时校验；同进程强类型边界不重复防御。
- 配置缺失或模型引用无效时尽早失败，不跳过、不猜测、不用空结果伪装成功。
- 禁止宽泛 `catch` 后继续返回成功；错误必须保留稳定错误码、关联 ID 和可操作消息。
- 不使用裸字符串承载不同语义 ID。类型系统可用时使用 branded/newtype/value object。
- 注释解释非显而易见的约束和原因，不复述代码。
- 文件以一个换行结尾；提交前运行 `git diff --check`。
- 不提交凭据、生产连接串、Cookie、Token、数据库快照或未经脱敏的源数据。
- 新增依赖前先证明它能删除自有代码或明显降低风险；依赖版本必须固定在项目采用的包管理机制中。

## DDD 与代码组织

本项目采用边界驱动的渐进式 DDD。限界上下文及关系见 [CONTEXT-MAP.md](CONTEXT-MAP.md)，采用级别和升级条件见 [渐进式 DDD 采用规则](docs/architecture/progressive-ddd.md)。本体模型提供候选语义，业务复杂度决定使用 L0 至 L4 中的哪一级。DDD 用于保护业务语义和一致性，不用于制造形式化目录或空壳类型。

- 每个限界上下文维护自己的统一语言；代码、测试、事件、错误和文档使用相同术语。
- 领域 Module 不依赖 FastAPI、Pydantic、SQLAlchemy、LangGraph、React、HTTP、MCP 或 DPA DTO。
- 应用 Module 负责编排用例、事务和跨上下文调用，不包含核心业务判断。
- Adapter 位于 Seam 上，负责 PostgreSQL、HTTP、MCP、LLM、文件和 DPA 协议转换。
- DPA Integration 是显式 Anticorruption Layer；DPA Controller、DTO、表名和错误不得成为核心领域类型。
- Entity 只用于需要稳定身份和生命周期的概念；纯描述值使用不可变 Value Object。
- Aggregate 只围绕必须保持强一致的不变量建立，并只允许通过 Aggregate Root 修改内部状态。
- Repository 只服务需要持久化的 Aggregate Root，不为每张表或每个 DTO 创建 Repository。
- Domain Service 只承载无法自然归属 Entity/Value Object 的重要领域运算，不得成为通用业务逻辑容器。
- Factory 只用于创建过程复杂且必须保证有效构造的 Aggregate；简单构造不增加 Factory。
- Command 与 Query 分离：Query 不改变业务状态，Command 必须表达业务意图和结果。
- Domain Event 使用过去式业务名称，表示已经发生的事实；不得用事件隐藏同步一致性要求。
- 跨上下文只传递稳定 ID、发布模型、命令、查询或事件，不共享内部对象和数据库事务。
- 禁止 `BaseEntity`、`BaseRepository`、`GenericService` 等只减少少量重复却扩大耦合的通用抽象。
- 禁止只有 getter/setter 的贫血 Aggregate；不变量、合法状态转换和业务判断应位于领域模型。
- 不要求所有 Module 都采用 Aggregate。Evidence Adapter、Renderer 和协议转换等技术 Module 可以保持过程式或函数式。
- 新 Module 默认从最低足够级别开始；只有出现规则重复、非法状态、事务一致性、并发冲突或跨上下文翻译压力时才逐级深化。
- M1/M2/M3/M5/M6/M7/MU/MI 不能机械映射为 Entity、Service、Repository 或数据库表；必须经过场景和不变量分析。

### 上下文内推荐结构

仅在对应目录真实需要这些职责时创建，不预先生成空目录：

```text
<context>/
  domain/          Entity、Value Object、Aggregate、领域规则和领域事件
  application/     用例、Command/Query Handler、事务编排
  ports/           外部依赖需要满足的 Interface
  adapters/        PostgreSQL、HTTP、MCP、LLM 和文件实现
  api/             FastAPI 或事件协议映射
```

依赖方向必须指向领域：

```text
api/adapters → application → domain
```

`domain` 不反向导入其他层。跨上下文调用通过对方公开 Interface 或 Published Language。

### DDD 测试规则

- Aggregate 测试直接使用统一语言描述合法构造、不变量和允许/禁止状态转换。
- Application 测试通过 Port fake 验证编排、事务和跨上下文交互。
- Adapter 使用契约测试证明与 Interface 一致，不在领域测试中启动数据库、HTTP 或 LangGraph。
- 防腐层测试必须同时包含 DPA 原始响应和平台领域结果，证明翻译不会泄漏遗留模型。
- 每次修正规则时增加一个体现业务场景的回归测试，不只测试方法调用次数。

## C# / Roslyn

- codebase-memory MCP 是源码图谱、符号搜索、调用链和变更分析的首选引擎；不得在未验证缺口前重复实现完整扫描器。
- C#/.NET + Roslyn 只用于补充 MCP 无法可靠识别的 ASP.NET/DPA 专有语义，并将结果交给统一 Evidence Adapter。
- 启用 nullable reference types，警告不得通过全局禁用规避。
- 公共 API 使用明确类型；异步 I/O 接受并传递 `CancellationToken`。
- Roslyn 分析优先使用语义模型和符号 ID，不用正则表达式替代可获得的语义信息。
- 扫描器输出必须确定性排序；同一 revision 重复扫描应产生字节稳定的规范化结果。
- 每条推断区分 `FACT`、`INFERENCE`、`ASSUMPTION`，并携带文件、行号、符号和提取器版本。
- 不加载或执行被分析项目的业务代码；扫描默认只读。
- 访问图、SQL、存储过程和 UI 绑定时保留证据链，不把命名启发式提升为事实。
- 测试使用最小 C# fixture 覆盖 Controller、Filter、BLL、Service、Repository、EF、Dapper、存储过程和混合副作用。

## Python / Gateway

- Python 是独立 Agent Runtime、LangGraph 编排、Gateway、Registry、Policy、HITL、MI 和审计服务的主实现语言。
- Python 3.12+；使用类型标注，公共函数和协议不得依赖隐式 `Any`。
- Pydantic 只用于不可信边界和持久化/网络协议；领域内部使用明确 dataclass、enum 或 value object。
- FastAPI 路由只负责认证上下文、输入解析和响应映射；Policy、Proposal、Approval 和 Execution 进入独立服务。
- `planning` 不得依赖 HTTP client、Cookie forwarding 或数据库连接。
- 只有 `execution` 可以解析 MI 的技术目标；Agent Tool 层不得读取 DPA 凭据。
- HTTP client 必须设置连接、读取和总超时；写请求默认不自动重试。
- 数据库事务边界由拥有状态转换的服务控制，不由路由或 repository 隐式控制。
- 日志采用结构化字段；禁止记录完整 Tool 参数、Cookie、Token 或敏感业务字段。
- Gateway 配置统一由 `.env` 存放（不入 git，模板 `.env.example` 入 git），`gateway/config.py` 是唯一映射点；其它代码只从 config 导入，禁止散落硬编码连接串、URL、端口、模式开关；配置缺失或非法时启动即失败（fail-fast），不猜测、不用空值伪装。
- 配置文件与代码不存放凭据；测试库默认走 Windows 集成认证，生产凭据只在运行时经 secret 管理注入。
- Gateway 数据分层：真实库仅在引导同步时被只读访问（gateway/sync_local.py，白名单表 SELECT）；运行时读写一律基于本地持久化数据，运行时不连接真实库；写操作更新本地数据并追加写日志（台账可换任意后端，Port + 适配器），禁止直接写业务库；经 DPA 原业务链真实写入的模式必须显式开启且不得伪装成功。

## TypeScript / React

- TypeScript/React 是独立 Agent UI、Ontology Studio、Runtime Workbench、Ontology Explorer 和 Renderer 的主实现语言。
- TypeScript 使用 `strict`，禁止无说明的 `any`、双重类型断言和以断言替代数据校验。
- Renderer 以判别联合处理协议；封闭联合必须穷尽检查。
- 前端不接收、拼装或覆盖 DPA URL、HTTP Method、Header 和执行参数。
- 批准动作只能提交服务端签发的 `proposalId` 与 `approvalToken`。
- UI 状态来自权威事件或查询结果，不根据按钮点击乐观伪造 `Succeeded`。
- Renderer 是纯投影组件；行为执行、权限判断和风险计算不得放入 React 组件。
- 不使用 `dangerouslySetInnerHTML` 注入 DPA 返回 HTML；Legacy View 使用受控同源导航。
- 可访问性要求：键盘可操作、焦点可见、语义按钮、错误与状态不只依赖颜色。

## YAML 和本体模型

- YAML 是人工审核和版本控制的规范表示，JSON Schema 是机器校验契约；二者不得由语言内部类定义取代。
- 稳定 ID 使用 ASCII；显示名和业务描述可以使用中文。
- Schema 中明确 `additionalProperties` 策略；未知字段不得被静默忽略。
- 跨模型只通过稳定 ID 引用，不复制对象、行为、规则或权限定义。
- 每个正式模型包含版本、状态、领域、所有者和证据引用。
- M2 行为描述业务结果，不以 Controller/Action 名称作为规范名称。
- M3 规则只判断或派生，不直接执行写操作。
- MI 显式记录副作用、固定参数、禁止参数、认证模式、超时、重试、幂等、错误映射和 DPA 证据。
- 模型文件和列表采用确定性排序；格式化不得改变语义顺序。
- 发布时校验 Schema、引用闭包、证据存在、版本兼容和循环依赖；任何错误阻断发布。

## 身份、安全与数据治理

- DPA 原授权器永远执行最终检查；Gateway 前置权限不能替代它。
- 同源 Cookie 透传只是试点机制，必须限制 Origin、有效期和服务端使用范围。
- Database MCP 只暴露审核视图、字段、关系、指标或存储过程；禁止模型提交任意 SQL。
- 查询强制用户数据范围、行数、连接数、复杂度、超时和导出策略。
- Approval Token 至少绑定用户、Proposal、参数哈希、本体版本、MI 版本、有效期和单次 `jti`。
- 执行审计必须能关联用户、会话、Proposal、Execution、模型版本、MI、DPA 请求摘要和结果。

## 测试纪律

- 修改模型 Schema：增加有效和无效 fixture，并覆盖跨模型引用失败。
- 修改扫描器：增加最小源码 fixture 和稳定快照，验证证据级别与读写分类。
- 修改 Policy/HITL：覆盖所有合法状态转换和非法转换拒绝。
- 修改 MI Executor：使用本地 stub 验证参数锁定、超时、错误映射、无重试写入和幂等。
- 修改 Agent 协议：增加 keyless Tool/事件 transcript，证明模型看不到技术接口和凭据。
- 修改 Renderer：增加组件行为测试和一条组装后的关键用户路径。
- 不默认运行全套；先运行覆盖变更面的最小命令，再根据失败扩大范围。
- 不因现有无关测试失败而修改无关代码；明确记录基线失败。

## 文档与决策

- `CONTEXT.md` 只保存领域词汇，不写实现、计划或历史。
- 架构图、数据流图和时序图必须引用权威模型或代码证据，未知内容明确标记。
- ADR 只用于难以撤销、缺少上下文会令人意外、且经过真实权衡的决策。
- 一个事实只保留一个权威位置，其他文档用链接引用。
- 非平凡实现变更必须同时更新受影响的契约、架构说明和验收路径。

## Git 纪律

- 未经用户明确要求，不执行 `git add`、`commit` 或 `push`。
- 不修改、删除或还原非本任务产生的工作树变更。
- 禁止 `git reset --hard`、无批准的历史重写和裸 `--force`。
- 用户要求提交时，先展示待提交 diff；提交消息必须说明行为变化和影响范围。
