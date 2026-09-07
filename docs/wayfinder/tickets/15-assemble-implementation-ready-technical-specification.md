---
title: 组装可实施技术规格
status: open
labels:
  - wayfinder:task
parent: ../map.md
assignee:
blocked_by:
  - 10-prototype-four-critical-user-flows.md
  - 11-define-platform-modules-and-deployment.md
  - 12-define-audit-observability-and-change-governance.md
  - 13-define-masterdata-reference-slice.md
  - 14-define-verification-and-acceptance-strategy.md
---

## 工作包目标

把已关闭工作包、正式 ADR、MasterData 参考切片和验证基线组装成一套单一、连贯、可追踪的《DPA 本体建模与运行工作台技术规格》。规格必须让交付团队能够直接拆分实施迭代，而无需重新决定重大架构、安全、数据治理、产品、部署或协议问题。

本工作包只整合已解决结论、消除冲突并暴露开放项，不以编写总文档为名重新发明架构。所有规范性结论必须指向权威来源；重复表述必须明确哪一处是规范正文、哪一处只是摘要。

## 必需 Task

### [ ] T15.1 建立规格目录与来源清单

**达成目标**

确定技术规格的章节结构、规范性来源、引用规则和缺口状态，防止遗漏已确认结论或把未决内容写成正式要求。

**输入**

- `README.md` 与 `docs/wayfinder/map.md`。
- 工作包 01 至 14 的最终产出、解决记录和正式 ADR。
- 工作包 13 的参考切片 manifest。
- 工作包 14 的需求测试矩阵和最终门禁。

**执行步骤**

1. 建立章节目录，至少覆盖目标边界、领域模型、证据流水线、运行时、安全、产品、协议、部署、运维、样例、实施、验证、风险和开放项。
2. 为每章指定权威工作包、ADR、模型或协议来源，并记录版本或基线。
3. 标记来源冲突、缺失、过期和重复结论；为每项指定责任人和处理方式。
4. 定义稳定 ID、术语、图表、代码样例和跨文档链接的编写约定。
5. 生成来源完整性检查，确保每个已关闭工作包至少被规范正文引用一次。

**产出物**

- `docs/specification/README.md`
- `docs/specification/source-catalog.yaml`
- `docs/specification/traceability/source-to-section.csv`
- `tools/validation/check-specification-sources.*`

**验证方式**

- 运行来源完整性检查，退出码必须为 0。
- 01 至 14 每个工作包均映射到至少一个规格章节；明确不进入正文的产出必须写明理由。
- 所有冲突均已解决或进入有责任人与期限的开放项，不得静默择一。

### [ ] T15.2 编写领域模型与治理规格

**前置 Task**

- T15.1

**达成目标**

形成关于统一语言、八类模型、证据、稳定 ID、引用、版本、发布、变更治理和影响分析的完整规范。

**输入**

- 工作包 01、02、03、12 的最终结论。
- 工作包 13 的 M1/M2/M3/M5/M7/MU/MI 参考样例。

**执行步骤**

1. 编写领域边界与统一术语，明确 DPA、独立 Agent Runtime、Agent UI、本体平台和 Database MCP 的职责。
2. 描述证据生成、候选模型、人工评审、发布和废弃的生命周期。
3. 对 M1/M2/M3/M5/M6/M7/MU/MI 分别列出职责、必填字段、禁止字段、引用方向和最小示例。
4. 定义稳定 ID、版本兼容、不可变发布、回滚、证据漂移和 `REVIEW_REQUIRED`。
5. 链接 MasterData 样例而非在正文复制多份可能漂移的 YAML。

**产出物**

- `docs/specification/01-domain-and-model-governance.md`
- `docs/specification/diagrams/model-lifecycle.*`
- `docs/specification/diagrams/model-reference-graph.*`

**验证方式**

- 运行术语、稳定 ID 和链接检查，退出码必须为 0。
- 八类模型均有职责、边界、引用与生命周期说明。
- 随机抽取规格中的模型结论，均能追踪到工作包、ADR 或已验证样例。

### [ ] T15.3 编写运行时、安全与集成规格

**前置 Task**

- T15.1

**达成目标**

把身份、会话、Registry、Policy、M7 查询、MI、防腐层、HITL、执行、Agent Tool、事件、审计和失败策略整合为无矛盾的运行时契约。

**输入**

- 工作包 04 至 08、11、12、14 的最终结论。
- 工作包 13 的查询、草稿应用和条件性简单命令样例。

**执行步骤**

1. 描述浏览器 Entra ID/OIDC、自定义 `UserToken`、Gateway 和 DPA 最终授权的信任边界。
2. 编写查询解析、行列权限、限制、结果投影、Database MCP 只读和 `MIXED/HIGH` 默认拒绝规则。
3. 编写 Action Proposal、审批令牌、草稿应用、简单命令、幂等、超时、重试和不确定结果处理。
4. 固化 Agent Tool、运行时事件、错误码、版本协商和 correlation ID 契约。
5. 加入威胁模型、审计链、脱敏、可观测性和依赖故障时的默认拒绝或降级行为。
6. 检查模型永远不能选择 URL、HTTP Method、凭据、Header、任意 SQL 或内部 DTO 映射。

