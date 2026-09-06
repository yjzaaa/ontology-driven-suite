# Palantir Ontology 知识体系（扩展版）

> 本文是在 `知识体系_Palantir_Ontology.md` 的基础上扩展形成的新版本，不覆盖原文。扩展重点包括：更完整解释 Palantir Ontology 的思想、产品结构和建模方法；按入门、进阶、高级三层解读 `knowledge_middle.html` 的多维矩阵；逐条说明 `knowledge_learning_path.html` 下拉框中的通识入门、产品架构、AI Agent、安全治理、开发者、行业落地等学习路线。本文仍与四个可视化文件保持对应：顶层思维导图、中间层矩阵、底层知识图谱、左到右学习路线图。

## 建模前置分析

【领域】：Palantir Ontology

【核心定义】：Palantir Ontology 是 Palantir Foundry/AIP 中用于表示企业或机构真实业务对象、关系、属性、动作、权限与应用行为的操作语义层。它不是单纯的数据字典，也不是只读知识图谱，而是把组织运行中的事实、状态、流程、权限和可执行动作统一到一套可计算语义模型中。

【范围边界】：

- 包含：Ontology 思想与定位、Object/Property/Link 建模、数据映射、Action/Function/Workflow、权限治理、AIP/Agent 集成、Workshop/OSDK 应用、行业落地蓝图。
- 不包含：Palantir 公司商业估值、股票分析、非公开产品内部实现、Gotham 具体机密使用场景、无法公开验证的客户案例细节。
- 前置依赖：数据建模、业务流程建模、权限控制、API 基础、LLM 工具调用基础、企业应用系统常识。

【目标受众与用途】：适合希望系统理解 Palantir Ontology 的学习者、企业数据平台架构师、AI 平台产品经理、行业解决方案设计者和知识工程实践者。学习目的不是记住产品名，而是掌握一种将“组织现实”转化为“可操作语义系统”的方法。

【典型应用场景】：

- 为企业设计可操作语义层，把分散在 ERP、MES、CRM、数据湖和人工流程中的事实统一到业务对象上。
- 理解 AIP 为什么需要 Ontology 才能从聊天工具升级为可控的业务 Agent。
- 为供应链、制造、金融风控、医疗运营、国防情报等领域设计对象、关系、动作和治理闭环。

【三层粒度规划】：顶层设 8 个主干，对应 `knowledge_top.html`；中间层采用「系统层级 × 任务类型 × 难度层级」三维矩阵，对应 `knowledge_middle.html`；底层抽取 63 个 Atom 节点和 83 条关系边，对应 `knowledge_bottom.html`；学习路线图采用 D3.js + dagre-d3 的 LR 左到右分层 DAG，对应 `knowledge_learning_path.html`。

## 知识抽取

### 概念

1. Ontology：把业务对象、关系、属性、动作和权限组织为统一语义层。
2. Object Type：业务对象类型，例如资产、订单、供应商、人员、事件。
3. Object Instance：Object Type 的具体实例，例如某个订单、某台设备、某个供应商。
4. Property：对象属性或状态，可由数据源、计算逻辑或动作更新。
5. Primary Key：稳定识别对象实例的唯一键，是对象同步和链接的基础。
6. Link Type：对象之间的语义关系，如订单属于客户、设备位于工厂。
7. Object Set：满足条件的一组对象，是分析、应用和 AI 操作的输入集合。
8. Action Type：允许用户或系统对对象执行的业务动作。
9. Function：可复用计算逻辑，可读写 Ontology、聚合、校验或调用 AI。
10. Workflow State：对象在业务流程中的状态，例如待审批、执行中、已关闭。
11. Object Permission：控制用户对对象类型和对象实例的可见性与可操作性。
12. Dynamic Policy：基于用户、对象和上下文动态决定访问权限。
13. AIP Grounding：把大模型回答和行动锚定到可授权的业务对象与工具上。
14. LLM Tool：供模型调用的函数、查询或动作能力。
15. OSDK：让开发者通过类型化 API 访问 Ontology 对象、链接与动作。

### 方法

