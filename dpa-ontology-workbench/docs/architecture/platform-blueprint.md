# 本体平台蓝图：从「写死 Python」到「声明式 + 标准底座」

> 状态：设计提案（DRAFT）——跨五轮讨论收敛的技术方向，未纳入 ADR、未进入生产。
> 关联：`docs/architecture/declarative-action-schema.md`、`docs/architecture/progressive-ddd.md`、`ontology-explorer/`、`gateway/`。

---

## 0. 一句话定位

本体 YAML 是**唯一真相源**；表单负责**结构化录入**，图谱负责**可视化理解**，MCP 是**唯一 Agent 协议**，ActionEngine 是**唯一运行时底座**。异构系统接入统一声明进 **MI（集成模型）**，由标准协议 adapter 动态执行。

---

## 1. 分层总览

```
┌──────────────────────────────────────────────────────────────────────┐
│ 入口层（治理工作台）                                                   │
│   Ontology Studio 表单 ──结构化填写──► ① 本体 YAML（业务语义 + 证据）   │
│                                     ② MI YAML（异构集成契约）         │
├──────────────────────────────────────────────────────────────────────┤
│ 投影层（可视化，只读，不成为第二事实源）                               │
│   Visual Model 图谱：树 / 矩阵 / 拓扑 / 影响分析 / 证据溯源            │
│        ▲  从 registry 动态生成                                        │
├────────┼──────────────────────────────────────────────────────────────┤
│ 运行时底座                                                             │
│   ModelRegistry 动态加载 + fail-closed 校验（引用闭包 / Schema / 封闭词表）│
│        │                                                               │
│        ├──► 查询工具 ──► MCP tools/list                                │
│        └──► 写回 Action ──► ActionEngine ──► MI adapter ──► 异构系统   │
├──────────────────────────────────────────────────────────────────────┤
│ 交互层                                                                 │
│   任意 MCP 客户端 ──MCP（唯一协议，官方 SDK）──► Agent                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. 三层本体，三种治理（不可混为一谈）

| 层 | 内容 | 治理者 | 状态 |
|---|------|--------|------|
| ① 业务本体（M1/M2/M3/M5/M6/M7/MU） | 业务语义：对象/行为/规则/生命周期 | 业务人 + 证据锚定 | 表单录入 |
| ② 集成契约（MI） | 异构系统接入：executor/协议/认证/参数映射/错误 | 集成工程师 + 协议 adapter 库 | 表单录入，独立于① |
| ③ 运行时投影 | Agent 工具 / 查询 / 写回 | 引擎 | 动态生成，零手写 |

**红线（项目边界 #3）**：URL、HTTP Method、凭据、Header、DTO 映射只存在于 MI；业务本体不接触技术接口。否则本体会退化成技术映射表。

---

## 3. 可视化图谱（Visual Model 前端）

### 3.1 三种视图，各司其职

| 视图 | 回答的问题 | 建议技术 |
|------|-----------|---------|
| 树状图 | 由什么组成 / 属于谁（对象→子实体→字段、上下文→对象） | ECharts `tree` / 缩进列表 |
| 矩阵图 | 谁耦合谁 / 哪里空着（对象×对象、角色×权限、行为×规则、对象×MI） | ECharts `heatmap` / 自绘表格 |
| 拓扑图 | 怎么流转 / 改了谁连带谁（引用网、数据流、状态机、证据链） | Cytoscape.js |

### 3.2 两个核心视图（Palantir 图谱的灵魂）

**影响分析**（利用已有引用闭包反推）：
```python
def impact_of(registry, object_id) -> list:
    return [m for m in registry.all_models() if object_id in registry.refs_of(m)]
# 改 tax_rate 字段 → 波及 3 查询、2 规则、1 写回 MI
```

**证据溯源**（边界 #7 的可视化）：
```yaml
evidence_refs: ["ev:WS:ce9ad5ca:...Controller.cs:UpdateSubtableData"]
                                              └── 点它 → 跳源码 #行
