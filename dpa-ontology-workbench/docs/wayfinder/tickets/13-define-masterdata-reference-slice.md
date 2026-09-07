---
title: 定义 MasterData 参考纵向切片
status: open
labels:
  - wayfinder:grilling
parent: ../map.md
assignee:
blocked_by:
  - 03-define-ontology-contracts-and-lifecycle.md
  - 05-define-mi-integration-contract.md
  - 06-define-governed-query-and-data-scope.md
  - 07-define-hitl-and-action-execution.md
  - 09-define-product-surfaces-and-rendering.md
---

## 工作包目标

选择一个边界清晰、证据充分且能代表真实 DPA 约束的 MasterData 业务对象，建立从源码证据到 M1/M3/M5、M7/MU、M2/MI、Agent Tool、界面投影和验收场景的完整参考纵向切片。该切片只覆盖证明架构与契约可实施所需的最小业务范围，不扩展为整个 MasterData 领域模型，也不建设生产代码。

完成后，交付团队应能按稳定 ID 和明确路径找到每个样例，重复验证所有跨模型引用，并沿追踪矩阵回答“某项语义来自哪份证据、由什么权限约束、如何查询或应用、由哪个场景验收”。

## 必需 Task

### [ ] T13.1 选择参考对象并冻结切片边界

**达成目标**

选出一个同时具备查询、校验、权限、页面展示和草稿应用价值的 MasterData 对象，并冻结纳入与排除范围，避免样例在后续任务中持续膨胀。

**输入**

- 工作包 01 的统一领域语言、对象边界和稳定 ID 规则。
- 工作包 02 的源码证据目录与覆盖率报告。
- 工作包 03、05、06、07、09 已确认的模型、集成、查询、执行和界面契约。
- DPA MasterData Controller、业务服务、DTO、权限过滤器、视图或表单的候选清单。

**执行步骤**

1. 按“证据完整度、读取路径、编辑路径、权限差异、规则代表性、页面可观察性”六项指标建立候选评分表。
2. 对得分最高的两个候选各抽查一条读取链和一条编辑链，记录缺失证据与不可控副作用。
3. 选择一个参考对象，分配稳定 ID，例如 `masterdata.<object>`；记录业务名称、源码符号、所有者和选择理由。
4. 明确切片只包含的字段、关系、查询、规则、角色、展示和行为数量上限，并列出明确排除项。
5. 将无法从证据证明的假设标记为“开放项”，不得写成已确认事实。

**产出物**

- `docs/specification/masterdata/reference-slice-scope.md`
- `docs/specification/masterdata/reference-object-scorecard.md`

**验证方式**

- 重新按评分公式计算候选得分，结果与文档一致。
- 范围文档包含唯一参考对象、稳定 ID、纳入项、排除项、证据缺口和所有者。
- 任一后续样例均能归入纳入项；否则必须回到本 Task 更新范围并留下变更记录。

**边界**

- 不反向建模整个 MasterData。
- 不因演示方便而选择没有真实 DPA 编辑路径的虚构对象。

### [ ] T13.2 建立参考对象证据包

**前置 Task**

- T13.1

**达成目标**

形成可机器检查、可人工复核的最小证据包，证明参考对象的字段、关系、权限、查询、校验和编辑入口确实存在于 DPA。

**输入**

- T13.1 的范围与稳定 ID。
- 工作包 02 定义的证据 Schema、来源定位和增量变更规则。
- 已扫描的 Controller、Action、业务服务、DTO、过滤器、视图、脚本和数据库只读元数据。

**执行步骤**

1. 收集参考对象相关的源码符号、文件位置、调用边、路由、表单字段、校验提示和权限检查。
2. 为每条证据记录 `evidence_id`、来源提交或版本、文件与符号定位、证据类型、提取时间和置信度。
3. 将推断与直接证据分开；推断必须列出依据和待确认人。
4. 生成读取链、草稿应用链和原 DPA 保存链的证据摘要，不记录凭据、会话值或生产数据。
5. 执行证据 Schema 校验并保存校验结果。

**产出物**

