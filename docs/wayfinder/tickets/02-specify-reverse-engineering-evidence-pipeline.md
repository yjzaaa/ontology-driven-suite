---
title: 定义 DPA 反向工程证据流水线
status: closed
labels:
  - wayfinder:research
parent: ../map.md
assignee: copilot-agent
blocked_by: []
---

## 工作包目标

规定可重复执行的 DPA 反向工程证据流水线，使源码、数据库、Job 和 UI 资产被稳定识别、关联、快照化并计量覆盖率。所有结论必须保留 `FACT`、`INFERENCE`、`ASSUMPTION` 来源，自动提取不得越过人工审核边界，也不得因证据存在而获得运行执行权。

试点扫描范围以 [MasterDataPROnlineApprovalController / SubtableType](../masterdata-scope.md) 为锚点：完整盘点枚举值和直接使用点，只沿可达调用链扩展，不扫描整个 MasterData 作为试点交付范围。

## 必需 Task

### [x] T02.1 建立反向工程资产清单与扫描边界

**达成目标**

形成 DPA 待扫描资产的分类清单、纳入规则、排除规则和责任仓库基线，避免扫描范围依赖个人记忆。

**输入**

- DPA 源码仓库及固定 revision
- 数据库对象清单
- Job、脚本和前端项目清单
- `docs/wayfinder/map.md` 的已确认边界

**执行步骤**

1. 按 Controller/route、过滤器/权限、业务服务、状态转换、SQL、存储过程、表、Job、callback、UI 页面与绑定分类资产。
2. 为每类资产记录仓库、revision、根路径、技术栈、扫描方式和负责人。
3. 定义生成代码、第三方依赖、测试夹具、废弃模块和不可访问资产的纳入或排除规则。
4. 为不可扫描资产分配缺口编号 `GAP-XXX`，记录原因和补证方式。

**产出物**

- `docs/meta-model/reverse-engineering-asset-inventory.md`

**验证方式**

- 清单覆盖源码、数据库、Job 和 UI 四个资产域，每项都有固定 revision 或等价快照标识。
- 每个排除项都有规则和理由，不允许使用“暂不处理”作为唯一说明。
- 任一缺失资产都可通过 `GAP-XXX` 定位到责任人、影响范围和补证方式。

### [x] T02.2 定义证据记录契约与稳定标识

**前置 Task**

- T02.1

**达成目标**

定义机器证据、推断和假设的统一信封、稳定 ID、定位信息及派生关系，使每条结论可追溯和可校验。

**输入**

- `docs/meta-model/reverse-engineering-asset-inventory.md`
- `docs/AGENTS.md` 的引用要求

**执行步骤**

1. 定义 `FACT`、`INFERENCE`、`ASSUMPTION` 的准入条件和禁止互相替代的规则。
2. 规定证据字段，至少包含 `evidence_id`、`kind`、`source_repo`、`revision`、`path`、`symbol`、`line_range`、`extractor`、`observed_at`、`derived_from` 和 `confidence`。
3. 定义源码符号、路由、数据库对象、Job、UI 元素及跨资产关系的稳定 ID 生成规则。
4. 编写有效、缺字段、悬空派生和 revision 不一致的样例。

**产出物**

- `docs/meta-model/evidence-contract.md`
- `schemas/evidence/evidence-record.schema.json`
- `evidence/examples/evidence-records.json`

**验证方式**

- 示例文件可通过 `schemas/evidence/evidence-record.schema.json` 校验。
- 每个 `INFERENCE` 和 `ASSUMPTION` 都至少有一个 `derived_from`，且引用存在于同一快照或声明的外部快照。
- 相同 revision 的同一资产重复扫描产生相同稳定 ID，不把绝对工作目录或扫描时间写入 ID。

### [x] T02.3 规定 codebase-memory 图谱提取与 Roslyn 补证

**前置 Task**

- T02.1
- T02.2

**达成目标**

规定以 codebase-memory MCP 为主发现 Controller、route、过滤器、权限、业务调用、状态转换、callback 与副作用，并仅对验证后的能力缺口使用定向 .NET/Roslyn extractor。

**输入**

