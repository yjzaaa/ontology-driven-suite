# 证据快照、覆盖率与质量门槛（T02.6 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.6 产出。
> 任务：规定证据快照的目录、清单、完整性校验和分层覆盖率，确保扫描结果可比较且不会用单一百分比掩盖缺口。
> 前置：T02.3–T02.5。

## 1. 快照目录与清单

- 快照目录：`evidence/snapshots/<revision>/`。
- 快照内容：`evidence/*.json` 证据记录、`manifest.json`、覆盖率报告、资产清单（T02.1）、调用链（T02.3）、数据库/Job（T02.4）、UI 绑定（T02.5）。
- 清单字段：

```json
{
  "snapshot_id": "snap-<revision>-<generatorVersion>-<configHash>",
  "source_revision": "ce9ad5ca",
  "generator_version": "adapter@1.0.0",
  "config_digest": "<sha256>",
  "files": [ { "path": "...", "sha256": "..." } ],
  "created_at": "..."
}
```

- 完整性校验：按清单逐文件校验 `sha256`，发现缺失或替换即快照无效（阻断）。

## 2. 分层覆盖率

覆盖率按五层分别计算，不合并成单一百分比：

| 层 | 分子 | 分母 |
|---|---|---|
| 资产发现 | 已发现的资产数 | 资产清单（T02.1）应发现资产数 |
| 符号解析 | 已解析到符号的证据 | 涉及符号的资产数 |
| 关系解析 | 已建立调用/绑定/读写关系的资产 | 存在潜在关系的资产数 |
| 证据定位 | 有 `path+line_range` 定位的证据 | 全部证据数 |
| 人工审核 | 已审核的证据数 | 需审核的证据数（高风险/动态/UNKNOWN） |

## 3. 资产域覆盖率

按 Controller、数据库、Job、UI 四域分别给分子/分母：

- Controller：试点可达 Action / `MasterDataPROnlineApprovalController` 全部 Action（37 个）。
- 数据库：`SubtableType` 可达表/读写关系 / T02.4 识别的关系集。
- Job：`SubtableType` 可达 Job / AutoJob 全部 Job。
- UI：`SubtableType` 可达页面/绑定 / MasterData 试点 Views。
- 不可扫描项（GAP-001~005）进入对应分母或提供书面排除依据。

## 4. 快照状态判定

| 状态 | 条件 |
|---|---|
| 可接受 | 完整性校验通过；四域覆盖率 ≥ 阈值（试点定 80%，未达时给出书面排除） |
| 降级 | 完整性通过但某域覆盖率低于阈值，且有 GAP 与补证计划 |
| 阻断 | 清单校验失败、存在悬空派生证据、或 `MIXED/HIGH` 关系被声明为可自动执行 |

## 5. MasterData 覆盖率样例

- 见 `evidence/examples/masterdata-coverage-report.json`：分别展示四域和五层覆盖率，不只给总百分比。
- 所有 `GAP-XXX` 进入对应覆盖率分母或附带书面排除依据。

## 6. 验证记录

- 快照样例可通过 `schemas/evidence/snapshot-manifest.schema.json` 校验，且文件摘要能发现缺失或被替换的证据文件。
- 覆盖率报告能分别显示四个资产域和五个覆盖层级，不只给出总百分比。
- 所有 `GAP-XXX` 均进入对应覆盖率分母或有书面排除依据。
- 命令：`git diff --check` 应通过。
