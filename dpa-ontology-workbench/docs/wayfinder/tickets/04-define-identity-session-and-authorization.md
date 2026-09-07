---
title: 定义身份、会话转发与授权边界
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee: copilot-agent
blocked_by: []
---

## 工作包目标

以可追踪的 DPA 当前事实为起点，定义独立本体平台在试点期和长期演进期的身份、会话与授权契约。工作包必须明确浏览器、Agent UI、Gateway、DPA、Entra ID/OIDC 与 `UserToken` 之间的信任边界；证明模型永远不能读取 Cookie、Token 或认证 Header；并将 DPA 保持为业务数据访问和业务操作的最终授权裁决者。

本工作包只形成事实报告、契约、责任矩阵、失败语义、威胁验证和演进决策，不实现生产认证组件，不保存任何真实凭据。

## 必需 Task

### [ ] T04.1 建立 DPA 当前身份事实链

**达成目标**

形成从 Entra ID/OIDC 登录到 DPA `UserToken` 建立、读取、续期和失效的可审核事实链，区分源码事实、配置事实、运行假设和待验证项。

**输入**

- DPA 登录入口、OIDC 配置、认证中间件、过滤器和业务层源码。
- `UserToken` 的创建、读取、校验、续期、删除相关源码与配置。
- `README.md` 和 `docs/wayfinder/map.md` 中已确认的系统边界。

**执行步骤**

1. 定位登录回调、会话建立、Cookie 写入、`UserToken` 生成与用户装载的调用链。
2. 记录每一跳的主体标识、凭据载体、信任方、有效期、刷新机制和失败响应。
3. 定位 DPA 授权过滤器与业务层的最终权限检查点，标明不可由平台复制或绕过的判断。
4. 对无法从源码证明的环节标记为“待验证”，并给出最小验证方法，不得以推测补齐。
5. 为事实证据记录仓库、revision、路径、符号和行号。

**产出物**

- `docs/architecture/identity/dpa-current-identity-fact-chain.md`
- `docs/architecture/identity/dpa-current-identity-sequence.md`

**验证方式**

- 从任一已认证 DPA 请求出发，能够沿文档反向追踪到登录主体、`UserToken` 和最终授权点。
- 文档中每个“当前行为”均有源码或配置证据；抽查至少一条成功链、一次会话过期链和一次权限拒绝链。
- 搜索产出物，确认不存在 Cookie、Token、Secret 或 Header 的真实值。

**边界**

- 不修改 DPA 认证实现。
- 不把 Entra ID 声明直接等同于 DPA 业务权限。

### [ ] T04.2 定义同源 Cookie 转发试点

**达成目标**

定义试点期在受控同源部署下，由 Gateway 代表当前浏览器会话调用 DPA 的最小可行凭据转发方案，并明确 Cookie 不进入模型上下文、日志、事件载荷或持久化存储。

**输入**

- T04.1 的事实链与信任边界。
- 试点部署拓扑、反向代理规则、DPA Cookie 属性和 CSRF 防护现状。
- Agent UI 到 Gateway、Gateway 到 DPA 的候选请求链。

**执行步骤**

1. 固定允许转发的入口、目标主机、路径前缀、HTTP Method 和 Header 白名单。
2. 定义浏览器到 Gateway 的同源条件，以及 `Secure`、`HttpOnly`、`SameSite`、Domain、Path 和 TLS 约束。
3. 定义 Gateway 仅在服务端内存中读取并按目标白名单转发 Cookie 的处理流程。
4. 定义 CSRF 校验、Origin/Referer 校验、请求关联 ID、日志脱敏和禁止缓存规则。
5. 列出模型输入、Tool 参数、审计事件和错误对象中明确禁止出现的凭据字段。
6. 给出本地、测试和生产拓扑下允许与拒绝的配置样例。

**产出物**

- `docs/architecture/identity/same-origin-cookie-forwarding-pilot.md`
- `docs/architecture/identity/same-origin-forwarding-config-examples.yaml`

**验证方式**

- 使用文档中的表格逐项验证：同源合法请求可转发，跨域、目标不在白名单、Origin 不匹配和 CSRF 缺失的请求均被拒绝。
- 对示例事件、日志和 Tool 请求执行字段检查，确认不包含 Cookie、Authorization、`UserToken` 或其派生值。
- 由安全评审者按文档独立画出凭据流，结果与时序图一致。

**前置 Task**

- T04.1

