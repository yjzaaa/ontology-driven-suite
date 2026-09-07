---
title: 统一领域语言与模型边界
status: closed
labels:
  - wayfinder:grilling
parent: ../map.md
assignee: copilot-agent
blocked_by: []
---

## 工作包目标

建立 DPA 本体平台的统一领域语言和可判定的模型边界，使后续 Schema、反向工程、运行时协议与 MasterData 样例使用同一组术语。工作包必须用可复查的定义、职责矩阵和正反例消除表、DTO、业务对象、接口、行为、规则、执行及运行时投影之间的歧义，不在本工作包内设计具体 Schema。

本工作包中的 MasterData 示例仅使用 [MasterDataPROnlineApprovalController / SubtableType 范围](../masterdata-scope.md)，不得扩展到无 `SubtableType` 可达证据的其他 MasterData 逻辑。

## 必需 Task

### [x] T01.1 盘点现有术语及冲突用法

**达成目标**

形成覆盖当前仓库规范、参考资料和 MasterData 语境的术语清单，标出同名异义、异名同义、未定义和跨层混用问题。

**输入**

- `README.md`
- `CONTEXT.md`
- `docs/wayfinder/map.md`
- `docs/AGENTS.md`
- 路线图中引用的参考项目文档

**执行步骤**

1. 提取 Evidence、Business Object、Behavior、Rule、Actor/Permission、Flow、Query、Presentation、Integration Mapping、Action Proposal、Draft Application、Runtime Projection、Legacy View 及其中文候选名称。
2. 为每个术语记录来源、原始含义、所在层次和代表性用例。
3. 标记冲突用法，并区分已确认事实、推断和待裁决项。
4. 给每个冲突项分配稳定编号 `TERM-XXX`，供后续 Task 引用。

**产出物**

- `docs/meta-model/domain-term-inventory.md`

**验证方式**

- 清单逐项覆盖上述 13 个核心概念，且每项至少包含“来源、当前用法、冲突、状态”四列。
- 使用 `rg "TERM-[0-9]{3}" docs/meta-model/domain-term-inventory.md` 可定位全部冲突项。
- 任一待裁决项都能追溯到具体文档、路径或 MasterData 示例，而不是仅记录口头判断。

### [x] T01.2 划定八类本体模型的职责边界

**前置 Task**

- T01.1

**达成目标**

为 M1 Object、M2 Behavior、M3 Rule、M5 Actor/Permission、M6 Flow、M7 Query、MU Presentation、MI Integration 建立互斥且可判定的职责矩阵。

**输入**

- `docs/meta-model/domain-term-inventory.md`
- `docs/wayfinder/map.md` 的已确认边界

**执行步骤**

1. 为八类模型分别说明“表达什么、不得表达什么、主要引用对象、运行时用途”。
2. 给出模型选择判定树，处理一个事实可能同时涉及多个模型的情况。
3. 为每类模型编写至少一个 MasterData 正例和一个反例。
4. 记录跨模型信息应通过引用连接还是在目标模型内复制。

**产出物**

- `docs/meta-model/model-boundary-matrix.md`

**验证方式**

- 文档存在八类模型的独立条目，且每个条目均包含职责、禁止项、引用方向、正例和反例。
- 对文档中的每个 MasterData 示例按判定树执行时，只得到一个主模型类型；需要协作的其他模型以引用表示。
- 矩阵不把 URL、HTTP Method、任意 SQL、凭据或内部 DTO 映射暴露为模型可选择的业务语义。

### [x] T01.3 区分表、DTO、数据形状与业务对象

**前置 Task**

- T01.1
- T01.2

**达成目标**

给出从数据库表、存储过程结果、HTTP DTO、页面 ViewModel 到 M1 Object 的明确判定规则，避免按物理数据结构一比一生成业务对象。

**输入**

- `docs/meta-model/model-boundary-matrix.md`
- MasterData 代表性表、DTO、ViewModel 和接口证据

**执行步骤**

