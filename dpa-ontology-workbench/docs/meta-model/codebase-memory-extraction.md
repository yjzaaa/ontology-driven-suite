# codebase-memory 图谱提取规范（T02.3 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.3 产出。
> 任务：规定以 codebase-memory MCP 为主发现 Controller、route、过滤器、权限、业务调用、状态转换、callback 与副作用，并仅对验证后的能力缺口使用定向 Roslyn extractor。
> 前置：T02.1、T02.2。本文件基于对 `D-WorkSpace`（revision `ce9ad5ca`）的实际 MCP 查询实测。

## 1. 项目索引模式

- 索引目标：`D:\WorkSpace`，项目标识 `D-WorkSpace`。
- 已索引规模：36,702 节点 / 113,337 边；C# 1,755 文件、JS 479、CSS 438、HTML 331、SQL 3。
- 文件过滤：索引应排除 `obj/`、`bin/`、`wwwroot/lib/`、`wwwroot/jqwidgets*/`、`packages/` 第三方与生成产物；但当前索引仍包含大量 `wwwroot.jqwidgets`、`echarts`、`jquery.layout` 节点（见 §4 噪声，需在 Evidence Adapter 层过滤）。
- 索引新鲜度：每次扫描前检查 `source_repo` 的 `git rev-parse HEAD`，与快照 revision 不一致时重建索引或明确标注版本漂移。

## 2. 查询模板

### 2.1 从 Route/Controller 出发

- `search_graph(query="<Controller 或 Action 名>", project="D-WorkSpace")` 定位符号。
- `trace_path(function_name="<qualified_name>", direction="outbound", mode="calls", depth=3..4)` 展开调用边。
- `get_code_snippet(qualified_name=..., project=...)` 取源码片段核对行号与副作用。

### 2.2 调用边 / 数据流展开边界

- 试点锚点（`MasterDataPROnlineApprovalController.UpdateSubtableData`）outbound 展开深度默认 3，最大 4（避免跨入第三方 JS 无限扩散）。
- 数据流使用 `mode="data_flow"` 按参数名（如 `entityJson`、`DicType`、`subtableType`）追踪，确认 `SubtableType` 分派路径。
- 权限/身份：关注 `DataRepository.GetUserByToken`、`CookieHelper.GetCookie`、`SessionHelper.GetSession`、`Operator.Current`（身份上下文）。

### 2.3 噪声过滤规则

- 排除 `wwwroot/*`、`jqwidgets`、`echarts`、`jquery.*`、`layui`、`semantic-ui` 等第三方前端库节点（实测出现在调用链中，属误报）。
- 排除与试点无 `SubtableType` 可达关系的其他业务域调用（如 `FormController.Select`——经核对与 MasterData 无业务关系，判定为跨 Controller 误匹配）。
- 排除生成代码（`*.Designer.cs`、`bin/obj` 产物）。

## 3. 实测调用链（revision `ce9ad5ca`）

从 `MasterDataPROnlineApprovalController.UpdateSubtableData`（`YiSha.Web/.../MasterDataPROnlineApprovalController.cs:655`）展开：

```text
Controller.UpdateSubtableData (write + 缓存清理，MIXED)
 └─ MasterDataPROnlineApprovalDll.UpdateSubtableData  [YiSha.Business/MasterData]
     ├─ ISubtableDataHandler.ValidateFunc                 [校验]
     ├─ MasterDataPROnlineApprovalDll.GetUpdateMasterdataPROnlineApprovalDto
     ├─ MasterDataPROnlineApprovalService.SetMasterDataPROnlineApproval  [业务服务]
     ├─ MasterDataPROnlineApprovalDll.LogUpdate            [变更日志]
     ├─ MasterDataPROnlineApprovalService.SaveOperateLog   [操作日志]
     ├─ Repository.Insert / Repository.Update              [写库，YiSha.Data]
     └─ MemoryCacheImp.SetCache + clearSubtableCache       [缓存副作用]
 └─ 身份：DataRepository.GetUserByToken / CookieHelper.GetCookie / SessionHelper.GetSession
```

**判定**：该链包含写库（`Repository.Insert/Update`）、操作日志、缓存清理三重副作用 → `MIXED/HIGH`，不得自动执行（与 T01.4 CASE-05 一致）。该样例同时证明 MCP 可发现权限/身份/副作用关键节点。

## 4. 抽样准确率检查（实测）

| 项 | 结果 | 说明 |
|---|---|---|
| 误报边 | 高 | `echarts`、`jqwidgets`、`jquery.layout` 第三方 JS 被并入调用链 |
| 跨域误匹配 | 有 | `FormController.Select` 出现在 Dll 调用链（与 MasterData 无关） |
| 漏报/截断 | 有 | 深度 4 截断；ASP.NET MVC 路由节点多数为空（Route 76 个几乎全空） |
| 副作用识别 | 中 | 依赖名称启发式（`Insert/Update/SetCache`）识别写与缓存；动态分派需人工 |

**结论**：codebase-memory 擅长符号/调用链/数据流发现，但存在（a）Route 识别缺口、（b）第三方前端噪声、（c）动态分派/副作用判定缺口。前两者在 Adapter 层可部分过滤；Route 与动态分派需定向 Roslyn 补证（见 gap-analysis 与 roslyn-gap-extractors）。

## 5. 提取结果到证据格式的转换

- 每个 MCP 节点/边转换为 `evidence-record.schema.json` 信封（T02.2）。
- 直接命中的源码符号 → `FACT`（`extractor=codebase-memory`）。
- 由调用边推导的“副作用/权限/分派”结论 → `INFERENCE`（`derived_from` 指向源符号 FACT）。
- 无法解析的分派/动态调用 → `ASSUMPTION` 或 `GAP-XXX`，不得伪装为 `FACT`。
- 记录查询参数、分页完整性、截断（`has_more`）和覆盖率分母。

## 6. 验证记录

- 对选定 MasterData 入口重复运行提取时，节点、边和稳定 ID 顺序无关且内容一致（MCP 返回稳定 qualified_name 与 file_path/行号）。
- 样例调用链可从 Controller 追溯到权限（`GetUserByToken`）、业务服务（`SetMasterDataPROnlineApproval`）及已发现的副作用（写库/日志/缓存）。
- 对 codebase-memory 输出中的 Route 和调用边进行抽样准确率检查，误报、漏报和截断已记录（§4）。
- 未达到覆盖门槛的能力（Route、动态分派、副作用判定）必须有 Roslyn 补证 fixture；达到门槛的能力不得重复开发 extractor。
- 命令：`git diff --check` 应通过。
