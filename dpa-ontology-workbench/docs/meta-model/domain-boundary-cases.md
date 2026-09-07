# 领域边界判例（T01.6 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.6 产出。
> 任务：为易混概念提供可复用、可重复得到相同结论的稳定判例。
> 规范词汇见 [domain-language.md](domain-language.md)；判例编号 `CASE-XX` 稳定，新增不重排。
> 所有 MasterData 事实来自 `docs/wayfinder/masterdata-scope.md` 与 DPA 源码（revision `ce9ad5ca`）。

## 判例表（12 个）

| 编号 | 场景 | 输入事实 | 适用规则 | 结论 | 不适用条件 |
|---|---|---|---|---|---|
| CASE-01 | `SubtableType` 枚举 | 0–86 成员，常量字符串名 | 业务身份/生命周期判定（T01.3 §3.1） | 是 M1 候选，具体归属待证据（TERM-013） | 若仅为配置注册表则非 M1 |
| CASE-02 | `tb_Master_Data_PR_Online_Approval` 表 | 单表多 `DicType` | 一个表承载多个概念 | 物理表映射 = DTO，非 M1 | 若某类型独享表结构则另判 |
| CASE-03 | `SubtableViewModelBase` | 页面组装形状 | DTO/ViewModel 非对象 | 非 M1，归 MU | 若承载业务不变量则需复审 |
| CASE-04 | `GetSubtableDatalist` | `[HttpGet]` 查询 | 纯读→M7 | M7 Query（待证据证明纯读） | 无法证明纯读→MIXED/HIGH |
| CASE-05 | `UpdateSubtableData` | `[HttpPost]` 写+缓存 | 单一 endpoint 多副作用 | M2 Behavior + MIXED/HIGH，须 HITL | 纯读时另判 |
| CASE-06 | 禁止更新列表 | `ESN`/`Tax_Rate` 等 | 可复用判断→M3 | M3 Rule | 页面级校验则非 Rule |
| CASE-07 | 审批权限 | 在线审批角色 | 谁在什么范围可做什么→M5 | M5 Actor/Permission（待证据） | 技术过滤器实现非 M5 |
| CASE-08 | 审批→通过/驳回 | 状态转换 | 跨行为编排→M6 | M6 Flow（待证据） | 单次页面刷新非 Flow |
| CASE-09 | `Depth_Structure` Jedox | 特殊数据源读取 | 查询语义→M7 | M7 Query + MI 技术目标 | 若含写副作用则 MIXED |
| CASE-10 | 子表表单字段 | `SubTableViewInfo` 元数据 | 展示契约→MU | MU Presentation | 业务规则不写入 MU |
| CASE-11 | 批量覆盖导入 | `DirectOverwriteSubtableDataFromExcel` | 批量写+高风险 | M2 + MIXED/HIGH，禁自动执行 | 若只读则另判 |
| CASE-12 | 提案→草稿→DPA 保存 | 编辑流程 | 写操作默认提案 | Action Proposal→Draft Application→DPA 保存 | 复杂表单走 Legacy View |

## 判例详述

### CASE-01：`SubtableType` 是否业务对象（TERM-013）

- 输入事实：`SubtableType` 定义 `ESN=0`…`Depth_Structure=46`… 共 0–86 成员；常量字符串名 `ESN`、`Standard_Goods`、`Tax_Rate` 等。
- 适用规则：业务身份（独立于物理存储）+ 生命周期 + 业务规则约束，三者齐备才判 M1（T01.3 §3.1）。
- 结论：目前是 M1 候选；是否为“分类体系/配置注册表/能力选择器/技术聚合入口”取决于工作包 02 证据快照（`masterdata-scope.md` 范围锚点）。
- 不适用条件：若证据证明其仅为配置注册表或能力选择器，则不判为 M1。

### CASE-02：单表承载多概念

- 输入事实：`tb_Master_Data_PR_Online_Approval` 以 `DicType` 区分多个 `SubtableType`。
- 适用规则：一个表可承载多个业务概念，表映射不等同于业务对象。
- 结论：`MasterDataPROnlineApproval` Entity = 物理表映射（DTO），非 M1。
- 不适用条件：若某 SubtableType 拥有独立表结构与独立业务身份，需单独评估。

