# Roslyn 补证 extractor 边界（T02.3 条件产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.3 条件产出。
> 前提：仅当 fixture 证明 codebase-memory MCP 存在确定性缺口时才开发。本文件为三个缺口定义 extractor 的最小契约，不实现生产扫描器。

## 1. roslyn-controller-route（GAP-001 路由）

- **目标**：重建 ASP.NET MVC 路由映射（HTTP Method + 约定/attribute 路由）。
- **输入**：`YiSha.Web/YiSha.Admin.Web/Areas/**/Controllers/*.cs`、`Startup.cs` 路由配置。
- **逻辑**：读取 Controller 类与 Action 上的 `[HttpGet]/[HttpPost]/[HttpPut]/[HttpDelete]/[Route]` attribute；无 attribute 时按 `{area}/{controller}/{action}/{id?}` 约定路由。
- **输出**：`route:{repo}:{revision}:{method}:{normalizedPath}` 证据，`extractor=roslyn-controller-route`。
- **fixture**：最小 MVC Controller 含 2 个 attribute 路由 + 1 个约定路由 Action。
- **确定性**：输出按 Controller/Action 字典序排序；同一 revision 重复运行字节稳定。

## 2. roslyn-subtable-dispatch（GAP-002 动态分派）

- **目标**：解析 `SubtableType` 到具体 `ISubtableHandler`/ViewModel 实现的工厂分派。
- **输入**：`SubtableHandlerFactory`、`SubtableDataHandler`、`SubtableType` 枚举。
- **逻辑**：语义模型解析 `switch/字典/工厂` 到实现类的绑定；无法静态解析的分支标记 `ASSUMPTION`/`GAP`。
- **输出**：分派关系 `INFERENCE`（`derived_from` 指向工厂与枚举 FACT），映射 `SubtableType` → 实现类 → 对应表/行为。
- **fixture**：`SubtableHandlerFactory` 最小副本（`Standard_Goods`/`Depth_Structure` 两个分支）。
- **确定性**：稳定 ID 不依赖扫描顺序。

## 3. roslyn-side-effect（GAP-003 副作用/读写分类）

- **目标**：判定数据访问调用为 `READ/WRITE/MIXED`，识别缓存、日志等副作用。
- **输入**：业务方法调用 `Repository.Insert/Update/Delete/GetById`、`DbContext.*`、`MemoryCache*`、`SaveOperateLog` 等。
- **逻辑**：基于语义模型识别数据访问 API 的读写语义；同一方法含写 + 缓存/日志 → `MIXED`；无法证明纯读 → `MIXED/HIGH`。
- **输出**：为证据记录附加 `tags: read|write|mixed`，`extractor=roslyn-side-effect`。
- **fixture**：写 + 缓存清理 + 日志的最小方法（对齐 `UpdateSubtableData`）。
- **确定性**：结论可重复，不依赖运行顺序。

## 4. 通用约束

- extractor 只读，不加载或执行 DPA 业务代码。
- 每条推断区分 `FACT`/`INFERENCE`/`ASSUMPTION`，携带文件、行号、符号、extractor 版本（`AGENTS.md` C#/Roslyn 纪律）。
- 输出转换为 `evidence-record.schema.json` 信封（T02.2），不直接生成候选 YAML。

## 5. 验证记录

- 三个 extractor 均有最小 fixture、明确输入、逻辑、输出格式与确定性要求。
- 未达到覆盖门槛的能力有 Roslyn 补证；达到门槛的不重复开发（见 gap-analysis）。
- 命令：`git diff --check` 应通过。
