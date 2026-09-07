# 领域术语清单（T01.1 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.1 产出。
> 任务：盘点当前仓库规范、参考项目和 MasterData 语境中的术语，标出同名异义、异名同义、未定义和跨层混用问题，并为每个冲突项分配稳定编号 `TERM-XXX`。
> 本文件只记录“现状和冲突”，不给出最终裁决；裁决由 T01.6 完成。

## 术语集合与来源

| # | 核心概念 | 中文候选名 | 规范来源（本项目） | 主要引用点 |
|---|---|---|---|---|
| 1 | Evidence | 证据 | `CONTEXT.md`「Evidence」 | `AGENTS.md`、`docs/wayfinder/map.md`、`docs/meta-model/README.md` |
| 2 | Business Object | 业务对象 | `CONTEXT.md`「Business Object」 | `docs/wayfinder/masterdata-scope.md` |
| 3 | Behavior | 行为 | `CONTEXT.md`「Behavior」 | `AGENTS.md`、`docs/architecture/progressive-ddd.md` |
| 4 | Rule | 规则 | `CONTEXT.md`「Rule」 | `AGENTS.md`、`docs/architecture/progressive-ddd.md` |
| 5 | Actor / Permission | 参与者 / 权限 | `AGENTS.md`「M5 Actor/Permission」 | `docs/architecture/progressive-ddd.md` |
| 6 | Flow | 流程 | `AGENTS.md`「M6 Flow」 | `docs/architecture/progressive-ddd.md` |
| 7 | Query | 查询 | `AGENTS.md`「M7 Query」 | `docs/architecture/progressive-ddd.md`、`docs/architecture/technology-selection/baseline.md` |
| 8 | Presentation | 展示 / 表现 | `AGENTS.md`「MU Presentation」、`CONTEXT.md`「Renderer」 | `docs/architecture/progressive-ddd.md` |
| 9 | Integration Mapping (MI) | 集成映射 | `CONTEXT.md`「Integration Mapping」 | `docs/wayfinder/map.md`（工作包 05） |
| 10 | Action Proposal | 行为提案 | `CONTEXT.md`「Action Proposal」 | `CONTEXT-MAP.md`「Action Governance」 |
| 11 | Draft Application | 草稿应用 | `CONTEXT.md`「Draft Application」 | `CONTEXT-MAP.md` |
| 12 | Runtime Projection | 运行时投影 | `CONTEXT.md`「Runtime Projection」 | `CONTEXT-MAP.md` |
| 13 | Legacy View | 遗留视图 | `CONTEXT.md`「Legacy View」 | `docs/wayfinder/map.md`、`AGENTS.md` |

## 逐项清单

每项包含“来源、当前用法、冲突、状态”四列要求；冲突为“无”或引用 `TERM-XXX`。

### 1. Evidence（证据）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：从 DPA 代码、接口行为、UI 绑定、配置或数据库访问中发现的事实、推断或假设；Evidence 本身不授予运行时执行权。`codebase-reverse/references/evidence-protocol.md` 定义证据纪律。 |
| 当前用法 | `AGENTS.md`：所有对象、行为、规则、权限、查询和 MI 都必须引用 DPA 证据。`docs/meta-model/README.md`：机器可读证据进入 `evidence/snapshots/<revision>/`。 |
| 冲突 | 无。Evidence 与 `FACT/INFERENCE/ASSUMPTION` 是“总称 / 分级”关系，非同名冲突（见 TERM-018 记录“证据”与“事实”的混用风险）。 |
| 状态 | 已确认 |

### 2. Business Object（业务对象）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：具有业务身份、属性、生命周期和关系的领域概念；不自动等同于数据库表、Entity 或 DTO。 |
| 当前用法 | `docs/wayfinder/masterdata-scope.md`：`SubtableType` 可能最终被判定为分类体系、配置注册表、能力选择器或多个业务对象的技术聚合入口——即“是否业务对象”本身是待裁决事实。 |
| 冲突 | 无直接冲突；与“表 / DTO / ViewModel / 数据形状”的边界是 T01.3 的判定范围，不在此判。 |
| 状态 | 已确认（定义）；具体实例待证据（`SubtableType` 归属待裁决，见 TERM-013） |

