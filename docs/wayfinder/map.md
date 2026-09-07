---
title: DPA 本体建模与运行工作台实施规格路线图
status: open
labels:
  - wayfinder:map
tracker: local-markdown
---

## 最终目的地

形成一套可直接进入研发实施的《DPA 本体建模与运行工作台技术规格》。规格以 `MasterDataPROnlineApprovalController` 中 `SubtableType` 相关可达逻辑为纵向切片，覆盖 DPA 反向工程、本体契约、MI 集成、身份与授权、受治理查询、人工审核执行、Agent 语义工具、前端投影、部署运维、测试验收和分阶段推广。

本路线图只完成分析、决策、契约、样例和低保真原型，不实现生产代码。完成后，交付团队不应再需要自行决定重大架构、安全、数据治理或产品边界。

## 工作方式

- `tickets/` 下的每个文件代表一个工作包，不是一个笼统问题。
- 每个工作包继续拆分为多个可执行 Task。
- 所有工作包和 Task 默认由当前 Copilot 主 Agent 按依赖顺序执行。
- 主 Agent 基于任务需要调用专业 Skill、codebase-memory MCP、文件与命令工具，并将无共享写入的独立子问题分派给并行子 Agent。
- 主 Agent 对子 Agent 结果承担整合与验收责任；人工参与仅用于无法由工具证明的业务裁决、安全接受和发布授权。
- 每个 Task 必须说明达成目标、输入、执行步骤、产出物和验证方式。
- Task 的完成以产出物通过验证为准，不以“已经讨论”或“已经写文档”为准。
- 工作包只有在全部必需 Task 完成且通过工作包验收后才能关闭。
- 被阻塞的工作包不得提前形成最终结论，但可以收集事实和准备输入材料。

## 已确认边界

- 目标系统是大型遗留 ASP.NET DPA，浏览器登录使用 Entra ID/OIDC，业务会话依赖自定义 `UserToken`，业务权限由 DPA 现有过滤器和业务层最终裁决。
- MasterData 试点严格遵循 [范围说明](masterdata-scope.md)：以 `SubtableType` 为追踪锚点，不反推整个 MasterData。
- 本项目自主实现独立 Agent Runtime 与 Agent UI；不依赖、不复用、不集成 InsightBot。
- 源码分析基线为 codebase-memory MCP 主引擎 + Python Evidence Adapter；C#/.NET + Roslyn 只补充经验证的 DPA 专有语义缺口，不预先建设完整扫描器。
- 其他技术语言基线为：Python + LangGraph + FastAPI/Pydantic 负责 Agent Runtime 与后端治理服务；TypeScript + React 负责独立 Agent UI、Studio 和 Explorer；YAML + JSON Schema 负责本体契约。
- 产品生成本体、运行时投影和 Agent 能力，不生成替代 DPA 的第二套完整 CRUD 系统。
- 所有持久化业务写入仍通过 DPA 原 HTTP/业务层路径；Database MCP 永远只读。
- 写入体验按风险与证据成熟度分级（2026-09-07 修订，机械路由与证据门槛见 WP07 T07.1）：未通过 MI 证明与三项证据门槛的写行为，体验为“生成草稿、校验草稿、在 Agent UI 审核、应用到原 DPA 表单、由用户使用原保存动作提交”（兜底路径）；通过门槛的简单写行为，目标默认体验为 Agent UI 内提案审批与 HITL 受控执行。
- 所有级别的业务落库均沿 DPA 原业务层路径；DPA 原授权器保留最终检查与授权，写入体验升级不改变落库路径与授权模型。
- `models/<domain>/` 下经审核发布的 YAML 是运行时语义唯一事实源。
- 反向工程报告、机器证据和候选 YAML 都是输入，不具有运行执行权。
- 无法证明纯读的接口按 `MIXED/HIGH` 风险处理，不允许自动执行。
- 模型只选择业务对象、查询和行为，不接触 URL、HTTP Method、凭据、Header、任意 SQL 或内部 DTO 映射。

## 工作包与依赖