- 对象建模：识别现实世界核心实体，定义 Object Type、主键、属性和显示语义。
- 关系建模：定义 Link Type、方向、基数和跨域连接方式。
- 数据映射：把源系统数据集映射为对象属性和关系，并保持同步与血缘。
- 动作建模：把业务流程中的可执行操作定义为 Action Type，并配置校验、权限和写回。
- 治理建模：把权限、审计、血缘、版本、模拟和评估放入操作闭环。
- AI 接入：让 LLM 在 Ontology 上查询对象、调用函数、执行动作，并接受权限和审计约束。
- 应用构建：通过 Workshop、OSDK 和 AIP 应用把 Ontology 暴露给业务用户、开发者和 AI Agent。

### 关系

Palantir Ontology 的关系不是静态知识图谱关系，而是面向行动的业务关系。Object Type 是核心语义单位；Property、Link Type 和 Object Set 围绕对象展开；Action Type 和 Function 把对象变成可操作系统；权限、审计和模拟保证动作可控；AIP 将 LLM 接入这些对象和动作；Workshop 与 OSDK 则把 Ontology 暴露给业务用户和开发者。这个体系的关键不在于“看见数据”，而在于“围绕对象采取受控行动”。

## 一、顶层知识：领域主干

> 查看对应图表：[knowledge_top.html](knowledge_top.html)

### 1.1 思想与定位

Palantir Ontology 的核心是 operational ontology，即面向组织运行的本体。它把企业或机构中的现实对象、关系、状态和动作抽象为可计算语义层，使数据、应用、人和 AI 围绕同一套业务对象协同。传统数据平台通常从表、指标和报表出发，而 Palantir Ontology 更强调从现实对象出发，例如供应链中的订单、供应商、库存、运输、风险，制造中的设备、工艺、批次、质量、产能。

这一层需要理解三个区别。第一，Ontology 不是数据库 schema。数据库 schema 关心数据如何存储，Ontology 关心业务世界如何被理解和操作。第二，Ontology 不是普通知识图谱。知识图谱强调实体关系的表达，Palantir Ontology 还要包含权限、动作、工作流和应用行为。第三，Ontology 不是 BI 语义层。BI 语义层通常服务于看数和分析，Palantir Ontology 服务于分析之后的行动闭环。

### 1.2 核心语义模型

核心语义模型由 Object Type、Property、Link Type、Object Set 等构成。Object Type 定义对象类别，Property 定义对象属性，Link Type 定义对象关系，Object Set 定义一组对象的查询结果。这个结构看似简单，但它决定了后续所有数据映射、动作执行、权限治理和 AI 工具调用是否稳固。

例如在供应链场景中，Object Type 可以包括 Supplier、Purchase Order、Part、Shipment、Risk Event。Property 可以包括订单金额、交付日期、供应商评级、库存数量。Link Type 可以表达“供应商供应零件”“订单包含零件”“运输关联订单”。Object Set 可以是“未来 14 天内存在延迟风险的订单集合”。一旦这些对象集合可以被查询和授权，就可以被应用界面、函数、AIP Agent 和动作流程复用。

### 1.3 数据与集成

Ontology 不替代源系统，而是把源系统中的事实映射到业务对象。源系统可能是 ERP、MES、CRM、数据湖、文件系统或人工维护表。关键工作包括 Dataset Mapping、Pipeline、Entity Resolution、Master Data Alignment、Data Quality Rule 和 Data Lineage。

这一层最容易被误解为“数据接入”。实际上，数据接入只是起点。真正困难的是把不同系统中对同一现实实体的记录对齐，把字段含义统一，把刷新策略稳定下来，并让每个对象属性都能说明来源、更新时间和质量状态。没有这一层，Ontology 会变成漂亮但不可信的对象目录。

### 1.4 动作与工作流

Action Type 是 Palantir Ontology 与普通数据模型的关键差异。一个对象不只是被查看，还可以被操作。例如对订单执行“标记风险”“调整优先级”“发起审批”“创建补货任务”；对设备执行“创建维修工单”“更新状态”“关闭告警”。Action Type 将这些操作建模为受权限、规则和审计约束的可执行动作。

Function 则提供计算和逻辑封装。它可以读取对象集合、计算风险分、生成聚合指标、校验参数，也可以作为 LLM Tool 被 AIP 调用。Workflow State 将对象生命周期表达为状态机，例如从“待处理”到“审批中”到“已执行”再到“已关闭”。动作层的目标是把 Ontology 从“可理解”推进到“可执行”。

