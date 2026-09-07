# 行为、接口、规则与执行边界（T01.4 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.4 产出。
> 任务：建立 endpoint、M2 Behavior、M3 Rule、validation、Action Proposal、Draft Application 和实际执行之间的分层关系及判定规则。
> MasterData 示例仅使用 `SubtableType` 可达证据。
> 源码证据来自 DPA 仓库 `D:\WorkSpace`，分支 `SSME.DPA.DEV`，revision `ce9ad5ca`。

## 1. 概念分层

| 层 | 概念 | 表达 | 执行能力 | 是否 Agent 可见 |
|---|---|---|---|---|
| 技术接口 | DPA Endpoint（Controller Action） | HTTP 调用、参数绑定、路由 | 是（DPA 侧） | 否（URL/Method/Header 不进入模型，归 MI 技术侧） |
| 业务语义 | M2 Behavior | 业务结果能力 | 否（需经提案） | 是（语义 Tool） |
| 业务约束 | M3 Rule | 判断/派生 | 否 | 是（语义） |
| 输入校验 | validation | 参数合法性检查 | 否 | 视情况（区分业务/技术） |
| 授权检查 | Authorization | 谁能做什么 | 否 | 预检，不替代 DPA |
| 行为请求 | Action Proposal | 不可变行为请求 | 否（待审批） | 是 |
| 草稿应用 | Draft Application | 应用建议值到原表单，不持久化 | 否（不写库） | 是 |
| 实际执行 | Execution | 批准后的持久化/副作用 | 是（经 Gateway→DPA） | 审计可见 |

## 2. 源码证据基线（FACT）

| 事实 | 证据位置（revision `ce9ad5ca`） |
|---|---|
| Controller 存在大量 `[HttpGet]` 查询端点（`GetSubtableDatalist`、`GetSubtableViewModel`、`GetListJson`、`GetOperatorLog` 等） | `MasterDataPROnlineApprovalController.cs` |
| `UpdateSubtableData` 为 `[HttpPost]`，调用 `MasterDataPROnlineApprovalDll.UpdateSubtableData`，随后 `dll.clearSubtableCache()` 与 `new HrEmployeeInfoCache().Remove()` —— 写操作伴随两处缓存清理（混合副作用） | `MasterDataPROnlineApprovalController.cs:655-663` |
| `UpdateSubtableDataList` 同理，为批量写 + 缓存清理 | 同文件 665-671 |
| `SaveMutiEditData` 为 `[HttpPost]` 批量编辑保存 | 同文件 546-547 |
| `DirectOverwriteSubtableDataFromExcel` 为 `[HttpPost]` 批量覆盖导入（`MasterDataExcelOverwriteParam`） | 同文件 451-452 |
| `MutiEditDataLog` 为 `[HttpPost]`，入参 `List<UpdateMasterdataPROnlineApprovalDto>` | 同文件 470 |
| Controller 中出现 `DuplicateValidatorInfo` 字典（重复性校验器信息）与 `VarifyLists` | 同文件 124、138 |
| `SaveEditByBatchIdsToSession` 为 `[HttpPost]`，把批量编辑 ID 写入 Session | 同文件 522-523 |
| 存在 Job 型入口 `RefreshEntertainmentAutoJob`、注释掉的 `VendorTypeAutoJob` | 同文件 464、710 |
| `CreateTestDataList` 为 `[HttpGet]`，疑似测试数据生成（需确认是否只读，见风险） | 同文件 418-419 |

## 3. 判定规则

### 3.1 endpoint 与 M2 的映射

- 一个 endpoint **可映射多个行为**：如 `Index` 端点同时生成页面、判断下载 URL、序列化禁用列表（`MasterDataPROnlineApprovalController.cs:144-180`），其业务结果需按子表类型拆分行为。
- 多个 endpoint 可实现同一行为：`UpdateSubtableData` 与 `UpdateSubtableDataList` 都表达“更新子表数据”（单个/批量），业务上可能是同一 M2 行为。
- **endpoint 不因可调用就自动判定为 M2**：`[HttpGet]` 查询端点必须先判断是否纯读（工作包 05/06 判定），无法证明纯读的按 `MIXED/HIGH` 处理。

