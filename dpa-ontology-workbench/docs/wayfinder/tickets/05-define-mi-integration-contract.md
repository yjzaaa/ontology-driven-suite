---
title: 定义 MI 集成与副作用契约
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 03-define-ontology-contracts-and-lifecycle.md
  - 04-define-identity-session-and-authorization.md
---

## 工作包目标

定义 MI Integration 如何把稳定的语义 Query 或 Behavior 绑定到既有 DPA HTTP 端点或受治理的 Database MCP 能力，并形成可校验、可版本化、可审计的防腐层契约。契约必须固定技术参数与凭据处理，准确分类副作用，约束超时、重试和幂等，标准化响应与错误，并在源码证据变化时自动失效为 `REVIEW_REQUIRED`。

本工作包不开放任意 URL、HTTP Method、Header、SQL 或 DTO 映射给模型，不实现生产连接器，也不改变 DPA 原有接口。

## 必需 Task

### [ ] T05.1 定义 MI 核心字段与引用规则

**达成目标**

形成 MI Integration 的字段级契约，使每个映射都能唯一绑定语义能力、技术执行目标、身份策略、证据与版本。

**输入**

- 工作包 03 产出的 MI Integration Schema、稳定 ID 和生命周期规则。
- 工作包 04 产出的 `IdentityContext` 与凭据边界。
- DPA HTTP 和 Database MCP 的代表性候选能力。

**执行步骤**

1. 定义 MI 的标识、版本、状态、语义引用、执行器类型、目标引用、请求映射、响应映射、副作用、策略、证据和失效字段。
2. 至少明确 `integration_id`、`version`、`status`、`binds_to`、`executor`、`operation_ref`、`request_mapping`、`response_mapping`、`side_effect`、`timeout_policy`、`retry_policy`、`idempotency_policy`、`identity_policy`、`evidence_refs` 和 `evidence_fingerprint`。
3. 为字段定义类型、必填条件、默认值、枚举、互斥关系和向后兼容规则。
4. 定义 MI 对 M2 Behavior、M7 Query、DPA 端点和 Database MCP capability 的合法引用方向。
5. 生成合法、缺字段、非法跨引用和版本不兼容样例。

**产出物**

- `docs/contracts/mi/mi-integration-contract.md`
- `models/schema/mi-integration.schema.json`
- `models/examples/mi/mi-core-field-examples.yaml`

**验证方式**

- 使用工作包 03 规定的 Schema 校验方式运行样例：合法样例通过，负向样例按预期失败。
- 每个运行时必需字段均有唯一语义，任何字段不得要求模型提供 URL、Header、凭据或 SQL。
- MI 引用不存在从技术端点反向授予 Behavior 或 Query 业务语义的路径。

**前置 Task**

- 工作包 03
- 工作包 04

### [ ] T05.2 固定参数并定义禁止覆盖规则

**达成目标**

明确哪些参数来自发布后的 MI、`IdentityContext`、语义请求或服务端计算，并阻止模型和客户端覆盖安全关键技术参数。

**输入**

- T05.1 的字段契约。
- 代表性 DPA 请求 DTO、Route、QueryString、Header 和 Database MCP 参数。
- 工作包 04 的身份上下文字段。

**执行步骤**

1. 将参数来源分类为 `FIXED`、`SEMANTIC_INPUT`、`IDENTITY_CONTEXT`、`SERVER_DERIVED` 和 `FORBIDDEN`。
2. 固定目标主机、路径模板、HTTP Method、Content-Type、凭据 Header、租户字段和服务端安全开关。
3. 定义同名冲突时的优先级与拒绝规则，禁止通过嵌套对象、大小写变化或额外字段绕过。
4. 定义语义输入到技术 DTO 的显式白名单映射、类型转换、默认值和范围校验。
5. 为 URL、Method、Authorization、Cookie、任意 SQL、用户/组织范围覆盖生成负向样例。

**产出物**

- `docs/contracts/mi/mi-parameter-source-and-override-rules.md`
- `models/examples/mi/mi-parameter-binding-examples.yaml`
- `tests/spec/mi/forbidden-override-cases.yaml`

**验证方式**

- 每个技术参数都能映射到唯一来源分类。
- 逐项执行负向用例，所有安全关键字段覆盖尝试均在调用执行器前失败。
- 合法样例生成的技术请求与固定快照一致，重复生成结果相同。

**前置 Task**

- T05.1

### [ ] T05.3 建立副作用分类与执行准入规则

**达成目标**

将 DPA 端点和 Database MCP capability 按可证明的副作用分类，并决定哪些映射可自动读取、必须进入 HITL 或一律禁止执行。

**输入**

- T05.1 的 MI 字段。
- DPA Controller、Service、Repository 调用链和 Database MCP 能力证据。
- `docs/wayfinder/map.md` 中“无法证明纯读则按 `MIXED/HIGH` 处理”的边界。

**执行步骤**

