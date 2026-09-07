# 跨模型引用闭包与版本兼容（T03.6 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.6 产出。
> 前置：T03.2–T03.5。

## 1. 引用格式

| 形式 | 语法 | 说明 |
|---|---|---|
| 同领域同版本 | `masterdata.m1.subtable-type` | 引用同发布集合内最新兼容版 |
| 显式版本 | `masterdata.m2.update-subtable-data@1.2.0` | 锁定版本 |
| 版本范围 | `masterdata.m7.list-subtable-data@^1.0` | major 内兼容 |

## 2. 引用目标类型矩阵

| 源模型 | 允许引用目标 |
|---|---|
| M1 | M1（关系）、M7（查询） |
| M2 | M1、M3、M5 |
| M3 | M1、M2 |
| M5 | M1、M2、M7、M6 |
| M6 | M2、M3、M5 |
| M7 | M1、M5、MU |
| MU | M1、M2、M7 |
| MI | M2、M7 |

禁止循环：引用图必须是有向无环图（DAG）；任一环路阻断发布。

## 3. 引用闭包解析与失败行为

- 解析：从根模型沿引用边展开，得到唯一封闭集合；同 `model_id` 不同版本可共存，但发布集合内版本必须解析唯一。
- 失败行为（稳定错误码）：
  - `REF_MISSING`：目标 `model_id` 不存在。
  - `REF_TYPE_MISMATCH`：目标类型不在允许矩阵。
  - `REF_CYCLE`：检测到引用环。
  - `REF_VERSION_UNRESOLVED`：版本范围无解或目标已撤回。
  - `REF_WITHDRAWN`：引用已 `WITHDRAWN` 版本。

## 4. 兼容性分类

| 变化类型 | 判定 |
|---|---|
| 新增可选字段/属性 | minor（向后兼容） |
| 新增必填字段 | major（不兼容，旧实例缺字段失败） |
| 枚举值新增 | minor；移除枚举值 major |
| 约束收紧（BLOCK 更严格） | major |
| 行为副作用变化（READ→MIXED） | major |
| 修复拼写/说明文字 | patch |
| 删除模型或改 `model_id` | major（或新增模型） |

## 5. Schema 与样例

- Schema：`schemas/ontology/reference.schema.json`。
- 样例：`models/examples/masterdata/reference-closure/`（完整闭包）、`models/examples/masterdata/incompatible-change/`（不兼容升级）。

## 6. 验证记录

- 完整样例能解析出唯一、封闭的模型集合。
- 悬空引用、目标类型错误、禁止循环和版本范围无解均产生稳定错误码并阻断发布。
- 兼容性表能对样例中的每项变化给出唯一 major/minor/patch 或禁止结论。
- 命令：`git diff --check` 应通过。
