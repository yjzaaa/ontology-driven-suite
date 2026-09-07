# 证据记录契约与稳定标识（T02.2 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.2 产出。
> 任务：定义机器证据、推断和假设的统一信封、稳定 ID、定位信息及派生关系，使每条结论可追溯和可校验。
> 前置：T02.1 `reverse-engineering-asset-inventory.md`。

## 1. 证据等级（FACT / INFERENCE / ASSUMPTION）

| 等级 | 准入条件 | 禁止替代 |
|---|---|---|
| `FACT` | 直接由源码、配置、数据库元数据或已捕获行为证明，能给出仓库、revision、路径、符号、行范围 | 不得由 `INFERENCE`/`ASSUMPTION` 升级；不得用命名启发式替代 |
| `INFERENCE` | 由至少一个 `FACT` 通过明确规则推导（如调用边、数据流、分派结论），`derived_from` 必须可解析 | 不得直接当作 `FACT`；推导规则需可重复 |
| `ASSUMPTION` | 无直接证据但为推进分析而作的明确假设；必须标记为待验证 | 不得伪装为 `FACT` 或 `INFERENCE` |

## 2. 证据字段契约

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `evidence_id` | string | 是 | 稳定 ID，生成规则见 §3 |
| `kind` | enum | 是 | `FACT` / `INFERENCE` / `ASSUMPTION` |
| `source_repo` | string | 是 | 资产来源仓库（如 `D:\WorkSpace`） |
| `revision` | string | 是 | 固定 revision（如 `ce9ad5ca`） |
| `path` | string | 是 | 相对仓库根的文件路径 |
| `symbol` | string | 是 | 符号名（类/方法/字段/路由） |
| `line_range` | string | 是 | `start-end` 行范围 |
| `extractor` | string | 是 | 提取器标识（`codebase-memory` / `roslyn-<name>` / `db-metadata` / `manual` / `adapter` 版本） |
| `observed_at` | datetime | 是 | 观测时间 |
| `derived_from` | string[] | 条件 | `INFERENCE`/`ASSUMPTION` 必填 ≥1 个 `evidence_id` |
| `confidence` | number | 是 | 0–1 |
| `relation` | object | 否 | 跨资产关系（见 §4） |
| `tags` | string[] | 否 | 如 `read`、`write`、`mixed`、`dynamic`、`gap` |

## 3. 稳定 ID 生成规则

稳定 ID 必须满足：**相同 revision 的同一资产重复扫描产生相同 ID**；不得把绝对工作目录或扫描时间写入 ID。

| 资产类型 | 稳定 ID 规则 | 示例 |
|---|---|---|
| 源码符号 | `ev:{repo}:{revision}:{fileHashOrPath}:{symbol}` | `ev:WS:ce9ad5ca:YiSha.Web/.../MasterDataPROnlineApprovalController.cs:UpdateSubtableData` |
| 路由 | `route:{repo}:{revision}:{method}:{normalizedPath}` | `route:WS:ce9ad5ca:POST:/MasterData/...` |
| 数据库对象 | `db:{repo}:{revision}:{schema}.{table}[.{column}]` | `db:WS:ce9ad5ca:dbo.tb_Master_Data_PR_Online_Approval` |
| Job | `job:{repo}:{revision}:{jobName}` | `job:WS:ce9ad5ca:RefreshEntertainmentAutoJob` |
| UI 元素 | `ui:{repo}:{revision}:{pagePath}:{elementKey}` | `ui:WS:ce9ad5ca:.../Index.cshtml:subtable-grid` |
| 跨资产关系 | 由 `relation.from` 与 `relation.to` 的 ID 拼接 | — |
| 证据信封 | `evidence_id` 本身即上述规则产物 | — |

**路径规范化**：路径统一使用 `/` 分隔的相对路径，去除绝对工作目录前缀；文件移动但稳定符号未变时不制造新业务资产 ID（T02.7）。

## 4. 跨资产关系

`relation` 对象：

```json
{
  "from": "ev:...",
  "to": "db:...",
  "type": "READ" | "WRITE" | "CALLS" | "BINDS" | "TRIGGERS" | "DERIVES"
}
```

关系必须两端 ID 均可解析到同一快照或声明的外部快照，否则为悬空派生。

## 5. Schema 与样例

- Schema：`schemas/evidence/evidence-record.schema.json`（见本工作包产出）
- 样例：`evidence/examples/evidence-records.json`

## 6. 有效 / 缺字段 / 悬空派生 / revision 不一致样例判定

| 样例类型 | 判定 |
|---|---|
| 有效：`FACT` 且含全部必填字段、无 `derived_from` | 通过 |
| 有效：`INFERENCE` 且 `derived_from` 指向存在的 `evidence_id` | 通过 |
| 缺字段：缺 `symbol` 或 `line_range` | 拒绝 |
| 悬空派生：`derived_from` 指向不存在的 ID | 拒绝 |
| revision 不一致：`derived_from` 的 revision 与当前声明不符且未声明外部快照 | 拒绝 |

## 7. 验证记录

- 示例文件可通过 `schemas/evidence/evidence-record.schema.json` 校验。
- 每个 `INFERENCE` 和 `ASSUMPTION` 至少有一个 `derived_from`，且引用存在。
- 相同 revision 的同一资产重复扫描产生相同稳定 ID，不把绝对工作目录或扫描时间写入 ID。
- 命令：`git diff --check` 应通过。