### 3. Behavior（行为）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：针对业务对象或领域产生稳定业务结果的能力，与实现它的 DPA Endpoint 相互独立。 |
| 当前用法 | `AGENTS.md`：M2 行为描述业务结果，不以 Controller/Action 名称作为规范名称。`docs/architecture/progressive-ddd.md`：M2 Behavior 与 M3 Rule 形成稳定关联。 |
| 冲突 | TERM-003：与 DPA “Controller Action”同名异义。 |
| 状态 | 已确认（定义）；实例映射待证据 |

### 4. Rule（规则）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：用于判断条件或派生结果的可复用业务约束；不直接执行状态修改。`AGENTS.md`：M3 规则只判断或派生，不直接执行写操作。 |
| 当前用法 | `docs/architecture/progressive-ddd.md`：行为是否允许取决于对象状态、用户范围或多个条件。 |
| 冲突 | TERM-007：与“输入校验 validation”的边界存在混用风险。 |
| 状态 | 已确认（定义）；与 validation 的边界待 T01.4 裁决 |

### 5. Actor / Permission（参与者 / 权限）

| 维度 | 内容 |
|---|---|
| 来源 | `AGENTS.md`：M5 Actor/Permission。`CONTEXT-MAP.md`：DPA 业务权限由 DPA 现有过滤器和业务层最终裁决。 |
| 当前用法 | `docs/architecture/progressive-ddd.md`：M5 Actor/Permission 会改变行为可用性；M5 映射 Policy 输入、Identity Context、授权规则。 |
| 冲突 | TERM-008：与 HITL “Approval（审批）”的中文映射易混（授权 vs 审批）。 |
| 状态 | 已确认（定义）；权限模型细节待 T03/T04 展开 |

### 6. Flow（流程）

| 维度 | 内容 |
|---|---|
| 来源 | `AGENTS.md`：M6 Flow。`CONTEXT-MAP.md`：Action Governance 在 Draft Application、Gateway Execution 和 Legacy View 之间作出受治理选择。 |
| 当前用法 | `docs/wayfinder/tickets/10`：四条“关键用户路径”称为 user flows（用户流）。DPA 侧存在“工作流（workflow）”。 |
| 冲突 | TERM-005：M6 Flow / 用户流 / DPA Workflow 三个含义共用 “Flow/流程/工作流” 词族。 |
| 状态 | 已确认（M6 定义）；与用户流、DPA Workflow 的边界待裁决 |

### 7. Query（查询）

| 维度 | 内容 |
|---|---|
| 来源 | `AGENTS.md`：M7 Query。`CONTEXT-MAP.md`「Semantic Query」：解析已发布 M7 Query，通过 MI 选择受治理读取能力。 |
| 当前用法 | `docs/architecture/technology-selection/baseline.md`：前端用 TanStack Query；`docs/architecture/progressive-ddd.md`：Query Handler、只读投影。 |
| 冲突 | TERM-004：M7 Query / TanStack Query（第三方库名）/ DPA SQL Query 共用 “Query” 词。 |
| 状态 | 已确认（M7 定义）；技术库名与本体系无语义冲突但需在文档中区分 |

### 8. Presentation（展示 / 表现）

| 维度 | 内容 |
|---|---|
| 来源 | `AGENTS.md`：MU Presentation。`CONTEXT.md`：Renderer 由已发布 Presentation 选择，显示对象、集合、图表、关系、Proposal、Execution 或 Legacy View 链接。 |
| 当前用法 | `docs/architecture/progressive-ddd.md`：MU Presentation 映射 Renderer 元数据、视图模型。 |
| 冲突 | TERM-009：MU 在本项目 = Presentation；在参考项目 `ontology-driven-dev` 的 MU = UI 模型；`Onto-Contract` 用 M9 表示 UI。模型编号与含义均不一致。 |
| 状态 | 已确认（本项目定义）；跨参考项目编号冲突待 T01.2 裁决 |

