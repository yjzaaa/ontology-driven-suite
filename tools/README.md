# 工具边界

本目录计划包含 codebase-memory Evidence Adapter、定向 Roslyn extractor、候选模型生成器、模型验证器和源码变化检测器。

工具生成证据和候选模型，不直接发布模型，也不调用生产 DPA 写接口。

DPA 源码分析优先使用 [codebase-memory Evidence Adapter](codebase-memory-adapter/README.md)。当前 `D:\WorkSpace` 索引已经覆盖 1,755 个 C# 文件并提供调用图、符号搜索、数据流和变化影响能力，因此不预先自研完整 Scanner。

只有通过最小 fixture 证明 codebase-memory MCP 存在确定性缺口时，才新增窄范围 C#/.NET Roslyn extractor，例如 DPA 自定义权限 Filter、动态路由或特殊 ORM 映射。所有来源最终进入同一 Evidence Schema。

`D:\sharptoolbox\codebase-reverse` 已经符合标准 Skill 目录结构，可作为通用逆向工程方法和流程入口。DPA 项目不直接修改其通用规则，而是在本仓库提供薄包装 Skill：

- 复用其全量资产盘点、功能穿透、数据库逆向、证据分级和覆盖率校验方法。
- 将 Java/Spring 偏好的识别规则替换为 ASP.NET MVC、codebase-memory 图查询和 DPA 专有规则。
- 将 Markdown 元模型输出补充映射为 `evidence/snapshots/<revision>/` 的机器证据。
- 通过 Evidence Adapter 获取机器事实，不允许 LLM 自行把源码猜测写成 `FACT`。
- 候选结果只写入 `.build/candidates/`，不得直接发布或获得执行权。
