# codebase-reverse 包装 Skill 适配说明（T02.10 产出）

> 本文件是 Wayfinder 工作包 [02-specify-reverse-engineering-evidence-pipeline](../wayfinder/tickets/02-specify-reverse-engineering-evidence-pipeline.md) 的 T02.10 产出。
> 说明通用 `D:\sharptoolbox\codebase-reverse` 到 DPA 专用 Skill（`skills/dpa-codebase-reverse/`）的适配边界，不复制通用引用文档。

## 1. 复用与包装边界

| 内容 | 处理 |
|---|---|
| 通用方法论（全量资产盘点、功能穿透、数据库逆向、证据分级、覆盖率） | 复用，引用上游 `references/*.md` |
| 通用规则全文 | **不复制**到本仓库；通过引用升级 |
| Java/Spring 偏好识别规则 | 映射为 ASP.NET MVC / Roslyn / EF / Dapper 规则（见 REFERENCE.md §4） |
| Markdown 元模型输出 | 补充映射为 `evidence/snapshots/<revision>/` 机器证据 + `.build/candidates/` 候选 YAML |

## 2. 包装 Skill 组成

- `skills/dpa-codebase-reverse/SKILL.md`：触发条件、入口、阶段、门禁、非协商规则（保持简洁）。
- `skills/dpa-codebase-reverse/REFERENCE.md`：唯一一层细节（输入参数、阶段产出、规则映射、调用链、验证）。
- `skills/dpa-codebase-reverse/EXAMPLES.md`：示例提示词与最小 ASP.NET MVC fixture。
- `skills/dpa-codebase-reverse/scripts/validate-dpa-reverse.ps1`：静态校验（Schema、稳定 ID、MIXED/HIGH 标注）。

## 3. 编排关系

```text
dpa-codebase-reverse Skill
  ├─ 资产盘点（T02.1）
  ├─ codebase-memory MCP 主引擎（T02.3）
  ├─ 定向 Roslyn extractor（T02.3，缺口补证）
  ├─ Evidence Adapter 规范化（T02.2）
  ├─ 快照与覆盖率（T02.6）
  ├─ 人工门禁（T02.8/02.9）
  └─ 候选输出到 .build/candidates/（不发布）
```

- Skill 不直接把 LLM 推断写成 `FACT`；推断只进入候选或审核队列。
- Skill 不发布本体、不注册 Agent Tool、不调用 DPA 写接口。

## 4. 升级策略

- 上游 `codebase-reverse` 更新时，包装层通过引用与版本记录升级，不需要手工合并整套复制文档。
- REFERENCE.md 记录上游路径与使用的 references 清单，便于版本对应。

## 5. 验证记录

- `scripts/validate-dpa-reverse.ps1` 已运行通过（exit=0）：Schema 校验、稳定 ID 无日期污染、MIXED/HIGH 标注全部通过。
- Skill 描述可由“DPA 源码逆向、Controller 到数据库穿透、MasterData 反向建模、混合副作用分析”等请求触发。
- 上游 `codebase-reverse` 存在且结构完整（`SKILL.md`/`references/`/`scripts/validate_meta_model.ps1`/`agents/openai.yaml`）。
- 命令：`git diff --check` 应通过。
