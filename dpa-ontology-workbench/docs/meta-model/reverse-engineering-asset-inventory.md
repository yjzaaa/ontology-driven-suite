# DPA 反向工程资产清单与扫描边界（T02.1 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.1 产出。
> 任务：形成 DPA 待扫描资产的分类清单、纳入规则、排除规则和责任仓库基线，避免扫描范围依赖个人记忆。
> 试点范围以 [MasterDataPROnlineApprovalController / SubtableType](../wayfinder/masterdata-scope.md) 为锚点，不扫描整个 MasterData 作为试点交付范围。

## 1. 仓库基线（FACT）

| 项 | 值 |
|---|---|
| 仓库路径 | `D:\WorkSpace` |
| 当前分支 | `SSME.DPA.DEV` |
| 固定 revision | `ce9ad5ca`（`ce9ad5ca4b4d4a4c3c3c11a8ea9ea3ac0870f3b7`） |
| 技术栈 | ASP.NET MVC（`YiSha.Admin.Web`）+ Web API（`YiSha.Admin.WebApi`）+ EF/Dapper + Redis 缓存 |
| codebase-memory 索引 | `D-WorkSpace`：36,702 节点 / 113,337 边；C# 1,755 文件、JS 479、CSS 438、HTML 331、SQL 3 |
| 试点锚点 | `MasterDataPROnlineApprovalController.cs` + `MasterDataPROnlineApprovalConfig.cs` 的 `SubtableType` |

## 2. 资产分类清单

### 2.1 Controller / Route

| 资产 | 数量/位置 | 说明 |
|---|---|---|
| Controller 文件 | 117 个 `*Controller.cs` | `YiSha.Web/YiSha.Admin.Web/Areas/**/Controllers/` |
| 试点 Controller | `MasterDataPROnlineApprovalController.cs` | 37 个 Action；按 `SubtableType` 分派 |
| 专用子表 Controller | `Areas/MasterData/Controllers/SubtableControllers/SubtableController.cs` 及专用控制器目录 | `Standard_Goods`、`Reference_No` 等分支 |
| Route | codebase-memory 识别 76 个，但大部分为空 | **MCP 对 ASP.NET MVC 路由识别存在缺口（见 §4 GAP-002）** |

### 2.2 过滤器 / 权限

| 资产 | 位置 | 说明 |
|---|---|---|
| 授权过滤器 | `YiSha.Web/YiSha.Admin.Web/Filter/AuthorizeFilterAttribute.cs`、`YiSha.Admin.WebApi/Filter/AuthorizeFilterAttribute.cs` | DPA 最终授权检查点 |
| 全局异常 | `GlobalExceptionFilter.cs`、`GlobalExceptionMiddleware.cs` | 错误归一化 |
| 权限实体 | `DPA.Enties/DbModels/com_paasit_pai_core_sys*PermissionFilterObj*.cs` 等 | 权限过滤对象表 |

### 2.3 业务服务

| 资产 | 数量/位置 | 说明 |
|---|---|---|
| Dll/BLL | 93 个 `*Dll.cs` / `*BLL.cs` | `YiSha.Business/YiSha.Business/**` |
| 试点 Dll | `MasterData/MasterDataPROnlineApprovalDll.cs` | 含 `UpdateSubtableData`、缓存清理 |
| Service | `YiSha.Business/YiSha.Service/MasterData/MasterDataPROnlineApprovalService.cs` 及 `*.JedoxDiffProcessors.cs` | Jedox 分支处理 |
| 状态转换 | `MasterDataPROnlineApproval` 相关 `ActiveStatus`/审批流 | 待证据确认 |

### 2.4 SQL / 存储过程 / 表

| 资产 | 数量/位置 | 说明 |
|---|---|---|
| 建库脚本 | `Document/DatabaseScript/sqlserver.sql`、`oracle.sql`、`mysql.sql` | `sqlserver.sql` 含 16 个 `CREATE TABLE`；未命中 `CREATE PROCEDURE` |
| `[Table]` Entity | 90 个带 `[Table(...)]` 的类 | `YiSha.Entity/YiSha.Entity/**`（157 类） |
| DbModels | 476 个 | `DPA.Enties/DbModels/` |
| 存储过程 | 当前脚本未发现显式存储过程 | 见 §4 GAP-003，需确认是否全 ORM |

### 2.5 Job / 调度

| 资产 | 位置 | 说明 |
|---|---|---|
| AutoJob 框架 | `YiSha.Business/YiSha.Business.AutoJob/{JobScheduler,JobExecute,JobCenter}.cs` | 调度器/执行器 |
| Job Service | `YiSha.Service/SystemManage/AutoJobService.cs`、`AutoJobLogService.cs` | Job 定义与日志 |
| Worker | `DPAService/Worker.cs`、`Program.cs` | 后台服务 |
| 试点 Job 入口 | `RefreshEntertainmentAutoJob`（Controller 内） | 混合副作用候选 |