**产出物**

- `docs/specification/02-runtime-security-and-integration.md`
- `docs/specification/contracts/semantic-tool-api.yaml`
- `docs/specification/contracts/runtime-events.yaml`
- `docs/specification/contracts/error-catalog.yaml`
- `docs/specification/diagrams/runtime-sequences.*`
- `docs/specification/diagrams/trust-boundaries.*`

**验证方式**

- 对协议样例执行 Schema 和兼容性检查，退出码必须为 0。
- 使用工作包 14 的固定场景核对查询、草稿应用和简单命令序列，事件与错误码一致。
- 安全审阅确认不存在绕过 DPA 最终授权、Database MCP 写入或任意技术目标选择。

### [ ] T15.4 编写产品、部署、运维与参考样例规格

**前置 Task**

- T15.2
- T15.3

**达成目标**

说明用户如何使用工作台、各模块如何部署和运维，并用 MasterData 样例证明模型、运行时与界面可以共同落地。

**输入**

- 工作包 09、10、11、12、13 的最终产出。
- 工作包 14 的 Agent/UI、性能和恢复验收结果。

**执行步骤**

1. 编写 Agent UI、Ontology Explorer、受信任 Renderer 和 Legacy View 的职责与导航关系。
2. 纳入四条关键用户路径，明确每一步的用户、Tool、模型、事件、权限和失败反馈。
3. 描述仓库模块、持久化责任、进程边界、部署拓扑、配置、密钥、网络、容量与环境差异。
4. 明确监控、告警、审计保留、备份恢复、模型发布、回滚和事故响应责任。
5. 建立 MasterData 样例入口页，链接证据、模型、查询、行为、界面、追踪矩阵与验收结果。
6. 提供最小本地或集成环境部署样例，所有占位值必须显式标记，不包含真实凭据。

**产出物**

- `docs/specification/03-product-deployment-and-operations.md`
- `docs/specification/examples/masterdata-reference-slice.md`
- `docs/specification/examples/deployment/`
- `docs/specification/diagrams/deployment-topology.*`
- `docs/specification/diagrams/user-journeys.*`

**验证方式**

- 从样例入口可到达工作包 13 manifest 中的全部必需产出，链接检查退出码为 0。
- 部署样例通过已有的配置或结构校验，且敏感信息扫描无发现。
- 产品、平台、DPA、独立 Agent Runtime、Agent UI 和运维责任不存在无人负责或重复最终裁决。

### [ ] T15.5 制定分阶段实施计划

**前置 Task**

- T15.2
- T15.3
- T15.4

**达成目标**

将规格拆分为可交付、可验证、可回滚的实施阶段，每个阶段都形成纵向能力而非只建设长期不可用的技术层。

**输入**

- 规格前三章。
- 工作包 11 的模块与部署边界。
- 工作包 14 的测试分层和门禁。

**执行步骤**

1. 定义阶段 0 的仓库、Schema、CI、测试和环境基线。
2. 定义证据与模型治理、只读查询、Agent/UI 投影、草稿应用、条件性简单命令的递进阶段。
3. 为每阶段列出目标、范围、前置依赖、接口、数据迁移、演示路径、测试门禁、回滚点和完成定义。
4. 明确哪些阶段禁止开启写执行，以及开启简单命令前必须满足的安全和运维条件。
5. 将阶段拆分建议映射到模块、责任团队和粗粒度工作量，不给出未经团队校准的虚假精确日期。

**产出物**

- `docs/specification/04-staged-implementation-plan.md`
- `docs/specification/traceability/phase-capability-matrix.csv`

**验证方式**

- 每个阶段都能在不依赖未来未交付能力的情况下演示和验收。
- 每项规格能力只在一个明确阶段首次交付，并有对应测试门禁。
- 任一阶段失败均有回滚或停止扩展方案，不要求回退 DPA 生产数据。

### [ ] T15.6 汇总风险、验收标准与开放项

**前置 Task**

- T15.5

**达成目标**

将剩余风险、可接受例外、跨阶段验收和真正未决事项集中管理，避免开放项散落在正文并被误认为已解决。

**输入**

- 工作包 01 至 14 的解决记录和遗留项。
- 工作包 14 的最终门禁、风险例外和性能恢复结果。
- T15.1 发现的来源冲突与缺口。

**执行步骤**