1. 分别定义 Table、Row、DTO、ViewModel、Query Result Shape 与 Business Object。
2. 说明主键、字段、聚合边界、业务身份和生命周期在各概念中的作用。
3. 编写至少三个 MasterData 边界案例：多表组成一个对象、一个表承载多个概念、DTO 不等于对象。
4. 给出证据不足时保持候选或要求人工审核的条件。

**产出物**

- `docs/meta-model/object-data-shape-boundaries.md`

**验证方式**

- 每个案例都包含输入证据、判定过程、结论和反例。
- 使用文档规则能够回答“表是否必然生成 M1”“DTO 是否可直接成为 M1”“查询结果是否拥有业务生命周期”，且答案无互相矛盾。
- 未证明业务身份和生命周期的数据形状不会被判定为已发布 M1 Object。

### [x] T01.4 区分行为、接口、规则与执行

**前置 Task**

- T01.1
- T01.2

**达成目标**

建立 endpoint、M2 Behavior、M3 Rule、validation、Action Proposal、Draft Application 和实际执行之间的分层关系及判定规则。

**输入**

- `docs/meta-model/model-boundary-matrix.md`
- MasterData Controller、业务服务、校验器和保存流程证据

**执行步骤**

1. 定义技术接口、业务行为、业务规则、输入校验、授权检查和持久化副作用的区别。
2. 说明一个 endpoint 映射多个行为、多个 endpoint 实现同一行为及 `MIXED/HIGH` 副作用的处理方式。
3. 描述 Action Proposal、人工审核、Draft Application 与 DPA 原保存动作的责任分界。
4. 用查询、草稿填充、保存和混合副作用各给出一个 MasterData 判定案例。

**产出物**

- `docs/meta-model/behavior-rule-execution-boundaries.md`

**验证方式**

- 文档中的每个案例均能分别标注 endpoint、M2、M3、提案、执行者和最终持久化责任。
- validation 不因出现在校验器中就自动判定为 M3 Rule，endpoint 不因可调用就自动判定为 M2 Behavior。
- 无法证明纯读的案例明确归入 `MIXED/HIGH`，且不得自动执行。

### [x] T01.5 定义运行时概念及其所有权

**前置 Task**

- T01.2
- T01.4

**达成目标**

统一 Runtime Projection、Legacy View、Action Proposal、Draft Application、执行记录等运行时概念，明确它们与已发布 YAML 的关系。

**输入**

- `docs/wayfinder/map.md`
- `docs/meta-model/model-boundary-matrix.md`
- `docs/meta-model/behavior-rule-execution-boundaries.md`

**执行步骤**

1. 定义每个运行时概念的创建者、事实来源、可变性、生命周期和消费方。
2. 标明哪些是已发布本体的只读投影，哪些是用户会话内临时对象，哪些仅是遗留系统入口。
3. 说明 Runtime Projection 和 Legacy View 不得成为第二事实源的约束。
4. 给出从 M2/MU/MI 到提案、草稿应用和 DPA 保存动作的概念链路。

**产出物**

- `docs/meta-model/runtime-concept-boundaries.md`

**验证方式**

- 每个概念都有唯一所有者和事实来源。
- 文档明确 `models/<domain>/` 下已发布 YAML 是运行时语义唯一事实源。
- 任一运行时对象都能追溯到模型版本、用户会话或 DPA 原入口之一，不存在来源不明的持久语义。

### [x] T01.6 发布统一词汇表与边界判例

**前置 Task**

- T01.3
- T01.4
- T01.5

**达成目标**

把前述裁决收敛为后续工作包可直接引用的规范词汇表，并为易混概念提供稳定判例。

**输入**

- `docs/meta-model/domain-term-inventory.md`
- `docs/meta-model/model-boundary-matrix.md`
- `docs/meta-model/object-data-shape-boundaries.md`
- `docs/meta-model/behavior-rule-execution-boundaries.md`
- `docs/meta-model/runtime-concept-boundaries.md`

**执行步骤**

1. 为每个规范术语确定中文名、保留英文名、定义、非目标和允许的近义词。
2. 将所有 `TERM-XXX` 冲突项标记为已裁决或明确保留为阻塞项。
3. 编制不少于 12 个可复用判例，覆盖对象、行为、规则、权限、流程、查询、展示、集成和运行时概念。
4. 为后续文档规定首次出现、交叉引用和源码符号保留规则。

