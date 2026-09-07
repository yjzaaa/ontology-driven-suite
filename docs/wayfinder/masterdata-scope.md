# MasterData 试点范围

## 范围锚点

本路线图中的“MasterData 参考切片”统一指：

- Controller：`YiSha.Web/YiSha.Admin.Web/Areas/MasterData/Controllers/MasterDataPROnlineApprovalController.cs`
- 枚举：`YiSha.Entity/YiSha.Enum/MasterDataPROnlineApproval/MasterDataPROnlineApprovalConfig.cs` 中的 `SubtableType`

`SubtableType` 是源码发现和追踪的范围锚点，不预先假定它本身是 M1 Business Object。它可能最终被判定为分类体系、配置注册表、能力选择器或多个业务对象的技术聚合入口。

## 纳入范围

- `SubtableType` 的全部枚举值、数值、`Description` 和变更历史。
- `MasterDataPROnlineApprovalController` 中解析、比较、映射或传递 `SubtableType` 的 Action。
- `SubTableViewInfo`、表单字段、列表列、上传模板和 URL 映射。
- `MasterDataPROnlineApprovalDll`、Service、Repository、SQL、存储过程和 Job 中由 `SubtableType` 分派的可达调用链。
- 由 `SubtableType` 分支跳转到专用 Controller 的入口，例如 `StandardGoods`、`RenferenceNo`、`Vendor_type` 等；只分析与该分支直接相关的行为。
- 与 `SubtableType` 相关的页面、脚本、权限、会话键、缓存键、刷新和批量编辑路径。
- 每个枚举值对应的数据源、对象候选、查询、行为、规则、呈现和 MI 候选。

## 排除范围

- MasterData 区域内与 `SubtableType` 无调用或数据关系的其他 Controller。
- `MasterDataPROnlineApprovalController` 中无法追踪到 `SubtableType` 的独立功能。
- 其他 MasterData 业务域的完整本体建模。
- 为每个枚举值自动生成独立 Aggregate、Tool、页面或微服务。
- 在没有证据时推断枚举值的业务含义、数据表或权限。

## 广度与深度

### 广度盘点

必须登记所有 `SubtableType` 枚举值，并回答：

- 在哪些 Action、配置、页面和服务中被引用。
- 使用通用处理路径还是专用 Controller。
- 数据来源和副作用是否已识别。
- 当前证据等级和缺口是什么。

广度盘点用于防止漏项，不要求立即为 87 个枚举值建立完整本体。

### 深度样例

完整纵向穿透优先选择能够覆盖不同实现形态的代表分支：

1. **通用子表路径**：通过 `SubTableViewInfo` 和通用 DLL 处理。
2. **专用 Controller 路径**：例如 `Standard_Goods` 或 `Reference_No`。
3. **特殊数据源路径**：例如 `Depth_Structure` 的 Jedox 分支。
4. **受限编辑路径**：例如只读或禁止更新列表中的类型。
5. **批量或刷新路径**：用于识别混合副作用、Job 和并发风险。

最终样例由证据完整度和业务代表性决定，不在本范围声明中预先认定具体业务模型。

## 当前已观察事实

- `SubtableType` 当前定义了数值 `0` 至 `86` 的枚举成员。
- `MasterDataPROnlineApprovalController` 根据 `SubtableType` 执行通用页面生成、专用 Controller 重定向、数据查询、ViewModel 构建、刷新和批量编辑会话处理。
- `Standard_Goods`、`Reference_No`、`Vendor_type`、`Mapping_WBSType_ProjType`、`Mapping_CC_CategoryFunction`、`Moblie_HAAS_Phone_List`、`PC_HAAS_List` 和 `PC_HAAS_Package` 存在专用 Controller 映射。
- `Depth_Structure` 存在特殊 Jedox 数据读取分支。
- `ESN`、`Tax_Rate`、`Tax_Code`、`Tax_code_prefix` 和 `Exchange_Rate` 出现在禁止更新列表中。

以上事实仍需在正式 Evidence Snapshot 中记录 revision、符号和精确源码位置。

## 范围完成判定

- 全部枚举值均进入资产清单，未使用值也显式标记。
- 所有直接使用 `SubtableType` 的 Action 均已归属或排除。
- 代表性分支可以从 Controller 追踪到权限、页面、Service、数据访问和副作用。
- 任一扩展到其他 MasterData 逻辑的工作都有明确的 `SubtableType` 可达证据。
- 无关 MasterData 功能不会因位于同一区域或同一 Controller 而自动进入本体。