### 1.5 安全治理

治理层决定 Ontology 是否能进入真实业务环境。对象级权限控制谁能看到哪些对象，属性级权限控制谁能看到或编辑敏感字段，动态策略根据用户、组织关系、对象状态和场景决定访问边界。Audit Log 记录谁在什么时候看了什么、改了什么、调用了什么工具。

当 AI 被引入后，治理变得更重要。AIP Agent 不应绕过权限直接访问对象或执行动作。Tool Authorization 需要规定模型可调用哪些工具、在哪些对象集合上调用、何时必须进入人工复核。Simulation 和 AIP Evals 用来测试动作、函数和 AI 计划，避免试验污染生产对象。

### 1.6 AIP 与 Agent

AIP 的价值在于让 LLM 工作在受控的业务语义层上，而不是只做开放问答。AIP Grounding 将模型上下文锚定到 Ontology 的对象、关系、属性和动作上。LLM Tool 将 Function、查询或 Action 暴露给模型。AIP Logic Blocks 将提示、对象查询、工具调用和条件分支编排成可执行逻辑。

Agent Plan 是更高一层能力。它让模型根据任务目标拆解步骤，例如先查询风险订单，再聚合影响金额，再调用函数估算替代供应商，再生成动作建议，最后进入人工审核。这里的关键不是“模型很聪明”，而是模型的每一步都落在 Ontology 的对象、工具、权限和审计轨道上。

### 1.7 应用与开发

Workshop、OSDK 和 AIP 应用分别服务于不同使用者。Workshop 面向业务用户和产品团队，用于围绕对象构建页面、表单、对象视图和动作入口。OSDK 面向开发者，让外部应用通过 TypeScript、Python、Java 等方式访问对象、链接和动作。AIP 应用则面向分析、问答、自动化和 Agent 工作台。

应用层的核心问题是：怎样让业务用户真正围绕对象工作。一个好的 Object View 不只是展示属性，还应展示关系、历史、状态、风险、可执行动作和相关解释。一个好的 AIP 应用也不只是聊天框，而是把对象视图、工具调用、计划生成和人工审批组合成可控工作台。

### 1.8 行业落地

行业落地不是把通用概念套一遍，而是把行业中的关键对象、关键关系和关键动作抽象出来。供应链 Ontology 关注订单、供应商、库存、运输、风险。制造 Ontology 关注设备、工艺、批次、质量、产能。金融风险 Ontology 关注账户、交易、实体、敞口、告警、调查。国防情报 Ontology 关注人员、组织、地点、事件、线索、行动。

行业本体蓝图的价值在于复用。一个好的蓝图不仅包含对象和关系，还要包含常见动作、权限策略、应用视图、数据质量规则和价值闭环。落地路线通常从一个高价值场景试点开始，然后扩展对象范围、动作范围和 AI 自动化程度。

## 二、中间层知识：多维矩阵

> 查看对应图表：[knowledge_middle.html](knowledge_middle.html)

### 2.1 维度定义

中间层矩阵采用三个维度。

- 系统层级：思想层、语义层、数据层、动作层、治理层、AI层、产品层。
- 任务类型：建模、集成、操作、治理、开发、应用。
- 难度层级：入门、进阶、高级。

`knowledge_middle.html` 中的每个知识块都细化为“焦点、产出、前导”。这意味着矩阵不是简单概念表，而是一张学习任务表。读者可以从任意两个维度切入。例如选择“系统层级 × 任务类型”，可以看到每一层需要做哪些工作；选择“难度层级 × 任务类型”，可以看到入门、进阶、高级分别应该完成哪些建模、集成、治理或开发任务；选择“系统层级 × 难度层级”，可以看到每个层级如何由浅入深推进。

### 2.2 入门层解读

入门层的目标是建立正确的对象化思维，不急于写代码，也不急于设计复杂 Agent。对应矩阵中的入门知识块主要包括 Operational Ontology 定位、现实对象优先原则、Object Type 切分、Property 设计、Link Type 设计、对象显示与业务语言、源系统盘点、Dataset Mapping、Action Type 基础、Action Form 设计、Object Permission、Ontology Grounding、Prompt Template、Workshop 页面建模、Object View 设计。

