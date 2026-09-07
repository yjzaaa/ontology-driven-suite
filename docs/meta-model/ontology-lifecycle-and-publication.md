# 本体生命周期、发布校验与不可变性（T03.7 产出）

> 本文件是 Wayfinder 工作包 [03-define-ontology-contracts-and-lifecycle](../wayfinder/tickets/03-define-ontology-contracts-and-lifecycle.md) 的 T03.7 产出。
> 前置：T03.6。

## 1. 生命周期状态机

```text
GENERATED → REVIEW_REQUIRED → APPROVED → PUBLISHED → DEPRECATED → WITHDRAWN
   │             │               │
   └─────────────┴───────────────┘ (任意阶段可回到 GENERATED/REVIEW_REQUIRED 修正)
```

合法迁移（仅允许）：

| from | to |
|---|---|
| GENERATED | REVIEW_REQUIRED |
| REVIEW_REQUIRED | GENERATED（修正）/ APPROVED |
| APPROVED | REVIEW_REQUIRED（复审）/ PUBLISHED |
| PUBLISHED | DEPRECATED / WITHDRAWN |
| DEPRECATED | WITHDRAWN |

禁止：从 `GENERATED`/`REVIEW_REQUIRED` 直接 `PUBLISHED`（跳过审核与门禁）；从失败状态直接发布；`PUBLISHED` 原位修改。

## 2. 发布校验顺序

1. 证据有效性（`evidence_refs` 全部存在且未失效，T02.7）。
2. Schema 校验（八类模型 Schema + envelope）。
3. 引用闭包（T03.6：REF_MISSING/REF_TYPE_MISMATCH/REF_CYCLE/REF_VERSION_UNRESOLVED/REF_WITHDRAWN）。
4. 兼容性（相对已发布版本，major/minor/patch）。
5. 风险门禁（`MIXED/HIGH`、`UNKNOWN` 必须已人工审核，T02.8）。
6. 人工审核记录存在（T02.8/T02.9）。

任一步失败阻断发布，返回稳定错误码。

## 3. 原子发布与不可变性

- 发布集合：一个 `publication-manifest` 声明一组模型版本，整体发布（全部成功或全部回滚）。
- 版本锁：manifest 锁定每个 `model_id@version` 与内容摘要（sha256）。
- `PUBLISHED` 内容不可原位修改；任何语义变化必须生成新版本。
- 已发布 YAML 被篡改 → 内容摘要校验失败，标记 `TAMPERED` 并阻断 Runtime Registry 加载。

## 4. Schema 与样例

- Schema：`schemas/ontology/publication-manifest.schema.json`。
- 样例：`models/examples/masterdata/publication-manifest.yaml`（成功发布）、`publication-failures.yaml`（校验失败场景）。

## 5. 验证记录

- 状态机覆盖所有允许迁移，拒绝跳过审核、从失败状态直接发布等非法迁移。
- 发布失败场景分别验证 Schema、证据、引用闭包、兼容性和风险门禁能够阻断。
- 修改已发布 YAML 后内容摘要校验失败；合法修订使用新版本和新 manifest。
- 原子发布保证同一集合不会部分发布。
- 命令：`git diff --check` 应通过。
