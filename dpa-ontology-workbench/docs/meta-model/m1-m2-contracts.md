# M1 Object 与 M2 Behavior 契约（T03.2 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.2 产出。
> 前置：T03.1（`model-envelope.schema.json`）、T01.3、T01.4。

## 1. M1 Object 契约要点

- 表达业务身份、属性、生命周期、关系；**不得**承载表/DTO 映射、URL、HTTP Method、SQL、凭据。
- 字段（在 envelope 之外）：`attributes[]`、`relations[]`、`lifecycle[]`、`identity_fields`。
- `identity_fields`：构成业务身份的字段；不等于物理主键（T01.3 CASE-02/03）。

## 2. M2 Behavior 契约要点

- 表达业务结果能力；**不得**承载 URL、HTTP Method、凭据或内部请求 DTO。
- 字段：`target_object`（引用 M1）、`semantic_inputs`、`semantic_outputs`、`preconditions`（引用 M3）、`side_effect`（`READ`/`WRITE`/`MIXED`）、`risk`（`LOW`/`MEDIUM`/`HIGH`）。
- `MIXED/HIGH` 行为禁止自动执行，必须人工审核（T01.4 CASE-05/11）。

## 3. Schema 与样例

- Schema：`schemas/ontology/m1-object.schema.json`、`schemas/ontology/m2-behavior.schema.json`。
- 样例：`models/examples/masterdata/m1-object.yaml`（`SubtableType` 候选）、`m2-behavior.yaml`（`update-subtable-data`）。

## 4. 校验负向规则

- 把表名/DTO 映射放入 M1 → 校验失败（`additionalProperties: false` + 类型约束）。
- 把 URL/HTTP Method 放入 M2 → 校验失败。
- M2 引用的目标 M1/M3/M5 使用稳定 `model_id`（引用语法见 T03.6）。

## 5. 验证记录

- 两个 MasterData 样例分别通过对应 Schema。
- 表名/DTO 放入 M1、URL/HTTP Method 放入 M2 时校验失败。
- M2 引用使用稳定 `model_id`。
- 命令：`git diff --check` 应通过。
