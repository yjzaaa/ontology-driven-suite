---
name: dpa-codebase-reverse
description: "DPA 专用源码逆向与证据流水线编排 Skill。将通用 codebase-reverse 方法（功能穿透、数据库逆向、证据分级、覆盖率校验）包装为 ASP.NET MVC / DPA 定制工作流，统一编排 codebase-memory MCP、Python Evidence Adapter 和定向 Roslyn extractor，输出证据快照与候选 YAML。使用场景：DPA 源码逆向、Controller 到数据库穿透、MasterData 反向建模、SubtableType 追踪、混合副作用分析、证据快照与覆盖率。上游通用 Skill 位于 D:\\sharptoolbox\\codebase-reverse，本 Skill 只做包装不复制其全部引用文档。"
---

# DPA 专用源码逆向 Skill

本 Skill 把通用 `D:\sharptoolbox\codebase-reverse` 方法包装为 DPA（ASP.NET MVC / EF / Dapper / Redis）定制工作流，统一编排 codebase-memory MCP、Evidence Adapter 与定向 Roslyn extractor，并把结果转换为本项目统一的证据契约与候选模型。

## Read First

1. `REFERENCE.md`：本 Skill 的规则、阶段、产出、人工门禁与失败规则（唯一一层细节）。
2. 上游通用方法（不复制）：`D:\sharptoolbox\codebase-reverse\references\*.md`（全量资产盘点、功能穿透、数据库逆向、证据分级、覆盖率校验）。
3. 本项目规范：`AGENTS.md`、`docs/wayfinder/map.md`、`docs/wayfinder/masterdata-scope.md`。
4. 证据契约：`docs/meta-model/evidence-contract.md`、`schemas/evidence/evidence-record.schema.json`。

## 触发条件

以下请求应稳定触发本 Skill：

- “DPA 源码逆向 / Controller 到数据库穿透 / MasterData 反向建模 / 混合副作用分析”
- “SubtableType 追踪 / 证据快照 / 覆盖率 / 增量变更影响”

## 阶段（详见 REFERENCE.md）

1. **资产盘点**：登记资产清单与扫描边界（T02.1）。
2. **证据提取**：codebase-memory MCP 主引擎 + 定向 Roslyn 补证（路由/分派/副作用）。
3. **证据规范化**：转换为 `evidence-record.schema.json` 信封（FACT/INFERENCE/ASSUMPTION）。
4. **快照与覆盖率**：生成 `evidence/snapshots/<revision>/` + 分层覆盖率。
5. **人工门禁**：高风险/动态/混合副作用路由到人工审核（T02.8）。
6. **候选输出**：仅写入 `.build/candidates/`，不发布、不注册 Tool、不调用 DPA 写接口。

## 非协商规则

1. 不使用本 Skill 生成 `FACT`；LLM 推断只能进入候选或审核队列。
2. 不把 Spring/MyBatis 等上游 Java 偏好当作 DPA 事实；替换为 ASP.NET MVC/Roslyn/EF/Dapper 规则。
3. 不直接发布本体、不注册 Agent Tool、不调用 DPA 写接口。
4. 无法证明纯读的接口按 `MIXED/HIGH`，禁止自动执行。
5. 相同输入重复执行产生稳定证据 ID；扫描只读，不加载或执行 DPA 业务代码。

## 入口

- 参数、输出目录、验证命令见 `REFERENCE.md`。
- 静态校验：`scripts/validate-dpa-reverse.ps1`。
- 示例：`EXAMPLES.md`。
