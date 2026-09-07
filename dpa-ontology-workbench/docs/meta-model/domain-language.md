# 统一领域词汇表（T01.6 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.6 产出。
> 任务：把 T01.1–T01.5 的裁决收敛为后续工作包可直接引用的规范词汇表，并为易混概念提供稳定判例。
> 词汇表是运行时与文档的规范术语源；`CONTEXT.md` 是跨上下文统一使用的权威词汇位置，本文件是词汇表的组织与裁决依据，T01.7 将把差异写回 `CONTEXT.md`。

## 1. 规范术语表

| 规范英文 | 保留英文 | 中文名 | 定义（一句话） | 非目标 | 允许近义词 | 状态 |
|---|---|---|---|---|---|---|
| Evidence | Evidence | 证据 | 从 DPA 源码/接口/UI/配置/数据库发现的事实、推断或假设，不授予执行权 | 不授予运行执行权；不等于最终业务事实 | 无（不鼓励“证据=事实”混用，TERM-018） | 已裁决 |
| Business Object | Business Object | 业务对象 | 具有业务身份、属性、生命周期和关系的领域概念 | 不等同于表、Entity、DTO、ViewModel | 无 | 已裁决 |
| Behavior | Behavior | 行为 | 针对业务对象或领域产生稳定业务结果的能力，与 endpoint 解耦 | 不承载 URL/Method/Header；不以 Controller/Action 名为规范名 | 无 | 已裁决 |
| Rule | Rule | 规则 | 可复用判断/派生约束，不直接执行状态修改 | 不等于页面级输入校验 validation | 校验（仅业务约束场景，TERM-007） | 已裁决 |
| Actor / Permission | Actor / Permission | 参与者/权限 | 角色与权限语义，约束谁在什么范围可做什么 | 不含用户身份值、Cookie/Token、DPA 过滤器实现 | 无 | 已裁决 |
| Flow | Flow | 流程 | 跨行为的业务/编排流程与状态转换 | 不等于用户路径(scenario)、不等于 DPA Workflow | 无（用户路径用“场景”，TERM-005） | 已裁决 |
| Query | Query | 查询 | 受治理查询及其结果形状，由 M7 表达 | 不等于任意 SQL、不等于 TanStack Query、不等于 DPA SQL | 无（TERM-004） | 已裁决 |
| Presentation | Presentation | 展示 | 展示契约、渲染选择与 Legacy View 入口，由 MU 表达 | 不承载业务规则/权限/执行；不复制复杂表单 | 表现、UI（仅在 MU 语境，TERM-009） | 已裁决 |
| Integration | Integration（MI） | 集成映射 | 防腐层集成契约，连接语义模型与 DPA 技术目标 | 不承载业务语义/Agent 可见参数/凭据/任意 SQL | 无（不再写作“MI 集成”，TERM-002） | 已裁决 |
| Action Proposal | Action Proposal | 行为提案 | 针对已验证参数提出的不可变行为请求，绑定风险/影响/本体版本/MI 版本 | 不等于 DPA Controller Action、不等于 Execution | 提案 | 已裁决 |
| Draft Application | Draft Application | 草稿应用 | 把已验证建议值应用到原 DPA 表单但不持久化 | 不等于 DPA 表单自身草稿；不持久化 | 草稿（需限定“平台草稿应用”，TERM-011） | 已裁决 |
| Runtime Projection | Runtime Projection | 运行时投影 | 由已发布本体生成的只读投影，非新事实源 | 不等于技术可重建视图、不等于 Runtime Workbench（TERM-006/015） | 投影（需限定语义投影） | 已裁决 |
| Legacy View | Legacy View | 遗留视图 | 为复杂编辑/工作流/页面专有行为保留的原 DPA 页面 | 不成为平台业务事实源；不复制复杂表单 | 原页面 | 已裁决 |
| Execution | Execution | 执行 | HITL 批准后经 Gateway→DPA 的实际业务执行及不可变收据 | 不等于 DPA Executor、不等于平台“执行”泛指（TERM-010/017） | 无 | 已裁决 |
| Renderer | Renderer | 渲染器 | 由已发布 Presentation 选择的受信任 UI 投影组件 | 不判断权限、不执行行为 | 无 | 已裁决 |
| IdentityContext | IdentityContext | 身份上下文 | 平台内部可消费、可审计且不携带原始凭据的当前用户表达 | 不含 Cookie/Token；不替代 DPA 授权（TERM-014） | 无 | 已裁决 |

## 2. 模型编号定稿

