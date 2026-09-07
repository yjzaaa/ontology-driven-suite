# DPA Ontology Platform — Domain Language

## DPA Ontology Studio

用于审核源码证据，并将证据提升为有版本的业务对象、行为、规则、权限、查询、展现和集成映射的治理工作台。

## Runtime Workbench

已发布本体面向业务用户的投影，包括 Agent 对话、对象视图、查询结果、行为提案、执行状态和原 DPA 页面入口。

## Ontology Gateway

解析已发布语义、执行策略、创建行为提案，并将批准后的操作委托给内部执行器的运行时服务。

## Evidence

从 DPA 代码、接口行为、UI 绑定、配置或数据库访问中发现的事实、推断或假设。Evidence 本身不授予运行时执行权。

## Published Ontology

经过验证、审核和版本发布，作为运行时唯一语义来源的一组 YAML 模型。

## Business Object

具有业务身份、属性、生命周期和关系的领域概念。Business Object 不自动等同于数据库表、Entity 或 DTO。

## Behavior

针对业务对象或领域产生稳定业务结果的能力，与实现它的 DPA Endpoint 相互独立。

## Rule

用于判断条件或派生结果的可复用业务约束。Rule 不直接执行状态修改。

## Integration（MI）

将已发布 Behavior 或 Query 连接到现有 DPA API、受治理 Database MCP 能力或其他批准执行器的防腐契约，简称 MI。全称采用 Integration，避免 “Integration Mapping / MI 集成” 冗余（TERM-002）。

## Action Proposal

针对特定目标和已验证参数提出的不可变行为请求，绑定风险、影响、本体版本和 MI 版本。

## Draft Application

将已验证建议值应用到原 DPA 表单但不持久化。用户仍需执行原 DPA 保存动作。

## Runtime Projection

由已发布本体生成的 Agent Tool、对象视图、查询结果、行为卡片、流程、状态或关系图，不是新的业务事实来源。

## Legacy View

为复杂编辑、工作流或页面专有行为保留的原 DPA 页面。

## Renderer

由已发布 Presentation 选择，用于显示对象、集合、图表、关系、Proposal、Execution 或 Legacy View 链接的受信任 UI 组件。