1. 定义 `READ_ONLY`、`MIXED`、`WRITE`、`EXTERNAL_EFFECT` 和 `UNKNOWN` 的判定标准。
2. 检查 HTTP Method 之外的实际调用链、副作用写库、消息、文件、缓存、工作流和外部系统调用。
3. 定义 Query 与 Behavior 对副作用类别的引用限制，以及自动执行、HITL、草稿应用和禁止执行的准入矩阵。
4. 明确 Database MCP 永远只读；出现 DDL、DML 或不可证明的存储过程时拒绝发布。
5. 为“GET 但写审计业务表”“POST 纯查询”“读写混合 Action”等易错案例给出裁决。

**产出物**

- `docs/contracts/mi/mi-side-effect-classification.md`
- `docs/contracts/mi/mi-execution-admission-matrix.md`
- `models/examples/mi/mi-side-effect-examples.yaml`

**验证方式**

- 每个代表性端点均有调用链证据、分类理由和准入结论。
- `UNKNOWN` 和无法证明纯读的能力不会进入自动执行路径。
- 同一证据输入由两名评审者独立分类时，结论一致；不一致项有明确升级规则。

**前置 Task**

- T05.1

### [ ] T05.4 定义超时、重试与幂等契约

**达成目标**

为不同执行器和副作用类别规定可预测的超时、取消、重试和幂等行为，避免重复写入、长时间占用和不受控级联重试。

**输入**

- T05.3 的副作用分类与准入矩阵。
- DPA 与 Database MCP 的性能基线、现有超时和幂等能力。
- Gateway 调用链和请求关联 ID 规则。

**执行步骤**

1. 分别定义连接超时、首字节超时、总超时、取消传播和最大响应体限制。
2. 对 `READ_ONLY`、`MIXED`、`WRITE`、`EXTERNAL_EFFECT` 定义默认重试次数、退避、可重试错误和禁止重试条件。
3. 定义 `idempotency_key` 的生成、作用域、保存期限、冲突处理和结果复用规则。
4. 对不具备 DPA 服务端幂等保证的写操作规定禁止自动重试。
5. 定义 Gateway、反向代理、DPA 客户端三层超时与重试预算，防止乘法放大。
6. 生成超时、取消、网络中断、重复提交和未知执行结果场景。

**产出物**

- `docs/contracts/mi/mi-timeout-retry-idempotency.md`
- `tests/spec/mi/resilience-and-idempotency-scenarios.yaml`

**验证方式**

- 每个场景均可计算最大尝试次数和最坏总耗时。
- 对同一 `idempotency_key` 重复提交，不会产生两个被视为独立成功的写入。
- 未知执行结果不得被自动标记为失败后重试，必须进入人工确认或对账状态。

**前置 Task**

- T05.3

### [ ] T05.5 标准化响应投影与错误契约

**达成目标**

将不同 DPA 端点和 Database MCP 响应转换为稳定的语义结果与错误对象，隔离内部 DTO、登录页、堆栈和传输细节。

**输入**

- T05.1 的请求与响应映射字段。
- DPA 代表性成功响应、业务错误、验证错误、401、403、404、409、429、5xx 和登录重定向。
- Database MCP 的成功与失败响应。

**执行步骤**

1. 定义成功结果的 `data`、`metadata`、`warnings`、`correlation_id` 和来源版本字段。
2. 定义稳定错误字段，至少包含 `code`、`category`、`message_key`、`retryable`、`details`、`correlation_id` 和 `source_status`。
3. 建立认证、授权、校验、冲突、限流、超时、上游不可用、映射失败和未知错误的归一化表。
4. 定义 HTML、空响应、非预期 Content-Type、部分成功和字段缺失的处理。
5. 定义对模型可见、对用户可见和仅审计可见的信息分层与脱敏。

**产出物**

- `docs/contracts/mi/mi-response-and-error-contract.md`
- `models/schema/mi-runtime-result.schema.json`
- `tests/spec/mi/response-error-normalization-cases.yaml`

**验证方式**

- 代表性响应均能确定性转换为 Schema 合法的结果或错误对象。
- 401 与 403、业务校验与系统失败、可重试与不可重试错误具有不同稳定码。
- 任何样例均不向模型暴露堆栈、内部 URL、Cookie、Token、SQL 或原始敏感 DTO。

**前置 Task**

- T05.2
- T05.4

### [ ] T05.6 定义证据版本、变更检测与自动失效

**达成目标**

使每个已发布 MI 能追踪到具体源码与能力证据，并在端点签名、DTO、调用链、副作用或安全参数变化时自动进入 `REVIEW_REQUIRED`。

**输入**

- 工作包 02 的证据契约与增量变更规则。
- 工作包 03 的发布状态机和不可变版本规则。
- T05.1 至 T05.5 的 MI 契约。

**执行步骤**

1. 定义 MI 绑定证据的最小集合与 `evidence_fingerprint` 计算输入。
2. 将变更分为兼容、需复核、破坏性和安全关键，并规定状态迁移。
3. 至少覆盖 Route、Method、参数、DTO、响应、授权属性、调用链、副作用、Database MCP capability 和固定配置变化。
4. 定义发现漂移后的运行时行为：阻断、降级、继续只读或仅告警。
5. 生成无变化、兼容增字段、删除字段、Method 改变、副作用升级和证据缺失样例。

