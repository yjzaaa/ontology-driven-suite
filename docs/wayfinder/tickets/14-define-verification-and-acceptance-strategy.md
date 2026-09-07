---
title: 定义验证与验收策略
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 07-define-hitl-and-action-execution.md
  - 10-prototype-four-critical-user-flows.md
  - 11-define-platform-modules-and-deployment.md
  - 12-define-audit-observability-and-change-governance.md
  - 13-define-masterdata-reference-slice.md
---

## 工作包目标

建立覆盖证据生成、模型发布、身份与查询治理、HITL 与执行、Agent/UI、审计安全、性能恢复的分层验证体系，并把工作包 13 的 MasterData 参考切片转化为可自动执行、可人工复核、可阻断发布的验收基线。

策略必须明确每项需求由什么测试证明、使用什么固定输入、在什么环境运行、输出保存到哪里、失败由谁处理。最终门禁不得以“主要流程可用”代替负向、安全、恢复和追踪检查。

## 必需 Task

### [ ] T14.1 建立需求追踪与测试分层基线

**达成目标**

把路线图、已关闭工作包、ADR 和 MasterData 参考切片中的规范性要求映射到唯一测试项，形成后续所有测试的共同编号与覆盖率口径。

**输入**

- `docs/wayfinder/map.md`。
- 工作包 01 至 13 的最终产出、ADR 和解决记录。
- 工作包 13 的 `reference-slice-manifest.yaml` 与追踪矩阵。

**执行步骤**

1. 提取使用“必须、不得、仅允许、失败时”等措辞的规范性要求并分配稳定需求 ID。
2. 按单元、契约、集成、端到端、安全、性能恢复、人工验收进行测试分层。
3. 为每个需求记录测试 ID、测试层、执行环境、fixture、预期结果、责任人和证据路径。
4. 标记无法自动化的要求并定义人工检查表、双人复核和保留证据。
5. 编写覆盖率检查规则：所有高风险要求必须至少有一个正向和一个负向测试。

**产出物**

- `docs/specification/verification/requirements-test-matrix.csv`
- `docs/specification/verification/test-levels-and-environments.md`
- `docs/specification/verification/manual-checklists.md`
- `tools/validation/check-requirements-coverage.*`

**验证方式**

- 运行需求覆盖检查，退出码必须为 0。
- 随机抽取至少 20 个需求，均能定位到来源、测试和证据路径。
- 所有安全、授权、写入和模型发布要求均包含负向测试。

### [ ] T14.2 定义扫描与证据测试

**前置 Task**

- T14.1

**达成目标**

证明 Scanner 对声明范围内的 DPA 源码能稳定发现目标符号、生成合规证据、报告覆盖缺口，并在源码变化后触发增量重扫与评审。

**输入**

- 工作包 02 的扫描范围、证据 Schema、覆盖率和增量规则。
- 工作包 12 的源码变更信号和 `REVIEW_REQUIRED` 规则。
- 工作包 13 的参考对象证据包。

**执行步骤**

1. 建立包含 Controller、Action、DTO、业务服务、权限过滤器、视图和混合副作用端点的黄金样本。
2. 定义发现率、错误关联、重复证据、来源定位和敏感信息泄漏测试。
3. 定义证据 Schema、哈希、来源版本和置信度字段的契约测试。
4. 通过增加、删除、重命名和改变副作用四类受控变更验证增量扫描。
5. 验证证据漂移会标记受影响模型并阻止其继续作为可执行基线。

**产出物**

- `tests/fixtures/scanner/masterdata-golden-set/`
- `tests/scanner/scanner-evidence-cases.*`
- `docs/specification/verification/scanner-acceptance.md`
- `docs/specification/verification/results/scanner-baseline.txt`

**验证方式**

- 使用工作包 02 指定的测试命令执行黄金样本，退出码必须为 0。
- 声明必须达到的发现率和误报上限，并在基线结果中给出实际值。
- 四类增量变更均产生预期差异；副作用改变必须触发 `REVIEW_REQUIRED`。

### [ ] T14.3 定义模型 Registry 与发布生命周期测试

**前置 Task**

- T14.1

**达成目标**

验证 M1/M2/M3/M5/M6/M7/MU/MI 的 Schema、引用闭包、版本兼容、不可变发布和 Registry 加载行为，确保候选证据或未发布 YAML 永远不能获得运行执行权。

**输入**

- 工作包 03 的模型契约与发布状态机。
- 工作包 11 的 Registry 模块和持久化边界。
- 工作包 13 的已验证模型样例。

**执行步骤**

1. 为每类模型建立最小有效、字段缺失、未知字段、类型错误和禁止字段 fixture。
2. 建立悬空引用、循环引用、重复稳定 ID、跨版本不兼容和证据缺失测试。
3. 验证候选、评审中、已发布、已废弃和 `REVIEW_REQUIRED` 状态的加载权限。
4. 验证已发布版本不可原地修改，回滚只能切换到已存在且合规的不可变版本。
5. 验证 Registry 启动失败、缓存过期和模型集合不完整时默认拒绝服务。