| 工作包 | 名称 | 主要结果 | 前置工作包 |
|---|---|---|---|
| 01 | [统一领域语言与模型边界](tickets/01-define-domain-language-and-model-boundaries.md) | 统一词汇、模型职责矩阵、边界判定案例 | 无 |
| 02 | [定义 DPA 反向工程证据流水线](tickets/02-specify-reverse-engineering-evidence-pipeline.md) | 扫描范围、证据契约、覆盖率和增量变更规则 | 无 |
| 03 | [定义本体契约、校验与发布生命周期](tickets/03-define-ontology-contracts-and-lifecycle.md) | 八类模型 Schema、引用规则、版本和发布状态机 | 01、02 |
| 04 | [定义身份、会话转发与授权边界](tickets/04-define-identity-session-and-authorization.md) | 试点认证链路、长期目标、失败与安全边界 | 无 |
| 05 | [定义 MI 集成与副作用契约](tickets/05-define-mi-integration-contract.md) | 语义到技术执行的防腐层契约 | 03、04 |
| 06 | [定义受治理查询与数据范围](tickets/06-define-governed-query-and-data-scope.md) | 查询解析、行列权限、限制、审计和结果投影 | 03、04 |
| 07 | [定义 HITL 与行为执行语义](tickets/07-define-hitl-and-action-execution.md) | 提案、审批、执行状态机和安全执行规则 | 05、06 |
| 08 | [定义 Agent Tool 与运行时事件协议](tickets/08-define-agent-tool-and-runtime-protocol.md) | Agent 编排框架、稳定语义 Tool、事件、错误和上下文边界 | 03、06、07 |
| 09 | [定义产品界面与元数据驱动渲染](tickets/09-define-product-surfaces-and-rendering.md) | 产品导航、Renderer 契约、可视化技术选型和 Legacy View 边界 | 03、08 |
| 10 | [制作四条关键用户路径原型](tickets/10-prototype-four-critical-user-flows.md) | 可交互低保真原型和可用性结论 | 09 |
| 11 | [定义平台模块、仓库边界与部署](tickets/11-define-platform-modules-and-deployment.md) | 模块接口、平台技术选型、持久化责任、部署拓扑和运维责任 | 04、05、08 |
| 12 | [定义审计、可观测性与变更治理](tickets/12-define-audit-observability-and-change-governance.md) | 审计链、指标、脱敏、变更评审与阻断规则 | 02、03、05、07 |
| 13 | [定义 SubtableType 参考纵向切片](tickets/13-define-masterdata-reference-slice.md) | `SubtableType` 可达路径的一套模型、查询、行为和页面样例 | 03、05、06、07、09 |
| 14 | [定义验证与验收策略](tickets/14-define-verification-and-acceptance-strategy.md) | 自动化测试矩阵、人工验收和非功能门槛 | 07、10、11、12、13 |
| 15 | [组装可实施技术规格](tickets/15-assemble-implementation-ready-technical-specification.md) | 完整技术规格、实施批次、风险和追踪矩阵 | 10、11、12、13、14 |

## 当前可领取工作包

- [统一领域语言与模型边界](tickets/01-define-domain-language-and-model-boundaries.md)
- [定义 DPA 反向工程证据流水线](tickets/02-specify-reverse-engineering-evidence-pipeline.md)
- [定义身份、会话转发与授权边界](tickets/04-define-identity-session-and-authorization.md)

## 已完成决策

- [工作包 01 已关闭：采用 M1/M2/M3/M5/M6/M7/MU/MI 八类模型，MI=Integration，建立统一词汇与 12 个 MasterData 判例](tickets/01-define-domain-language-and-model-boundaries.md#解决记录)
- [工作包 02 已关闭：定义 DPA 反向工程证据流水线，codebase-memory 主引擎 + 定向 Roslyn 补证，封装 DPA codebase-reverse 包装 Skill](tickets/02-specify-reverse-engineering-evidence-pipeline.md#解决记录)
- [工作包 03 已关闭：定义八类本体模型 Schema、引用闭包、版本兼容与发布生命周期，MasterData 候选 YAML 样例落库](tickets/03-define-ontology-contracts-and-lifecycle.md#解决记录)

## 尚未明确

- MasterData 试点通过后，其他 DPA 领域按什么准入标准进入本体治理。
- 是否在 YAML 审核成熟后提供受控的图形化模型编辑。
- 同源会话转发试点之后，何时迁移到 delegated token 或 token exchange。
- DPA 之外的外部系统是否复用同一本体和行为契约。
- DPA 源码存在硬编码跨库三段名（`[shai472a].[SSME.DPAMS]`）：MasterData 域 3 个查询、2 个定时作业（含 INSERT）在测试环境仍访问生产库；子表表单字典加载路径受影响。需作为新证据项（跨库字面量扫描）承接——WP02 已关闭，待开新 Task 并入 WP05/WP07 证据门槛。
- 在证据质量和审核工作量可量化后，允许多大程度的自动本体推断。

## 不在本路线图范围内

- 在本路线图阶段实现生产平台。
- 在 MasterData 纵向切片验证前，反向建模全部 DPA 领域和全部 Controller。
- 替换 DPA 业务服务、工作流、授权过滤器或复杂表单。
- 向 Agent 暴露任意 DPA 接口、任意 SQL、DDL、DML 或数据库写入。
- 根据本体生成一套替代 DPA 的独立 CRUD 应用。

## 路线图完成判定

- 15 个工作包全部关闭，且每个必需 Task 均有可定位的产出物和验证记录。
- 所有跨工作包术语、稳定 ID、状态名和协议字段不存在冲突。
- MasterData 样例能从源代码证据追踪到本体、运行时投影、查询或行为，再追踪到验收场景。
- 技术规格中的每项关键结论都能链接到已关闭工作包或正式 ADR。
- 交付团队可以据此拆分开发迭代，而无需补做重大方案选择。