- `docs/meta-model/reverse-engineering-asset-inventory.md`
- `docs/meta-model/evidence-contract.md`
- DPA 代表性 Controller 到业务服务的调用链
- codebase-memory MCP 的索引、搜索、图查询、路径追踪和变化检测能力

**执行步骤**

1. 定义 codebase-memory 项目索引模式、文件过滤、分页、图查询模板和索引新鲜度检查。
2. 规定从 Route 或 Controller 到数据库或外部调用的调用边、数据流和最大展开边界。
3. 建立噪声过滤规则，排除第三方脚本中的伪 Route、生成文件和无关依赖节点。
4. 用最小 ASP.NET fixture 测量 attribute、Filter、接口分派、依赖注入、EF/Dapper 和存储过程的识别覆盖。
5. 仅为未达门槛的语义设计窄范围 Roslyn extractor，并把结果转换为相同证据格式。
6. 对动态调用、反射、字符串路由和无法解析的分派生成明确的 `ASSUMPTION` 或 `GAP-XXX`，不得伪装为 `FACT`。

**产出物**

- `docs/meta-model/codebase-memory-extraction.md`
- `docs/meta-model/codebase-memory-gap-analysis.md`
- 条件产出：`docs/meta-model/roslyn-gap-extractors.md`
- `evidence/examples/masterdata-call-chain.json`

**验证方式**

- 对选定 MasterData 入口重复运行提取时，节点、边和稳定 ID 顺序无关且内容一致。
- 样例调用链可从 Controller/route 追溯到权限、业务服务及已发现的副作用。
- 对 codebase-memory 输出中的 Route 和调用边进行抽样准确率检查，并记录误报、漏报和截断。
- 未达到覆盖门槛的能力必须有 Roslyn 补证 fixture；达到门槛的能力不得重复开发 extractor。
- 动态或未解析调用在样例中具有显式缺口，不存在无证据补全的调用边。

### [x] T02.4 规定数据库与 Job 证据提取

**前置 Task**

- T02.1
- T02.2

**达成目标**

定义 SQL、存储过程、表、数据库读写、调度 Job、重试和 callback 的提取与关联规则。

**输入**

- 数据库对象清单和只读元数据
- DPA 内嵌 SQL、ORM/ADO.NET 调用证据
- Job 配置、入口和调度信息

**执行步骤**

1. 规定静态 SQL、参数化 SQL、存储过程调用和动态 SQL 的解析层级。
2. 为表、列、存储过程及读写关系生成稳定 ID 和证据定位。
3. 关联 Job 调度定义、代码入口、数据库访问、外部调用、重试和 callback。
4. 对无法证明只读、动态拼接或跨事务副作用标记 `MIXED/HIGH` 和人工审核要求。

**产出物**

- `docs/meta-model/database-job-evidence-extraction.md`
- `evidence/examples/masterdata-database-job-links.json`

**验证方式**

- 样例中每条数据库关系均标明 `READ`、`WRITE`、`MIXED` 或 `UNKNOWN`，并链接到证据。
- 存储过程只在可解析语句或数据库元数据支持时细分表级关系，否则保留为存储过程级事实。
- 任一 `MIXED`、`UNKNOWN` 或动态 SQL 关系均不能被声明为可自动执行的纯读能力。

### [x] T02.5 规定 UI 页面与绑定证据提取

**前置 Task**

- T02.1
- T02.2

**达成目标**

定义页面、组件、表单字段、事件处理器、route/API 调用、DTO 和展示条件之间的可追溯绑定。

**输入**

- DPA 前端项目及固定 revision
- MasterData 页面、脚本、ViewModel 和网络调用证据
- `docs/meta-model/evidence-contract.md`

**执行步骤**

1. 定义页面、组件、字段、命令和请求调用的资产类型与稳定 ID。
2. 规定模板绑定、事件绑定、条件可见性、校验提示和 DTO 字段映射的提取规则。
3. 将 UI 调用与后端 route、权限和调用链按证据关联。
4. 对运行时生成控件、字符串拼接字段和无法静态解析的绑定记录缺口及人工补证入口。

**产出物**

- `docs/meta-model/ui-binding-evidence-extraction.md`
- `evidence/examples/masterdata-ui-bindings.json`