### 9. Integration Mapping（集成映射，MI）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：将已发布 Behavior 或 Query 连接到现有 DPA API、受治理 Database MCP 能力或其他批准执行器的防腐契约，简称 MI。`CONTEXT-MAP.md`：MI 是 DPA Integration 的内部模型，Agent Experience 只能看到语义引用。 |
| 当前用法 | `docs/wayfinder/map.md`：工作包 05 “定义 MI 集成与副作用契约”；`baseline.md`：MI 技术目标和 DPA 凭据。 |
| 冲突 | TERM-002：MI 全称 Integration Mapping 已含“集成”，工作包标题“MI 集成”存在冗余表达。 |
| 状态 | 已确认（定义）；命名冗余待 T01.6 收敛 |

### 10. Action Proposal（行为提案）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：针对特定目标和已验证参数提出的不可变行为请求，绑定风险、影响、本体版本和 MI 版本。`CONTEXT-MAP.md`：Action Governance 创建和校验 Action Proposal。 |
| 当前用法 | `docs/wayfinder/tickets/07`：提案、审批、执行状态机；`AGENTS.md`：写操作默认只生成提案。 |
| 冲突 | TERM-003：名称含 “Action”，与 DPA Controller Action、M2 Behavior 易混；Proposal 与 Execution 是不同聚合（CONTEXT-MAP 明确）。 |
| 状态 | 已确认 |

### 11. Draft Application（草稿应用）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：将已验证建议值应用到原 DPA 表单但不持久化；用户仍需执行原 DPA 保存动作。 |
| 当前用法 | `CONTEXT-MAP.md`：Action Governance 在 Draft Application、Gateway Execution 和 Legacy View 之间作出受治理选择。 |
| 冲突 | TERM-011：与 DPA 自身表单“草稿（暂存）”易混——平台草稿应用与 DPA 表单草稿是不同概念。 |
| 状态 | 已确认（定义）；与 DPA 草稿概念的区分待 T01.5 细化 |

### 12. Runtime Projection（运行时投影）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：由已发布本体生成的 Agent Tool、对象视图、查询结果、行为卡片、流程、状态或关系图，不是新的业务事实来源。 |
| 当前用法 | `CONTEXT-MAP.md`：Agent Experience 使用已发布语义 Tool、Runtime Projection 和事件协议。 |
| 冲突 | TERM-006：与 `baseline.md` 中“数据库、内存索引和关系图都是可重建投影”的“投影”含义不同——前者是语义投影，后者是技术可重建视图。另与产品名 “Runtime Workbench” 相近（TERM-015）。 |
| 状态 | 已确认（定义）；语义投影与技术投影的区分待 T01.5 澄清 |

### 13. Legacy View（遗留视图）

| 维度 | 内容 |
|---|---|
| 来源 | `CONTEXT.md`：为复杂编辑、工作流或页面专有行为保留的原 DPA 页面。`AGENTS.md`：Legacy View 使用受控同源导航，不使用 `dangerouslySetInnerHTML` 注入 DPA 返回 HTML。 |
| 当前用法 | `docs/wayfinder/map.md`：不复制 DPA 复杂表单，复杂编辑回到原 DPA 页面；`tickets/09`、`tickets/13`。 |
| 冲突 | 无。 |
| 状态 | 已确认 |

## 冲突编号索引

`rg "TERM-[0-9]{3}" docs/meta-model/domain-term-inventory.md` 可定位全部冲突项。

