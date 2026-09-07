# 表、DTO、数据形状与业务对象边界（T01.3 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.3 产出。
> 任务：给出从数据库表、存储过程结果、HTTP DTO、页面 ViewModel 到 M1 Object 的明确判定规则，避免按物理数据结构一比一生成业务对象。
> MasterData 示例仅使用 `SubtableType` 可达证据（`docs/wayfinder/masterdata-scope.md`）。
> 源码证据均来自 DPA 仓库 `D:\WorkSpace`，分支 `SSME.DPA.DEV`，revision `ce9ad5ca`；正式 Evidence Snapshot（工作包 02）将固化这些位置。

## 1. 概念定义

| 概念 | 定义 | 主键/身份 | 生命周期 | 是否 M1 Object |
|---|---|---|---|---|
| Table（表） | DPA 数据库物理表，如 `tb_Master_Data_PR_Online_Approval` | 物理主键（`Id`/`Guid`） | 由 DPA 持久化管理 | 否，仅是候选输入 |
| Row（行） | 表中一条记录，`MasterDataPROnlineApproval` 实例 | 行主键 | 同表 | 否 |
| DTO（数据传输对象） | 跨层/跨接口传输的数据形状，如 HTTP 请求/响应、`MasterDataPROnlineApprovalViewModel` | 通常无业务身份 | 随请求/响应 | 否 |
| ViewModel（页面模型） | 为页面呈现组装的数据形状，如 `SubtableViewModelBase`、`SubTableGridColum` | 无独立身份 | 页面生命周期 | 否 |
| Query Result Shape（查询结果形状） | 查询返回的集合/字段形状，如 `GetSubtableDataList()` 返回的 `List<JObject>` | 无身份 | 单次查询 | 否 |
| Business Object（业务对象） | 具有业务身份、属性、生命周期和关系的领域概念 | 业务身份（可能由多列/多表构成） | 由业务规则定义 | **是 M1** |

## 2. 源码证据基线（FACT）

以下为 DPA 源码中已观察事实，标注文件位置；`masterdata-scope.md` 中“当前已观察事实”将在工作包 02 固化为正式证据：

| 事实 | 证据位置（revision `ce9ad5ca`） |
|---|---|
| `MasterDataPROnlineApproval` 映射表 `tb_Master_Data_PR_Online_Approval`，字段 `Id`、`DicType`、`DicName`、`DicContent`、`ParentDicCode`、`ParentId`、`ActiveStatus`、`Remark` | `YiSha.Entity/YiSha.Entity/MasterData/MasterDataPROnlineApproval.cs` |
| `MasterDataPRJedox` 映射表 `tb_Master_Data_PR_Online_Approval_jedox`，含 `Id`(Guid)、`ParentId`、`DicName`、`mLevel`、`Info`、`desc` | 同文件 |
| `OperateLog` 映射表 `tb_Master_Data_PR_Online_Approval_oplog` | 同文件 |
| `SubTableViewInfo` 按 `SubtableType` 通过工厂分派到具体 ViewModel 实现，提供 `CreateColums/CreateForm/CreateMutiEditForm/CreateSubTableGridColum/CreateSubTableSourcefield/CreateViewModel/GetSubtableDataList` | `YiSha.Business/YiSha.Business/MasterData/DataHandler/SubTableDataUtil.cs`（`SubTableViewInfo` 类，141 行起） |
| `GetSubtableDataList()` 返回 `List<JObject>`（无强类型的查询结果形状） | `SubTableDataUtil.cs` |
| Controller 构造 `SubTableViewInfo`、`MasterDataPROnlineApprovalViewModel`、`SubtableUploadExcelTemp`，并通过 `ViewBag` 传页面 | `YiSha.Web/YiSha.Admin.Web/Areas/MasterData/Controllers/MasterDataPROnlineApprovalController.cs` |
| `SubtableType` 枚举定义 `ESN=0`…`Depth_Structure=46`… 等 0–86 成员，并有常量字符串名 | `YiSha.Entity/YiSha.Enum/MasterDataPROnlineApproval/MasterDataPROnlineApprovalConfig.cs` |

## 3. 判定规则

### 3.1 判定顺序

对任一数据形状，按顺序回答：

1. 是否具有**独立于物理存储的业务身份**（业务认为“这是同一个东西”的标识，可能跨多表）？→ 无 → 不是 M1。
2. 是否具有**业务定义的生命周期**（创建→变更→归档/删除的状态变化由业务规则管理）？→ 无 → 不是 M1。
3. 是否由**业务规则**约束其属性与关系？→ 无 → 不是 M1。
4. 满足 1–3 且能从证据追溯 → M1 Object 候选；否则为数据形状（Table/Row/DTO/ViewModel/Query Result）。

### 3.2 各概念角色

