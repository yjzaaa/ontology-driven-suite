# MasterData 源码反推业务逻辑报告

> 本文档基于 DPA 仓库 `D:\WorkSpace`（分支 `SSME.DPA.DEV`，revision `ce9ad5ca`）实际源码反推，只陈述源码可见的业务事实，不臆断。
> 证据等级标注：`FACT`（源码直接可见）、`INFERENCE`（由 FACT 推导）、`ASSUMPTION`（无直接证据的假设）。
> 范围：`MasterDataPROnlineApprovalController` / `SubtableType` 可达逻辑（`docs/wayfinder/masterdata-scope.md`）。

## 1. 业务范围锚点：SubtableType 枚举

`YiSha.Entity/YiSha.Enum/MasterDataPROnlineApproval/MasterDataPROnlineApprovalConfig.cs` 定义 **`SubtableType` 枚举 0–86，共 87 个成员**（FACT）。

枚举成员按批次新增（源码注释为证）：

| 批次 | 成员示例 |
|---|---|
| 基础 | `ESN(0)`、`GL_Account(1)`、`UOM(2)`、`Tax_Rate(3)`、`Tax_Code(4)`、`Currency(5)`、`Exchange_Rate(6)`、`Entertainment(7)`、`Asset_Class(8)`…`Standard_Goods(15)`、`Reference_No(13)`… |
| 2025-04 | `Tax_code_prefix(32)`、`Cost_Center_Category(33)`…`Depth_Structure(46)`、`Jedox_*` 系列(50-54) |
| 2025-04-18 | `Cost_Planning_Scenario(55)`、`Mapping_BL_Plant(56)`…`Customer_Product(61)` |
| 2025-07/09 | `Vendor_type_choose(62)`、`Moblie_HAAS_Option(63)`、`Mapping_Slo_Plant(64)`、`Application(65)`、`Moblie_HAAS_Phone_List(66)` |
| 2025-10 | `MD_DLP_Request_Type(67)`…`MD_DeviceCapacity(72)` |
| 2025-11/12 | `ImprovementCategory(73)`…`ImpactRate(79)`、`MetrixForLA(80)` |
| 2026-01/03/04 | `SiteToWork(81)`、`SQEResponsible(82)`、`CCTVArea(83)`、`SystemType(84)` |
| 2026-07 | `PC_HAAS_Package(85)`、`PC_HAAS_List(86)` |

**业务含义**：每个枚举值代表一类"主数据子表"，即一类可在线维护/审批的主数据（税率、税码、币种、汇率、物料、成本中心、映射关系、DLP 设备、PC HaaS 等）。同一控制器统一处理，按 `SubtableType` 分派。

## 2. 核心业务规则（源码可见）

### 2.1 禁止更新子表列表（FACT）

`MasterDataPROnlineApprovalController.cs` `Form` 方法中硬编码 `unUpdateSubtableList`：

- `ESN`(0)、`Tax_Rate`(3)、`Tax_Code`(4)、`Tax_code_prefix`(32)、`Exchange_Rate`(6)

行为：命中列表的子表，编辑表单字段 `IsEnable` 处理——**已有记录时这些字段不可编辑**（`string.IsNullOrEmpty(RecordId) ? true : x.IsEnable`）。即：**税/汇率/ESN 类主数据只能新增，不能修改既有记录**（INFERENCE：列表语义为"不可更新"）。

### 2.2 禁用表单操作的子表（FACT）

`Index` 方法中 `DisableFormActionSubtableTypesJson`：

- `Moblie_HAAS_Phone_List`(66)、`PC_HAAS_List`(86)

行为：这两个子表的"表单操作"（如 Add/Edit）被禁用，前端收到 JSON 后不显示对应操作按钮。

### 2.3 专用 Controller 重定向（FACT）

| 子表 | 重定向 |
|---|---|
| `Standard_Goods`(15) | `Form`/`EditByBatchForm` → `StandardGoods` Controller |
| `Reference_No`(13) | `MutiEdit`/`Log` → `RenferenceNo` Controller |
| `PC_HAAS_List`(86) | `Index` → `PC_HAAS_List` Controller |

