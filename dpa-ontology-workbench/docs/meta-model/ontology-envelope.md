# 本体模型通用信封（T03.1 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.1 产出。
> 任务：为八类模型建立统一顶层信封，固定身份、领域、版本、证据、状态和审计字段。
> 前置：T01（`domain-language.md`、`model-boundary-matrix.md`）、T02（`evidence-contract.md`、`evidence-record.schema.json`）。

## 1. 公共字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `model_id` | string | 是 | 稳定 ID，规则见 §2 |
| `model_type` | enum | 是 | `M1`/`M2`/`M3`/`M5`/`M6`/`M7`/`MU`/`MI` |
| `domain` | string | 是 | 领域（`masterdata`） |
| `name` | object | 是 | `{ zh, en }` 显示名 |
| `version` | string | 是 | 语义版本 `major.minor.patch` |
| `status` | enum | 是 | `GENERATED`/`REVIEW_REQUIRED`/`APPROVED`/`PUBLISHED`/`DEPRECATED`/`WITHDRAWN` |
| `evidence_refs` | string[] | 条件 | 引用 T02 证据稳定 ID；`PUBLISHED` 必填 |
| `created_at` | datetime | 是 | 创建时间 |
| `created_by` | string | 是 | 创建者/角色 |
| `schema_version` | string | 是 | 本 Schema 版本（如 `3.0.0`） |

## 2. 稳定 ID 与版本规则

- `model_id`：`{domain}.{model_type}.{slug}`，`slug` 为 ASCII 短名（如 `masterdata.m1.subtable-type`）。
- 显示名使用中文；稳定 ID 使用 ASCII（`AGENTS.md` YAML 纪律）。
- 语义版本：major（不兼容）/ minor（向后兼容新增）/ patch（无行为变化修正）。
- 同一 `model_id` 的不同版本并存；引用默认同 major 内最新兼容版。

## 3. 证据引用规则

- `evidence_refs` 只能引用符合 T02 证据契约的稳定 ID（`ev:/route:/db:/job:/ui:` 前缀）。
- `FACT` 是发布的最低可接受证据；`INFERENCE`/`ASSUMPTION` 引用的模型必须处于 `REVIEW_REQUIRED`，且不阻断人工审核（T02.8）。
- 无证据来源的结论不得写入模型。

## 4. 扩展与规范化

- 未知字段策略：`additionalProperties: false`——未知字段不被静默忽略（`AGENTS.md`）。
- 空值：语义必需字段不得为 null；可选字段省略而非置 null。
- 排序：数组字段（`evidence_refs`、引用列表）按稳定 ID 字典序排序；格式化不改变语义顺序。
- 规范化输出：同一模型内容不因 YAML 键顺序变化而改变身份；`model_id`+`version` 是唯一身份。

## 5. 验证记录

- 有效样例通过 `schemas/ontology/model-envelope.schema.json`；无效样例因预期字段或约束失败。
- 相同模型内容规范化后产生稳定结果，不因 YAML 键顺序变化而改变身份。
- `evidence_refs` 只能引用符合 T02 证据契约的稳定 ID。
- 命令：`git diff --check` 应通过。
