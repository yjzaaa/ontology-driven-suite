---
title: 定义产品界面与元数据驱动渲染
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 03-define-ontology-contracts-and-lifecycle.md
  - 08-define-agent-tool-and-runtime-protocol.md
---

## 工作包目标

定义 Ontology Studio、Runtime Workbench、Ontology Explorer、行为中心、审计中心与原 DPA 页面之间清晰的产品信息架构和导航边界，并形成受信任 Renderer 契约。界面必须从已发布本体与运行时协议投影对象、集合、关系、行为提案、执行状态和本体图，不生成第二套复杂 CRUD；所有高风险交互都应可理解、可审核、可追踪且满足可访问性要求。

## 必需 Task

### [ ] T09.1 定义产品信息架构与界面职责

- **达成目标**：确定各产品界面的用户、核心任务、信息范围、入口、出口和禁止承担的职责。
- **输入**：`README.md`、`docs/wayfinder/map.md`、工作包 03 与 08 的模型和运行时协议。
- **执行步骤**：
  1. 为 Ontology Studio、Runtime Workbench、Ontology Explorer、行为中心、审计中心和 Legacy DPA 建立职责卡。
  2. 定义全局导航、领域导航、对象上下文和跨界面深链规则。
  3. 标明模型编辑、运行查询、审核行为、查看审计、执行原业务表单分别归属何处。
  4. 列出禁止复制的 DPA 能力和必须返回 Legacy View 的任务。
- **产出物**：`docs/specification/product/product-information-architecture.md`；`docs/specification/product/surface-responsibility-matrix.yaml`；`docs/specification/product/navigation-map.mmd`。
- **验证方式**：用 MasterData 的建模、查询、审核、应用草稿和审计五条任务逐步走查；每一步必须有唯一责任界面和明确返回路径，不出现跨界面重复编辑职责。
- **边界**：不在本平台重建复杂 DPA 表单、工作流设计器或完整后台管理系统。

### [ ] T09.2 定义受信任 Renderer 契约与组件注册机制

- **达成目标**：定义由平台控制、只渲染允许类型和字段的 Renderer 协议，禁止模型输出任意 HTML、脚本或组件代码；LLM 不参与运行期渲染，只能选择已发布视图与行为。
- **输入**：T09.1、工作包 03 的展示元数据、工作包 08 的 Tool、事件与 artifact Schema。
- **执行步骤**：
  1. 定义 `renderer_id`、`projection_type`、`schema_version`、`data`、`actions`、`source_refs` 和 `trust_metadata`。
  2. 建立 Renderer allowlist、组件版本、Schema 验证和未知类型降级规则。
  3. 规定文本转义、链接协议、媒体来源、内容安全策略和敏感字段遮蔽。
  4. 定义加载、空、部分数据、错误、过期和权限变化状态。
  5. 规定 LLM 与渲染的边界：模型在运行期只能引用已发布的 Renderer/视图标识与行为标识；任何模型生成内容进入投影前必须通过 Schema 校验，校验失败降级为纯文本错误卡。
  6. 定义写表单渲染路由：读取走对象/集合投影；简单写表单仅在通过工作包 05 T05.8 三项证据门槛且存在已发布 MI 时由 M1+M2 自渲染，MU 只提供封闭词表内的布局提示，禁止像素级复刻；复杂表单一律返回 Legacy View。
- **产出物**：`docs/specification/product/trusted-renderer-contract.md`；`models/schemas/renderers/renderer-envelope.schema.json`；`docs/specification/product/renderer-registry.yaml`。
- **验证方式**：用有效投影及脚本注入、未知 Renderer、越权字段、危险链接等反例执行 Schema 与安全测试；反例必须安全拒绝或降级为纯文本错误卡；模型伪造 `renderer_id` 或在投影字段注入模型生成结构化内容的反例必须被拒绝。
- **前置 Task**：T09.1。

### [ ] T09.3 定义业务对象与集合投影

- **达成目标**：为对象详情、集合、字段组、分页、排序、筛选和敏感字段建立一致的元数据驱动呈现规则。
- **输入**：T09.2、工作包 06 的对象与集合投影、数据范围和字段敏感度。
- **执行步骤**：
  1. 定义对象标题、标识、摘要字段、字段分组、状态、来源和更新时间。
  2. 定义集合列选择、分页、排序、筛选摘要、总数不确定和截断提示。
  3. 规定字段级隐藏、遮蔽、不可用原因和按需加载。
  4. 规定卡片与表格之间的响应式切换以及空结果、部分结果和陈旧数据呈现。