1. 汇总架构、安全、身份、数据治理、证据质量、产品可用性、性能、运维和组织责任风险。
2. 为每项风险记录概率、影响、触发信号、缓解措施、补偿控制、责任人和复审时间。
3. 将验收标准按总体、阶段和 MasterData 参考切片分层，并链接到测试 ID。
4. 将开放项分为“实施前必须关闭”“阶段门禁前关闭”“可延期探索”，明确决策人和期限。
5. 检查开放项不包含路线图要求本应已经解决的重大架构或安全决策；发现此类项目时回退相应工作包。

**产出物**

- `docs/specification/05-risks-acceptance-and-open-items.md`
- `docs/specification/traceability/risk-register.csv`
- `docs/specification/traceability/acceptance-criteria.csv`

**验证方式**

- 每项高风险均有责任人、缓解措施和可观察触发信号。
- 每条验收标准至少映射一个工作包 14 的测试 ID。
- “实施前必须关闭”的开放项数量为 0，或规格不得标记为可实施。

### [ ] T15.7 执行全规格一致性与可追踪性检查

**前置 Task**

- T15.6

**达成目标**

证明整套规格在术语、稳定 ID、协议字段、状态机、安全边界、图表、样例、实施阶段和验收标准之间不存在断链或冲突。

**输入**

- T15.1 至 T15.6 的全部规格文件。
- 工作包 13 的追踪矩阵。
- 工作包 14 的需求测试矩阵与最终门禁。

**执行步骤**

1. 合并“来源→章节→稳定 ID/协议→阶段→测试→验收”的总追踪矩阵。
2. 运行链接、术语、稳定 ID、协议 Schema、引用、敏感信息和来源完整性检查。
3. 人工比较正文、图表和样例中的状态名、错误码、风险级别与责任边界。
4. 查找重复规范、相互矛盾的默认值和没有权威来源的要求。
5. 修复全部阻断与重要问题，保存最终检查报告和规格 manifest。

**产出物**

- `docs/specification/traceability/end-to-end-matrix.csv`
- `docs/specification/specification-manifest.yaml`
- `docs/specification/validation/specification-validation.md`
- `tools/validation/check-complete-specification.*`

**验证方式**

- 完整规格检查退出码必须为 0。
- 从任一高风险需求出发，能追踪到来源、规范章节、实施阶段、测试和验收证据。
- manifest 中的文件、版本和摘要与实际内容一致，且不存在未关闭的阻断或重要问题。

### [ ] T15.8 执行独立读者测试并冻结交付基线

**前置 Task**

- T15.7

**达成目标**

由未参与前述方案制定的读者验证规格是否足以实施，并在修复理解缺口后冻结正式交付基线。

**输入**

- 完整技术规格与 specification manifest。
- 代表性交付角色：后端、前端、平台、安全、测试、运维和 DPA 业务维护者。
- 工作包 14 的最终验收门禁。

**执行步骤**

1. 为每类读者准备不附带口头背景的任务脚本，例如定位接口、实现查询、处理权限失败、部署环境和编写测试。
2. 要求读者仅使用规格回答问题并列出需要自行做出的重大决策、歧义、矛盾和缺失输入。
3. 将反馈分类为阻断、重要、编辑性；阻断和重要问题必须修复并重新测试。
4. 在干净环境运行工作包 14 的最终门禁和 T15.7 的完整规格检查。
5. 记录基线版本、manifest 摘要、签署人、开放项和变更控制规则。

**产出物**

- `docs/specification/validation/independent-reader-test.md`
- `docs/specification/validation/final-delivery-record.md`
- 更新后的 `docs/specification/specification-manifest.yaml`

**验证方式**

- 每类代表性读者均完成至少一个任务脚本并留下结果。
- 独立读者不需要自行决定重大架构、安全、数据治理、产品或协议问题。
- 阻断和重要问题为 0；完整规格检查与最终验收门禁退出码均为 0。
- manifest 摘要固定，后续任何规范性变更都必须走正式变更评审。

## 工作包验收

- 技术规格目录完整，01 至 14 的所有权威结论均有明确来源和规范落点。
- 领域模型治理、运行时安全集成、产品界面、部署运维、MasterData 样例和分阶段实施均可直接执行。
- API、事件、错误、持久化责任、状态机、稳定 ID 和图表不存在冲突。
- 所有高风险需求可追踪到实施阶段、测试 ID 和验收证据。
- “实施前必须关闭”的开放项为 0，剩余风险均有责任人、补偿控制和复审条件。
- 独立读者测试证明交付团队无需补做重大方案选择。
- 完整规格检查和工作包 14 最终门禁均通过，交付基线已冻结。

## 解决记录

工作包关闭时填写，至少包含：

- 技术规格基线版本、manifest 路径与摘要。
- 规范章节、图表、协议、样例、实施计划和追踪矩阵的最终链接。
- 完整规格检查与最终验收门禁的命令、环境和结果。
- 独立读者角色、任务、发现问题和修复结果。
- 最终风险、延期开放项、责任人和复审时间。
- 各责任域签署及后续变更控制入口。