入门学习的第一步是理解 Operational Ontology 定位。你需要能说清楚 Palantir Ontology 位于哪里：它不是源系统，不是数据湖，不是单独应用，也不是纯 AI 模型，而是把源系统事实转化为业务对象，并让应用和 AI 围绕对象操作的中间语义层。对应的产出是一个简单架构图：源系统在左侧，Ontology 在中间，应用、动作和 AI 在右侧。

第二步是现实对象优先原则。很多企业建模失败，是因为从已有表结构出发，把宽表、报表或流程节点误认为对象。Ontology 的入门训练应从现实对象开始：谁在业务中被追踪，什么东西有状态，什么东西会被操作，什么东西能产生责任。对应产出是一份核心业务对象候选清单。

第三步进入语义层建模。Object Type 切分决定对象粒度，Property 设计决定对象状态，Link Type 设计决定对象间关系。入门阶段不需要一次建全，但需要避免三个错误：对象太粗，导致后续动作无法精准执行；对象太细，导致业务用户无法理解；关系缺失，导致对象之间无法导航和推理。

第四步是数据层入门。源系统盘点和 Dataset Mapping 帮助你知道每个对象来自哪里、哪些属性来自哪些字段、哪些对象缺少稳定主键。此时不必解决所有数据质量问题，但必须建立“对象属性不是凭空来的”意识。

第五步是动作和应用入门。Action Type 基础让你意识到对象必须能被操作，Action Form 设计让动作能被业务用户执行。Workshop 页面建模和 Object View 设计则把对象、属性、关系和动作组织成可用界面。入门阶段学完后，理想状态是能围绕一个小场景设计出对象清单、属性字典、关系清单、一个动作和一个对象详情页。

### 2.3 进阶层解读

进阶层的目标是让 Ontology 从“概念正确”变成“系统可运行”。对应矩阵中的进阶知识块包括 Ontology vs Data Model、Primary Key 与对象稳定性、关系基数与导航路径、Object Set 查询语义、Property 口径治理、Pipeline 到对象同步、Entity Resolution、Master Data Alignment、Data Quality Rule、Data Lineage、Validation Rule、Writeback 与事务边界、Function 基础、Aggregation 与指标计算、Property Permission、Audit Log、Lineage Governance、LLM Tool 定义、Tool Authorization、AIP Logic Blocks、AIP Analyst 使用模式、Dashboard 与运营视图、OSDK 应用开发、SDK 选择、Application Permission。

进阶学习首先要解决模型边界问题。Ontology vs Data Model 要求你区分四件事：数据库如何存储、业务对象如何表达、指标如何计算、应用如何呈现。很多系统混乱，根源是把这四层混在一起。进阶阶段应能写出边界说明：哪些字段属于源数据，哪些属性属于对象语义，哪些指标属于函数或聚合，哪些展示属于应用视图。

第二个重点是对象稳定性。Primary Key 与 Entity Resolution 是进阶层的核心。没有稳定主键，对象实例就会重复、断裂或错连。Entity Resolution 则解决跨系统中同一实体的合并问题。例如供应商在 ERP、采购系统、风险系统中可能有不同编码，Ontology 需要建立匹配规则、置信度和人工复核机制。

第三个重点是 Object Set。Object Set 是后续函数、应用和 AIP 的常用输入。你要能定义“未来 30 天交付且风险评分大于阈值的订单集合”“所有与某供应商相关的风险事件集合”“某工厂当前处于异常状态的设备集合”。Object Set 查询语义连接了对象建模和后续自动化。

第四个重点是动作可靠性。Validation Rule、Writeback 与事务边界决定 Action Type 能否进入生产环境。动作执行前要校验参数、对象状态和权限；动作执行后要知道写回哪里、失败如何处理、是否需要回滚、是否需要人工确认。

第五个重点是 Function 和 AIP Logic。Function 基础和 Aggregation 与指标计算让系统具备可复用计算能力。LLM Tool 定义和 AIP Logic Blocks 则把这些能力暴露给 AI。进阶阶段不应把工具随意暴露给模型，而应明确工具名称、参数 schema、返回结构、失败策略和授权边界。

