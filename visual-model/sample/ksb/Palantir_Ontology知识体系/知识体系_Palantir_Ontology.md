# Palantir Ontology 知识体系

> Palantir Ontology 是一种把组织中的现实对象、关系、权限、动作、应用与 AI 能力统一到同一操作语义层的产品化本体方法。本体系参考 Palantir 官方文档构建，用于系统学习 Foundry Ontology、AIP、OSDK 与行业落地方法。

## 建模前置分析

【领域】：Palantir Ontology

【核心定义】：Palantir Ontology 是 Palantir Foundry/AIP 中用于表示企业或机构真实业务对象、关系、属性、动作、权限与应用行为的操作语义层。

【范围边界】：

- 包含：Ontology 思想与定位、Object/Property/Link 建模、数据映射、Action/Function/Workflow、权限治理、AIP/Agent 集成、Workshop/OSDK 应用、行业落地蓝图。
- 不包含：Palantir 公司商业估值、股票分析、非公开产品内部实现、Gotham 具体机密使用场景。
- 前置依赖：数据建模、业务流程建模、权限控制、API 基础、LLM 工具调用基础。

【目标受众与用途】：学习入门、产品架构理解、企业数据平台/AI 平台设计参考、行业本体建模方法学习。

【典型应用场景】：为企业设计可操作语义层；理解 AIP 如何基于业务对象执行动作；规划供应链、制造、风控、国防情报等行业本体。

【三层粒度规划】：顶层设 8 个主干，默认展开到三级；中间层采用「系统层级 × 任务类型 × 难度层级」三维矩阵；底层抽取 63 个 Atom 节点、83 条关系边；额外输出强制学习路线图 `knowledge_learning_path.html`，以 LR 分层 DAG 表达前导知识和知识组装路径。

## 知识抽取

### 概念

1. Ontology：把业务对象、关系、属性、动作和权限组织为统一语义层。
2. Object Type：业务对象类型，例如资产、订单、供应商、人员、事件。
3. Property：对象属性或状态，可由数据源、计算逻辑或动作更新。
4. Link Type：对象之间的语义关系，如订单属于客户、设备位于工厂。
5. Object Set：满足条件的一组对象，是分析、应用和 AI 操作的输入集合。
6. Action Type：允许用户或系统对对象执行的业务动作。
7. Function：可复用计算逻辑，可读写 Ontology、聚合、校验或调用 AI。
8. Dynamic Policy：基于用户、对象和上下文动态决定访问权限。
9. AIP Grounding：把大模型回答和行动锚定到可授权的业务对象与工具上。
10. OSDK：让开发者通过类型化 API 访问 Ontology 对象、链接与动作。

### 方法

- 对象建模：识别现实世界核心实体，定义 Object type、主键、属性和显示语义。
- 关系建模：定义 Link type、方向、基数和跨域连接方式。
- 数据映射：把源系统数据集映射为对象属性和关系，并保持同步与血缘。
- 动作建模：把业务流程中的可执行操作定义为 Action type，并配置校验、权限和写回。
- AI 接入：让 LLM 在 Ontology 上查询对象、调用函数、执行动作，并接受权限和审计约束。

### 关系

Palantir Ontology 的关系不是静态知识图谱关系，而是面向行动的业务关系。Object type 是核心语义单位；Property、Link type 和 Object set 围绕对象展开；Action type 和 Function 把对象变成可操作系统；权限、审计和模拟保证动作可控；AIP 将 LLM 接入这些对象和动作；Workshop 与 OSDK 则把 Ontology 暴露给业务用户和开发者。

## 一、顶层知识：领域主干

> 📊 查看对应图表：[knowledge_top.html](knowledge_top.html)

### 1.1 思想与定位

Palantir Ontology 的核心不是“画一个知识图谱”，而是为组织建立可计算、可授权、可行动的业务现实模型。它位于源系统、数据平台、应用和 AI 之间，让不同角色围绕相同的对象和动作协同。

### 1.2 核心语义模型

Ontology 的基本语法由 Object type、Property、Link type、Object set 等组成。Object type 定义业务对象类别，Property 表示对象状态，Link type 表达对象间关系，Object set 则把对象集合化，作为分析和操作的入口。

### 1.3 数据与集成

Ontology 不替代源系统，而是将源系统中的事实映射到业务对象。关键工作包括数据集映射、实体解析、主数据对齐、增量同步、数据质量和血缘治理。

### 1.4 动作与工作流

Action type 是 Palantir Ontology 与普通数据模型的关键差异。它把业务操作显式建模，使用户、系统和 AI 都能在权限和规则约束下修改对象状态、创建任务、触发审批或写回外部系统。

### 1.5 安全治理