**验证方式**

- 样例至少包含页面到字段、字段到 DTO、事件到 route 三类关系。
- 每条跨前后端关系均能定位双方 revision 和源文件，不使用仅凭命名相似得出的 `FACT`。
- 无法解析的绑定被计入缺口和覆盖率分母。

### [x] T02.6 定义快照、覆盖率与质量门槛

**前置 Task**

- T02.3
- T02.4
- T02.5

**达成目标**

规定证据快照的目录、清单、完整性校验和分层覆盖率，确保扫描结果可比较且不会用单一百分比掩盖缺口。

**输入**

- T02.3 至 T02.5 的提取规范和样例
- `docs/meta-model/reverse-engineering-asset-inventory.md`

**执行步骤**

1. 定义快照 ID、源 revision 集、生成器版本、配置摘要、文件清单和内容摘要。
2. 分别定义资产发现、符号解析、关系解析、证据定位和人工审核覆盖率。
3. 规定 Controller、数据库、Job、UI 各资产域的分子、分母和不可扫描项处理方式。
4. 定义快照可接受、降级和阻断条件，并给出 MasterData 覆盖率样例。

**产出物**

- `docs/meta-model/evidence-snapshot-and-coverage.md`
- `schemas/evidence/snapshot-manifest.schema.json`
- `evidence/examples/masterdata-snapshot-manifest.json`
- `evidence/examples/masterdata-coverage-report.json`

**验证方式**

- 快照样例可通过 manifest Schema 校验，且文件摘要能发现缺失或被替换的证据文件。
- 覆盖率报告能分别显示四个资产域和五个覆盖层级，不只给出总百分比。
- 所有 `GAP-XXX` 均进入对应覆盖率分母或有书面排除依据。

### [x] T02.7 定义增量变更检测与失效传播

**前置 Task**

- T02.2
- T02.6

**达成目标**

规定源代码或配置变更如何使证据、派生结论和候选模型失效，并限制增量重扫范围。

**输入**

- `docs/meta-model/evidence-contract.md`
- `docs/meta-model/evidence-snapshot-and-coverage.md`
- 连续两个 DPA revision 的代表性变更

**执行步骤**

1. 定义新增、修改、删除、重命名和仅移动资产的判定规则。
2. 按 `derived_from` 和调用/绑定关系计算失效闭包。
3. 规定何时局部重扫、何时必须重建整个 project、数据库域或 UI 域快照。
4. 定义失效证据、待复核推断和受影响候选 YAML 的状态及报告格式。

**产出物**

- `docs/meta-model/incremental-evidence-invalidation.md`
- `evidence/examples/masterdata-change-impact.json`

**验证方式**

- 对样例 revision 差异重复计算得到相同的新增、失效和重扫集合。
- 删除或语义修改上游证据时，所有派生 `INFERENCE`、`ASSUMPTION` 和候选模型均进入影响集合。
- 文件移动但稳定符号未变时不会无条件制造新的业务资产 ID。

### [x] T02.8 划定自动提取与人工审核边界

**前置 Task**

- T02.3
- T02.4
- T02.5
- T02.6
- T02.7

**达成目标**

明确哪些结论可自动接受、哪些必须人工确认、哪些证据不足时必须阻断，并形成可审计的审核队列契约。

**输入**

- T02.3 至 T02.7 的规范和样例
- `FACT`、`INFERENCE`、`ASSUMPTION` 证据等级
- `MIXED/HIGH` 风险边界

**执行步骤**

1. 按结论类型、证据等级、覆盖率、动态特征和副作用等级建立审核决策表。
2. 定义审核项字段、分派、接受、修正、拒绝、补证和重新打开状态。
3. 规定人工裁决不得覆盖原始证据，只能追加带身份和时间的决策记录。
4. 为动态 SQL、反射调用、UI 动态绑定、混合副作用和权限不明各编写一个审核样例。

**产出物**

- `docs/meta-model/automated-extraction-review-boundary.md`
- `schemas/evidence/review-item.schema.json`
- `evidence/examples/masterdata-review-queue.json`

**验证方式**