- **主键（物理 PK）**：只证明行身份，不证明业务身份。`tb_Master_Data_PR_Online_Approval.Id`（int）只是物理主键。
- **字段**：DTO/ViewModel 的字段是传输/呈现形状；业务对象的属性必须具有业务语义且可追溯到证据。
- **聚合边界**：只有需要保持强一致不变量的对象集合才构成 Aggregate（见 `docs/architecture/progressive-ddd.md`），不按表一一对应。
- **业务身份**：可能由 `SubtableType + DicName + ParentId` 等多字段构成，而非单物理主键（INFERENCE，需工作包 02 证据确认）。
- **生命周期**：`ActiveStatus`、`CreateDate`、`LastUpdatedDate`、`OperateLog` 的存在暗示业务状态与历史，但生命周期语义需业务裁决（INFERENCE）。

### 3.3 证据不足的处理

- 无法证明业务身份或生命周期的数据形状 → **保持候选（candidate）**，不判定为已发布 M1。
- 证据只支持“技术映射”而不支持业务语义 → 归入 MI 技术侧或 `MIXED/HIGH` 审核。
- 动态 SQL、反射、无法静态解析的绑定 → 记 `GAP-XXX` 并进入人工审核，不自动升级为 M1。

## 4. MasterData 边界案例

### 案例 A：一个业务对象由多表/多源组成（INFERENCE，需证据确认）

- 输入证据：`MasterDataPROnlineApproval`（主表）、`MasterDataPRJedox`（Jedox 数据源表）、`OperateLog`（操作日志表）、`SubTableViewInfo` 元数据（字段/列/表单）。
- 判定过程：`Depth_Structure`（`SubtableType=46`）使用 Jedox 分支，其数据读自 `tb_Master_Data_PR_Online_Approval_jedox`；同一 SubtableType 的业务对象可能由“主表数据 + Jedox 数据 + 元数据描述 + 变更日志”共同构成，分散在至少三张表与代码元数据中。
- 结论：按 3.1，只有满足业务身份+生命周期的组合才能成为 M1 Object；**不应**把 `tb_Master_Data_PR_Online_Approval` 单独判为一个 M1，也不应把三张表自动合并成一个 M1。最终归属由证据完整度与业务裁决决定（TERM-013）。
- 反例：若直接“一张表 → 一个 Entity → 一个 M1”，会错误地把 `MasterDataPRJedox` 判为独立业务对象。

### 案例 B：一个表承载多个概念

- 输入证据：`tb_Master_Data_PR_Online_Approval` 的 `DicType` 区分不同 `SubtableType`（`ESN=0`…`Depth_Structure=46`…），`DicName`/`DicContent`/`ParentDicCode` 承载不同子表类型的通用结构。
- 判定过程：同一物理表是 87 个枚举值共享的通用审批数据载体；它承载的是“多个子表类型”的数据，不承载单一业务概念。
- 结论：`MasterDataPROnlineApproval` Entity 是**物理表映射（DTO）**，不代表一个 M1 业务对象；真正的 M1 候选是“某个 SubtableType 对应的业务实体”，其数据落在该表内由 `DicType` 区分的行中。
- 反例：把 `MasterDataPROnlineApproval` 直接发布为 M1 Object，会让 87 个不同概念共用一个业务对象，违背“一个对象一个稳定身份”的边界。

### 案例 C：DTO/ViewModel 不等于对象

- 输入证据：`SubTableViewInfo.CreateViewModel()` 返回 `SubtableViewModelBase`；`CreateSubTableGridColum()` 返回 `List<SubTableGridColum>`；`GetSubtableDataList()` 返回 `List<JObject>`；Controller 用 `ViewBag` 传递 `FormFields`、`AuthorizeList`、`DownloadUrl`。
- 判定过程：这些形状是为页面呈现或 JSON 传输组装的，无独立业务身份、生命周期，也不承载业务不变量。
- 结论：DTO（`MasterDataPROnlineApprovalViewModel`）、ViewModel（`SubtableViewModelBase`）、查询结果（`List<JObject>`）、页面参数（`ViewBag.*`）**均不是 M1**；它们最多是 MU Presentation 展示契约或 M7 Query 结果投影的输入。
- 反例：把 `SubTableViewInfo`（工厂/适配对象）或 `SubtableViewModelBase` 判为 M1，会把技术层形状误当业务对象。

### 案例 D：查询结果是否拥有业务生命周期

- 输入证据：`GetSubtableDataList()` 每次查询返回 `List<JObject>`，无持久身份。
- 判定过程：查询结果是单次执行的可重建投影（TERM-006），不满足 3.1 的生命周期要求。
- 结论：查询结果形状不是 M1，也不拥有业务生命周期；它由 M7 Query 定义、MU 投影，最终由 DPA 原数据源保证事实。
- 反例：认为“查询返回的对象就是业务对象”，会导致把投影当事实源。

## 5. 结论汇总

- “表是否必然生成 M1”——否。表是候选输入，需业务身份与生命周期判定。
- “DTO 是否可直接成为 M1”——否。DTO/ViewModel 是传输/呈现形状。
- “查询结果是否拥有业务生命周期”——否。查询结果是可重建投影。
- 未证明业务身份和生命周期的数据形状不会被判定为已发布 M1 Object。

## 6. 验证记录

- 每个案例包含输入证据、判定过程、结论和反例。
- 使用本文件规则回答第 5 节三个问题，答案互不矛盾。
- 证据位置、revision 已记录；正式 Evidence Snapshot 由工作包 02 固化。
- 命令：`git diff --check` 应通过。