**产出物**

- `docs/contracts/mi/mi-evidence-version-and-invalidation.md`
- `tests/spec/mi/mi-evidence-drift-cases.yaml`

**验证方式**

- 对相同证据重复计算得到相同 fingerprint。
- 安全关键或破坏性变化必然使对应 MI 进入 `REVIEW_REQUIRED`，且不能继续自动执行。
- 发布版本保持不可变；复核后的修订产生新版本，不覆盖原版本。

**前置 Task**

- T05.3
- T05.5
- 工作包 02
- 工作包 03

### [ ] T05.7 制作代表性 MI 样例与一致性验收

**达成目标**

用一组覆盖主要风险的 MasterData 样例证明 MI 契约能够完整表达查询、草稿应用和受控行为，而无需模型接触技术执行细节。

**输入**

- T05.1 至 T05.6 的全部契约。
- MasterData 的 DPA 端点、Database MCP 视图和候选 M2/M7 模型。

**执行步骤**

1. 制作至少一个 Database MCP 只读查询映射、一个 DPA 只读端点映射、一个将结果应用到原表单的草稿映射。
2. 制作至少一个 `MIXED/HIGH` 且被阻断或要求 HITL 的映射。
3. 为每个样例提供语义输入、期望技术请求快照、响应投影、错误投影、证据引用和版本状态。
4. 加入固定参数覆盖、超时、重复提交、证据漂移和权限拒绝的负向场景。
5. 建立从 M2/M7 稳定 ID 到 MI、证据、测试场景和预期结果的追踪矩阵。

**产出物**

- `models/examples/mi/masterdata/`
- `tests/spec/mi/masterdata-mi-scenarios.yaml`
- `docs/contracts/mi/masterdata-mi-traceability-matrix.md`

**验证方式**

- 全部样例通过 Schema 和引用校验，负向样例在预期阶段失败。
- 给定同一语义输入和 MI 版本，生成的技术请求与响应投影可重复。
- 评审者仅查看语义 Tool 输入时无法指定 URL、Method、Header、凭据或 SQL。
- 追踪矩阵不存在缺失的 M2/M7、MI、证据或验证场景链接。

**前置 Task**

- T05.6

### [ ] T05.8 定义保存端点服务端校验闭包分析契约

**达成目标**

为候选写行为证明“服务端校验闭包”与“客户端计算字段”边界，使自渲染写表单与 HITL 受控执行的三项证据门槛（工作包 07 T07.1）可机械判定。

**输入**

- T05.1 至 T05.3 的 MI 字段、参数来源与副作用分类。
- 工作包 02 的调用链证据契约（Controller → BLL → Repository）。
- MasterData 候选保存端点。

**执行步骤**

1. 定义从保存端点源码证据提取服务端校验规则（必填、格式、范围、跨字段、权限前置）的方法；规则标注 `FACT`/`INFERENCE` 并附文件与行号。
2. 定义客户端计算字段的识别与标记方法：凡由前端脚本计算且服务端无对应校验的字段必须显式列出。
3. 定义字段闭包覆盖判定：MI 语义输入 + `SERVER_DERIVED` 字段集必须覆盖服务端校验闭包的全部必填项。
4. 定义三项证据门槛的结论 Schema：服务端校验闭包完整、无未处理客户端计算字段、字段闭包覆盖；任一不满足即要求走草稿回填路径。
5. 生成 MasterData 保存端点的分析样例，含通过与拒绝案例。

**产出物**

- `docs/contracts/mi/mi-validation-closure-analysis.md`
- `models/examples/mi/mi-validation-closure-examples.yaml`

**验证方式**

- 分析产物可由固定证据输入重复生成，结论一致。
- 门槛结论直接被工作包 07 T07.1 的执行模式判定引用；缺失闭包证据的候选写行为机械落入 `DRAFT_ONLY`。

**前置 Task**

- T05.3
- 工作包 02

## 工作包验收

- T05.1 至 T05.8 全部完成，MI 核心字段、引用和版本规则可由 Schema 或明确检查表验证。
- 所有参数具有唯一来源，模型和客户端不能覆盖 URL、Method、凭据、租户、组织范围或任意 SQL。
- 副作用分类有源码证据；无法证明纯读的能力按 `MIXED/HIGH` 或更严格规则处理。
- 候选写行为均有服务端校验闭包分析结论；未通过三项证据门槛的行为不进入 HITL 受控执行样例。
- 超时、重试和幂等策略可计算、可复现，不会把未知写入结果自动重试成重复副作用。
- DPA 与 Database MCP 的响应和错误被投影为稳定协议，不泄露内部实现与凭据。
- 证据漂移能够确定性触发 `REVIEW_REQUIRED`，已发布版本不可原地修改。
- MasterData 代表性样例覆盖成功、拒绝、超时、重复、漂移和副作用升级。

## 解决记录

<!-- 工作包关闭时填写：最终 MI 契约、参数边界、副作用策略、失效规则、代表性样例、验证结果和产出物链接。 -->
