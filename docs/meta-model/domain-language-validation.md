# 跨文档术语一致性检查记录（T01.7 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.7 产出。
> 任务：验证统一词汇（[domain-language.md](domain-language.md)）能够覆盖路线图现有文本，并生成后续工作包可重复执行的术语一致性检查记录。
> 检查范围：`README.md`、`CONTEXT.md`、`CONTEXT-MAP.md`、`AGENTS.md`、`docs/wayfinder/**/*.md`、`docs/meta-model/*.md`。

## 1. 可重复执行的检查命令

以下命令可重复执行（在仓库根目录）：

```powershell
# 1) 规范英文名是否唯一（不应出现同名异义）
rg -n "^\| (Evidence|Business Object|Behavior|Rule|Actor|Flow|Query|Presentation|Integration|Action Proposal|Draft Application|Runtime Projection|Legacy View|Execution|Renderer|IdentityContext) \|" docs/meta-model/domain-language.md

# 2) 旧全称/冗余写法是否仍出现在非本工作包文档
rg -n "Integration Mapping" CONTEXT.md README.md docs
rg -n "MI 集成" docs/wayfinder/map.md docs/wayfinder/tickets/05-define-mi-integration-contract.md

# 3) 冲突编号是否可定位
rg -o "TERM-[0-9]{3}" docs/meta-model/domain-term-inventory.md | sort -u

# 4) 判例编号是否可定位
rg -o "CASE-[0-9]{2}" docs/meta-model/domain-boundary-cases.md | sort -u
```

## 2. 检查结果（差异判定）

| 位置 | 现文本 | 规范要求 | 判定 |
|---|---|---|---|
| `CONTEXT.md:35` | `## Integration Mapping` | `Integration（MI）`，全称不再使用 “Integration Mapping”（TERM-002） | **真实冲突 → 本工作包修订**（T01.7 已写回，见第 4 节） |
| `docs/wayfinder/map.md:11,51` | “MI 集成” | 规范为 “MI（集成映射）”，避免 “MI 集成” 冗余 | **待后续工作包修订**（责任：工作包 05 或文档维护） |
| `docs/wayfinder/tickets/05-...md:title` | “定义 MI 集成与副作用契约” | 同上 | **待后续工作包修订**（责任：工作包 05） |
| `docs/wayfinder/masterdata-scope.md:20` | “…规则、呈现和 MI 候选” | “呈现”为允许近义词（MU 语境），无需修订 | 允许的近义词 |
| `docs/meta-model/*.md`（本工作包产出） | 使用规范名称 | 一致 | 已符合 |
| 源码符号（`SubtableType`、`MasterDataPROnlineApprovalController`、`UpdateSubtableData` 等） | 保持原文 | 保持原文（`docs/AGENTS.md`） | 允许的源码名称 |

未发现 `表现模型`、`呈现模型` 等同义异名冲突（第 2 次搜索为空）；未发现 M4/ME 被当作本体模型使用。

## 3. 五个未参与词汇编写的 MasterData 场景试跑

以下场景来自 DPA 源码（`D:\WorkSpace`，revision `ce9ad5ca`），未使用判例 CASE-01~12，用于试跑边界判定：

| 场景 | 源码事实 | 判定过程 | 唯一主模型 | 运行时责任边界 |
|---|---|---|---|---|
| 场景 A：`CopyItem(RecordId, DicType)` | Controller 复制项端点 | 产生新业务结果的写操作，非查询 | M2 Behavior | 复制须生成 Proposal，经 HITL 后执行；M3 判断可复制条件 |
| 场景 B：`SaveEditByBatchIdsToSession` | 把批量编辑 ID 写入 Session | 会话副作用，非持久化写；不产生业务状态变更 | 非本体模型（会话内临时对象） | Draft Application 范畴；不持久化，用户仍需原 DPA 保存 |
| 场景 C：`ExportMasterDataToJson` | `[HttpGet]` 导出数据为 JSON | 查询/导出，候选纯读 | M7 Query（待证明纯读） | 受治理导出，受数据范围/行数/复杂度限制 |
| 场景 D：`GetOperatorLog` | 操作日志查询 | 只读查询 | M7 Query | 审计视图投影，只读 |
| 场景 E：`RefreshData(subtableType)` | 刷新数据（含 Job/缓存嫌疑） | 可能含写与外部调用，无法证明纯读 | M2 + `MIXED/HIGH`（禁止自动执行） | 需人工审核，M6 若涉编排；MI 记录副作用 |

**结果**：五个场景均能得到唯一主模型类型和明确的运行时责任边界，且与 `model-boundary-matrix.md` 判定树一致，无矛盾结论。

## 4. 写回 CONTEXT.md 的差异

T01.6 裁决 MI 全称 = **Integration**（集成映射），不再使用 “Integration Mapping”。本工作包按“词汇权威位置唯一”原则，已将 `CONTEXT.md` 第 35 行标题由 `Integration Mapping` 更新为 `Integration（MI）`，定义正文保留“简称 MI”说明。变更内容见 git diff。

## 5. 遗留项及责任工作包

| 遗留项 | 责任工作包 | 说明 |
|---|---|---|
| `docs/wayfinder/map.md` 与 `tickets/05` 中 “MI 集成” 冗余写法 | 工作包 05（关闭时修订） | 本工作包不修改其他工作包标题；工作包 05 关闭或文档维护时统一为规范写法 |
| `SubtableType` 是否业务对象（TERM-013） | 工作包 02（证据快照） | 阻塞项，非术语冲突 |
| 技术库名（TanStack Query）与 M7 Query 的文档区分 | 工作包 06/09 | 书写时以 “TanStack Query” 全名避免歧义 |

## 6. 验证记录

- 检查记录包含可重复执行的 `rg` 命令（第 1 节）和逐项结果（第 2 节）。
- 五个试跑场景均得到唯一主模型类型和明确的运行时责任边界（第 3 节）。
- 无遗留未编号、无责任工作包的术语冲突（第 5 节：所有遗留项均绑定责任工作包）。
- 命令：`git diff --check` 应通过。

## 7. 执行过的检查命令与输出摘要

```text
$ rg -n "Integration Mapping" CONTEXT.md          → CONTEXT.md:35（已修订）
$ rg -n "MI 集成" docs/wayfinder/map.md            → 第 11、51 行（遗留项，工作包 05）
$ rg -n "\bM4\b|\bME\b" docs/wayfinder/map.md …    → 无（无 M4/ME 当作模型）
$ rg -n "表现模型|呈现模型|展示模型" docs CONTEXT.md → 无（无同义异名冲突）
$ git diff --check                                 → 通过
```
