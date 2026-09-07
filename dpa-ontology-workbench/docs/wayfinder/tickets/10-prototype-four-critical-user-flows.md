---
title: 制作四条关键用户路径原型
status: open
labels:
  - wayfinder:prototype
parent: ../map.md
assignee:
blocked_by:
  - 09-define-product-surfaces-and-rendering.md
---

## 工作包目标

制作并验证四条可交互低保真用户路径，使本体审核员、业务查询用户、行为审批人和 DPA 表单操作员能够理解系统边界、完成关键任务并识别风险。原型只用于验证交互、协议投影和跨角色交接，不实现生产功能，不模拟绕过 DPA 最终授权或保存动作的能力。

四条必测路径为：

1. 审核反向工程产生的候选本体；
2. 查询并检查 MasterData 业务对象；
3. 审核并批准 Action Proposal；
4. 将已校验草稿应用到原 DPA 表单。

## 必需 Task

### [ ] T10.1 制定原型测试计划

**达成目标**

定义测试对象、角色、场景、任务成功标准和证据采集方法，使四条路径能够按同一套方法重复验证。

**输入**

- `docs/wayfinder/tickets/09-define-product-surfaces-and-rendering.md`
- `docs/wayfinder/map.md` 中已确认的产品与安全边界
- 四条关键用户路径及其预期角色

**执行步骤**

1. 为每条路径定义主要角色、前置状态、触发入口、核心任务和结束状态。
2. 为每个任务定义可观察的成功、失败和放弃判定，不以主观“看起来可用”作为结论。
3. 设计主持脚本、受试者说明、记录表和问题严重度分级。
4. 明确原型数据均为虚构数据，禁止录入真实凭据、个人信息或生产业务数据。
5. 定义至少一次跨角色走查和一次修订后复测的安排。

**产出物**

- `docs/prototypes/critical-flows/test-plan.md`
- `docs/prototypes/critical-flows/session-record-template.md`

**验证方式**

由未参与编写的评审者仅依据测试计划，逐条复述四条路径的角色、起止条件、成功判定和证据位置；复述结果全部一致，且模板能够记录完成时间、错误点、严重度和观察证据。

### [ ] T10.2 制作候选本体审核原型

**前置 Task**

- T10.1

**达成目标**

验证审核员能从源码证据进入候选模型，区分事实、推断和待确认项，并对候选本体作出接受、退回或请求补证决定。

**输入**

- 工作包 02、03 定义的证据与本体生命周期契约
- 工作包 09 定义的 Ontology Studio 与 Ontology Explorer 边界
- 一组包含稳定 ID、证据引用、差异和校验结果的虚构候选本体数据

**执行步骤**

1. 制作候选列表、候选详情、证据定位、模型差异和校验结果页面。
2. 展示候选版本与已发布版本的字段、关系、规则和证据变化。
3. 为无法确认的推断提供“请求补证”，为不合格候选提供带原因的“退回”。
4. 明确候选 YAML 不具有运行执行权，审核动作不得直接发布模型。
5. 按 T10.1 脚本记录审核员寻找证据、理解差异和提交决定的过程。

**产出物**

- `docs/prototypes/critical-flows/ontology-candidate-review/`
- `docs/prototypes/critical-flows/ontology-candidate-review/findings.md`

**验证方式**

使用固定测试数据重复执行一次接受、一次退回和一次请求补证；每次均能从决定追踪到候选稳定 ID、版本、差异项和源码证据，且界面中不存在“候选即发布”或“候选可执行”的歧义。

### [ ] T10.3 制作 MasterData 查询与对象检查原型

**前置 Task**

- T10.1

**达成目标**

验证业务用户能用受治理查询查找 MasterData 对象，理解查询范围、结果截断、字段权限和对象关系，并能返回可审计的查询上下文。

**输入**

- 工作包 06、08、09 定义的查询、Tool、事件和 Renderer 契约
- MasterData 虚构对象、集合、关系和权限裁剪样例

**执行步骤**

1. 制作查询输入、条件确认、执行状态、结果集合和对象详情页面。
2. 展示生效的数据范围、过滤条件、排序、分页或结果上限。
3. 对不可见字段、被裁剪行、空结果、超限和查询失败给出可区分反馈。
4. 展示对象稳定 ID、来源、关系和 Legacy View 链接，不暴露 SQL、内部 DTO 或任意 URL。
5. 按固定查询集记录用户定位对象、解释结果和进入对象详情的过程。

**产出物**

- `docs/prototypes/critical-flows/masterdata-query/`
- `docs/prototypes/critical-flows/masterdata-query/query-cases.yaml`
- `docs/prototypes/critical-flows/masterdata-query/findings.md`

**验证方式**

用同一组查询案例执行正常、空结果、权限裁剪和超限场景；原型显示与 `query-cases.yaml` 的预期一致，用户能够说明当前数据范围与限制，且无法从界面构造任意 SQL 或越权查询。

### [ ] T10.4 制作行为提案审核原型

**前置 Task**

- T10.1

**达成目标**

验证审批人能理解 Action Proposal 的意图、目标对象、拟议变更、风险、有效期和执行方式，并在信息不足时拒绝批准。

**输入**

- 工作包 07、08、09 定义的 Action Proposal、HITL、状态和渲染契约
- 包含低风险草稿应用、需人工批准和 `REVIEW_REQUIRED` 的虚构提案

**执行步骤**