- `evidence/masterdata/reference-slice/evidence.json`
- `evidence/masterdata/reference-slice/source-index.json`
- `docs/specification/masterdata/reference-evidence-report.md`
- `docs/specification/masterdata/validation/evidence-validation.txt`

**验证方式**

- 使用工作包 02 规定的校验命令验证 `evidence.json`，退出码必须为 0。
- 从报告随机选择至少 10 条结论，均能定位到 `evidence_id` 和具体源码符号或视图位置。
- 扫描结果不得包含访问令牌、Cookie、连接字符串或真实敏感业务值。

### [ ] T13.3 编写 M1、M3、M5 核心模型样例

**前置 Task**

- T13.2

**达成目标**

用已发布模型契约表达参考对象、业务规则和角色/权限，建立后续查询、展示和行为样例共同依赖的语义核心。

**输入**

- T13.1 的切片范围。
- T13.2 的证据包。
- 工作包 03 的 M1、M3、M5 Schema、引用、版本与发布规则。
- 工作包 04、06 的身份、权限、行列范围结论。

**执行步骤**

1. 编写一个 M1 对象，定义稳定 ID、业务键、字段类型、敏感级别、只读属性、关系和来源证据。
2. 编写不少于三条 M3 规则，至少覆盖必填、格式或值域、跨字段条件；区分客户端提示与 DPA 最终裁决。
3. 编写 M5 角色/权限映射，至少覆盖可查看、可编辑、受限字段和无权访问四类结果。
4. 为所有跨模型引用和证据引用使用稳定 ID，不复制易漂移的显示名称作为主键。
5. 运行 Schema、引用闭包和禁止字段检查；修复所有错误后保存验证报告。

**产出物**

- `models/masterdata/reference/m1-object.yaml`
- `models/masterdata/reference/m3-rules.yaml`
- `models/masterdata/reference/m5-permissions.yaml`
- `docs/specification/masterdata/validation/core-model-validation.txt`

**验证方式**

- 使用工作包 03 规定的模型校验命令执行三份 YAML，退出码必须为 0。
- 删除任一被引用稳定 ID 后，引用校验必须失败，以证明检查不是空跑。
- M1 中每个纳入字段至少关联一条证据；M3、M5 的每项结论均可回溯到证据或正式决策。

### [ ] T13.4 编写 M7 查询与 MU 展示样例

**前置 Task**

- T13.3

**达成目标**

定义安全、可投影且可在 Agent UI 与对象视图复用的查询和展示样例，证明查询结果不会绕过用户身份、行范围或字段敏感性约束。

**输入**

- T13.3 的 M1、M3、M5。
- 工作包 06 的查询限制、行列权限、分页、导出和审计规则。
- 工作包 09 的 Renderer、页面和 Legacy View 边界。

**执行步骤**

1. 编写至少两个 M7 查询：一个受限列表查询和一个按业务键获取详情的查询。
2. 为查询声明允许的过滤、排序、分页上限、超时、字段投影、行范围策略和审计事件。
3. 编写 MU 列表与详情投影，明确字段顺序、标签、格式、敏感字段遮蔽、空态和错误态。
4. 为每个 M7 查询绑定允许的 MU 投影，不允许模型选择 URL、HTTP Method、Header、SQL 或内部 DTO。
5. 准备允许、越权、超限和敏感字段四组固定测试向量。
6. 其中至少一个 MU 由工作包 09 T09.10 的 UI 证据提取管线从参考页面生成：记录查全率、查准率与绑定正确率，并通过 Renderer 对该 MU 的零代码渲染验证。

**产出物**

- `models/masterdata/reference/m7-queries.yaml`
- `models/masterdata/reference/mu-presentations.yaml`
- `docs/specification/masterdata/examples/query-vectors.json`
- `docs/specification/masterdata/validation/query-presentation-validation.txt`

**验证方式**

- 模型 Schema 和跨引用校验退出码为 0。
- 对固定测试向量执行工作包 06 定义的策略测试：允许用例返回声明字段，越权、超限和未授权敏感字段用例被拒绝或遮蔽。
- MU 引用的每个字段都存在于 M1 或明确的派生字段契约中。
- 提取管线生成的 MU 满足 T09.10 的确定性要求，重复提取快照一致。