第六个重点是应用和开发。OSDK 应用开发让外部系统可以访问对象、链接和动作。Dashboard 与运营视图让业务用户看到对象集合和指标。Application Permission 让应用层权限与对象权限保持一致。进阶阶段学完后，理想状态是能把一个小型 Ontology 接入数据源，构建对象查询、动作、函数、审计和一个可用应用界面。

### 2.4 高级层解读

高级层的目标是规模化、自动化和治理闭环。对应矩阵中的高级知识块包括价值闭环设计、数据可观测性、Workflow State、Human-in-the-loop、Dynamic Policy、Ontology Versioning、Simulation Sandbox、AIP Evals、Agent Plan、AI Action Review、AIP 应用工作台、行业本体蓝图、落地路线与扩展模式。

高级学习首先要回到价值闭环。很多 Ontology 项目能建对象，却无法证明价值，因为没有把对象、动作和业务结果连起来。价值闭环设计要求明确：什么事件触发关注，哪些对象被分析，采取什么动作，动作后看什么指标，指标如何反过来优化模型和流程。

第二个高级主题是 Workflow State。对象有生命周期，动作不是孤立按钮。订单可能从待审核到已确认到执行中到异常到关闭；设备可能从正常到告警到维修中到恢复。Workflow State 要求你把状态、允许动作、迁移条件和异常分支建成状态机。

第三个高级主题是动态安全。Dynamic Policy 不只是角色权限，而是根据用户、对象状态、组织关系和场景动态决定访问。例如某用户平时不能看到敏感供应商信息，但在其负责的风险事件处置流程中可以查看必要字段。动态策略是 AI Agent 进入真实业务前必须掌握的治理能力。

第四个高级主题是模拟和评估。Simulation Sandbox 让动作、函数和 AI 计划可以在非生产环境中测试。AIP Evals 进一步评估模型是否正确查询对象、是否安全调用工具、是否在失败样例中保持边界。没有评估，AI 自动化只能停留在演示阶段。

第五个高级主题是 Agent 行动闭环。Agent Plan 要能把目标拆成步骤，AI Action Review 要能让高风险动作进入人工复核。AIP 应用工作台则把对象视图、Agent 计划、工具调用、审批和审计整合起来。高级阶段的重点不是让 AI 替代所有人，而是让 AI 在清晰边界内加速分析和执行。

第六个高级主题是行业本体蓝图。行业蓝图将供应链、制造、风控、医疗运营等领域中的通用对象、关系和动作抽象出来，并形成可复用模板。高级学习的终点不是掌握某个产品按钮，而是能为一个行业设计对象层、动作层、治理层和 AI 应用层。

## 三、最底层知识：知识网络

> 查看对应图表：[knowledge_bottom.html](knowledge_bottom.html)

### 3.1 核心节点群

底层图谱包含 63 个核心 Atom，覆盖 8 个主干。最重要的枢纽包括 Ontology 思想、Object Type、Property、Link Type、Action Type、Function、Object Permission、AIP Grounding、OSDK、Ontology Blueprint。这些节点共同构成从业务语义、数据映射、动作执行到 AI 应用的主干链路。

从图谱角度看，Object Type 是语义层核心，Property 和 Link Type 围绕它扩展，Object Set 让对象进入查询、函数和应用。Action Type 是动作层核心，Validation Rule、Writeback、Workflow State 和 Human-in-the-loop 围绕它形成业务执行系统。Object Permission 和 Dynamic Policy 是治理层核心，它们同时约束应用用户和 AI 工具调用。AIP Grounding、LLM Tool、AIP Logic Block 和 Agent Plan 构成 AI 层路径。Workshop 和 OSDK 则把 Ontology 转化为产品和开发者能力。

### 3.2 关联类型与网络特征

`depends` 表示学习或实现前置，例如 Action Type 依赖 Object Type 和 Property，因为没有对象和属性就无法定义动作作用对象。`contains` 表示组装关系，例如 Action Type 包含 Action Form、Validation Rule、Writeback 等子能力。`evolved` 表示能力演进，例如 Dataset Mapping 之后形成 Pipeline 到对象同步，Function 进一步支撑 LLM Tool。`contrast` 用于区分相似但不同的能力，例如 Workshop 与 OSDK 面向不同使用者。`analogy` 用于跨层类比，例如 Dynamic Policy 与 Tool Authorization 都是在不同层面对“谁能做什么”进行约束。