Ontology 将权限、审计、血缘、版本和模拟纳入同一操作层。对象级权限、属性级权限和动态策略决定谁能看什么、改什么；审计和 lineage 记录数据与动作的来源和影响。

### 1.6 AIP 与 Agent

AIP 将 LLM 与 Ontology、Function、Action type 连接起来，使模型能基于业务对象进行分析、调用工具、生成计划并触发动作。关键不是让模型“知道更多”，而是让模型在受控语义层中行动。

### 1.7 应用与开发

Workshop 面向业务应用搭建，OSDK 面向开发者编程接入，AIP 应用面向分析和自动化。三者共同把 Ontology 从后端语义层推向业务界面、代码系统和 AI 交互。

### 1.8 行业落地

行业 Ontology 不是从表开始，而是从业务对象、关系、动作和价值闭环开始。供应链关注订单、供应商、库存和风险；制造关注设备、批次、质量和产能；情报关注人、组织、地点、事件和线索。

## 二、中间层知识：多维矩阵

> 📊 查看对应图表：[knowledge_middle.html](knowledge_middle.html)

### 2.1 维度定义

- 系统层级：思想层、语义层、数据层、动作层、治理层、AI层、产品层。
- 任务类型：建模、集成、操作、治理、开发、应用。
- 难度层级：入门、进阶、高级。

### 2.2 矩阵解读

矩阵中的每个知识块均细化为“学习焦点、典型产出、前导知识”。入门阶段应优先理解思想层和语义层：为什么 Ontology 是 operational layer，以及 Object type、Property、Link type 如何表达现实业务。进阶阶段进入数据映射、实体解析、Action type、Function、权限治理、OSDK 和 AIP Logic。高级阶段关注 Workflow 状态机、动态策略、Simulation、AIP Evals、Agent 行动闭环、AIP 应用工作台和行业本体蓝图。

重点交叉包括：语义层 × 建模，它决定 Object type、Property、Link type 的质量；数据层 × 集成，它决定源系统事实能否稳定映射为对象；动作层 × 操作，它决定 Ontology 是否从“可看”变成“可执行”；治理层 × 治理，它决定权限、审计和变更是否可控；AI层 × 开发/应用，它决定 LLM 是否能在受控对象和工具上行动；产品层 × 应用，它决定业务用户是否真正能在对象语义层上完成工作。

## 三、最底层知识：知识网络

> 📊 查看对应图表：[knowledge_bottom.html](knowledge_bottom.html)

### 3.1 核心节点群

底层图谱包含 63 个核心 Atom，覆盖 8 个主干。最重要的枢纽包括：Ontology 思想、Object Type、Property、Link Type、Action Type、Function、Object Permission、AIP Grounding、OSDK、Ontology Blueprint。这些节点共同构成从业务语义、数据映射、动作执行到 AI 应用的主干链路。

### 3.2 关联类型与网络特征

`depends` 表示学习或实现前置，`contains` 表示组装关系，`evolved` 表示能力演进，`contrast` 用于区分相似产品能力或设计选择，`analogy` 用于跨层类比。该领域的核心特征是“对象模型 + 动作系统 + 权限治理 + AI 工具调用”共同形成操作闭环。

### 3.3 推荐学习路径

> 📊 查看对应图表：[knowledge_learning_path.html](knowledge_learning_path.html)

- **通识入门路线**：Ontology 思想 → Object Type → Property → Link Type → Object Set → Action Type → AIP Grounding → Workshop。
- **产品架构路线**：Operational Layer → 语义层优先 → Dataset Mapping → Pipeline → Action Type → Function → Object Permission → AIP Logic Block → OSDK。
- **AI Agent 路线**：Object Set → Function → LLM Tool → Tool Authorization → AIP Logic Block → Agent Plan → AI Action Review → AIP Evals。
- **行业落地路线**：Ontology Blueprint → Supply Chain/Manufacturing/Financial Risk Ontology → Deployment Pattern → Value Loop。

## 附录 A：图表索引

- 顶层思维导图：knowledge_top.html
- 中间层知识矩阵：knowledge_middle.html
- 最底层知识图谱：knowledge_bottom.html
- 左到右学习路线图：knowledge_learning_path.html
- 结构化数据：knowledge_graph.json / knowledge_graph.csv

## 附录 B：资料来源与版本

创建日期：2026-07-14

资料来源：
- [Palantir Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/)
- [Object types](https://www.palantir.com/docs/foundry/ontology/object-types/)
- [Link types](https://www.palantir.com/docs/foundry/ontology/link-types/)
- [Action types](https://www.palantir.com/docs/foundry/action-types/overview/)
- [Functions and AIP Logic](https://www.palantir.com/docs/foundry/functions/overview/)
- [Ontology SDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview/)

变更记录：v1.0 初版，按 KSB v3.6 生成。