**产出物**

- `docs/meta-model/domain-language.md`
- `docs/meta-model/domain-boundary-cases.md`

**验证方式**

- `domain-language.md` 中不存在两个定义不同但使用同一规范名称的条目。
- 每个判例都有唯一编号、输入事实、适用规则、结论和不适用条件。
- T01.1 中所有冲突项均能链接到裁决或明确的阻塞原因。

### [x] T01.7 执行跨文档术语一致性检查

**前置 Task**

- T01.6

**达成目标**

验证统一词汇能够覆盖路线图现有文本，并生成后续工作包可重复执行的术语一致性检查记录。

**输入**

- `docs/meta-model/domain-language.md`
- `docs/meta-model/domain-boundary-cases.md`
- `README.md`
- `CONTEXT.md`
- `docs/wayfinder/**/*.md`

**执行步骤**

1. 搜索核心术语的中英文写法，列出未采用规范名称或含义冲突的位置。
2. 对每处差异判定为允许的源码名称、待后续工作包修订或真实冲突。
3. 用至少五个未参与词汇编写的 MasterData 场景试跑边界判定。
4. 记录检查命令、结果、遗留项及责任工作包。

**产出物**

- `docs/meta-model/domain-language-validation.md`

**验证方式**

- 检查记录包含可重复执行的 `rg` 命令和逐项结果。
- 五个试跑场景均能得到唯一主模型类型和明确的运行时责任边界。
- 不允许遗留未编号、无责任工作包的术语冲突。

## 工作包验收

- T01.1 至 T01.7 全部完成，列出的产出物均已落库并可通过相对路径访问。
- 八类模型、物理数据结构、技术接口、业务规则和运行时对象之间不存在未记录的重叠职责。
- 至少 12 个 MasterData 判例能够按同一套规则重复得到相同结论。
- 后续工作包可直接引用 `docs/meta-model/domain-language.md` 和 `docs/meta-model/model-boundary-matrix.md`，无需再次发明术语。
- 验收记录确认未把未来 Schema 细节、具体执行协议或生产实现写成当前事实。

## 解决记录

**决策摘要**：采用 `M1 Object / M2 Behavior / M3 Rule / M5 Actor-Permission / M6 Flow / M7 Query / MU Presentation / MI Integration` 八类模型；MI 全称定为 Integration（不再用 Integration Mapping 造成冗余）；不引入 M4/ME。术语统一为 15 个规范英文名与中文名，建立 12 个 MasterData 判例和 5 个试跑场景。唯一阻塞项 TERM-013（`SubtableType` 是否业务对象）移交工作包 02 证据快照。

**关键取舍**：场景（scenario）与事件（event）不进入持久本体模型集，避免与参考项目 M4/ME 编号冲突；表/DTO/ViewModel 均不自动判定为 M1，需业务身份+生命周期+业务规则齐备。

**验证结果**：8 份产出物全部落库；18 个 TERM 冲突项可定位并裁决；12 个判例重复判定一致；`git diff --check` 通过。

**产出物**：

- [domain-term-inventory.md](../meta-model/domain-term-inventory.md)
- [model-boundary-matrix.md](../meta-model/model-boundary-matrix.md)
- [object-data-shape-boundaries.md](../meta-model/object-data-shape-boundaries.md)
- [behavior-rule-execution-boundaries.md](../meta-model/behavior-rule-execution-boundaries.md)
- [runtime-concept-boundaries.md](../meta-model/runtime-concept-boundaries.md)
- [domain-language.md](../meta-model/domain-language.md)
- [domain-boundary-cases.md](../meta-model/domain-boundary-cases.md)
- [domain-language-validation.md](../meta-model/domain-language-validation.md)

**遗留项**：`docs/wayfinder/map.md` 与 `tickets/05` 中 “MI 集成” 冗余写法交由工作包 05 关闭时修订；TERM-013 交工作包 02。
