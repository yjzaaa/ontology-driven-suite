# codebase-memory Evidence Adapter

本模块把 codebase-memory MCP 的代码图、符号、调用链、数据流、架构聚类和变更影响结果转换为本项目统一的证据契约。

## 定位

- codebase-memory MCP 是 DPA 源码分析的首选引擎。
- Evidence Adapter 负责查询编排、结果规范化、稳定 ID、revision 绑定、证据快照和覆盖率对账。
- C#/.NET Roslyn extractor 只补充经过 fixture 证明的能力缺口，不重复实现完整代码图。

## 责任（T02.9）

- 负责查询编排、证据规范化、稳定 ID、revision 绑定、快照和覆盖率对账（见 [docs/meta-model/source-analysis-responsibility-matrix.md](../../docs/meta-model/source-analysis-responsibility-matrix.md)）。
- 证据契约见 [docs/meta-model/evidence-contract.md](../../docs/meta-model/evidence-contract.md)，Schema 见 `schemas/evidence/evidence-record.schema.json`。
- 提取规范见 [docs/meta-model/codebase-memory-extraction.md](../../docs/meta-model/codebase-memory-extraction.md) 与 [codebase-memory-gap-analysis.md](../../docs/meta-model/codebase-memory-gap-analysis.md)。
- Agent/LLM 只能辅助候选模型整理，不得生成 `FACT`、替代人工裁决或直接发布（见 [source-analysis-review-workflow.md](../../docs/meta-model/source-analysis-review-workflow.md)）。

## 已确认可用能力

- 索引 C#、JavaScript、HTML、CSS 和 SQL 等项目资产。
- 搜索类、方法、变量和 Route。
- 查询调用图和跨层关系。
- 追踪 callers、callees、数据流和跨服务路径。
- 获取具体符号源码片段。
- 检测代码变化及其影响范围。
- 输出架构包、聚类和依赖概览。

## 必须补齐的治理能力

- 将 MCP 节点和边转换为项目 Evidence Schema。
- 绑定 DPA revision、查询模板版本和适配器版本。
- 过滤误识别 Route、第三方前端库和生成文件噪声。
- 为每条结论标记 `FACT`、`INFERENCE`、`ASSUMPTION`。
- 记录查询参数、分页完整性、截断和覆盖率分母。
- 将动态 SQL、反射、运行时路由和未知副作用转入人工审核。

## 不负责内容

- 不直接生成可发布本体。
- 不执行 DPA 业务代码或写数据库。
- 不把图谱推断自动升级为业务事实。
- 不向 Agent 注册 DPA 技术端点。
- 不让 MCP 的内部图结构成为运行时本体事实源。
