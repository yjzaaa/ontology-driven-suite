---
title: 定义本体契约、校验与发布生命周期
status: closed
labels:
  - wayfinder:grilling
parent: ../map.md
assignee: copilot-agent
blocked_by:
  - 01-define-domain-language-and-model-boundaries.md
  - 02-specify-reverse-engineering-evidence-pipeline.md
---

## 工作包目标

定义 M1 Object、M2 Behavior、M3 Rule、M5 Actor/Permission、M6 Flow、M7 Query、MU Presentation、MI Integration 的可机器校验契约，以及跨模型引用、版本兼容、生命周期和发布门禁。候选模型只有在证据、引用闭包和兼容性校验全部通过并完成人工审核后才能成为不可变的已发布 YAML。

## 必需 Task

### [x] T03.1 定义通用模型信封与证据引用

**达成目标**

为八类模型建立统一顶层信封，固定身份、领域、版本、证据、状态和审计字段，避免各模型重复发明公共协议。

**输入**

- `docs/meta-model/domain-language.md`
- `docs/meta-model/model-boundary-matrix.md`
- `docs/meta-model/evidence-contract.md`
- `schemas/evidence/evidence-record.schema.json`

**执行步骤**

1. 定义公共字段，至少包含 `model_id`、`model_type`、`domain`、`name`、`version`、`status`、`evidence_refs`、`created_at`、`created_by` 和 `schema_version`。
2. 规定稳定 `model_id`、语义版本、显示名称及领域命名规则。
3. 定义 `FACT`、`INFERENCE`、`ASSUMPTION` 如何被模型引用，以及最低证据要求。
4. 规定扩展字段、未知字段、空值、排序和规范化输出规则。

**产出物**

- `docs/meta-model/ontology-envelope.md`
- `schemas/ontology/model-envelope.schema.json`
- `models/examples/common/valid-envelope.yaml`
- `models/examples/common/invalid-envelope.yaml`

**验证方式**

- 有效样例通过 Schema 校验，无效样例因预期字段或约束失败。
- 相同模型内容规范化后产生稳定结果，不因 YAML 键顺序变化而改变身份。
- `evidence_refs` 只能引用符合 T02 证据契约的稳定 ID，不能嵌入无来源结论。

### [x] T03.2 定义 M1 Object 与 M2 Behavior 契约

**前置 Task**

- T03.1

**达成目标**

形成业务对象和业务行为的独立 Schema，明确身份、属性、输入输出、前置条件和副作用边界。

**输入**

- `docs/meta-model/object-data-shape-boundaries.md`
- `docs/meta-model/behavior-rule-execution-boundaries.md`
- `schemas/ontology/model-envelope.schema.json`

**执行步骤**

1. 为 M1 定义业务身份、属性、值类型、必填性、枚举、关系和生命周期引用。
2. 为 M2 定义目标对象、语义输入输出、前置条件、结果、失败语义和副作用分类。
3. 明确 M1 不承载表/DTO 映射，M2 不承载 URL、HTTP Method、凭据或内部请求 DTO。
4. 为 MasterData 各编写一组有效和无效样例。

**产出物**

- `schemas/ontology/m1-object.schema.json`
- `schemas/ontology/m2-behavior.schema.json`
- `docs/meta-model/m1-m2-contracts.md`
- `models/examples/masterdata/m1-object.yaml`
- `models/examples/masterdata/m2-behavior.yaml`

**验证方式**

- 两个 MasterData 样例分别通过对应 Schema。
- 把表名/DTO 映射放入 M1 或把 URL/HTTP Method 放入 M2 时，校验必须失败。
- M2 引用的目标 M1、规则或权限均使用稳定 `model_id`。

### [x] T03.3 定义 M3 Rule 与 M5 Actor/Permission 契约

**前置 Task**

- T03.1

**达成目标**

形成可解释的业务规则和参与者/权限 Schema，区分业务规则、输入校验、身份事实及 DPA 最终授权。

**输入**

- `docs/meta-model/model-boundary-matrix.md`
- `docs/meta-model/behavior-rule-execution-boundaries.md`
- `schemas/ontology/model-envelope.schema.json`

**执行步骤**

1. 为 M3 定义适用对象、条件、结果、严重级别、解释文本和证据。
2. 为 M5 定义 actor、permission、scope、适用行为/查询及授权来源。
3. 规定可声明的授权语义与 DPA 运行时最终裁决之间的边界。
4. 为业务规则、纯格式校验、权限允许和权限未知分别编写样例。

**产出物**