- **产出物**：`docs/specification/product/object-and-collection-rendering.md`；`models/schemas/renderers/object-view.schema.json`；`models/schemas/renderers/collection-view.schema.json`；`docs/specification/product/examples/masterdata-object-collection/`。
- **验证方式**：将固定对象与集合夹具渲染为规范化快照；检查字段顺序、分页、脱敏、截断和空状态，并验证不同用户只看到其数据范围内字段与记录。
- **前置 Task**：T09.2。

### [ ] T09.4 评估 visual-model 并定义关系、图表与本体图投影

- **达成目标**：评估 `D:\sharptoolbox\visual-model` 可复用的视觉语义与交互模式，区分业务数据关系视图、聚合图表和 Ontology Explorer 本体图，防止把内部实现细节误呈现为业务事实。
- **输入**：T09.2、工作包 03 的关系与本体模型、工作包 06 的聚合规则、`D:\sharptoolbox\visual-model` 的模型结构、视觉规范和可视化实现。
- **执行步骤**：
  1. 盘点 `visual-model` 的节点语义、边语义、分层方式、布局、筛选、状态表达、证据跳转和交互能力。
  2. 将其能力逐项分类为“直接复用”“参考后重做”“当前不采用”，并记录理由；不得直接把该项目当作生产运行时组件。
  3. 定义关系列表、邻接对象、方向、基数、来源和可导航目标。
  4. 定义允许的图表类型、维度、度量、单位、截断和数据新鲜度。
  5. 定义本体图的节点、边、分层、过滤、展开、证据链接和版本差异投影。
  6. 规定大图降级、循环关系、未知引用和无权限节点的处理。
- **产出物**：`docs/specification/product/visual-model-capability-mapping.md`；`docs/specification/product/relationship-chart-and-ontology-graph.md`；`models/schemas/renderers/relationship-view.schema.json`；`models/schemas/renderers/chart-view.schema.json`；`models/schemas/renderers/ontology-graph-view.schema.json`。
- **验证方式**：能力映射必须覆盖 `visual-model` 中与本体可视化相关的主要模块，并为每项给出采用结论和证据路径；再用小型、循环、大规模和含无权限节点的固定图夹具执行快照与可达性测试。聚合值必须可追踪到查询结果，隐藏节点不得通过边或计数泄露。
- **前置 Task**：T09.3。
- **边界**：`visual-model` 只作为视觉语义、交互模式和投影设计参考；已发布 YAML 仍是事实源，Ontology Explorer 不直接依赖其内部数据模型或运行时实现。

### [ ] T09.5 定义行为审核卡与执行状态呈现

- **达成目标**：使用户在批准、拒绝、取消或跟踪行为时能看清意图、风险、差异、影响、授权主体和当前状态。
- **输入**：T09.2、工作包 07 的 `ActionProposal`、影响预览、状态机与收据，工作包 08 的运行时事件。
- **执行步骤**：
  1. 定义审核卡必显字段、参数摘要、变更差异、影响范围、风险原因和过期时间。
  2. 定义批准、拒绝、取消和重新校验操作的可用条件及二次确认。
  3. 定义执行中、成功、失败、结果不确定、补偿中和待人工处置的状态文案与动作。
  4. 规定事件断线、状态陈旧、审批 Token 失效和 DPA 最终拒绝时的可信提示。
- **产出物**：`docs/specification/product/action-review-and-execution-ui.md`；`models/schemas/renderers/action-review-card.schema.json`；`docs/specification/product/examples/action-review-states/`。
- **验证方式**：对工作包 07 的全部状态和关键非法操作生成 UI 快照与交互断言；高风险批准前必须展示风险与影响，结果不确定不得显示为成功。
- **前置 Task**：T09.2。
- **边界**：Renderer 不签发或修改 `ApprovalToken`，不自行推断执行成功。

### [ ] T09.6 定义 Legacy View 与 Launch Ticket

- **达成目标**：建立从平台安全进入原 DPA 页面、应用草稿并返回原上下文的导航协议。
- **输入**：T09.1、工作包 07 的 `DraftApplication`、工作包 04 的会话边界。
- **执行步骤**：
  1. 定义 `LegacyViewRef` 的业务目标与显示元数据，不向 Agent 暴露真实路由拼接规则。
  2. 定义短期单次 `LaunchTicket` 的主体、目标、草稿引用、回跳地址、过期和消费规则。
  3. 规定 Gateway 将语义目标解析为 allowlist 中的 DPA 路由并完成会话检查。
  4. 定义页面不存在、无权限、草稿过期、浏览器阻止弹窗和保存后返回的用户体验。
  5. 规定自渲染写表单界面常驻“在原系统打开”入口，复用同一 LegacyViewRef 与 LaunchTicket 协议，并覆盖从对话与从表单两个入口的跳转与回跳路径。