### CASE-03：ViewModel 非对象

- 输入事实：`SubtableViewModelBase` 由 `SubTableViewInfo.CreateViewModel()` 生成，用于页面呈现。
- 适用规则：DTO/ViewModel 是传输/呈现形状，无业务身份与生命周期。
- 结论：非 M1，作为 MU Presentation 契约输入。
- 不适用条件：若形状本身承载业务不变量且具身份，需复审。

### CASE-04：纯查询

- 输入事实：`GetSubtableDatalist(string subtableType)` 为 `[HttpGet]`。
- 适用规则：可证明纯读→M7 Query；否则 MIXED/HIGH。
- 结论：M7 Query（读性由工作包 05/06 验证）。
- 不适用条件：无法证明纯读时按 MIXED/HIGH 处理，禁止自动执行。

### CASE-05：写 + 缓存副作用

- 输入事实：`UpdateSubtableData`（`[HttpPost]`）写库后 `clearSubtableCache()` + `HrEmployeeInfoCache().Remove()`。
- 适用规则：单一 endpoint 多副作用→MIXED/HIGH。
- 结论：M2 Behavior 表达业务结果；执行须经 HITL。
- 不适用条件：若确证纯读，则另判。

### CASE-06：禁止更新列表

- 输入事实：`ESN`、`Tax_Rate`、`Tax_Code`、`Tax_code_prefix`、`Exchange_Rate` 出现在禁止更新列表。
- 适用规则：可复用业务判断→M3 Rule。
- 结论：M3 Rule（“该类型不允许更新”）。
- 不适用条件：若只是表单级输入校验，则非 Rule（TERM-007）。

### CASE-07：审批权限

- 输入事实：在线审批行为存在权限要求（权限归属需证据确认）。
- 适用规则：谁在什么范围可做什么→M5。
- 结论：M5 Actor/Permission 语义。
- 不适用条件：DPA 过滤器/角色的技术实现不是 M5 本体内容。

### CASE-08：审批流程

- 输入事实：审批→通过/驳回 的状态转换（需证据确认存在）。
- 适用规则：跨行为编排→M6 Flow。
- 结论：M6 Flow（待证据确认）。
- 不适用条件：单次页面刷新/按钮导航不是 Flow（TERM-005）。

### CASE-09：Jedox 特殊数据源

- 输入事实：`Depth_Structure`（`SubtableType=46`）使用 Jedox 读取分支。
- 适用规则：查询语义→M7；技术目标→MI。
- 结论：M7 Query + MI 技术目标。
- 不适用条件：若 Jedox 分支含写副作用，则 MIXED/HIGH。

### CASE-10：子表表单元数据

- 输入事实：`SubTableViewInfo` 提供 `CreateForm/CreateSubTableGridColum/CreateSubTableSourcefield` 等。
- 适用规则：展示契约→MU。
- 结论：MU Presentation 契约。
- 不适用条件：业务规则、权限、执行逻辑不写入 MU。

### CASE-11：批量覆盖导入

- 输入事实：`DirectOverwriteSubtableDataFromExcel`（`[HttpPost]`，`MasterDataExcelOverwriteParam`）。
- 适用规则：批量写 + 高风险→禁自动执行。
- 结论：M2 + MIXED/HIGH。
- 不适用条件：若只读则另判。

### CASE-12：提案→草稿→DPA 保存

- 输入事实：编辑流程默认走写提案（`AGENTS.md`）。
- 适用规则：写操作默认只生成提案。
- 结论：Action Proposal→Draft Application→原 DPA 保存动作。
- 不适用条件：复杂表单/工作流走 Legacy View（不复制复杂表单）。

## 验证记录

- 12 个判例均有唯一编号、输入事实、适用规则、结论和不适用条件。
- 使用同一套规则重复运行可得到相同结论（判例相互一致，无矛盾结论）。
- 所有 MasterData 事实可追溯到 `masterdata-scope.md` 或 DPA 源码（revision `ce9ad5ca`）。
- 命令：`git diff --check` 应通过。