- `schemas/ontology/m3-rule.schema.json`
- `schemas/ontology/m5-actor-permission.schema.json`
- `docs/meta-model/m3-m5-contracts.md`
- `models/examples/masterdata/m3-rule.yaml`
- `models/examples/masterdata/m5-actor-permission.yaml`

**验证方式**

- 有效样例通过对应 Schema，纯 UI 格式校验不会被错误建模为 M3。
- M5 样例不得包含凭据、token 或绕过 DPA 授权的声明。
- 权限来源不明的样例保持候选或审核状态，不能发布为确定权限。

### [x] T03.4 定义 M6 Flow 与 M7 Query 契约

**前置 Task**

- T03.1
- T03.2
- T03.3

**达成目标**

形成流程和受治理查询 Schema，表达状态迁移、参与行为、查询语义、数据范围和限制，而不泄漏任意执行细节。

**输入**

- M1、M2、M3、M5 Schema
- `docs/meta-model/model-boundary-matrix.md`
- T02 的调用链、状态转换和数据库证据

**执行步骤**

1. 为 M6 定义状态、迁移、触发行为、守卫规则、参与权限和终止状态。
2. 为 M7 定义目标对象、语义参数、返回形状、过滤能力、排序、分页、行列范围和限制。
3. 规定循环、不可达状态、无终点流程、无界查询和任意 SQL 的拒绝条件。
4. 为 MasterData 状态流和列表查询编写有效及无效样例。

**产出物**

- `schemas/ontology/m6-flow.schema.json`
- `schemas/ontology/m7-query.schema.json`
- `docs/meta-model/m6-m7-contracts.md`
- `models/examples/masterdata/m6-flow.yaml`
- `models/examples/masterdata/m7-query.yaml`

**验证方式**

- M6 样例的每个迁移都引用存在的状态、M2、M3/M5；不可达引用校验失败。
- M7 样例不包含任意 SQL、数据库凭据或物理 DTO 映射。
- 无分页/上限的集合查询或越过声明数据范围的查询不能通过发布级校验。

### [x] T03.5 定义 MU Presentation 与 MI Integration 契约

**前置 Task**

- T03.1
- T03.2
- T03.4

**达成目标**

形成展示投影和技术集成映射 Schema，保持业务语义与 DPA endpoint、Database MCP、DTO 映射等技术细节隔离。

**输入**

- M1、M2、M7 Schema
- `docs/meta-model/runtime-concept-boundaries.md`
- T02 的 UI、route、数据库和副作用证据

**执行步骤**

1. 为 MU 定义绑定对象/查询、视图结构、字段展示、交互意图和 Legacy View 回退。
2. 为 MI 定义所绑定的 M2/M7、endpoint 或只读 Database MCP 能力、请求响应映射、固定/禁止参数和证据。
3. 定义副作用等级、超时、重试、幂等、错误归一化和凭据来源字段。
4. 为受信任 Renderer、Legacy View、纯读查询和 `MIXED/HIGH` 行为分别编写样例。

**产出物**

- `schemas/ontology/mu-presentation.schema.json`
- `schemas/ontology/mi-integration.schema.json`
- `docs/meta-model/mu-mi-contracts.md`
- `models/examples/masterdata/mu-presentation.yaml`
- `models/examples/masterdata/mi-integration.yaml`

**验证方式**

- MU 只能引用已声明的 M1/M2/M7 字段和意图，不成为新的业务事实源。
- MI 中凭据只描述来源或转发策略，不包含真实值；Database MCP 映射只能声明只读能力。
- `MIXED/HIGH` 或无法证明纯读的样例必须要求人工审核，不能声明自动执行。

### [x] T03.6 定义跨模型引用闭包与版本兼容

**前置 Task**

- T03.2
- T03.3
- T03.4
- T03.5

**达成目标**

规定模型引用语法、解析范围、闭包完整性、循环规则和兼容性判定，使一个发布集合可以被确定性装载。

**输入**

- 八类模型 Schema 和 MasterData 样例
- `docs/meta-model/ontology-envelope.md`

**执行步骤**

1. 定义同领域、跨领域、同版本和版本范围引用格式。
2. 建立各模型允许引用的目标类型矩阵及禁止循环规则。
3. 定义引用闭包解析、缺失引用、类型不匹配、版本冲突和已撤回版本的失败行为。
4. 规定 major/minor/patch 变更规则，以及字段、枚举、约束、行为和查询变化的兼容性分类。
5. 编写完整闭包、悬空引用、循环引用和不兼容升级样例。

**产出物**

- `docs/meta-model/ontology-reference-and-versioning.md`
- `schemas/ontology/reference.schema.json`
- `models/examples/masterdata/reference-closure/`
- `models/examples/masterdata/incompatible-change/`