- 采用八类模型：**M1 Object、M2 Behavior、M3 Rule、M5 Actor/Permission、M6 Flow、M7 Query、MU Presentation、MI Integration**。
- 全称：MI = **Integration**（集成映射），不再使用“Integration Mapping”造成 “MI 集成” 冗余（TERM-002）。
- 不引入 M4（scenario）与 ME（event）：场景作为分析与验收工具，事件作为运行时协议（TERM-012）。
- 与参考源差异已记录（TERM-001/009），本项目以 `AGENTS.md`/`docs/wayfinder/map.md` 为准。

## 3. TERM 冲突项裁决状态

| 编号 | 主题 | 状态 |
|---|---|---|
| TERM-001 | 八类模型编号体系 | 已裁决（第 2 节） |
| TERM-002 | MI 命名冗余 | 已裁决（MI=Integration） |
| TERM-003 | Action 一词多义 | 已裁决（区分 DPA Action / M2 Behavior / Action Proposal） |
| TERM-004 | Query 一词多义 | 已裁决（M7=受治理查询） |
| TERM-005 | Flow 一词多义 | 已裁决（M6=流程，用户路径=场景） |
| TERM-006 | 投影一词多义 | 已裁决（语义投影） |
| TERM-007 | Rule 与 validation | 已裁决（业务约束才为 Rule） |
| TERM-008 | 授权 vs 审批 | 已裁决（Authorization vs Approval） |
| TERM-009 | MU 模型含义 | 已裁决（MU=Presentation） |
| TERM-010 | Execution 与 Executor | 已裁决（Execution=执行聚合） |
| TERM-011 | 平台草稿 vs DPA 草稿 | 已裁决（Draft Application） |
| TERM-012 | 缺 M4/ME | 已裁决（不引入） |
| TERM-013 | SubtableType 语义归属 | **阻塞（待工作包 02 证据）** |
| TERM-014 | Identity 命名 | 已裁决（IdentityContext=对象名） |
| TERM-015 | Workbench vs Projection | 已裁决（产品名 vs 语义投影） |
| TERM-016 | Candidate 与 DRAFT | 已裁决（候选区） |
| TERM-017 | 执行层混用 | 已裁决（平台执行 vs DPA 执行） |
| TERM-018 | 证据与事实 | 已裁决（Evidence=FACT/INFERENCE/ASSUMPTION 总称） |

唯一保留的阻塞项是 TERM-013（`SubtableType` 是否业务对象），依赖证据快照，与工作包 02 的边界一致。

## 4. 边界判例

边界判例独立保存于 [domain-boundary-cases.md](domain-boundary-cases.md)，共 12 个 `CASE-01`–`CASE-12`，每个含输入事实、适用规则、结论和不适用条件。本文件只登记判例索引：

| 编号 | 场景 | 结论 |
|---|---|---|
| CASE-01 | `SubtableType` 归属 | M1 候选（TERM-013） |
| CASE-02 | 单表多概念 | 物理表映射=DTO，非 M1 |
| CASE-03 | ViewModel 非对象 | 非 M1，归 MU |
| CASE-04 | 纯查询 | M7 Query |
| CASE-05 | 写+缓存副作用 | M2 + MIXED/HIGH |
| CASE-06 | 禁止更新列表 | M3 Rule |
| CASE-07 | 审批权限 | M5 |
| CASE-08 | 审批流程 | M6 Flow（待证据） |
| CASE-09 | Jedox 数据源 | M7 + MI |
| CASE-10 | 子表表单元数据 | MU Presentation |
| CASE-11 | 批量覆盖导入 | M2 + MIXED/HIGH |
| CASE-12 | 提案→草稿→DPA 保存 | Proposal→Draft→DPA 保存 |

## 5. 文档书写规则

- **首次出现**：跨文档首次使用核心概念时，以“中文名（英文名）”首次出现并链接到本文件对应条目。
- **交叉引用**：术语冲突时引用 `TERM-XXX`；判例引用 `CASE-XX`。
- **源码符号保留**：`SubtableType`、`MasterDataPROnlineApprovalController`、`UpdateSubtableData` 等源码符号保持原文，不翻译、不规范化（`docs/AGENTS.md`）。
- **编号稳定**：`TERM-XXX` 与 `CASE-XX` 编号稳定，新增不重排。

## 6. 验证记录

- `domain-language.md` 中不存在两个定义不同但使用同一规范名称的条目（第 1 节表内英文名唯一）。
- 每个判例有唯一编号、输入事实、适用规则、结论和不适用条件（第 4 节）。
- T01.1 中 18 个冲突项均链接到裁决或明确的阻塞原因（第 3 节）。
- 命令：`git diff --check` 应通过。