- **产出物**：`docs/specification/product/legacy-view-and-launch-ticket.md`；`models/schemas/runtime/legacy-view-ref.schema.json`；`models/schemas/runtime/launch-ticket.schema.json`；`docs/specification/product/examples/legacy-launch-cases.yaml`。
- **验证方式**：重放有效、篡改、过期、重复使用、无权限和未知目标案例；只有有效 Ticket 能解析到 allowlist 路由，且 Agent transcript 中不出现内部 URL 或会话凭据。
- **前置 Task**：T09.5。
- **边界**：`LaunchTicket` 不替代 DPA 登录、授权、业务校验或保存动作。

### [ ] T09.7 定义可访问性与响应式呈现基线

- **达成目标**：为所有核心 Renderer 和跨界面流程建立可测试的可访问性、键盘和响应式要求。
- **输入**：T09.2 至 T09.6 的界面与组件契约。
- **执行步骤**：
  1. 规定语义结构、键盘顺序、焦点管理、可见焦点、跳转链接和对话框行为。
  2. 规定颜色对比、非颜色状态提示、文本缩放、减少动态效果和屏幕阅读器名称。
  3. 为图表和本体图定义等价文本、数据表或关系列表。
  4. 定义窄屏、宽屏、缩放和长文本下的布局验收尺寸。
- **产出物**：`docs/specification/product/accessibility-and-responsive-baseline.md`；`docs/specification/product/accessibility-test-matrix.yaml`。
- **验证方式**：对对象、集合、图、审核卡和 Legacy View 入口执行自动可访问性检查与全键盘人工脚本；所有关键任务无需鼠标可完成，图形信息存在等价文本。
- **前置 Task**：T09.3、T09.4、T09.5、T09.6。

### [ ] T09.8 定义可信交互准则与跨界面验收样例

- **达成目标**：统一来源、权限、数据新鲜度、风险、不可逆性和外部跳转提示，使用户能判断系统当前知道什么、将做什么和由谁负责。
- **输入**：T09.1 至 T09.7、工作包 08 的端到端 transcript。
- **执行步骤**：
  1. 定义所有投影必须展示或可展开查看的来源、版本、更新时间、范围和关联 ID。
  2. 规定加载与执行进度不得伪装完成，推断内容必须与事实数据视觉区分。
  3. 规定破坏性操作、外部 Legacy 跳转、权限拒绝、部分数据和结果不确定的文案模式。
  4. 将查询、审核、Draft Application、Gateway Execution 和审计追踪整理为跨界面验收样例。
- **产出物**：`docs/specification/product/trustworthy-interaction-guidelines.md`；`docs/specification/product/examples/cross-surface-acceptance/`；`docs/specification/product/cross-surface-traceability-matrix.yaml`。
- **验证方式**：逐条重放跨界面样例并检查信息来源、状态、风险和下一步动作；让未参与设计的评审者仅依据产出物回答验收问题，答案必须与状态机和 transcript 一致。
- **前置 Task**：T09.7。

### [ ] T09.9 完成前端渲染与可视化技术选型

- **达成目标**：为 Runtime Workbench 和 Ontology Explorer 选择可实施的前端框架、Renderer 机制、关系图引擎、自动布局引擎和统计图表组件，并明确 `visual-model` 的复用方式。
- **输入**：T09.2 至 T09.8 的协议和交互要求；[技术选型基线](../../architecture/technology-selection/baseline.md)；`D:\sharptoolbox\visual-model`；独立 Agent UI 的会话与渲染要求；候选技术 React Flow、Cytoscape.js、ELK.js、Dagre、ECharts 及同类方案的官方资料。
- **执行步骤**：
  1. 固化必须满足的评价维度：TypeScript 类型支持、React 集成、千级节点性能、自定义节点与边、自动布局、增量更新、可访问性、许可证、维护活跃度、包体积、导出能力和团队学习成本。
  2. 分别比较关系图引擎、布局引擎、图表引擎和 Renderer 注册机制；不得把不同类别的库放在同一维度直接替代比较。
  3. 使用同一组 MasterData 小图、循环图和千级节点图建立最小 PoC，测量首屏时间、交互帧率、布局耗时、内存和开发复杂度。
  4. 对照 `visual-model`，明确可复用的是视觉语言、交互模式、数据转换代码还是组件代码，并记录不复用部分及原因。
  5. 形成首选方案、备选方案、淘汰理由、版本锁定策略和替换边界。
  6. 若选型属于难以撤销且存在真实权衡的长期决策，创建正式 ADR。