**验证方式**

- 完整样例能解析出唯一、封闭的模型集合。
- 悬空引用、目标类型错误、禁止循环和版本范围无解均产生稳定错误码并阻断发布。
- 兼容性表能对样例中的每项变化给出唯一的 major/minor/patch 或禁止结论。

### [x] T03.7 定义生命周期、发布校验与不可变性

**前置 Task**

- T03.6

**达成目标**

定义候选模型从生成、审核到发布、弃用和撤回的状态机，以及发布前校验顺序、原子性和已发布版本不可变规则。

**输入**

- 八类模型 Schema
- `docs/meta-model/ontology-reference-and-versioning.md`
- T02 的证据快照、覆盖率和人工审核契约

**执行步骤**

1. 定义 `GENERATED`、`REVIEW_REQUIRED`、`APPROVED`、`PUBLISHED`、`DEPRECATED`、`WITHDRAWN` 等状态及合法迁移。
2. 规定证据有效性、Schema、引用闭包、兼容性、风险和人工审核的发布校验顺序。
3. 定义发布集合、版本锁、内容摘要、签署记录、原子发布和失败回滚。
4. 规定 `PUBLISHED` 内容不可原位修改；任何语义变化必须生成新版本。
5. 编写成功发布、校验失败、并发发布和已发布文件被篡改的场景。

**产出物**

- `docs/meta-model/ontology-lifecycle-and-publication.md`
- `schemas/ontology/publication-manifest.schema.json`
- `models/examples/masterdata/publication-manifest.yaml`
- `models/examples/masterdata/publication-failures.yaml`

**验证方式**

- 状态机测试覆盖所有允许迁移，并拒绝跳过审核、从失败状态直接发布等非法迁移。
- 发布失败场景分别验证 Schema、证据、引用闭包、兼容性和风险门禁能够阻断。
- 修改已发布 YAML 后，内容摘要校验失败；合法修订必须使用新版本和新 manifest。
- 原子发布场景保证同一集合不会出现部分模型已发布、部分模型未发布。

## 工作包验收

- T03.1 至 T03.7 全部完成，通用信封和八类模型均有独立 Schema、说明文档及 MasterData 样例。
- 所有有效样例通过 Schema、证据、引用闭包和兼容性校验；所有无效样例以预期错误码失败。
- 任一发布集合都能解析为唯一引用闭包，并能追溯到证据快照、审核记录、模型版本和 publication manifest。
- 生命周期不能绕过人工审核或风险门禁，`PUBLISHED` 内容不可原位修改。
- `models/<domain>/` 下已发布 YAML 明确为运行时语义唯一事实源，候选、证据和报告不具有运行执行权。

## 解决记录

**决策摘要**：建立八类本体模型（M1/M2/M3/M5/M6/M7/MU/MI）的可机器校验契约与发布生命周期。统一信封固定 model_id/model_type/domain/version/status/evidence_refs 等公共字段；八类模型各有独立 Schema；定义引用闭包（DAG、稳定错误码）与版本兼容分类（major/minor/patch）；定义 GENERATED→REVIEW_REQUIRED→APPROVED→PUBLISHED→DEPRECATED→WITHDRAWN 状态机、发布校验顺序与 PUBLISHED 不可变性。

**关键取舍**：envelope 不设置 additionalProperties，由具体模型 Schema 用 unevaluatedProperties:false 收口（支持扩展 + 拒绝未知字段）；M7 分页必填；MI 的 database-mcp-readonly 强制 side_effect=READ；M2 的 MIXED 强制 risk=HIGH；M6 状态成员校验归引用闭包（T03.6）而非 Schema。

**验证结果**：8 类模型 MasterData 样例全部通过对应 Schema；负向用例（表名进 M1、URL 进 M2、raw SQL、无分页、M5 带凭据、MCP 只读+WRITE）全部被拒；引用闭包样例可解析唯一封闭集合；publication-manifest 摘要与篡改检测通过；`git diff --check` 通过。

**产出物**：11 份 `schemas/ontology/*.schema.json`、8 份 `models/examples/masterdata/*.yaml` + reference-closure/ + incompatible-change/ + publication 样例、7 份 `docs/meta-model/*-contracts.md`/envelope/reference/lifecycle 文档。

**遗留项**：MasterData 样例均为 `REVIEW_REQUIRED` 候选（TERM-013 SubtableType 归属仍待证据快照）；正式发布需人工审核（T02.9 责任矩阵）后再进入 `models/masterdata/`。
