# dpa-codebase-reverse EXAMPLES

DPA 专用逆向 Skill 的示例提示词与最小端到端 fixture 说明。

## 1. 示例提示词

### 全量基线

```
dpa-codebase-reverse repo=D:\WorkSpace revision=ce9ad5ca scope=full-baseline out=evidence/snapshots/ce9ad5ca/
```

预期：资产清单、功能穿透、证据记录、快照 manifest、分层覆盖率。

### 单功能全集（F-FULL）

```
dpa-codebase-reverse repo=D:\WorkSpace revision=ce9ad5ca scope=F-FULL anchor=MasterDataPROnlineApprovalController out=evidence/snapshots/ce9ad5ca/
```

预期：从 Controller 到数据库/Job/UI 绑定的完整调用链（如 `UpdateSubtableData` → Repository → 缓存），含副作用分级。

### 技术无关需求（F-REQ）

```
dpa-codebase-reverse repo=D:\WorkSpace revision=ce9ad5ca scope=F-REQ anchor=SubtableType out=evidence/snapshots/ce9ad5ca/
```

预期：`SubtableType` 相关业务需求规格，技术实现无关，含数据库对象模型与溯源。

### 增量重扫

```
dpa-codebase-reverse repo=D:\WorkSpace revision=ce9ad5ca scope=incremental from=391d82d5 to=ce9ad5ca out=evidence/snapshots/ce9ad5ca/
```

预期：失效闭包、重扫范围、影响候选 YAML 列表。

## 2. 最小 ASP.NET MVC fixture（端到端验证）

fixture 内容（`tests/fixtures/dpa-reverse-minimal/`）：

- `Controllers/SubtableController.cs`：含 `[HttpGet]` 查询 Action + `[HttpPost]` 写 Action。
- `Filters/AuthorizeFilterAttribute.cs`：授权过滤器。
- `Business/SubtableService.cs`：调用 `Repository.Insert/Update` + 缓存。
- `Data/Repository.cs`：`Insert/Update/FindList`。
- `Views/Subtable/Index.cshtml`：`@Url.Action("GetList")` 绑定。

执行：

```
dpa-codebase-reverse repo=tests/fixtures/dpa-reverse-minimal revision=f1 scope=full-baseline out=evidence/snapshots/f1/
scripts/validate-dpa-reverse.ps1 -SnapshotDir evidence/snapshots/f1/
```

预期输出同时包含：源码资产清单、调用链、数据库访问、权限（Filter）、证据等级（FACT/INFERENCE/ASSUMPTION）。

## 3. 确定性

- 相同输入重复执行产生稳定证据 ID（不把绝对工作目录或扫描时间写入 ID）。
- 输出按符号/文件字典序排序。
- LLM 推断只进入候选或审核队列，不写入 `evidence/snapshots/` 事实记录。

## 4. 失败示例（应被拒绝）

- 尝试用 Java/Spring 规则解释 ASP.NET MVC 路由。
- 把 LLM 对 SQL 的猜测写成 `FACT`。
- 直接发布本体或调用 DPA 写接口。