- 五类高风险样例均被稳定路由到人工审核或阻断，不会自动升级为已确认事实。
- 接受、修正和拒绝操作均保留操作者、理由、时间和所依据的证据 ID。
- 文档明确机器证据、审核结果和候选 YAML 均不授予运行执行权。

### [x] T02.9 明确源码分析组件与人员责任

**前置 Task**

- T02.8

**达成目标**

明确“谁执行扫描、谁解释技术事实、谁裁决业务语义、谁批准发布”，避免把 DPA 源码分析误解为由 Agent/LLM 自主完成。

**输入**

- T02.1 至 T02.8 的扫描、证据和审核规则。
- `tools/codebase-memory-adapter/README.md`。
- 平台工程、DPA 技术、领域、安全和发布治理角色。

**执行步骤**

1. 指定 codebase-memory MCP 为源码图谱、符号搜索、调用链、数据流和变化分析的首选引擎。
2. 指定 Python Evidence Adapter 为查询编排、证据规范化、快照、稳定 ID 和覆盖率的责任组件。
3. 仅在可重复 fixture 证明 MCP 能力缺口时，由平台工程团队开发窄范围 C#/.NET Roslyn extractor。
4. 指定 DPA 技术负责人复核调用链、权限、事务、SQL、Job 和副作用。
5. 指定领域专家或本体审核员裁决业务对象、行为、规则、流程和术语。
6. 指定安全与数据负责人复核身份、敏感字段、数据范围和高风险能力。
7. 指定本体发布审批人决定候选模型是否进入 `PUBLISHED`。
8. 明确 Agent/LLM 只能辅助候选模型整理，不得生成 `FACT`、替代人工裁决或直接发布。

**产出物**

- `docs/meta-model/source-analysis-responsibility-matrix.md`
- `docs/meta-model/source-analysis-review-workflow.md`
- 更新后的 `tools/codebase-memory-adapter/README.md`

**验证方式**

- 对一条 MasterData 调用链执行桌面走查，每个扫描、解释、修正、审核和发布动作都有唯一责任角色。
- 任一自动结论都能指出 codebase-memory 索引版本、查询模板和适配器版本；Roslyn 补证还必须记录 extractor 版本。
- Agent/LLM 输出只能进入候选区，无法直接写入 `evidence/snapshots/` 的事实记录或 `models/<domain>/` 的发布模型。

**边界**

- 人工审核不手工改写原始机器证据，只追加裁决和修正记录。
- DPA 技术负责人不单独决定业务本体语义，本体审核员也不单独确认代码副作用。

### [x] T02.10 封装 DPA 专用 codebase-reverse Skill

**前置 Task**

- T02.3
- T02.4
- T02.5
- T02.8
- T02.9

**达成目标**

在不复制和分叉通用规则的前提下，将 `D:\sharptoolbox\codebase-reverse` 包装为 DPA 专用逆向工程 Skill，统一编排扫描器、证据生成、人工审核和候选模型输出。

**输入**

- `D:\sharptoolbox\codebase-reverse\SKILL.md`、`references/`、`scripts/validate_meta_model.ps1` 和 `agents/openai.yaml`。
- T02.1 至 T02.9 的 DPA 资产、证据、扫描和责任规则。
- ASP.NET MVC、C#、Roslyn、DPA Filter/BLL/Service/Repository、SQL 和 UI 绑定约定。

**执行步骤**

1. 保留 `codebase-reverse` 作为通用上游 Skill，不在本项目内复制其全部引用文档。
2. 创建 DPA 包装 Skill，描述触发条件、输入参数、阶段、产出、人工门禁和失败规则。
3. 将 Spring/MyBatis 等上游默认识别规则映射为 ASP.NET MVC、Roslyn、EF/Dapper、存储过程和 DPA 自定义权限规则。
4. 定义 Skill 如何调用 codebase-memory MCP 和 Evidence Adapter，并在需要时调用定向 Roslyn extractor；Skill 不直接把 LLM 推断写成 `FACT`。
5. 定义通用 Markdown 元模型到 `evidence/snapshots/<revision>/` 证据和 `.build/candidates/` 候选 YAML 的转换边界。
6. 为全量基线、单功能 `F-FULL`、技术无关 `F-REQ` 和增量重扫提供 DPA 示例提示词。
7. 增加包装 Skill 的静态校验和最小端到端 fixture。