**边界**

- 该方案仅用于受控试点，不作为跨域或第三方客户端的长期认证方案。

### [ ] T04.3 定义平台身份上下文契约

**达成目标**

定义平台内部可消费、可审计且不携带原始凭据的 `IdentityContext`，统一 Agent UI、Gateway、Policy、Registry、查询与行为提案对“当前用户”的表达。

**输入**

- T04.1 的 DPA 用户事实字段。
- T04.2 的试点凭据流。
- M5 Actor/Permission 的候选稳定 ID 与版本规则。

**执行步骤**

1. 定义 `IdentityContext` 的必需字段、可选字段、来源、类型、生命周期和敏感级别。
2. 至少覆盖 `subject_id`、`dpa_user_id`、`tenant_id`、`organization_scope`、`session_id`、`auth_time`、`expires_at`、`assurance_level`、`source` 和 `correlation_id`。
3. 区分“已认证身份事实”“平台推导上下文”和“必须由 DPA 实时裁决的权限”，禁止把推导值当成授权结论。
4. 定义上下文创建、跨模块传递、最小化、脱敏、过期检查和审计引用规则。
5. 给出已认证、匿名、字段缺失、租户不匹配和上下文过期的规范样例。

**产出物**

- `docs/architecture/identity/platform-identity-context-contract.md`
- `docs/architecture/identity/examples/identity-context.examples.json`

**验证方式**

- 使用 Schema 或逐字段检查表验证所有样例，合法样例全部通过，缺少必需字段和包含原始凭据的样例必须失败。
- 任一 `IdentityContext` 字段都能追踪到明确来源或推导规则。
- 权限字段不得宣称替代 DPA 最终授权。

**前置 Task**

- T04.1
- T04.2

### [ ] T04.4 建立认证与授权责任矩阵

**达成目标**

明确 Entra ID、浏览器、Agent UI、Gateway、DPA 认证层、DPA 业务层、Database MCP 和模型在认证、会话、数据范围与操作授权中的责任、禁止事项和失败责任。

**输入**

- T04.1 至 T04.3 的事实与契约。
- `docs/wayfinder/map.md` 中关于 DPA 最终授权和 Database MCP 只读的边界。
- M5 Actor/Permission、M7 Query 和 MI Integration 的职责定义。

**执行步骤**

1. 按“建立身份、携带会话、解析身份、预检策略、行级范围、字段范围、行为授权、最终裁决、审计”列出责任。
2. 对每项责任标明 Responsible、Accountable、Consulted、Informed 和明确禁止承担者。
3. 区分平台快速拒绝、DPA 最终拒绝和 Database MCP 数据范围执行。
4. 定义禁止缓存 DPA 授权结论、禁止模型声明权限、禁止 Gateway 绕过 DPA 业务层写入的规则。
5. 用 MasterData 读取、草稿应用和受控命令三个案例验证矩阵。

**产出物**

- `docs/architecture/identity/authentication-authorization-responsibility-matrix.md`

**验证方式**

- 三个案例中的每个授权判断均能映射到唯一最终责任方。
- 矩阵不存在 Gateway 与 DPA 同时被标为业务写入最终裁决者的冲突。
- Database MCP 在所有案例中均无写入责任，模型在所有案例中均不接触凭据。

**前置 Task**

- T04.3

### [ ] T04.5 定义过期、退出与跨域失败语义

**达成目标**

为身份和会话异常定义稳定、无泄密、可恢复的状态与错误契约，使前端、Gateway 和 DPA 对重新认证、重新授权和禁止重试具有一致行为。

**输入**

- T04.2 的同源试点规则。
- T04.3 的 `IdentityContext`。
- DPA 当前对 401、403、重定向、登录页和会话过期的实际响应。

**执行步骤**

1. 建立会话过期、用户主动退出、DPA 退出但平台未退出、平台退出但 DPA 未退出、Cookie 缺失、Cookie 被拒、跨域、租户不匹配和时钟偏差场景。
2. 为每个场景定义检测点、稳定错误码、HTTP 状态、用户提示、审计事件和允许的恢复动作。
3. 明确禁止将 DPA 登录 HTML、重定向链、内部异常或凭据片段直接返回模型。
4. 定义退出后的上下文清理、缓存失效、在途请求处理和重放阻断规则。
5. 给出可重复执行的场景表和预期结果。

**产出物**