### 3.2 validation 与 M3 的边界

- `DuplicateValidatorInfo`、`VarifyLists` 出现在 Controller，但它们是否属于**可复用业务约束**（M3）取决于：是否跨行为复用、是否承载业务不变量。页面级/字段级输入检查不自动升级为 M3（TERM-007）。
- M3 Rule 只判断或派生，不直接执行写操作（`AGENTS.md`）。

### 3.3 Action Proposal、审批、Draft 与执行责任分界

- **Action Proposal**：针对已验证参数提出的不可变行为请求，绑定风险、影响、本体版本、MI 版本（`CONTEXT.md`）。写操作默认只生成提案（`AGENTS.md`）。
- **Draft Application**：把建议值应用到原 DPA 表单但不持久化；用户仍需执行原 DPA 保存动作。
- **Execution**：仅在 HITL 批准后，由 Gateway 经 DPA 执行；`UpdateSubtableData` 这类 DPA 写端点只能由 Execution 阶段（DPA HTTP 或受治理执行）触发，Agent 不直接调用。
- 平台侧“执行”（Policy→Proposal→Approval→Execution 状态机）与 DPA 侧“执行”（实际持久化）是两层，不能混用（TERM-017）。

## 4. MasterData 判定案例

### 案例 1：纯查询（读）

- 证据：`GetSubtableDatalist(string subtableType)` 为 `[HttpGet]`，返回子表数据列表。
- 判定：业务结果 = 查询/统计 → 主模型 **M7 Query**（若可证明纯读）；endpoint 技术细节归 MI。
- 责任：M7 定义语义；MU 投影结果；DPA 提供数据事实。无提案、无执行。

### 案例 2：草稿填充（读→写提案）

- 证据：`GetSubtableViewModel` 返回表单字段与视图模型，用户编辑后提交。
- 判定：读取端为 M7 Query + MU 展示；写端（`SaveMutiEditData`/`UpdateSubtableData`）为 **M2 Behavior**。
- 责任：编辑操作生成 Draft Application 应用建议值；用户在原 DPA 表单确认保存；平台默认不自动持久化。

### 案例 3：保存（写 + 缓存副作用 = MIXED）

- 证据：`UpdateSubtableData` 写库 + `clearSubtableCache()` + `HrEmployeeInfoCache().Remove()`。
- 判定：单一 endpoint 同时产生持久化写与缓存清理副作用 → **MIXED/HIGH**，不得自动执行。
- 责任：M2 表达“更新子表数据”业务结果；M3 判断允许条件（如禁止更新列表）；M5 约束权限；执行必须经 Proposal→Approval→Execution。
- 反例：把 `UpdateSubtableData` 当作纯写行为自动执行，会绕过 HITL 且未处理缓存副作用。

### 案例 4：混合副作用（Job / 批量覆盖）

- 证据：`DirectOverwriteSubtableDataFromExcel`（批量覆盖导入）、`RefreshEntertainmentAutoJob`（Job）。
- 判定：覆盖导入与 Job 触发可能影响大量行、含外部调用与缓存/通知副作用 → **MIXED/HIGH**，禁止自动执行。
- 责任：M2 表达导入/刷新行为；M6 Flow 表达 Job 编排；MI 描述技术目标、幂等、超时与错误映射（工作包 05）；执行需人工审批。
- 反例：把批量覆盖导入视为普通更新自动执行，风险不可接受。

## 5. 结论汇总

- **validation 不因出现在校验器中就自动判定为 M3 Rule**：需证明跨行为复用且承载业务不变量。
- **endpoint 不因可调用就自动判定为 M2 Behavior**：需先判定业务结果与纯读性。
- 无法证明纯读的案例明确归入 `MIXED/HIGH`，且不得自动执行。
- 每个案例均可分别标注 endpoint、M2、M3、提案、执行者和最终持久化责任（见第 4 节）。

## 6. 验证记录

- 四个案例均覆盖查询、草稿填充、保存和混合副作用四类。
- 每案例可区分 endpoint、M2、M3、提案、执行者、持久化责任。
- 证据位置、revision 已记录；正式 Evidence Snapshot 由工作包 02 固化。
- 命令：`git diff --check` 应通过。
