# 源码分析审核工作流（T02.9 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.9 产出。
> 定义源码证据从扫描到发布的审核流程、状态与角色门禁，与 [source-analysis-responsibility-matrix.md](source-analysis-responsibility-matrix.md) 配套。

## 1. 审核阶段

| 阶段 | 输入 | 动作 | 输出 | 责任角色 |
|---|---|---|---|---|
| 扫描 | 资产清单（T02.1） | codebase-memory + 定向 Roslyn 提取 | 证据记录（T02.2 信封） | 平台工程 |
| 技术复核 | 证据记录 | 复核调用链/权限/SQL/Job/副作用 | 复核结论 | DPA 技术负责人 |
| 业务裁决 | 技术复核通过的证据 | 裁决对象/行为/规则/流程/术语 | 业务语义结论 | 领域本体审核员 |
| 安全复核 | 高风险证据 | 复核身份/敏感字段/数据范围 | 安全结论 | 安全与数据负责人 |
| 候选整理 | 各复核结论 | LLM 辅助生成候选 YAML | `.build/candidates/` | 平台工程 + LLM |
| 发布审批 | 候选 YAML | 校验 Schema/引用/证据/兼容性 | `PUBLISHED` | 发布审批人 |

## 2. 状态与门禁

- 每一阶段必须前一阶段结论存在才能进入；`MIXED/HIGH`、动态、证据不足的结论在任何阶段都不得升级为已确认事实（T02.8）。
- 候选 YAML 只有通过全部复核才能进入发布审批；未发布前不进入 Runtime Registry（边界 8）。
- Agent/LLM 输出只能进入候选区，无法直接写入 `evidence/snapshots/` 的事实记录或 `models/<domain>/` 的发布模型。

## 3. 审核项状态机

- `pending` → `accepted` / `corrected` / `rejected` → `reopened`（T02.8 §2）。
- 修正不覆盖原始证据，只追加 `decision` 记录。

## 4. 人工与自动分工

- 自动：扫描、调用边解析、静态符号/路由（Roslyn 补证）、覆盖率计算、变更失效闭包。
- 人工：技术事实复核、业务语义裁决、安全接受、发布授权。
- LLM 仅辅助候选整理与报告，不生成 `FACT`、不替代人工裁决、不直接发布。

## 5. 验证记录

- 每个审核阶段有唯一责任角色和门禁；桌面走查 `UpdateSubtableData` 链每个动作都有角色（见责任矩阵 §4）。
- 任何阶段都不允许把自动结论无门禁地升为事实或发布。
- 命令：`git diff --check` 应通过。