行为：这些子表不走通用页面，而是跳转到专用 Controller（各自实现复杂表单/批量编辑）。

### 2.4 特殊数据源分支（FACT）

`GetSubtableDatalist` 方法：当 `subtableType == Depth_Structure(46)` 时，数据源不是通用表，而是 `MasterDataPROnlineApprovalService.GetMasterDataPROnlineApprovalJedox()`（Jedox 表 `tb_Master_Data_PR_Online_Approval_jedox`），并按 `DicName == "Depth_Structure"` 过滤。

即：**Depth_Structure 的结构数据来自 Jedox 特殊表**，其他子表走通用表 `tb_Master_Data_PR_Online_Approval`。

## 3. 通用数据模型（FACT）

- 所有子表数据共用主表 `tb_Master_Data_PR_Online_Approval`，以 `DicType`（= SubtableType 数值）区分（INFERENCE）。
- Jedox 分支用 `tb_Master_Data_PR_Online_Approval_jedox`。
- 操作日志表 `tb_Master_Data_PR_Online_Approval_oplog`（实体 `OperateLog`）。

## 4. 校验规则（FACT）

### 4.1 重复性校验（DuplicateValidatorInfo）

`Form` 方法构造重复校验器：

- `dic_code` 不允许重复（错误提示"dic_code已存在"）
- `VendorCode` 不允许重复（错误提示"VendorCode已存在"）

### 4.2 表单字段校验类型（FormValidationRules）

常量定义校验类型：`required`、`number`、`digits`、`email`、`url`、`date`、`dateISO`、`creditcard`、`percentage`、`dic_code`；Special_Goods 专用：`per`、`validateAmount`、`validateNumber`。

Standard_Goods 示例数据（注释中）展示其字段：`matType/catalogCode/shortDesc/Buyer/vendorCode/vendorMail/vPrice/cCurrency/exchangeRate/uom/glAccount/AssetClass/esnCode/leadTime/taxRate/invoice_type/assetFlag/AssetType/ITAssetType/BuyerAcc/created_by/last_modified_by` 等。

## 5. 用户操作动作（RoleButtonActions，FACT）

`MasterDataNameConfig.cs` 定义页面可用的操作按钮动作：`AddNew`、`CopyItem`、`Edit`、`Disable`、`Enable`、`DownLoad`、`Form`、`Log`(修改历史日志)、`MutiEdit`、`Upload`、`DirectOverwriteImport`、`Search`、`TransferNomination`、`CreationNomination`、`CancelNomination`、`CreateDelegation`、`RevokeDelegation` 等。

即：**每类子表页面支持新增、复制、编辑、启用/禁用、下载模板、查看日志、批量编辑、上传、直接覆盖导入等动作**，具体哪些动作对哪些子表开放需权限配置（ASSUMPTION，未在源码见角色-动作矩阵）。

## 6. 批量编辑（MutiEdit，FACT）

- `MutiEditDataLog`：批量编辑前记录操作日志（入参 `List<UpdateMasterdataPROnlineApprovalDto>`）。
- `SaveMutiEditData`：批量保存（入参 `MutiEditForm`）。
- `SaveEditByBatchIdsToSession`：把批量编辑的 ID 先写入 Session。
- `ProcessIdAsync`：用 `SemaphoreSlim` 并发处理，每个任务独立反序列化 `EntityJson`，避免共享对象问题（并发正确性处理，INFERENCE）。

## 7. 缓存（FACT）

- `MasterDataPROnlineApprovalDll` 使用 `ConcurrentDictionary<SubtableType, ImmutableList<MasterDataPROnlineApproval>> _subtableCache` 缓存子表数据。
- 写操作后调用 `dll.clearSubtableCache()` 和 `HrEmployeeInfoCache().Remove()` 清理缓存。

## 8. 上传模板（FACT）

`SubtableUploadExcelTempName` 定义各子表的 Excel 上传模板（`.xlsm`）：`ESN upload template.xlsm`、`Tax Rate upload template.xlsm`、`Tax Code upload template.xlsm`、`Tax Code Prefix upload template.xlsm`、`Exchange Rate upload template.xlsm`、`Standard goods upload template.xlsm`、`Vendor type upload template.xlsm`、`Cost Center Function upload template.xlsm`、`Cost Planning Scenario upload template.xlsm`、`Mapping AssetClass GLAccount upload template.xlsm`、`Mapping TaxCode TaxRate upload template.xlsm`、`Reference number upload template.xlsm` 等。