1. 制作提案列表、提案详情、影响预览、审批确认和状态反馈页面。
2. 明确展示提案稳定 ID、目标对象、变更前后值、风险、依据、有效期和执行通道。
3. 对批准、拒绝、取消、过期、已消费和并发变化提供不同状态反馈。
4. 对 `REVIEW_REQUIRED` 明确禁止自动执行，并要求审批人完成显式确认。
5. 记录审批人是否能在不查看技术 URL、HTTP Method 或内部 DTO 的情况下作出决定。

**产出物**

- `docs/prototypes/critical-flows/action-proposal-review/`
- `docs/prototypes/critical-flows/action-proposal-review/state-cases.yaml`
- `docs/prototypes/critical-flows/action-proposal-review/findings.md`

**验证方式**

逐一回放 `state-cases.yaml` 中的批准、拒绝、过期、重复消费和 `REVIEW_REQUIRED` 场景；原型不得把批准误表示为业务写入成功，且所有决定都能关联到提案稳定 ID 和状态变化。

### [ ] T10.5 制作草稿应用到 DPA 表单的原型

**前置 Task**

- T10.1
- T10.4

**达成目标**

验证用户能将已校验草稿安全地带入原 DPA 表单，确认字段映射和冲突，并明确由 DPA 原保存动作完成最终提交。

**输入**

- 工作包 05、07、08、09 定义的 MI、草稿应用、事件和 Legacy View 边界
- 虚构的草稿、字段映射、校验错误、版本冲突和会话失效案例

**执行步骤**

1. 制作草稿摘要、字段映射预览、校验结果和“应用到 DPA 表单”入口。
2. 展示未映射字段、只读字段、格式错误和源对象版本变化。
3. 设计同源跳转或嵌入交接状态，明确会话失效和 DPA 拒绝时的恢复路径。
4. 在 DPA 表单侧标识草稿已填充但尚未保存，保留用户修改和取消能力。
5. 验证平台不直接持久化业务写入，也不把表单填充结果表示为保存成功。

**产出物**

- `docs/prototypes/critical-flows/dpa-draft-application/`
- `docs/prototypes/critical-flows/dpa-draft-application/handoff-cases.yaml`
- `docs/prototypes/critical-flows/dpa-draft-application/findings.md`

**验证方式**

重复执行正常应用、字段校验失败、对象版本冲突、会话失效和用户取消场景；每个场景均能回到明确状态，只有原 DPA 保存动作可产生“已提交”结果。

### [ ] T10.6 执行跨角色端到端走查

**前置 Task**

- T10.2
- T10.3
- T10.4
- T10.5

**达成目标**

验证四条路径之间的术语、状态、稳定 ID 和角色交接一致，发现单路径测试无法暴露的上下文断裂。

**输入**

- 四套可交互原型及测试发现
- T10.1 测试计划
- 工作包 08、09 的稳定协议与产品边界

**执行步骤**

1. 组织本体审核员、业务查询用户、行为审批人和 DPA 表单操作员角色走查。
2. 从候选审核开始，连续走查已发布语义的查询、行为提案审核和草稿应用。
3. 核对同一业务对象、模型版本、提案和草稿的稳定 ID 是否跨页面保持一致。
4. 记录角色切换、返回路径、错误恢复、权限变化和状态刷新中的断点。
5. 将问题按阻断、严重、一般、建议分级，并指定对应原型和责任 Task。

**产出物**

- `docs/prototypes/critical-flows/cross-role-walkthrough.md`
- `docs/prototypes/critical-flows/issues.yaml`

**验证方式**

依据 `cross-role-walkthrough.md` 从头复演一次完整链路；所有页面引用的稳定 ID、状态名称和角色责任一致，`issues.yaml` 中每个问题均包含复现步骤、证据、严重度和归属。

### [ ] T10.7 完成修订与原型验收

**前置 Task**

- T10.6

**达成目标**

修复阻断性和严重问题，复测关键场景，并形成可供工作包 14、15 使用的可用性结论和残余风险。

**输入**

- `docs/prototypes/critical-flows/issues.yaml`
- 各路径 `findings.md`
- 四套原型及跨角色走查记录

**执行步骤**

1. 修订所有阻断和严重问题对应的交互、文案、状态或导航。
2. 对每项修订记录问题 ID、修改位置、预期行为和复测结果。
3. 使用原测试数据复测四条路径及跨角色链路。
4. 汇总已解决问题、接受的残余风险和需要后续工作包处理的事项。
5. 冻结验收版本并记录原型版本标识。

**产出物**

- `docs/prototypes/critical-flows/acceptance-report.md`
- `docs/prototypes/critical-flows/issues.yaml` 的最终状态
- 四套通过验收的版本化原型

**验证方式**

阻断和严重问题全部关闭；四条路径的固定测试案例全部通过；验收报告能够从测试结论追踪到场景、问题 ID、修订位置和复测证据。

## 工作包验收

- 四条关键路径均有可交互低保真原型、固定测试数据、测试发现和重复执行说明。
- 原型明确区分候选与已发布模型、提案批准与执行成功、草稿填充与 DPA 最终保存。
- 正常、空结果、权限裁剪、校验失败、过期、重复消费、冲突和会话失效等关键状态均被覆盖。
- 跨角色走查中的稳定 ID、术语、状态和责任边界与前置工作包一致。
- 所有阻断和严重可用性问题均已修订并复测，残余风险有明确归属。
- `docs/prototypes/critical-flows/acceptance-report.md` 可直接作为工作包 14 的人工验收输入和工作包 15 的产品交互依据。

## 解决记录

> 工作包关闭时填写，只记录最终结论、关键取舍、验证结果和资产链接。

- 最终结论：待完成。
- 关键取舍：待完成。
- 验证结果：待完成。
- 资产链接：待完成。