| 编号 | 主题 | 冲突描述 | 涉及概念 | 状态 | 待裁决/已确认依据 |
|---|---|---|---|---|---|
| TERM-001 | 八类模型编号体系 | 本项目 `M1/M2/M3/M5/M6/M7/MU/MI`（`AGENTS.md`）与参考项目编号不一致：`ontology-driven-dev` 用 `M1/M2/M3/M5/M6/M7/MU`（MU=UI 模型）；`Onto-Contract` 用 `M1…M7/M9/ME`（M4=scenario、M6=compensation、M7=quality、M9=UI、ME=event）。 | Presentation / Flow / Query / 事件 | 待裁决（T01.2） | 来源：`AGENTS.md`；`D:\sharptoolbox\ontology-driven-dev\references\ontology_modeling_framework_v9.md`；`D:\sharptoolbox\Onto-Contract\models\contract\*.yaml` |
| TERM-002 | MI 命名冗余 | `Integration Mapping` 全称已含“集成”，`map.md` 工作包 05 标题写作“MI 集成”。 | Integration Mapping | 已确认（定义）、命名待收敛 | 来源：`CONTEXT.md:35`、`docs/wayfinder/map.md:51` |
| TERM-003 | Action 一词多义 | DPA Controller Action（技术动作）、M2 Behavior（业务行为）、Action Proposal（行为提案）共用 “Action/行为” 词族。 | Behavior / Action Proposal | 已确认（定义）、引用时需消歧 | 来源：`AGENTS.md`、`docs/wayfinder/masterdata-scope.md`（Controller Action）、`CONTEXT.md`（Action Proposal） |
| TERM-004 | Query 一词多义 | M7 Query（本体查询）、TanStack Query（前端库，`baseline.md:28`）、DPA SQL Query（技术查询）。 | Query | 已确认（定义）、文档书写时区分 | 来源：`docs/architecture/technology-selection/baseline.md:28` |
| TERM-005 | Flow 一词多义 | M6 Flow（业务流程）、user flows（`tickets/10` 四条关键用户路径）、DPA Workflow（遗留工作流）。 | Flow | 待裁决（T01.2/T01.4） | 来源：`docs/wayfinder/tickets/10-prototype-four-critical-user-flows.md` |
| TERM-006 | 投影一词多义 | Runtime Projection（语义投影，`CONTEXT.md`）vs “可重建投影”（技术视图，`baseline.md:13`）。 | Runtime Projection | 待裁决（T01.5） | 来源：`docs/architecture/technology-selection/baseline.md:13` |
| TERM-007 | Rule 与 validation 边界 | M3 Rule（可复用业务约束）与输入校验 validation 可能被混用；AGENTS.md 与 T01.4 明确二者不同层。 | Rule | 待裁决（T01.4） | 来源：`CONTEXT.md`、`docs/wayfinder/tickets/01`（T01.4） |
| TERM-008 | 授权 vs 审批 | Authorization（权限授权，M5/DPA 最终裁决）与 Approval（HITL 审批）中文同为“授权/审批”词族。 | Actor/Permission / Action Proposal | 已确认（定义）、书写时区分 | 来源：`CONTEXT-MAP.md`（Action Governance：Approval）、`AGENTS.md`（M5） |
| TERM-009 | MU 模型含义跨源不一致 | 本项目 MU=Presentation；`ontology-driven-dev` MU=UI 模型；`Onto-Contract` 用 M9 表示 UI。 | Presentation | 待裁决（T01.2） | 来源：`AGENTS.md`；`ontology_modeling_framework_v9.md` 第 8 章；`Onto-Contract/models/contract/m9-ui-model.yaml` |
| TERM-010 | Execution 与 Executor | Execution（执行聚合，`CONTEXT-MAP.md`）与 DPA Executor（内部执行器，`AGENTS.md`）为不同概念。 | Action Proposal（执行链） | 已确认（定义） | 来源：`CONTEXT-MAP.md`、`AGENTS.md` |
| TERM-011 | 平台草稿 vs DPA 草稿 | Draft Application（平台草稿应用）与 DPA 表单自身草稿/暂存可能混用。 | Draft Application | 待裁决（T01.5） | 来源：`CONTEXT.md` |
| TERM-012 | 缺 M4/ME 编号 | 本项目模型编号无 M4（scenario）与 ME（event）；参考项目 `Onto-Contract` 有 m4-scenario 与 me-event。事件在 CONTEXT-MAP 作为领域事件存在但不在八类模型中。 | 模型体系 | 待裁决（T01.2） | 来源：`AGENTS.md`；`Onto-Contract/models/contract/m4-scenario-model.yaml`、`me-event-model.yaml` |
| TERM-013 | SubtableType 语义归属 | `SubtableType` 是否业务对象未定：分类体系 / 配置注册表 / 能力选择器 / 技术聚合入口。 | Business Object | 待证据（T02/证据快照） | 来源：`docs/wayfinder/masterdata-scope.md`“范围锚点” |
| TERM-014 | Identity 命名 | `IdentityContext`（字段/对象，`tickets/04`）与限界上下文 “Identity and Audit”（`CONTEXT-MAP.md`）名称相近。 | 身份 | 已确认（定义）、书写时区分上下文名与对象名 | 来源：`CONTEXT-MAP.md`、`docs/wayfinder/tickets/04` |
| TERM-015 | Runtime Workbench 与 Runtime Projection | 产品名 “Runtime Workbench”（`CONTEXT.md`）与 “Runtime Projection”（语义投影）名称相近。 | Runtime Projection | 已确认（定义）、书写时区分 | 来源：`CONTEXT.md` |
| TERM-016 | Candidate 与 DRAFT | `candidate-generator` 生成 DRAFT YAML（`AGENTS.md`），`.build/candidates/` 是临时候选区，与 “已发布模型” 相对。 | 模型生命周期 | 已确认（定义） | 来源：`AGENTS.md`、`tools/README.md` |
| TERM-017 | Execution 与 “执行” 的层混用 | “执行” 在 `AGENTS.md` 中既指平台执行链（Policy→HITL→Execution）也指 DPA 业务执行；需区分“平台侧执行”与“DPA 侧执行”。 | Action Proposal | 待裁决（T01.4） | 来源：`AGENTS.md` |
| TERM-018 | “证据” 与 “事实” 混用 | Evidence 是总称（含 FACT/INFERENCE/ASSUMPTION），文档中可能出现把 FACT 直接称为 “证据” 或把推断称为 “事实”。 | Evidence | 已确认（定义）、引用时区分 | 来源：`codebase-reverse/references/evidence-protocol.md` |

