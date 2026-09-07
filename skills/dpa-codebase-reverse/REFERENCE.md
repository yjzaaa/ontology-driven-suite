# dpa-codebase-reverse REFERENCE

本文件是 DPA 专用逆向 Skill 的唯一细节层。SKILL.md 只引用本文件；本文件引用本项目 `docs/meta-model/` 契约与上游 `D:\sharptoolbox\codebase-reverse\references\` 方法。

## 1. 输入参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `repo` | 是 | DPA 仓库路径（默认 `D:\WorkSpace`） |
| `revision` | 是 | 固定 git revision（如 `ce9ad5ca`） |
| `scope` | 是 | `F-FULL`（业务+技术全集）/ `F-REQ`（技术无关需求规格）/ `full-baseline`（全量基线）/ `incremental`（增量重扫） |
| `anchor` | 条件 | 试点锚点（如 `MasterDataPROnlineApprovalController` / `SubtableType`） |
| `out` | 是 | 输出目录（默认 `evidence/snapshots/<revision>/`） |

## 2. 阶段与产出

| 阶段 | 动作 | 产出 | 责任 |
|---|---|---|---|
| 1 资产盘点 | 登记资产清单（T02.1） | `docs/meta-model/reverse-engineering-asset-inventory.md` | 平台工程 |
| 2 证据提取 | MCP 主引擎 + Roslyn 补证 | 证据记录（T02.2 信封） | 平台工程 |
| 3 规范化 | FACT/INFERENCE/ASSUMPTION + 稳定 ID | `evidence/*.json` | Evidence Adapter |
| 4 快照/覆盖率 | manifest + 分层覆盖率 | `evidence/snapshots/<revision>/` | Evidence Adapter |
| 5 人工门禁 | 高风险路由到审核队列 | `review-item` | DPA 技术负责人/领域/安全 |
| 6 候选输出 | 仅 `.build/candidates/` | 候选 YAML | 平台工程 + LLM |

## 3. 证据与覆盖率规则

- 证据契约：`docs/meta-model/evidence-contract.md`；Schema：`schemas/evidence/evidence-record.schema.json`。
- 快照与覆盖率：`docs/meta-model/evidence-snapshot-and-coverage.md`；manifest Schema：`schemas/evidence/snapshot-manifest.schema.json`。
- 增量失效：`docs/meta-model/incremental-evidence-invalidation.md`。
- 覆盖率分层计算，四域五层，不允许单一百分比掩盖缺口。

## 4. 上游规则映射（Java → ASP.NET MVC）

| 上游（codebase-reverse） | DPA 映射 |
|---|---|
| Controller/Service/DAO | ASP.NET MVC Controller / `YiSha.Business` Dll/Service / `YiSha.Data` Repository |
| MyBatis/XML SQL | EF (`Repository.Insert/Update`) + Dapper (`ExecuteAsync`/`QuerySingleOrDefault`) + 内嵌 SQL |
| Spring 权限/Filter | `AuthorizeFilterAttribute` + `[HttpGet]/[HttpPost]` 特性 + `BaseController` |
| 菜单/页面 | `Areas/**/Views/*.cshtml` + `@Url.Action` 绑定 |
| Job/事件 | `AutoJob`（`JobScheduler/JobCenter`）+ `IJobTask` + `Worker` |
| 证据分级 | FACT/INFERENCE/ASSUMPTION（`codebase-reverse/references/evidence-protocol.md`） |

## 5. 调用链与补证

- 首选 codebase-memory MCP：`trace_path`/`get_code_snippet`/`search_graph`（见 `docs/meta-model/codebase-memory-extraction.md`）。
- MCP 缺口（Route、动态分派、副作用）由定向 Roslyn extractor 补证（`docs/meta-model/roslyn-gap-extractors.md`），必须有最小 fixture 证明。
- 每步记录 extractor 版本与查询模板版本。

## 6. 人工门禁与失败规则

- 高风险（动态 SQL/反射/UI 动态绑定/混合副作用/权限不明）路由到人工审核，不自动升级为事实（T02.8）。
- 配置缺失、模型引用无效、证据不足：尽早失败，不跳过、不猜测、不用空结果伪装成功。
- 错误保留稳定错误码、关联 ID 和可操作消息。

## 7. 示例提示词

- 全量基线：`dpa-codebase-reverse repo=D:\WorkSpace revision=<rev> scope=full-baseline out=evidence/snapshots/<rev>/`
- 单功能全集：`... scope=F-FULL anchor=MasterDataPROnlineApprovalController ...`
- 技术无关需求：`... scope=F-REQ anchor=UpdateSubtableData ...`
- 增量重扫：`... scope=incremental from=<rev1> to=<rev2> ...`

## 8. 验证

- 静态校验：`scripts/validate-dpa-reverse.ps1`。
- 端到端 fixture：见 `EXAMPLES.md`。
- 输出确定性：相同输入重复执行产生稳定证据 ID。
