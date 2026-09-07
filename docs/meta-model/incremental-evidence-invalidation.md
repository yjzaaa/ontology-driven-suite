# 增量变更检测与失效传播（T02.7 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.7 产出。
> 任务：规定源代码或配置变更如何使证据、派生结论和候选模型失效，并限制增量重扫范围。
> 前置：T02.2、T02.6。

## 1. 资产变更判定规则

| 变更类型 | 判定 | 证据影响 |
|---|---|---|
| 新增 | 新增文件/符号/路由 | 新增证据；可能新增候选 |
| 修改 | 行级修改（diff 命中行范围） | 命中范围内证据失效，沿 `derived_from` 传播 |
| 删除 | 文件/符号删除 | 相关证据与派生结论失效 |
| 重命名 | 稳定符号未变（类/方法重命名但语义相同） | 不制造新业务资产 ID；更新定位 |
| 仅移动 | 文件移动，稳定符号未变 | 不制造新业务资产 ID；更新路径 |

## 2. 失效闭包计算

- 起点：被修改/删除资产对应的 `evidence_id`。
- 沿 `derived_from` 反向传播：所有 `INFERENCE`/`ASSUMPTION` 只要 `derived_from` 指向失效证据即失效。
- 沿调用/绑定关系传播：`CALLS`/`BINDS`/`TRIGGERS`/`READ`/`WRITE` 关系一端失效则关系待复核。
- 候选模型：引用失效证据的候选 YAML（`.build/candidates/`）进入 `REVIEW_REQUIRED`，不得发布。

## 3. 重扫范围判定

| 变更范围 | 重扫策略 |
|---|---|
| 单文件/单符号修改 | 局部重扫（仅该文件及其直接调用者/派生者） |
| 接口/基类/工厂分派变更 | 重建受影响 project 索引（分派面无法局部确定） |
| 数据库域变更（表/ORM/Repository） | 重建数据库域快照 |
| UI 域变更（Views/绑定） | 重建 UI 域快照 |
| 跨域传播（Job 写库） | 同时重建数据库域 + Job 域 |

## 4. 失效状态与报告

- 失效证据：状态 `INVALIDATED`，保留历史 ID 与失效原因。
- 待复核推断：状态 `REVIEW_REQUIRED`，列出受影响候选 YAML。
- 报告格式：`evidence/examples/masterdata-change-impact.json`（见样例）。

## 5. 实测样例（revision `ce9ad5ca` 相对 `HEAD~1`）

- 变更文件：`AssetStocktaingNewJob.cs`（修改）、`SyncFCTXT.cs`（修改）、`DLPReview/Index.cshtml`（修改）。
- 判定：`AssetStocktaingNewJob` 分支逻辑对调（`07-20` 与 `FullStampAdmin`/`SelfFullSampleCount` 交换）——该 Job 的副作用结论需重新抽取；若其访问 `SubtableType` 可达表则触发数据库域复核。
- 预期失效集合：该 Job 相关 `FACT`/`INFERENCE` 及其 `derived_from` 传播链、引用其副作用结论的候选模型。

## 6. 验证记录

- 对样例 revision 差异重复计算得到相同的新增、失效和重扫集合。
- 删除或语义修改上游证据时，所有派生 `INFERENCE`、`ASSUMPTION` 和候选模型均进入影响集合。
- 文件移动但稳定符号未变时不会无条件制造新的业务资产 ID。
- 命令：`git diff --check` 应通过。