### [ ] T13.5 编写 M2 与 MI 草稿应用路径

**前置 Task**

- T13.3
- T13.4

**达成目标**

定义默认写入体验：Agent 生成并校验行为草稿，经用户审核后应用到原 DPA 表单，最终仍由用户触发 DPA 原保存动作。

**输入**

- 工作包 05 的 MI 映射和副作用契约。
- 工作包 07 的 Action Proposal、HITL、幂等和审计状态机。
- 工作包 09 的 Agent UI 与 Legacy View 集成边界。
- T13.2 的表单与保存链证据。

**执行步骤**

1. 编写一个 M2 编辑行为，定义输入字段、适用对象、前置规则、影响预览和风险级别。
2. 编写对应 MI 草稿应用映射，只描述稳定语义到受信任表单字段的映射，不包含凭据、任意脚本或保存调用。
3. 明确状态流：草稿生成、模型校验、用户审核、应用到表单、用户修改、原 DPA 保存或取消。
4. 定义目标页面不匹配、字段缺失、页面版本漂移、权限变化和校验失败时的安全失败行为。
5. 准备可重复的示例输入、预期草稿、预期表单差异和审计记录。

**产出物**

- `models/masterdata/reference/m2-draft-application.yaml`
- `models/masterdata/reference/mi-draft-application.yaml`
- `docs/specification/masterdata/examples/draft-application-scenario.md`
- `docs/specification/masterdata/examples/draft-application-fixtures.json`

**验证方式**

- Schema、引用和禁止能力检查退出码为 0。
- 使用固定 fixture 重放映射，两次输出必须一致且只修改白名单字段。
- 检查样例中不存在自动触发原 DPA 保存、直接数据库写入或绕过 DPA 最终授权的路径。

### [ ] T13.6 评估并示例化一个简单命令

**前置 Task**

- T13.2
- T13.3

**达成目标**

依据正式准入规则判断参考对象是否存在可由 Gateway 在 HITL 后执行的简单命令；满足条件时提供一个完整样例，并优先保证“提案→审批→HITL 受控执行→收据→审计”的完整 L2 演示主路径；不满足时形成可复核的拒绝结论，并把 L2 演示主路径缺口上报地图“尚未明确”。

**输入**

- 工作包 05 的副作用分类、重试、幂等和错误归一化规则。
- 工作包 07 的审批令牌、单次消费和执行状态机。
- 工作包 12 的审计与 `REVIEW_REQUIRED` 阻断规则。
- T13.2 的真实端点和业务服务证据。

**执行步骤**

1. 按“单一明确副作用、可预览、可授权、可幂等、可审计、失败边界明确”逐项评估候选命令。
2. 任何无法证明纯读或单一副作用的候选均标记为 `MIXED/HIGH`，不得进入自动执行样例。
3. 若候选通过，编写 M2/MI 命令样例、固定参数、禁止参数、审批声明、超时、重试和幂等键规则。
4. 若无候选通过，记录拒绝原因，以“仅保留草稿应用”为参考切片结论，并在工作包解决记录中标注 L2 演示主路径缺口及其原因。
5. 为通过或拒绝结论准备正向与负向验证案例。

**产出物**

- `docs/specification/masterdata/simple-command-assessment.md`
- 条件产出：`models/masterdata/reference/m2-simple-command.yaml`
- 条件产出：`models/masterdata/reference/mi-simple-command.yaml`
- `docs/specification/masterdata/examples/simple-command-vectors.json`

**验证方式**

- 由工作包 05、07、12 的规则负责人逐项签署评估表。
- 若生成命令样例，策略测试必须证明：无审批、审批过期、重复消费、权限变化和幂等冲突均不会执行。
- 若拒绝命令样例，评估表必须包含至少一个真实候选及其证据化拒绝理由。

**边界**

- 本 Task 不为满足样例数量而降低命令准入标准。
- Database MCP 永远只读。

### [ ] T13.7 建立端到端追踪矩阵与可重放场景

**前置 Task**