这个网络的核心特征是闭环性。数据进入对象，对象被关系连接，对象集合被函数计算，动作改变对象状态，权限约束动作，审计记录行为，AI 在这些对象和工具上生成计划，应用把计划和动作交给用户。任何一个环节断裂，Ontology 都会退化成普通数据目录或应用配置。

## 四、学习路线图解读

> 查看对应图表：[knowledge_learning_path.html](knowledge_learning_path.html)

学习路线图使用 D3.js + dagre-d3，从左到右表示“前导知识 → 后续知识”。下拉框中的路线并不是互相排斥的课程，而是从不同目标切入同一张知识网络。全景路线显示全部节点；通识入门适合建立总体理解；产品架构适合理解系统如何搭起来；AI Agent 适合关注 AIP 与工具调用；安全治理适合关注权限、审计、模拟和评估；开发者路线适合写应用和集成；行业落地路线适合把 Ontology 方法应用到真实业务域。

### 4.1 全景路线

全景路线展示全部知识节点和主要关系。它适合在学习开始和学习结束时各看一次。开始时看全景，可以知道 Palantir Ontology 不是单点技术，而是思想、语义、数据、动作、治理、AI、应用、行业落地的组合系统。结束时看全景，可以检查自己是否理解了这些层之间的连接。

阅读全景路线时不要试图一次读完所有边。建议先找枢纽节点：Ontology 思想、Object Type、Action Type、Function、Object Permission、AIP Grounding、OSDK、Ontology Blueprint。然后观察这些枢纽左右两侧的前导和后续。左侧通常是基础语义或前置能力，右侧通常是组合能力、产品能力或行业落地能力。

### 4.2 通识入门路线

通识入门路线对应下拉框中的 `通识入门`，核心路径是：Ontology 思想 → Object Type → Property → Link Type → Object Set → Action Type → AIP Grounding → Workshop。

这条路线适合第一次系统学习 Palantir Ontology 的人。它从思想层开始，先回答“为什么需要 Ontology”。随后进入 Object Type、Property、Link Type，这是理解所有后续能力的语法基础。Object Set 是从对象到分析和应用的桥梁，因为很多操作不是针对单个对象，而是针对满足条件的一组对象。Action Type 将对象变成可执行系统，AIP Grounding 则说明 AI 为什么需要对象、关系、权限和动作作为落脚点。最后到 Workshop，表示业务用户如何在界面上使用这些对象和动作。

学习这条路线时，建议每一步都做一个小产出。学 Ontology 思想时画出系统位置图；学 Object Type 时列出一个业务场景的对象清单；学 Property 时写属性字典；学 Link Type 时画对象关系图；学 Object Set 时写三个查询条件；学 Action Type 时定义一个业务动作；学 AIP Grounding 时说明模型能看哪些对象、不能看哪些对象；学 Workshop 时设计一个对象详情页。

### 4.3 产品架构路线

产品架构路线对应下拉框中的 `产品架构`，核心路径是：Operational Layer → 语义层优先 → Dataset Mapping → Pipeline → Action Type → Function → Object Permission → AIP Logic Block → OSDK。

这条路线适合产品架构师、平台负责人和希望理解 Foundry/AIP 产品结构的人。它从 Operational Layer 开始，说明 Ontology 在系统架构中承担中间操作层角色。语义层优先说明架构设计应先定义业务对象和动作语义，而不是直接堆数据表。Dataset Mapping 和 Pipeline 解释源系统事实如何进入对象层。Action Type 和 Function 解释对象如何被操作和计算。Object Permission 解释平台如何控制访问。AIP Logic Block 解释 AI 逻辑如何编排。OSDK 说明 Ontology 如何被开发者以 API 方式使用。

这条路线的关键是理解“平台化”。如果只有对象，没有 Pipeline，Ontology 不会更新；如果只有 Pipeline，没有 Action Type，Ontology 只能看不能做；如果只有 Action，没有 Permission，系统不能进入真实组织；如果只有 AIP Logic，没有 OSDK 和应用接口，能力难以被集成到外部软件生态中。

