# 独立 Agent UI

本目录用于自主实现 Runtime Workbench 的对话界面、会话交互、运行时事件消费和受信任 Renderer。

Agent UI 只通过本项目定义的稳定语义 Tool/API 与 Agent Runtime 和 Ontology Gateway 通信，不依赖或复用 InsightBot 的源码、运行时、会话协议、组件或部署。

Runtime Workbench 不复制 DPA 复杂表单。复杂编辑通过受控 Legacy View 回到原 DPA 页面。
