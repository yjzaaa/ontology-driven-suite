# Evidence

本目录保存 DPA 扫描产生的机器可读证据。证据按 DPA revision 固化，不得在原快照上就地改写。

建议布局：

```text
snapshots/<revision>/
  manifest.json
  source-assets.jsonl
  controllers.jsonl
  call-graph.jsonl
  permissions.jsonl
  data-access.jsonl
  state-transitions.jsonl
  ui-bindings.jsonl
```

证据只描述 `FACT`、`INFERENCE` 或 `ASSUMPTION`，不授予 Agent 或 Gateway 执行权。