学习这条路线的推荐产出是一张产品架构图。图中应包含源系统、Dataset Mapping、Ontology Object/Link/Action、Function、Permission、AIP Logic、Workshop、OSDK、外部应用。每条连接都要说明数据流、控制流或权限边界。

### 4.4 AI Agent 路线

AI Agent 路线对应下拉框中的 `AI Agent`，核心路径是：Object Set → Function → LLM Tool → Tool Authorization → AIP Logic Block → Agent Plan → AI Action Review → AIP Evals。

这条路线适合关注 AIP、LLM 工具调用和企业 Agent 的学习者。它不是从大模型本身开始，而是从 Object Set 开始。这很重要，因为企业 Agent 不应在无边界文本中行动，而应在一组可授权、可追踪的对象上工作。Function 将对象读取、计算和业务规则封装起来。LLM Tool 将 Function、Action 或查询能力暴露给模型。Tool Authorization 决定模型能否调用这些工具。AIP Logic Block 负责把提示、对象查询和工具调用编排起来。Agent Plan 负责将目标拆解为步骤。AI Action Review 和 AIP Evals 则负责人工复核和系统评估。

这条路线的核心问题是“可控行动”。一个企业 Agent 不只是回答“哪些订单有风险”，还可能建议“创建替代供应商评估任务”或“更新订单优先级”。这些动作必须受对象权限、工具授权、动作校验、人工审核和评估集约束。否则 AI Agent 会变成不可审计的自动化风险源。

学习这条路线的推荐产出是一个 Agent 设计说明。至少包括：任务目标、可访问 Object Set、可调用 Function、可执行 Action、工具授权策略、人工复核点、失败处理、评估用例和审计字段。

### 4.5 安全治理路线

安全治理路线对应下拉框中的 `安全治理`，核心路径是：Object Permission → Property Permission → Dynamic Policy → Audit Log → Lineage Governance → Simulation → AIP Evals。

这条路线适合平台治理、安全、合规和 AI 风险控制角色。它从对象权限开始，因为任何操作都必须先知道谁能访问哪些对象。Property Permission 进一步控制敏感字段。Dynamic Policy 处理静态角色无法覆盖的复杂场景，例如用户是否属于某项目组、对象是否处于应急状态、动作是否高风险。Audit Log 记录行为，Lineage Governance 将数据来源、动作记录、函数调用和 AI 输出连接为可追溯链条。Simulation 让高风险逻辑先在沙盒中测试，AIP Evals 则评估 AI 工具调用和动作建议是否可靠。

这条路线强调“治理不是事后补丁”。在 Palantir Ontology 视角下，权限、审计和评估应当内生于对象和动作系统中。对象设计时就要知道哪些属性敏感；动作设计时就要知道谁能执行、何时执行、失败如何处理；AI 工具设计时就要知道模型能否调用、是否需要人工确认。

学习这条路线的推荐产出是一份治理策略包。包括对象权限矩阵、敏感属性清单、动态授权规则、审计日志字段、lineage 追踪路径、模拟测试方案和 AIP Evals 评估集。

### 4.6 开发者路线

开发者路线对应下拉框中的 `开发者`，核心路径是：Object Type → Object Set → Action Type → Function → OSDK → TypeScript SDK / Python SDK → Application Permission。

这条路线适合需要把 Ontology 接入代码系统的人。开发者首先要理解 Object Type，因为 SDK 访问的是对象语义而不是裸表。Object Set 是查询入口，Action Type 是写操作入口，Function 是可复用业务逻辑入口。OSDK 将这些能力以类型化 API 暴露给应用。TypeScript SDK 更适合前端和 Node 应用，Python SDK 更适合分析、自动化和数据科学场景，Java SDK 更适合企业后端。Application Permission 则保证应用层权限与 Ontology 权限一致。

这条路线的关键是避免把 OSDK 当成普通数据库访问层。开发者应围绕对象、关系和动作编程，而不是绕过语义层直接拼接数据。好的 OSDK 应用应该继承 Ontology 的对象命名、权限边界、动作规则和审计能力。

学习这条路线的推荐产出是一个小型应用原型。它应能查询对象集合，展示对象详情，调用一个 Function，执行一个 Action，并正确处理权限不足、参数错误和动作失败。