```

### 3.3 纪律（已存在 `ontology-explorer/generate-ontology-view.py` 并已守住）

> YAML 是事实源，图谱是 registry 生成的**只读投影**；第一阶段不允许图形编辑绕过 YAML Diff 与模型校验。

### 3.4 开源选型参考（结构化图编辑器，非自由白板）

**区分两类「画布」**：自由白板（tldraw / Excalidraw / Fabric.js / Konva）适合画草图，不适合有 schema 的本体图；本体图谱需要**结构化图编辑器**（节点有类型、边有语义、可回写）。

| 视图 | 首选 | 备选 |
|------|------|------|
| 拓扑/关系网 | **AntV G6**（或 React 封装 Graphin） | Cytoscape.js、Sigma.js |
| 树状图 | G6 TreeGraph / ECharts tree | D3 hierarchy |
| 矩阵图 | ECharts heatmap / 自绘表格 | — |
| 画布编辑（阶段二） | **AntV X6** / React Flow（已有经验） | JointJS |

**交互范式参照**（非库）：Neo4j Bloom（点节点下钻/路径高亮/联动面板）、Palantir Ontology Graph（点对象→右侧视图→点 Action→写回）。

**落地节奏**：阶段一只读投影（G6 渲染，点节点→下钻/证据/影响）；阶段二受控编辑（X6 画布，落盘仍走 YAML Diff + Schema 校验，YAML 恒为真相源）。

---

## 4. 集成契约（MI）：异构系统如何声明

### 4.1 有限标准协议 adapter 库（不逐系统发明协议）

| executor | 协议 | adapter |
|----------|------|---------|
| `HTTP` | REST/JSON（同源 Cookie / Bearer / mTLS） | HttpWriteAdapter（已有 DPA_HTTP） |
| `MCP` | Model Context Protocol | 直连 MCP Server（零适配） |
| `SQL_RO` | 关系库只读 | DatabaseMcp（已有 DATABASE_MCP） |
| `GRAPHQL` | GraphQL | GraphQLAdapter |
| `MSG` | 消息队列（异步写回） | 队列 Adapter |

### 4.2 MI 声明（运行时动态读取，新增写回 = 只改 YAML）

```yaml
- id: mi_pr_doc_update_status
  executor: DPA_HTTP
  effect: WRITE
  method: POST
  url_path: /MasterData/.../UpdateSubtableDataList
  auth_mode: same_origin_cookie
  retries: 0
  param_mapping: { ActiveStatu: "{input.active_status}", ... }  # 待升级 JMESPath
  error_mapping: { 401: DPA_SESSION_EXPIRED, ... }
  dpa_evidence: { symbol: "...Controller.UpdateSubtableDataList(...)", file: "...cs#665" }
```

通用适配器 `DpaHttpWriteAdapter.execute(mi, arguments, cookie)` 动态读 `mi[...]`，零业务知识。

---

## 5. Agent 交互层：唯一协议 MCP

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("dpa-ontology-gateway")
for action_id, action in registry.actions.items():
    InputModel = pydantic_from_json_schema(action["input_schema"])
    mcp.add_tool(make_handler(action_id), name=..., description=...)
```

- `input_schema` 一份声明三处复用：MCP tool 参数 / pydantic 校验 / 引擎输入。
- HITL 用 MCP elicit 或 confirm 两段式承载；授权恒在网关侧。
- LangGraph 降级为「可选的多步工作流实现」，非必选。

---

## 6. 写链路：声明式 Action（详见 declarative-action-schema.md）

`target`（对象+定位）+ `input_schema`（typed 输入）+ `effects`（JMESPath 组合）+ `rules`（结构化 when-then）+ `writeback`（显式声明写回/补偿）+ `approval`（HITL），由通用 `ActionEngine` 解释执行。

---

## 7. 待实现清单（其余底座已具备）

| # | 待实现 | 现状 |
|---|-------|------|
| 1 | Ontology Studio 表单（结构化录入本体 + MI + 挂证据） | 待建 |
| 2 | Visual Model 前端（树/矩阵/拓扑/影响分析/证据溯源） | 树+图已雏形，矩阵/拓扑/影响待补 |
| 3 | 有限标准协议 adapter 库（HTTP/GRAPHQL/MSG） | DPA_HTTP + DATABASE_MCP 已有 |
| 4 | 声明式 Action 迁移（typed input + JMESPath + 结构化规则） | 设计已定，待落样板 |
| 5 | MCP Server 化（官方 SDK 注册语义工具） | 待建 |

**已有底座**：ModelRegistry 动态加载 + fail-closed 校验、MCP 交互雏形、提案/HITL/writeback 链（`mvp_server.py`）、只读可视化投影（`ontology-explorer`）。