# codebase-memory 能力缺口分析（T02.3 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.3 产出。
> 任务：基于实测，量化 codebase-memory MCP 对 DPA ASP.NET MVC 语义的识别覆盖，判定哪些缺口需要定向 Roslyn extractor。

## 1. 能力对照（基于 `D-WorkSpace` revision `ce9ad5ca` 实测）

| 能力 | MCP 现状 | 门槛 | 判定 |
|---|---|---|---|
| Controller/Action 定位 | 命中（`MasterDataPROnlineApprovalController` 全部 Action） | 通过 | ✅ 不需补证 |
| 调用边/数据流 | 命中（Dll→Service→Repository→Cache） | 通过 | ✅ 不需补证 |
| 权限/身份节点 | 命中（`GetUserByToken`、`CookieHelper`） | 通过（需抽查） | ✅ 不需补证 |
| 跨文件/跨域关系 | 命中但含误报（`FormController.Select`） | 需过滤 | ⚠️ Adapter 层过滤 |
| ASP.NET MVC 路由映射 | **失败**（Route 76 个几乎全空） | 未通过 | ❌ 需 Roslyn 补证 |
| 动态分派（Factory/接口分派） | 仅部分（`ISubtableHandler` 接口可见，具体实例需核对） | 未通过 | ❌ 需 Roslyn 补证 |
| 副作用/读写分类 | 依赖名称启发式（`Insert/Update/SetCache`），无法证明 | 未通过 | ❌ 需 Roslyn/人工补证 |
| 第三方前端噪声过滤 | 不识别（echarts/jqwidgets 混入） | 未通过 | ⚠️ Adapter 层过滤 |

## 2. 必须补证的缺口（fixture 门禁）

### 2.1 路由映射（GAP-001）

- 现象：MCP Route 节点多数为空，无法从图获得完整 `[HttpGet]/[HttpPost]` + 约定路由映射。
- 补证：Roslyn extractor 读取 Controller 上的 `[Route]`/HTTP Method attribute + Action 名，重建路由清单；用最小 ASP.NET MVC fixture 验证。
- 产出格式：转换为 `route:...` 稳定 ID 证据。

### 2.2 动态分派（GAP-002）

- 现象：`MasterDataPROnlineApprovalDll.UpdateSubtableData` 经 `ISubtableDataHandler` 接口分派，MCP 能见接口方法但无法静态证明具体实现类。
- 补证：Roslyn extractor 解析 `SubtableHandlerFactory`/`SubtableDataHandler` 的分派逻辑，标注具体实现类与对应 `SubtableType`。
- 结果：分派结论为 `INFERENCE`；无法解析的记为 `ASSUMPTION`/`GAP`。

### 2.3 副作用与读写分类（GAP-003）

- 现象：`Repository.Insert/Update`、`MemoryCacheImp.SetCache` 由名称启发式识别；无法证明是否纯读、是否跨事务。
- 补证：Roslyn extractor 分析数据访问调用上下文，判定 `READ/WRITE/MIXED`；无法证明的标记 `MIXED/HIGH`。
- 结果：与 T02.4 数据库证据、人工审核边界衔接。

## 3. 达到门槛、禁止重复开发

- Controller 定位、调用边、数据流、权限/身份节点已达到门槛，**不得**重复开发 Roslyn 全量扫描器。
- 只允许为 §2 三个缺口开发窄范围 extractor，且必须有最小 C# fixture 证明 MCP 确实无法完成（`AGENTS.md` 测试纪律）。

## 4. 缺口与对应 extractor 映射

| 缺口 | Roslyn extractor | fixture | 输出证据 |
|---|---|---|---|
| GAP-001 路由 | `roslyn-controller-route` | 最小 ASP.NET MVC Controller（含 `[HttpGet]/[HttpPost]`） | `route:*` 证据 |
| GAP-002 分派 | `roslyn-subtable-dispatch` | `SubtableHandlerFactory` 最小 fixture | 分派 `INFERENCE` |
| GAP-003 副作用 | `roslyn-side-effect` | 写+缓存+日志混合 fixture | `READ/WRITE/MIXED` 标签 |

## 5. 验证记录

- 每个缺口有实测现象、补证方式、最小 fixture 和输出证据格式。
- 达到门槛的能力不重复开发 extractor（§3）。
- 动态/未解析调用在样例中具有显式 `GAP`/`ASSUMPTION`，不存在无证据补全的调用边。
- 命令：`git diff --check` 应通过。
