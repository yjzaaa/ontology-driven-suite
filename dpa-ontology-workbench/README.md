# DPA Ontology Studio & Runtime Workbench

本项目规划并实现一个独立的 DPA 本体平台，同时自主实现 Agent Runtime 与 Agent UI，并以 MasterData 作为首个纵向试点。

平台不会替代 DPA。DPA 继续负责复杂业务表单、业务服务、工作流、最终授权和持久化；本项目负责从源码证据中建立可审核的业务本体，并将已发布本体投影为 Agent 能力、业务对象视图、受控查询、行为提案、HITL、审计和影响分析。

## 技术语言基线

- **codebase-memory MCP + Python Evidence Adapter**：作为 DPA 源码图谱、调用链、搜索和变更分析主路径。
- **C#/.NET + Roslyn**：只补充 MCP 无法可靠提取的 ASP.NET/DPA 专有语义，不预先建设完整扫描器。
- **Python + LangGraph + FastAPI/Pydantic**：独立 Agent Runtime、语义 Tool Gateway、Registry、Policy、HITL、MI 和审计服务。
- **TypeScript + React**：独立 Agent UI、Ontology Studio、Runtime Workbench、Ontology Explorer 和受信任 Renderer。
- **YAML + JSON Schema**：本体模型、稳定契约、样例和发布校验。
- **PowerShell**：Windows 开发和部署辅助脚本；不承载业务逻辑。

语言之间只通过版本化 API、事件和 Schema 交互，不共享内部领域对象。具体运行时版本、包管理器和基础设施组件由 Wayfinder 技术选型 Task 通过 PoC 固化。

## 当前阶段

当前处于 Wayfinder 规划阶段。规划终点是形成一份无需继续做重大架构决策即可实施的技术规格；在地图完成前，不实现生产功能。

规范入口：

- [Agent 开发规范](AGENTS.md)
- [领域词汇表](CONTEXT.md)
- [限界上下文地图](CONTEXT-MAP.md)
- [Wayfinder 地图](docs/wayfinder/map.md)
- [Wayfinder 当前 frontier](docs/wayfinder/README.md)
- [文档规范](docs/AGENTS.md)

## 规划中的项目边界

```text
evidence/              DPA 扫描产生的机器可读证据，不授予执行权
models/                经审核发布的本体 YAML，运行时唯一语义来源
tools/                 Scanner、候选生成、模型校验、变更检测
gateway/               Registry、Policy、HITL、MI 与受控执行
agent-ui/              独立 Agent UI、会话交互与受信任 Renderer
ontology-explorer/     本体、证据、数据流与影响分析可视化
docs/                  架构、决策、反向工程报告和 Wayfinder 地图
```

## 参考项目

- `D:\sharptoolbox\ontology-driven-dev`
- `D:\sharptoolbox\Onto-Contract`
- `D:\sharptoolbox\codebase-reverse`
- `D:\sharptoolbox\mobile-manufacturing-togaf`
- `D:\sharptoolbox\visual-model`

这些仓库仅作为方法、模型和视觉表达参考；本项目不复制它们的示例技术底座。