### 2.6 callback / 外部调用

| 资产 | 说明 |
|---|---|
| Jedox 分支 | `MasterDataPROnlineApprovalService.JedoxDiffProcessors.cs` | 外部数据源回调/读取 |
| 缓存 | `YiSha.Cache`、`HrEmployeeInfoCache` | 写后缓存清理（副作用） |
| 外部 API | 待 MCP HTTP_CALLS 展开（238 条边） | callback/重试需确认 |

### 2.7 UI 页面与绑定

| 资产 | 位置 | 说明 |
|---|---|---|
| 试点页面 | `Areas/MasterData/Views/MasterDataPROnlineApproval/{Index,Index_Copy,MasterDataImport,MasterDataLog,gridwidget,DirectOverwriteImport}.cshtml` | 表单/列表/导入绑定 |
| 专用子表页面 | `Views/Standard_Goods/`、`Views/RenferenceNo/`（`Form/Log/MutiEdit/TransferBudget.cshtml`）、`Views/Moblie_HAAS_Phone_List/` 等 | 专用 Controller 对应页面 |
| 前端脚本 | `wwwroot/` 下 479 个 JS | 排除第三方库（§3） |

## 3. 纳入 / 排除规则

### 3.1 纳入

- 试点锚点可达的 Controller Action、Dll/Service 方法、表、页面绑定、权限过滤器。
- `SubtableType` 全部枚举值（0–86）的直接使用点（广度盘点）。
- 每个深度样例分支（通用子表 / 专用 Controller / Jedox / 受限编辑 / 批量刷新，见 `masterdata-scope.md`）。

### 3.2 排除

| 排除类别 | 规则 | 理由 |
|---|---|---|
| 生成代码 | `obj/`、`bin/`、`wwwroot/lib/`、`wwwroot/jqwidgets*/` 等第三方/编译产物 | 非 DPA 业务资产 |
| 第三方依赖 | `packages/`、`node_modules/`、jQuery/jqwidgets/layui 等 | 无 `SubtableType` 可达关系 |
| 测试夹具 | `YiSha.Test/`、`*.Tests` | 仅作验证参考，不进入业务本体 |
| 废弃/注释代码 | `//[HttpGet] VendorTypeAutoJob()` 等注释块 | 非运行资产，需标记为注释（§3.3） |
| 不可访问资产 | 需要凭据/环境才能触发的运行期行为 | 记为 `GAP-XXX`（§4） |
| 无关 MasterData 逻辑 | 与 `SubtableType` 无调用或数据关系的其他 Controller/功能 | 试点范围约束 |

### 3.3 注释代码与废弃模块

- 注释掉的代码（如 `VendorTypeAutoJob`）记为 `ASSUMPTION` 或 `GAP`，不作为 `FACT` 资产，除非有证据证明其在其他 revision 生效。

## 4. 不可扫描资产与缺口编号（GAP-XXX）

| 编号 | 资产/能力 | 原因 | 补证方式 |
|---|---|---|---|
| GAP-001 | 运行期路由表（ASP.NET MVC 约定路由 vs attribute route） | MCP Route 节点多数为空，无法从图直接获得完整路由映射 | 用 Roslyn/源码读取 `[HttpGet]`/`[HttpPost]` + Controller/Action 约定重建路由清单；人工确认 |
| GAP-002 | 运行时生成的控件/动态绑定（`gridwidget.cshtml` 等） | 静态解析无法确定字段来源 | 结合 ViewModel 元数据 + 人工补证 |
| GAP-003 | 存储过程 / 动态 SQL | 建库脚本未发现显式存储过程；需确认是否全 ORM | 读取 Repository/SQL 调用证据；若存在动态拼接标记 MIXED/HIGH |
| GAP-004 | 生产数据库对象清单（表、列、索引、权限） | 本机无生产库只读元数据访问 | 通过 Database MCP 只读视图（受治理）或 DBA 提供元数据 |
| GAP-005 | Job 实际调度触发（生产环境） | 调度配置在运行期/环境中 | 读取 `JobScheduler`/配置 + 运维确认 |

## 5. 验证记录

- 清单覆盖源码（Controller/Filter/BLL/SQL/表）、数据库（DbModels/Entity）、Job（AutoJob/Worker）和 UI（Views/JS）四个资产域，每项均绑定固定 revision `ce9ad5ca`。
- 每个排除项均有规则和理由，无“暂不处理”式说明。
- 缺失资产均可通过 `GAP-001`–`GAP-005` 定位到原因和补证方式。
- 命令：`git diff --check` 应通过。