## 9. 数据读取分派：ViewModel / DataHandler（FACT）

按子表类型，系统有两个分派层（特性 `[SubTableViewModel]` / `[SubtableDataHandler]` 标记专用实现，未标记的走基类通用逻辑）：

| 层 | 专用实现数 | 位置 |
|---|---|---|
| ViewModel（页面展示层） | 60 个专用 | `YiSha.Business/.../ViewModel/SubTableViewModel.cs` |
| DataHandler（数据读写层） | 86 个专用 | `YiSha.Business/.../MasterDataPROnlineApprovalSubTable/SubtableDataHandle.cs` |

DataHandler 专用子表覆盖绝大部分枚举值（含 `Jedox_*` 系列、`Mapping_*` 系列、`MD_*` 系列、`PC_HAAS_*` 等），说明**大多数子表有自定义的数据处理逻辑**（INFERENCE：如特殊字段映射、校验、数据源切换）。

## 10. 反推结论（业务逻辑提炼）

从源码可见的 DPA 业务逻辑（供本体建模使用，均为候选语义，待证据快照固化）：

1. **子表分类体系**：`SubtableType` 是 87 类主数据子表的统一分类键（可能被判定为分类体系/能力选择器，TERM-013 待裁决）。
2. **统一审批入口**：一个在线审批控制器统一承载所有子表的查看/编辑/审批/导入，按 `SubtableType` 分派。
3. **只读不可更新类**：税/汇率/ESN 类子表只能新增，既有记录不可编辑（禁止更新列表）。
4. **专用表单类**：Standard_Goods、Reference_No、PC_HAAS_List 等走专用 Controller（复杂业务逻辑）。
5. **特殊数据源类**：Depth_Structure 走 Jedox 表。
6. **只读操作受限类**：Moblie_HAAS_Phone_List、PC_HAAS_List 禁用表单操作。
7. **通用数据模型**：主数据共用一张主表 + 操作日志表 + 部分子表专用表/专用 Handler。
8. **通用操作能力**：新增/复制/编辑/启用禁用/日志/批量编辑/上传模板/直接覆盖导入。

## 11. 证据位置索引（均 revision `ce9ad5ca`）

| 事实 | 文件 |
|---|---|
| SubtableType 枚举 0–86 | `YiSha.Entity/YiSha.Enum/MasterDataPROnlineApproval/MasterDataPROnlineApprovalConfig.cs` |
| 禁止更新列表 / 重复校验 | `YiSha.Web/YiSha.Admin.Web/Areas/MasterData/Controllers/MasterDataPROnlineApprovalController.cs`（Form） |
| 专用重定向 / 禁用表单操作 | 同上（CopyItem/EditByBatchForm/Index） |
| Jedox 分支 | 同上（GetSubtableDatalist） |
| 操作动作按钮 | `YiSha.Entity/YiSha.Enum/MasterDataPROnlineApproval/MasterDataNameConfig.cs` |
| 上传模板名 | 同 Config.cs（SubtableUploadExcelTempName） |
| ViewModel 分派 | `YiSha.Business/YiSha.Business/MasterData/ViewModel/SubTableViewModel.cs` |
| DataHandler 分派 | `YiSha.Business/YiSha.Business/MasterData/MasterDataPROnlineApprovalSubTable/SubtableDataHandle.cs` |
| 实体/表 | `YiSha.Entity/YiSha.Entity/MasterData/MasterDataPROnlineApproval.cs` |

## 12. 验证记录

- 所有业务事实均标注源码文件（revision `ce9ad5ca`），可逐条回源核对。
- `FACT`/`INFERENCE`/`ASSUMPTION` 已标注，无证据的结论保持假设。
- 本报告是反推证据，不具备运行执行权；正式固化需 Evidence Snapshot（工作包 02 规则）。
- 命令：`git diff --check` 应通过。