- T13.4
- T13.5
- T13.6

**达成目标**

将证据、模型、集成、权限、界面、Tool 和验收场景连接为无断点的双向追踪链。

**输入**

- T13.2 至 T13.6 的全部产出。
- 工作包 08 的 Agent Tool 与运行时事件协议。
- 工作包 09 的产品页面与 Renderer 契约。

**执行步骤**

1. 为每个稳定 ID 建立“证据→模型→策略→MI→Tool/页面→验收场景”矩阵行。
2. 为列表查询、详情查询、草稿应用和条件性的简单命令编写可重放场景。
3. 在每个场景中固定身份、权限、输入、模型版本、预期事件、预期 UI 结果和审计关联 ID。
4. 编写自动检查，发现孤立证据、无证据模型、悬空引用或无验收场景能力时失败。
5. 保存一次完整检查结果作为基线。

**产出物**

- `docs/specification/masterdata/reference-slice-traceability.csv`
- `docs/specification/masterdata/reference-slice-scenarios.md`
- `tools/validation/check-reference-slice-traceability.*`
- `docs/specification/masterdata/validation/traceability-validation.txt`

**验证方式**

- 运行追踪检查脚本，退出码必须为 0。
- 从任一 M2、M7 或 MU 稳定 ID 出发，能正向定位到验收场景并反向定位到证据。
- 矩阵中不得出现空的必填链路；明确不适用的单元格必须填写理由。

### [ ] T13.8 执行一致性评审并封存参考基线

**前置 Task**

- T13.7

**达成目标**

由跨工作包负责人确认参考切片在术语、稳定 ID、权限、安全、查询、执行和界面行为上内部一致，并形成可供工作包 14、15 使用的冻结基线。

**输入**

- T13.1 至 T13.7 的全部产出与验证记录。
- 工作包 03、05、06、07、09、12 的最终决策和 ADR。

**执行步骤**

1. 召集模型、身份/权限、MI、查询、HITL、产品和审计负责人进行逐项评审。
2. 检查同一稳定 ID、状态名、风险级别、协议字段和错误码在所有文件中的含义是否一致。
3. 将问题分为阻断、需修正、开放项；关闭全部阻断和需修正问题。
4. 重新运行证据、模型、策略和追踪验证。
5. 记录基线版本、文件清单、校验摘要和后续变更触发 `REVIEW_REQUIRED` 的条件。

**产出物**

- `docs/specification/masterdata/reference-slice-review.md`
- `docs/specification/masterdata/reference-slice-manifest.yaml`
- `docs/specification/masterdata/validation/final-validation.txt`

**验证方式**

- 评审记录包含各责任域结论、问题处理状态和签署人。
- manifest 中列出的文件均存在，摘要与实际内容一致。
- 最终验证全部通过，且不存在未关闭的阻断或需修正问题。

## 工作包验收

- 已选择且只选择一个参考 MasterData 对象，范围、排除项和开放项明确。
- 证据包通过 Schema 校验，关键结论可定位到源码符号、视图或正式决策。
- M1、M3、M5、M7、MU、M2、MI 样例通过模型与跨引用校验，稳定 ID 无冲突。
- 至少包含受限列表查询、详情查询和原 DPA 表单草稿应用三个可重放场景。
- 简单命令已有证据化准入或拒绝结论；若准入，HITL、权限、幂等和审计负向测试全部通过。
- 至少一个 MU 由 UI 证据提取管线生成并通过零代码渲染验证；若简单命令获准入，可重放场景包含完整 L2 全链路。
- 端到端追踪矩阵不存在悬空引用、无来源能力或无验收场景能力。
- 跨工作包一致性评审完成，参考基线可被工作包 14 和 15 直接引用。

## 解决记录

工作包关闭时填写，至少包含：

- 最终选择的参考对象、稳定 ID 和选择理由。
- 基线 manifest 路径与版本。
- 各 Task 产出物链接和验证命令/结果摘要。
- 简单命令的准入或拒绝结论。
- 已关闭问题、保留开放项、责任人和目标解决时间。
- 与前置工作包结论的任何偏差及对应 ADR。