**产出物**

- `skills/dpa-codebase-reverse/SKILL.md`
- `skills/dpa-codebase-reverse/REFERENCE.md`
- `skills/dpa-codebase-reverse/EXAMPLES.md`
- `skills/dpa-codebase-reverse/scripts/validate-dpa-reverse.ps1`
- `docs/meta-model/codebase-reverse-adaptation.md`

**验证方式**

- Skill 描述可由“DPA 源码逆向、Controller 到数据库穿透、MasterData 反向建模、混合副作用分析”等请求稳定触发。
- `SKILL.md` 保持简洁，详细规则只引用一层 `REFERENCE.md`，脚本处理确定性校验。
- 使用一个最小 ASP.NET MVC fixture 执行后，输出同时包含源码资产清单、调用链、数据库访问、权限和证据等级。
- 相同输入重复执行产生稳定证据 ID；LLM 推断只进入候选或审核队列。
- 上游 `codebase-reverse` 更新时，包装层能够通过引用或版本记录升级，不需要手工合并整套复制文档。

**边界**

- 包装 Skill 是工作流编排和方法约束，不替代 codebase-memory MCP、Evidence Adapter 或定向 Roslyn extractor。
- 不把通用 `codebase-reverse` 的 Java 偏好原样当作 DPA 事实。
- 不允许 Skill 直接发布本体、注册 Agent Tool 或调用 DPA 写接口。

## 工作包验收

- T02.1 至 T02.10 全部完成，所有 Schema 示例通过相应 Schema 校验。
- 选定 MasterData 纵向样例可从 UI 或 route 追溯到权限、调用链、数据库/Job 副作用及原始证据位置。
- 相同 revision 与扫描配置重复运行得到相同稳定 ID、关系和覆盖率结果。
- 连续 revision 的增量样例能产生可解释的失效闭包、重扫范围和人工审核队列。
- 自动提取边界明确阻断动态、证据不足或 `MIXED/HIGH` 风险结论被当作可执行能力。
- 自动扫描、技术复核、业务裁决、安全复核和发布审批均有唯一责任角色，Agent/LLM 不具有事实确认或发布权。
- DPA 专用包装 Skill 能编排通用 `codebase-reverse` 方法、codebase-memory MCP、Evidence Adapter 和必要的 Roslyn 补证，并保持候选模型与运行时发布权限隔离。

## 解决记录

**决策摘要**：定义 DPA 反向工程证据流水线——资产清单（四资产域 + 5 个 GAP）、证据信封契约（FACT/INFERENCE/ASSUMPTION + 稳定 ID）、codebase-memory 主引擎 + 定向 Roslyn 补证（路由/分派/副作用）、数据库与 Job 证据（含 MobileHaasJob 跨库写）、UI 绑定证据、快照与分层覆盖率、增量失效闭包、自动提取与人工审核边界、责任矩阵，并封装 DPA 专用 codebase-reverse 包装 Skill。

**关键取舍**：codebase-memory 擅长符号/调用链但 Route 识别存在缺口（实测 Route 76 个几乎全空），故 Route/分派/副作用需定向 Roslyn extractor（GAP-001/002/003），达到门槛的符号与调用链不重复开发。LLM 只辅助候选整理，不生成 FACT、不替代人工裁决、不直接发布。

**验证结果**：MCP 实测调用链（`UpdateSubtableData` → Repository → 缓存）可追溯到权限与副作用；全部 Schema 通过 jsonschema 校验；样例 JSON 有效；`validate-dpa-reverse.ps1` 通过（exit=0）；`git diff --check` 通过。

**产出物**：13 份 `docs/meta-model/*.md`、3 份 `schemas/evidence/*.json`、8 份 `evidence/examples/*.json`、`skills/dpa-codebase-reverse/`（SKILL/REFERENCE/EXAMPLES/validate 脚本）、更新 `tools/codebase-memory-adapter/README.md`。

**遗留项**：TERM-013（`SubtableType` 是否业务对象）仍待正式 Evidence Snapshot 固化；GAP-004（生产库元数据）与 GAP-005（Job 实际调度）需 DBA/运维补证。