- **产出物**：`docs/architecture/technology-selection/frontend-visualization-options.md`；`docs/architecture/technology-selection/frontend-visualization-benchmark.md`；`docs/architecture/technology-selection/visual-model-reuse-decision.md`；必要时新增 `docs/adr/` 下的前端可视化选型 ADR。
- **验证方式**：候选矩阵中的每个评分都有官方资料、仓库证据或 PoC 测量支撑；首选方案通过 T09.2 至 T09.8 的全部必需能力；独立评审者可以根据相同数据复现选型结论。
- **前置 Task**：T09.8。
- **边界**：技术选型不得改变 YAML 作为事实源的原则；不得因为复用 `visual-model` 而继承其不适合生产运行时的内部模型或耦合。

### [ ] T09.10 定义 UI 证据提取与 MU 候选生成管线

- **达成目标**：建立从 DPA 视图证据到候选 MU 的构建期管线：解析器产出 UI 事实（控件树、字段绑定、校验器、布局拓扑，带 `FACT`/`INFERENCE` 与文件行号），LLM 仅在构建期将 UI 事实归纳为候选 MU（布局提示映射到封闭词表、字段绑定到 M1 别名），人审后进入既定发布生命周期；运行期不存在 LLM 渲染路径。
- **输入**：工作包 02 的证据契约与快照；工作包 03 的 MU Presentation Schema 与生命周期；T09.2 的渲染契约与封闭布局词表；MasterData 目标页面的 `.cshtml` 模板、渲染 DOM 抽样与受控截图。
- **执行步骤**：
  1. 定义视图证据提取器：Razor/HTML 静态解析（lxml/BeautifulSoup4 候选）+ Playwright DOM 抽样与受控截图（辅助证据）；输出必须带证据等级、文件行号和 revision。
  2. 定义封闭布局提示词表与字段类型映射，禁止开放文本布局描述；绑定语义锚定到字段名/标签/绑定表达式，禁止锚定框架生成的控件 ID。
  3. 定义 LLM 候选起草步骤的结构化输出契约与人工审核清单；LLM 产物一律为候选，永不直接发布。
  4. 规定脱敏与范围：证据提取仅使用测试环境与脱敏数据；不复制 DPA 视觉皮肤，只保留状态语义色等经审核的少量 token 映射。
  5. 定义确定性要求：同一页面同一 revision 重复提取结果字节稳定。
- **产出物**：`docs/specification/product/ui-evidence-extraction-pipeline.md`；提取器与候选生成器规格；`models/examples/masterdata/` 新增候选 MU 及其证据引用样例。
- **验证方式**：对 SubtableType 列表页与编辑表单页重复提取并做快照比对（字节稳定）；候选 MU 通过工作包 03 Schema 校验；字段提取查全率、查准率与绑定正确率达到预先登记的阈值；反例证明运行期不存在 LLM 渲染路径。
- **前置 Task**：T09.2。
- **边界**：不修改已关闭工作包 02/03 的产出，仅以其为输入基线；不做像素级视觉复刻；截图只作辅助证据不作主证据。

## 工作包验收

- T09.1 至 T09.10 的产出物全部存在并通过各自验证。
- 六类产品界面的职责和导航边界无重叠冲突，复杂业务编辑明确返回原 DPA。
- Renderer 只接受已注册类型和通过 Schema 校验的数据，模型不能注入 HTML、脚本、组件或内部链接。
- 对象、集合、关系、图表、本体图、行为审核卡和执行状态均有正常、空、错误、过期和无权限样例。
- `LegacyViewRef` 与 `LaunchTicket` 的篡改、过期、重放和越权测试全部被安全拒绝。
- 核心流程满足键盘操作、屏幕阅读器等价信息、对比度和响应式基线。
- 至少一条 MasterData 跨界面样例可从 Agent transcript 追踪到 Renderer、审批、Legacy View 或执行收据。
- UI 证据提取管线对参考页面重复运行字节稳定，LLM 仅存在于构建期，运行期渲染不存在模型生成路径。
- 前端框架、Renderer、关系图、布局和图表技术均有基于统一 PoC 的选型结论、备选方案与替换边界。

## 解决记录

完成工作包时填写：

- **关闭日期**：
- **负责人**：
- **关键决策**：
- **产出物索引**：
- **验证命令与结果**：
- **遗留风险与后续工作包**：