### 4.7 行业落地路线

行业落地路线对应下拉框中的 `行业落地`，核心路径是：Ontology Blueprint → Supply Chain Ontology / Manufacturing Ontology / Financial Risk Ontology → Deployment Pattern → Value Loop。

这条路线适合解决方案架构师、行业顾问和企业数字化负责人。它从 Ontology Blueprint 开始，说明行业落地不能从零散需求开始，而要抽象行业通用对象、关系和动作。例如供应链蓝图包含供应商、订单、零件、库存、运输、风险事件；制造蓝图包含设备、工艺、批次、质量、产能；金融风险蓝图包含账户、交易、实体、敞口、告警、调查。

Deployment Pattern 说明如何落地。通常不应一开始铺开全行业本体，而应选择高价值场景试点。第一阶段识别核心对象和数据源；第二阶段建立关键关系和对象视图；第三阶段加入动作和人工流程；第四阶段加入函数、AI 分析和 Agent 辅助；第五阶段将审计、评估和价值反馈纳入治理。

Value Loop 是行业落地的最终判断标准。一个行业 Ontology 是否有效，不看对象数量，而看它是否改善业务结果。例如供应链中是否缩短风险响应时间，制造中是否降低停机损失，金融风控中是否提高调查效率。学习这条路线的推荐产出是一份行业本体蓝图，包含对象清单、关系图、动作清单、权限策略、应用视图、AI 辅助场景和价值指标。

## 五、四图联动使用方法

### 5.1 顶层思维导图如何使用

`knowledge_top.html` 用于建立全局结构。第一次学习时，建议先看 8 个主干：思想与定位、核心语义模型、数据与集成、动作与工作流、安全治理、AIP 与 Agent、应用与开发、行业落地。每个主干下展开到三级，可以快速看到“这一块包含什么”。它回答的是“有哪些大块知识”。

### 5.2 中间层矩阵如何使用

`knowledge_middle.html` 用于定位学习任务。默认视图是系统层级 × 任务类型，筛选维度是难度层级。你可以先选择“全部”，查看每个交叉点包含哪些入门、进阶、高级知识块。然后按入门、进阶、高级分别筛选，形成阶段性学习清单。它回答的是“这些知识如何分类、如何交叉、每块学完产出什么”。

### 5.3 底层知识图谱如何使用

`knowledge_bottom.html` 用于理解关联密度。它展示 63 个 Atom 节点和 83 条关系边。学习时可以用关系筛选器先看 depends，理解前置依赖；再看 contains，理解知识组装；再看 evolved，理解能力演进；最后看 contrast 和 analogy，理解边界和类比。它回答的是“知识点如何关联成网”。

### 5.4 学习路线图如何使用

`knowledge_learning_path.html` 用于规划学习顺序。它不是简单列表，而是左到右分层 DAG。点击某个节点，可以看到它的直接前导和后续知识。选择不同路线，可以根据目标切换学习路径。它回答的是“先学什么、后学什么、哪些知识组装成更高级能力”。

## 附录 A：图表索引

- 顶层思维导图：[knowledge_top.html](knowledge_top.html)
- 中间层知识矩阵：[knowledge_middle.html](knowledge_middle.html)
- 最底层知识图谱：[knowledge_bottom.html](knowledge_bottom.html)
- 左到右学习路线图：[knowledge_learning_path.html](knowledge_learning_path.html)
- 结构化数据：[knowledge_graph.json](knowledge_graph.json) / [knowledge_graph.csv](knowledge_graph.csv)

## 附录 B：资料来源与版本

创建日期：2026-07-15

资料来源：

- [Palantir Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/)
- [Object types](https://www.palantir.com/docs/foundry/ontology/object-types/)
- [Link types](https://www.palantir.com/docs/foundry/ontology/link-types/)
- [Action types](https://www.palantir.com/docs/foundry/action-types/overview/)
- [Functions and AIP Logic](https://www.palantir.com/docs/foundry/functions/overview/)
- [Ontology SDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)

变更记录：

- v1.0：初版，按 KSB v3.6 生成。
- v1.1：扩展版，正文约扩展为原文两倍，重点增强中间层矩阵解读和学习路线解读，并与四个可视化文件保持对应。
