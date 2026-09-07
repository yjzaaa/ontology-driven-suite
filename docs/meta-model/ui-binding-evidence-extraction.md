# UI 页面与绑定证据提取规范（T02.5 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.5 产出。
> 任务：定义页面、组件、表单字段、事件处理器、route/API 调用、DTO 和展示条件之间的可追溯绑定。
> 前置：T02.1、T02.2。试点仅限 `SubtableType` 可达页面。

## 1. UI 资产类型与稳定 ID

| 资产类型 | 稳定 ID 规则 | 示例 |
|---|---|---|
| 页面 | `ui:{repo}:{rev}:{pagePath}` | `ui:WS:ce9ad5ca:.../MasterDataPROnlineApproval/Index.cshtml` |
| 组件/网格 | `ui:{repo}:{rev}:{pagePath}:{componentId}` | `ui:WS:ce9ad5ca:.../Index.cshtml:grid` |
| 字段/列 | `ui:{repo}:{rev}:{pagePath}:{fieldKey}` | `ui:WS:ce9ad5ca:.../Index.cshtml:subtable-grid` |
| 命令/事件 | `ui:{repo}:{rev}:{pagePath}:{handler}` | `ui:WS:ce9ad5ca:.../Index.cshtml:getSubtableDatalist` |
| 请求调用 | `ui:{repo}:{rev}:{pagePath}:{targetRoute}` | `ui:WS:ce9ad5ca:.../Index.cshtml:GetSubtableDatalist` |

## 2. 绑定提取规则

| 绑定类型 | 规则 |
|---|---|
| 模板绑定 | `@Url.Action("ActionName")` / `@Url.Content("~/...")` → 解析为后端 route，链接到 Controller Action |
| JS 事件绑定 | `$("#grid").jqxGrid(...)`、`getRequestFunc('@Url.Action(...)')` → 记录事件处理器与目标端点 |
| 条件可见性 | `gridwidget.cshtml` 中 `linkrenderer`/`setCellsStyle` 条件分支 → 记录展示条件 |
| 校验提示 | `ViewBag.VarifyLists`、`DuplicateValidatorInfo` → 记录校验器绑定 |
| DTO 字段映射 | `columns.push({name: list[i].datafield...})` → 记录列字段 → DTO 字段映射 |
| 混合副作用 | 绑定到 `UpdateSubtableData`（写端点）的调用 → 标记 `MIXED/HIGH` |

## 3. 源码证据基线（FACT，revision `ce9ad5ca`）

| 事实 | 证据位置 |
|---|---|
| `Index.cshtml` JS 绑定 `GetSubtableColumlist`、`GetSubtableDatalist`、`GetSubtableViewModel` 三个查询端点（`@Url.Action(...)`），参数 `subtableType` | `Areas/MasterData/Views/MasterDataPROnlineApproval/Index.cshtml:323-330` |
| 同一页面绑定写端点 `UpdateSubtableData`（`postRequestFunc('@Url.Content("~/MasterData/MasterDataPROnlineApproval/UpdateSubtableData")')`） | 同文件 333 |
| 页面使用 `jqxGrid` 渲染，`cellclick`/`getselectedrowindexes` 事件 | 同文件 203-268 |
| `gridwidget.cshtml` 绑定 `SSMEDPAManage/SSME_IBDB_Detail/GetPageListJson`、`SaveCustomColumn` 等 | `gridwidget.cshtml:703,813` |
| 列字段动态组装 `columns.push({name: list[i].datafield,...})`（运行时生成控件/列） | 同文件 802-807 |

## 4. 无法静态解析的绑定

- 运行时生成控件（`gridwidget.cshtml` 的 `columns` 动态 push）、字符串拼接字段、动态 URL → 记为 `GAP-002`，计入缺口与覆盖率分母（T02.6）。
- 无法从静态源码证明字段→DTO 映射的绑定，不声明为 `FACT`（不用命名相似推断，`AGENTS.md` 证据纪律）。

## 5. 样例：masterdata-ui-bindings.json

- 至少包含页面→字段、字段→DTO、事件→route 三类关系。
- 每条跨前后端关系均能定位双方 revision 和源文件，不使用仅凭命名相似得出的 `FACT`。
- 无法解析的绑定计入缺口和覆盖率分母。

## 6. 验证记录

- 样例至少包含页面到字段、字段到 DTO、事件到 route 三类关系。
- 每条跨前后端关系均能定位双方 revision 和源文件，不使用仅凭命名相似得出的 `FACT`。
- 无法解析的绑定被计入缺口和覆盖率分母。
- 命令：`git diff --check` 应通过。