**产出物**

- `tests/fixtures/models/`
- `tests/registry/model-contract-cases.*`
- `tests/registry/publication-lifecycle-cases.*`
- `docs/specification/verification/results/registry-baseline.txt`

**验证方式**

- 运行全部模型与 Registry 契约测试，退出码必须为 0。
- 对每类无效 fixture，断言明确且稳定的错误码。
- 尝试加载候选证据、未发布 YAML 和被标记 `REVIEW_REQUIRED` 的模型必须失败。

### [ ] T14.4 定义身份、受治理查询与数据范围测试

**前置 Task**

- T14.1

**达成目标**

证明身份上下文不可伪造，DPA 最终授权不被替代，M7 查询持续执行用户行范围、字段敏感性、限制、超时和导出策略。

**输入**

- 工作包 04 的 Entra ID/OIDC、`UserToken`、会话转发和失败边界。
- 工作包 06 的查询解析、行列权限和结果投影规则。
- 工作包 13 的 M5、M7、MU 与查询测试向量。

**执行步骤**

1. 建立有效会话、过期会话、缺失会话、用户不一致、权限变化和重放场景。
2. 对每个 M7 查询覆盖允许行、越权行、允许字段、敏感字段、分页上限、超时和禁止导出。
3. 验证模型只能选择业务对象与查询，不能传入 URL、HTTP Method、Header、凭据、任意 SQL 或内部 DTO 映射。
4. 对 DPA API 与 Database MCP 两条读取路径执行同一语义结果和策略一致性测试。
5. 验证 Database MCP 只读，无法证明纯读的接口按 `MIXED/HIGH` 拒绝自动查询。

**产出物**

- `tests/identity/session-forwarding-cases.*`
- `tests/query/governed-query-cases.*`
- `tests/query/data-scope-vectors.json`
- `docs/specification/verification/results/identity-query-baseline.txt`

**验证方式**

- 使用固定身份与数据 fixture 重放全部场景，结果必须确定且退出码为 0。
- 越权行和未授权字段不得出现在结果、日志或错误详情中。
- 伪造上下文、任意 SQL 和 `MIXED/HIGH` 自动读取请求必须被稳定错误码拒绝并产生审计事件。

### [ ] T14.5 定义 HITL、草稿应用与执行测试

**前置 Task**

- T14.1

**达成目标**

验证 Action Proposal 状态机、审批令牌、草稿应用、条件性简单命令、幂等、并发和失败处理，确保任何持久化业务写入仍由 DPA 原路径最终裁决。

**输入**

- 工作包 05 的 MI 与副作用契约。
- 工作包 07 的 HITL 和执行状态机。
- 工作包 13 的草稿应用及简单命令评估样例。

**执行步骤**

1. 为每个合法状态迁移建立正向测试，为越级、回退、重复消费和过期建立负向测试。
2. 验证审批令牌绑定用户、提案、模型版本、风险级别、到期时间和单次消费声明。
3. 重放草稿应用 fixture，验证只写入白名单表单字段、不自动保存、允许用户修改或取消。
4. 若参考切片准入简单命令，测试权限变化、超时、重试、幂等冲突、并发执行和 DPA 错误归一化。
5. 验证所有执行结果生成不可变回执；失败和不确定结果不得伪装为成功。

**产出物**

- `tests/hitl/action-proposal-state-cases.*`
- `tests/hitl/draft-application-cases.*`
- 条件产出：`tests/execution/simple-command-cases.*`
- `docs/specification/verification/results/hitl-execution-baseline.txt`

**验证方式**

- 状态转移表的每条允许边和禁止边至少被执行一次。
- 同一幂等键并发提交只允许一个有效执行结果。
- 自动保存、绕过审批、重复消费和过期令牌场景必须失败并产生可关联审计记录。

### [ ] T14.6 定义 Agent Tool、运行时事件与界面验收

**前置 Task**

- T14.1

**达成目标**

验证独立 Agent Runtime 只使用稳定语义 Tool，运行时事件顺序与错误契约可被自研 Agent UI 消费，元数据驱动界面正确呈现权限、风险、来源与草稿状态。

**输入**

- 工作包 08 的 Tool、事件、错误和上下文协议。
- 工作包 09 的产品界面与 Renderer 契约。
- 工作包 10 的四条关键用户路径原型及可用性结论。
- 工作包 13 的 M7、MU、M2 与场景。

**执行步骤**

1. 为 Tool 请求/响应、版本协商、未知稳定 ID、超时、取消和错误归一化建立契约测试。
2. 验证模型输出无法选择技术端点、凭据、Header 或任意 SQL。
3. 对四条关键用户路径执行端到端重放，核对事件顺序、关联 ID 和最终 UI 状态。
4. 执行 Renderer 快照或结构测试，覆盖加载、空态、遮蔽、无权、错误、影响预览和草稿已应用状态。
5. 使用工作包 10 定义的代表性用户和任务脚本执行人工可用性验收。

**产出物**