- `docs/architecture/identity/session-failure-and-logout-contract.md`
- `tests/spec/identity/session-failure-scenarios.yaml`

**验证方式**

- 对场景文件逐项检查，所有场景均包含前置状态、触发动作、预期错误码、审计事件和恢复动作。
- 401 与 403 的语义不可互换；跨域失败不得自动降级为无保护转发。
- 退出后复用旧 `IdentityContext`、旧 Cookie 引用或旧请求重放均被定义为拒绝。

**前置 Task**

- T04.2
- T04.3
- T04.4

### [ ] T04.6 完成威胁建模与安全验收用例

**达成目标**

证明试点方案能够抵御凭据泄露、CSRF、会话固定、混淆代理、跨租户、重放、日志泄密和模型提示注入诱导取凭据等主要威胁。

**输入**

- T04.2 至 T04.5 的契约和场景。
- 部署拓扑、日志字段、Tool 协议和审计事件候选定义。

**执行步骤**

1. 绘制身份链数据流和信任边界，标出凭据进入、使用和销毁位置。
2. 建立威胁清单，记录攻击前提、受影响资产、现有控制、缺口和验证方法。
3. 为高风险威胁生成负向验收用例，至少覆盖跨域伪造、目标主机篡改、Cookie 注入、Token 回显、跨租户上下文和退出后重放。
4. 定义发布阻断条件：任何原始凭据进入模型、日志或持久化存储即阻断。
5. 记录残余风险、责任人角色和进入长期方案前必须关闭的条件。

**产出物**

- `docs/architecture/identity/identity-session-threat-model.md`
- `tests/spec/identity/identity-security-acceptance.yaml`

**验证方式**

- 每个高风险威胁至少对应一个控制和一个可执行验收用例。
- 用例包含输入、执行动作、预期拒绝点和预期审计证据，可由非作者重复执行。
- 不存在“由模型遵守提示词”作为唯一安全控制的条目。

**前置 Task**

- T04.5

### [ ] T04.7 定义 delegated token 与 token exchange 长期演进

**达成目标**

将同源 Cookie 转发明确限制为试点方案，并给出迁移到 delegated token 或 token exchange 的目标架构、选择标准、兼容策略和退出门槛。

**输入**

- T04.1 至 T04.6 的事实、风险和试点约束。
- Entra ID/OIDC 可用授权流、DPA 可改造范围和跨域客户端需求。
- 预期服务间调用、代表用户调用和后台任务场景。

**执行步骤**

1. 分别描述 delegated token、OAuth 2.0 On-Behalf-Of 或等价 token exchange 的主体、受众、Scope、生命周期和撤销方式。
2. 比较 Cookie 转发、delegated token 和 token exchange 在跨域、最小权限、审计、撤销、运维和 DPA 改造成本上的差异。
3. 定义目标 `IdentityContext` 与上游凭据解耦的兼容要求，避免业务 Tool 协议随认证机制变化。
4. 定义从试点到长期方案的进入条件、双栈期、回退策略和 Cookie 转发下线条件。
5. 对无法在当前证据下决定的事项记录决策负责人、所需证据和最晚决策点。

**产出物**

- `docs/architecture/identity/delegated-token-evolution-plan.md`
- `docs/adr/ADR-identity-delegation-target.md`

**验证方式**

- ADR 至少比较两个长期候选方案，并明确选择条件或保留为有期限的待决项。
- 迁移前后 Agent Tool、M7 Query 和 MI Integration 不需要接收原始凭据。
- 演进计划包含可测量的试点退出门槛和 Cookie 转发停用检查表。

**前置 Task**

- T04.6

## 工作包验收

- T04.1 至 T04.7 全部完成，所有产出路径可访问，验证记录可由非作者重复执行。
- 当前事实、试点设计和长期目标在文档中明确分层，不将候选方案写成现状。
- 任一身份请求都能追踪主体、会话来源、平台上下文、DPA 最终授权点和审计关联 ID。
- Cookie、Token、Authorization Header 和 `UserToken` 的真实值不会进入模型、Tool 参数、日志、事件或持久化资产。
- 过期、退出、跨域、跨租户和重放场景均有稳定错误语义及拒绝位置。
- 同源 Cookie 转发具有明确试点退出条件，delegated token/token exchange 具有可执行的决策与迁移路径。

## 解决记录

<!-- 工作包关闭时填写：最终身份链、试点方案、长期目标、关键取舍、验证结果和产出物链接。 -->