## 待裁决项来源可追溯性

所有“待裁决”冲突项均可追溯：

- 模型编号体系（TERM-001/009/012）：`AGENTS.md` 与 `D:\sharptoolbox\ontology-driven-dev\references\ontology_modeling_framework_v9.md`、`D:\sharptoolbox\Onto-Contract\models\contract\*.yaml`。
- MasterData 实例（TERM-013）：`docs/wayfinder/masterdata-scope.md` 范围锚点，最终以正式 Evidence Snapshot（工作包 02）为准。
- 运行时/执行层（TERM-005/006/007/011/017）：`docs/architecture/technology-selection/baseline.md`、`docs/architecture/progressive-ddd.md`、`CONTEXT.md`、`CONTEXT-MAP.md`。

## 后续 Task 引用约定

- 本清单的冲突项由 T01.2（模型职责边界）、T01.3（数据形状）、T01.4（行为/接口/规则/执行）、T01.5（运行时概念）分别裁决。
- 所有 `TERM-XXX` 编号保持稳定；T01.6 将把已裁决项写入 `domain-language.md`，未裁决项保留为阻塞项。
- 跨文档首次使用核心概念时，应引用本清单对应行。

## 验证记录

- 覆盖检查：13 个核心概念均包含“来源、当前用法、冲突、状态”四列（见“逐项清单”）。
- 冲突定位：`rg "TERM-[0-9]{3}" docs/meta-model/domain-term-inventory.md` 可定位全部 18 个冲突项。
- 可追溯性：每个待裁决项均可追溯到具体文档路径、参考项目文件或 MasterData 示例。
- 命令：`git diff --check` 应通过（本文档无尾随空白）。
