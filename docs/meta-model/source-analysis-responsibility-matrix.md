# 源码分析组件与人员责任（T02.9 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.9 产出。
> 任务：明确“谁执行扫描、谁解释技术事实、谁裁决业务语义、谁批准发布”，避免把 DPA 源码分析误解为由 Agent/LLM 自主完成。
> 前置：T02.1–T02.8。

## 1. 组件责任

| 组件 | 责任 | 不负责 |
|---|---|---|
| codebase-memory MCP | 源码图谱、符号搜索、调用链、数据流、变化分析的首选引擎 | 不生成可发布本体、不执行 DPA 代码 |
| Python Evidence Adapter | 查询编排、证据规范化、稳定 ID、revision 绑定、快照、覆盖率对账 | 不裁决业务语义 |
| C#/.NET Roslyn extractor | 仅对 fixture 证明的缺口（路由/分派/副作用）做窄范围补证 | 不重复实现完整代码图 |
| LLM / Agent | 辅助候选模型整理、编写报告、组织审核 | 不生成 `FACT`、不替代人工裁决、不直接发布 |

## 2. 人员责任矩阵

| 角色 | 责任 |
|---|---|
| 平台工程（主 Agent / 开发者） | 执行扫描、编排查询、生成候选、维护 Adapter/extractor |
| DPA 技术负责人 | 复核调用链、权限、事务、SQL、Job、副作用等**技术事实** |
| 领域专家 / 本体审核员 | 裁决业务对象、行为、规则、流程、术语等**业务语义** |
| 安全与数据负责人 | 复核身份、敏感字段、数据范围和高风险能力 |
| 本体发布审批人 | 决定候选模型是否进入 `PUBLISHED` |

## 3. 工作流

```text
扫描（平台工程/codebase-memory+Adapter）
  → 证据（FACT/INFERENCE/ASSUMPTION，T02.2 信封）
  → 技术复核（DPA 技术负责人：调用链/权限/SQL/Job/副作用）
  → 业务裁决（领域专家：对象/行为/规则/术语）
  → 安全复核（安全负责人：身份/敏感字段/高风险）
  → 候选 YAML（.build/candidates/，LLM 可辅助整理）
  → 发布审批（发布审批人 → PUBLISHED）
```

- 人工审核不手工改写原始机器证据，只追加裁决和修正记录（T02.8）。
- DPA 技术负责人不单独决定业务本体语义，本体审核员也不单独确认代码副作用（交叉制衡）。
- Agent/LLM 输出只能进入候选区，无法直接写入 `evidence/snapshots/` 的事实记录或 `models/<domain>/` 的发布模型。

## 4. 桌面走查（一条 MasterData 调用链）

以 `UpdateSubtableData` 调用链为例：

| 步骤 | 动作 | 责任角色 |
|---|---|---|
| 1 | 索引并定位 Controller/Dll/Service 符号 | 平台工程（codebase-memory） |
| 2 | 展开调用链，生成 FACT/INFERENCE 证据 | 平台工程（Adapter） |
| 3 | 复核写库/缓存/日志副作用与 `MIXED/HIGH` | DPA 技术负责人 |
| 4 | 裁决“更新子表数据”是否为 M2 行为语义 | 领域专家 |
| 5 | 复核凭据/身份处理与高风险能力 | 安全与数据负责人 |
| 6 | 候选 YAML 审核并发布 | 发布审批人 |

每个扫描、解释、修正、审核和发布动作都有唯一责任角色。

## 5. 可追溯性

- 任一自动结论都能指出 codebase-memory 索引版本、查询模板和适配器版本；Roslyn 补证还必须记录 extractor 版本（`extractor` 字段，T02.2）。
- Agent/LLM 输出只能进入候选区，无法直接写入 `evidence/snapshots/` 的事实记录或 `models/<domain>/` 的发布模型。

## 6. 边界

- 人工审核不手工改写原始机器证据，只追加裁决和修正记录。
- DPA 技术负责人不单独决定业务本体语义，本体审核员也不单独确认代码副作用。

## 7. 验证记录

- 对一条 MasterData 调用链执行桌面走查，每个扫描、解释、修正、审核和发布动作都有唯一责任角色（§4）。
- 任一自动结论都能指出 codebase-memory 索引版本、查询模板和适配器版本；Roslyn 补证还记录 extractor 版本。
- Agent/LLM 输出只能进入候选区，无法直接写入 `evidence/snapshots/` 的事实记录或 `models/<domain>/` 的发布模型。
- 命令：`git diff --check` 应通过。