- `tests/contracts/agent-tool-cases.*`
- `tests/contracts/runtime-event-cases.*`
- `tests/ui/masterdata-renderer-cases.*`
- `docs/specification/verification/agent-ui-acceptance.md`
- `docs/specification/verification/results/agent-ui-baseline.txt`

**验证方式**

- 契约测试和四条端到端路径全部通过。
- UI 不得展示未经授权字段，风险和审批状态不得只用颜色表达。
- 人工验收记录任务完成率、关键错误、观察结论和未通过项；未通过项必须有责任人。

### [ ] T14.7 定义审计、安全、性能与恢复目标

**前置 Task**

- T14.2
- T14.3
- T14.4
- T14.5
- T14.6

**达成目标**

为安全边界、审计完整性、服务容量、超时降级、模型回滚和故障恢复设定可测量门槛。

**输入**

- 工作包 11 的部署拓扑、容量假设和运维责任。
- 工作包 12 的审计链、脱敏、指标、保留和变更治理。
- 前述 Task 的测试 fixture 与基线。

**执行步骤**

1. 建立威胁测试：权限提升、身份混淆、提示注入、参数走私、任意端点、任意 SQL、日志泄密、审批重放和证据漂移。
2. 定义查询与提案的端到端延迟分位数、并发量、错误率、超时、队列深度和资源上限。
3. 定义 Registry 不可用、DPA 超时、Database MCP 不可用、审计存储异常和模型版本故障的降级行为。
4. 明确并演练 `RTO`、`RPO`、模型回滚时间、审计零丢失要求及不确定执行的人工处置时限。
5. 验证日志、指标、trace 和执行回执通过 correlation ID 关联，且敏感字段按规则脱敏。

**产出物**

- `docs/specification/verification/security-test-plan.md`
- `docs/specification/verification/performance-recovery-targets.md`
- `tests/security/threat-cases.*`
- `tests/performance/masterdata-workloads.*`
- `docs/specification/verification/results/security-performance-recovery-baseline.md`

**验证方式**

- 所有高风险威胁测试均通过，失败请求默认拒绝并留下脱敏审计。
- 在工作包 11 的基准环境中执行固定负载，实际结果满足文档中的量化门槛。
- 至少完成一次模型回滚和一次依赖不可用演练，记录实际 `RTO`、`RPO` 与数据完整性结果。

### [ ] T14.8 建立最终验收门禁与签署流程

**前置 Task**

- T14.7

**达成目标**

将所有自动化测试、人工验收、风险例外和证据汇总为单一最终门禁，任何未满足条件都能明确阻止规格进入“可实施”状态。

**输入**

- T14.1 至 T14.7 的全部产出和基线结果。
- 工作包 13 的最终基线。
- 各责任域已确认的风险接受权限。

**执行步骤**

1. 定义门禁类别、必过项、允许例外项、禁止例外项和签署角色。
2. 编写门禁汇总脚本，检查需求覆盖、测试结果、人工验收、开放缺陷、安全门槛、性能恢复和证据新鲜度。
3. 规定阻断级缺陷、高风险安全失败、追踪缺口和过期证据不得豁免。
4. 为可接受例外记录范围、补偿控制、所有者、到期日和重新评审触发条件。
5. 在干净环境重跑门禁并保存机器结果与人工签署模板。

**产出物**

- `docs/specification/verification/final-acceptance-gate.md`
- `docs/specification/verification/acceptance-signoff.md`
- `tools/validation/run-final-acceptance-gate.*`
- `docs/specification/verification/results/final-gate-baseline.txt`

**验证方式**

- 在全绿基线上运行门禁，退出码为 0。
- 人为注入一个追踪缺口、一个授权失败和一个过期证据，门禁均必须返回非零退出码并指出原因。
- 签署模板覆盖产品、架构、安全、数据治理、DPA 业务所有者、测试和运维责任人。

## 工作包验收

- 所有规范性需求都有稳定需求 ID、来源、测试 ID、责任人和证据路径。
- Scanner、证据、模型 Registry、身份、查询、HITL、执行、Agent Tool、UI、审计、安全、性能和恢复均有可重复测试。
- MasterData 参考切片至少完成一次全链路正向重放和关键负向重放。
- 高风险要求同时具备正向与负向测试，任何未授权访问、自动保存、任意 SQL 或任意端点请求均被拒绝。
- 性能、`RTO`、`RPO`、回滚和不确定执行处置目标均为量化指标，并有基准或演练结果。
- 最终门禁在干净环境通过，故障注入能稳定阻断，并完成跨责任域签署。

## 解决记录

工作包关闭时填写，至少包含：

- 需求总数、自动化覆盖率、人工检查数量和高风险要求覆盖率。
- 各测试套件的执行命令、环境、基线结果和证据链接。
- 性能与恢复实测结果及其与目标的差异。
- 已接受例外、补偿控制、责任人和到期日。
- 最终门禁运行编号、结果和各责任域签署。
- 遗留缺陷、后续触发 `REVIEW_REQUIRED` 的条件及与工作包 15 的交接项。
