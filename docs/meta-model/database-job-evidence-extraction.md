# 数据库与 Job 证据提取规范（T02.4 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.4 产出。
> 任务：定义 SQL、存储过程、表、数据库读写、调度 Job、重试和 callback 的提取与关联规则。
> 前置：T02.1、T02.2。MasterData 试点仅限 `SubtableType` 可达关系。

## 1. SQL / 存储过程 / 表 解析层级

| 层级 | 规则 | 证据等级 |
|---|---|---|
| 静态 SQL | 字面量 SQL（如 `insert into ... select`）可解析表/列 → 表级关系 `FACT` | FACT |
| 参数化 SQL | `DbParameter` 参数化 → 可解析表级，参数名记录 | FACT/INFERENCE |
| 存储过程调用 | `ExecuteByProc(procName)` → 若元数据支持细分表级则细分，否则保留过程级事实 | FACT（过程级） |
| 动态 SQL | 运行时拼接字符串、`$"{var}"` → 无法静态证明 → `MIXED/HIGH` + `GAP` | MIXED/HIGH |
| ORM/EF | `Insert<T>/Update<T>/FindList<T>` → 泛型实体映射表 | FACT（经实体映射） |

## 2. 源码证据基线（FACT，revision `ce9ad5ca`）

| 事实 | 证据位置 |
|---|---|
| `Repository` 提供 `BeginTrans/CommitTrans/RollbackTrans/ExecuteBySql/ExecuteByProc/Insert/Update/Delete/FindList` | `YiSha.Data/YiSha.Data.Repository/Repository.cs` |
| `MobileHaasJob`（`IJobTask`）使用 Dapper 原始 SQL 跨库写入：`shai472a.[SSME.DPAMS]`、`tb_mobile_HAAS_report`、`MasterData.dbo.tb_Master_Data_PR_Online_Approval` | `YiSha.Business/YiSha.Business.AutoJob/Job/MobileHaasJob.cs:55-76` |
| 该 Job 以 `select ... where dic_type=66` 读 `tb_Master_Data_PR_Online_Approval`（`SubtableType` 可达） | 同文件 62 |
| Job 读计数后分支选择 SQL2 或 SQL3 写入（条件写入） | 同文件 60-73 |
| `MasterDataPROnlineApproval` 映射表 `tb_Master_Data_PR_Online_Approval`，Jedox 表 `tb_Master_Data_PR_Online_Approval_jedox` | `YiSha.Entity/YiSha.Entity/MasterData/MasterDataPROnlineApproval.cs` |

## 3. 表 / 列 / 读写关系稳定 ID

- 表：`db:{repo}:{revision}:{schema}.{table}`
- 列：`db:{repo}:{revision}:{schema}.{table}.{column}`
- 读写关系：`READ` / `WRITE` / `MIXED` / `UNKNOWN`，见 §5 样例。

## 4. Job 调度与关联

- 调度定义：`AutoJob` 框架（`JobScheduler`/`JobCenter`）+ `IJobTask` 实现类。
- 关联：Job 代码入口 → 数据库访问 → 外部调用 → 重试（`is_runing` 防重入标志）→ callback。
- `MobileHaasJob` 的 `is_runing` 静态标志为防并发重入，不是幂等保证；写入无显式重试 → 记入 MI 幂等性评估。

## 5. 样例：masterdata-database-job-links.json

- 记录 `MobileHaasJob` 与 `tb_Master_Data_PR_Online_Approval` 的 `READ`（`where dic_type=66`）和跨库 `WRITE`（`insert into tb_mobile_HAAS_report`）。
- 每条关系标明 `READ/WRITE/MIXED/UNKNOWN`，并链接证据。
- 任一 `MIXED`、`UNKNOWN` 或动态 SQL 关系均不能被声明为可自动执行的纯读能力。

## 6. 无法证明只读的处理

- 动态拼接、跨事务副作用、Job 条件写入 → 标记 `MIXED/HIGH` 与人工审核要求（T02.8）。
- 不因证据存在而获得运行执行权（`AGENTS.md` 边界 6、7）。

## 7. 验证记录

- 样例中每条数据库关系均标明 `READ/WRITE/MIXED/UNKNOWN`，并链接到证据。
- 存储过程只在可解析语句或数据库元数据支持时细分表级关系，否则保留为存储过程级事实。
- 任一 `MIXED`、`UNKNOWN` 或动态 SQL 关系均不能被声明为可自动执行的纯读能力。
- 命令：`git diff --check` 应通过。
