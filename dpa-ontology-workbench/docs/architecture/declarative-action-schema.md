# 声明式 Action Schema 设计提案（对齐 Palantir Action Type + WriteBack）

> 状态：设计提案（DRAFT）——未纳入 ADR，未进入 Wayfinder「已确认边界」，不构成生产实现依据。
> 目标读者：DPA 技术负责人、后续接手 Agent Runtime 的交付团队。
> 关联：`gateway/mvp_server.py`、`gateway/agent/runtime.py`、`gateway/execution/write_adapters.py`、`gateway/approval/proposal_store.py`。

---

## 1. 问题诊断：写链路为什么「写死 Python」

现有 MVP 已经跑通「提案 → 派生校验 → 写适配器」，但**写行为的语义被压平成了字符串，于是每一环都配了一个手写解释器**。四个确凿的弱类型点（均出自现有代码）：

| # | 弱类型点 | 现有实现（手写解释器） | 应有的形态 |
|---|---------|---------------------|-----------|
| 1 | M2 输入是「字符串列表」`semantic_inputs` | LLM 只能吐 `"参数名=值；参数名=值"`，再 `_parse_inputs` 手动 `split(";")` + `split("=")` | typed JSON Schema，LLM `structured_output` 直接产出对象 |
| 2 | 步骤协议是硬编码枚举 `("search"/"lookup"/"propose")` | LangGraph 图里写死三种 `kind` | 由 Action 声明的步骤驱动，图不再硬编码 |
| 3 | M3 条件是「中文自然语言」`condition: subtable_type 不在禁止更新列表中` | `_when_matches` / `_apply_derivations` / `_run_validation_rules` 手写封闭词表解释器 | 结构化约束（JSON Schema / when-then），通用求值器解释 |
| 4 | MI 参数映射是「字符串模板」`{target.xxx}` | `re.findall(r"\{...\}")` + `_dig` 点路径 + `re.sub` 渲染 | JMESPath 声明式映射 |

**结论**：问题不在「要不要给写操作」（Palantir 证明必须给），而在于**写操作（Action）没有被声明化**——Palantir 的 Action Type 本质是「写语义的 Schema 化」，而我们现在把这份 Schema 写成了散落的字符串 + Python 解释器。

---

## 2. 设计目标

把「写行为」从「散落字符串 + 手写解释器」收敛为「一份可校验、可回写、可补偿的声明式 Action 模型」，运行时交给一个**通用 ActionEngine** 解释执行：

1. **typed input**：Action 的输入参数用 JSON Schema 声明，LLM 结构化输出直接绑定，服务端强校验。
2. **declarative effects**：字段变更/参数映射用 JMESPath 声明，删除 `_dig` + 正则。
3. **structured rules**：M3 规则结构性落地为 when-then 约束，删除手写解释器（沿袭现有 fail-fast 封闭词表思路）。
4. **declared writeback**：显式声明写回底层系统的路径/时机/幂等/补偿，对齐 Palantir WriteBack，复用现有 adapter 模式（LocalJson / DpaHttp）。
5. **stable HITL**：审批仍是独立聚合（Proposal/Approval/Execution），引擎只产出 Proposal，授权恒在网关侧。

---

## 3. 核心设计：M2 write 升级为「声明式 Action」

不新增模型编号（保持八模型体系稳定），而是**增强 M2 的 write 行为**，新增一组必填声明字段。完整的 Action 声明如下：

```yaml
# 一个「受治理写语义」的完整声明（对齐 Palantir Action Type）
model_id: masterdata.m2.update-subtable-data
model_type: M2
domain: masterdata
name: { zh: 更新子表数据, en: Update Subtable Data }
version: 1.0.0
status: PUBLISHED
evidence_refs: [ "ev:WS:ce9ad5ca:...UpdateSubtableData" ]

# ── target：目标对象 + 定位方式（替代散落的 target_locator）──────────
target:
  object: masterdata.m1.subtable-type
  locator:                      # 写前定位（先查后写），可有可无
    query_ref: masterdata.m7.list-subtable-data
    key_field: record_id

# ── input_schema：typed 输入（替代 semantic_inputs 字符串列表）══════
input_schema:
  type: object
  additionalProperties: false
  properties:
    record_id: { type: string, description: 目标记录 ID }
    field_values:
      type: object
      description: 待更新的字段映射（字段名→新值）
      additionalProperties: true
  required: [record_id, field_values]

# ── effects：声明式字段变更（替代 MI param_mapping 正则）═════════════
effects:
  # 构造发往 DPA 的请求体；JMESPath 表达式，源数据域固定为 input / target
  compose:
    dpa_payload:
      id: "input.record_id"
      updates: "input.field_values"

# ── rules：结构化前置校验/派生（替代中文 condition + 手写解释器）══════
rules:
  - ref: masterdata.m3.allow-update-rule      # 引用 M3（M3 已结构化，见 §5.5）

# ── writeback：显式声明写回（对齐 Palantir WriteBack）════════════════
writeback:
  via: masterdata.mi.update-subtable           # 绑定 MI（防腐层）
  timing: on-approval                          # 审批通过后写回
  idempotency: request-id-header                # 幂等策略
  compensation:
    ref: masterdata.m2.restore-subtable-data   # 失败补偿动作引用（可空）

# ── approval：HITL 声明（替代散落 risk/requires_approval）────────────
approval:
  required: true
  risk: HIGH
  side_effect: MIXED
  token: single-use
```

对应新增的 JSON Schema（`schemas/ontology/action.schema.json` 摘要）：

```json
{
  "$id": "https://dpa-ontology-workbench/schemas/ontology/action.schema.json",
  "title": "Declarative Action (M2 write contract)",
  "type": "object",
  "required": ["target", "input_schema", "writeback", "approval"],
  "properties": {
    "target": {
      "type": "object",
      "required": ["object"],
      "properties": {
        "object": { "$ref": "reference.schema.json#/$defs/modelRef" },
        "locator": {
          "type": "object",
          "properties": {
            "query_ref": { "type": "string" },
            "key_field": { "type": "string" }
          }
        }
      }
    },
    "input_schema": { "$ref": "https://json-schema.org/draft/2020-12/schema" },
    "effects": {
      "type": "object",
      "properties": {
        "compose": { "type": "object", "additionalProperties": { "type": "string" } }
      }
    },
    "writeback": {
      "type": "object",
      "required": ["via", "timing"],
      "properties": {
        "via": { "type": "string" },
        "timing": { "enum": ["on-approval", "deferred", "manual"] },
        "idempotency": { "type": "string" },
        "compensation": { "type": "object" }
      }
    },
    "approval": {
      "type": "object",
      "required": ["required", "risk"],
      "properties": {
        "required": { "type": "boolean" },
        "risk": { "enum": ["LOW", "MEDIUM", "HIGH"] },
        "side_effect": { "enum": ["PURE_READ", "MIXED", "WRITE"] }
      }
    }
  }
}
```

---

## 4. 逐点改造对照

| 现有（手写） | 改造后（声明式 + 通用引擎） |
|------------|--------------------------|
| `semantic_inputs: [subtable_type, record_id, field_values]` | `input_schema: {type: object, properties: {...}}` |
| `_parse_inputs("active_status=Inactive")` | `pydantic` 按 `input_schema` 自动校验，LLM `with_structured_output(Model)` |
| `steps = ("propose", obj, ref, params)` 硬编码元组 | Action 的 `target.locator` + `effects` 驱动执行步骤，图只做 `plan → act → hltl` |
| `_when_matches` / `_apply_derivations` / `_run_validation_rules` | 通用规则求值器解释结构化 M3（`when: {field, equals}` / `derivation.cases`） |
| `re.findall(r"\{...\}")` + `_dig` 点路径 | `jmespath`：`effects.compose.dpa_payload.id = "input.record_id"` |
| `MI.param_mapping` + 启动时正则挖占位符校验 | `effects.compose` + JMESPath，启动时校验表达式引用的字段闭包 |

---

## 5. 代码说明

以下均为「示意代码」，用于说明设计如何落地成引擎，不构成生产实现。

### 5.1 typed input：JSON Schema → pydantic → LLM structured output

替代 `runtime.py` 里的 `Plan(inputs="参数名=值；...")` 字符串：

```python
# gateway/agent/typed_input.py（示意）
from pydantic import BaseModel, create_model

def input_model_from_schema(action: dict) -> type[BaseModel]:
    """从 Action.input_schema 动态生成输入模型，不再用字符串协议。"""
    schema = action["input_schema"]
    # 依赖 datamodel-code-generator 或 pydantic 的 JSON Schema 生成器
    # 此处示意：直接把 schema 交给 pydantic 校验（pydantic v2 支持 JSON Schema）
    return schema  # 实际工程中返回 pydantic 模型类，强类型

def plan_with_typed_input(message: str, action: dict, llm):
    """LLM 结构化输出直接绑到 input_schema，服务端再做一次 pydantic 校验。"""
    InputModel = input_model_from_schema(action)
    raw = llm.with_structured_output(InputModel).invoke(
        [{"role": "system",
          "content": f"按 {action['model_id']} 的输入契约解析用户意图，只输出合法参数。"},
         {"role": "user", "content": message}])
    return InputModel.model_validate(raw.model_dump())  # 双保险：服务端强校验
```

**对比**：旧 `_parse_inputs` 用一个 `split(";")` 字符串协议拼装参数，类型/必填/枚举全丢；新方案用 JSON Schema 声明 + pydantic 校验，LLM 输出一步到位且服务端强校验。

### 5.2 声明式 effects：JMESPath 替代正则 + `_dig`

替代 `mvp_server.py` 的 `build_arguments`（正则挖占位符 + `_dig`）：

```python
# gateway/action/effects.py（示意）
import jmespath

def compose_effects(action: dict, target_row: dict, inputs: dict) -> dict:
    """按 effects.compose 的 JMESPath 表达式构造写回载荷。
    源数据域固定为 {'input': inputs, 'target': target_row}。
    """
    env = {"input": inputs, "target": target_row}
    out = {}
    for field, expr in (action.get("effects") or {}).get("compose", {}).items():
        out[field] = jmespath.compile(expr).search(env)
    return out

# 例：effects.compose = {"id": "input.record_id", "updates": "input.field_values"}
# inputs = {"record_id": "9305733", "field_values": {"active_status": "Inactive"}}
# → {"id": "9305733", "updates": {"active_status": "Inactive"}}
```

`_dig` 那些手写点路径、`re.sub` 渲染文案，全部由 JMESPath 表达式声明替代；表达式引用的字段在启动时做闭包校验（对齐现有 `_validate` 的 fail-fast 思路）。

### 5.3 通用 ActionEngine：编排「定位 → 校验 → 组合 → 提案 → 写回」

替代散落在 `mvp_server.py` / `runtime.py` 的 `plan/act/create_proposal`：

```python
# gateway/action/engine.py（示意）
from dataclasses import dataclass, field

@dataclass
class ActionContext:
    thread_id: str
    actor: str
    cookie_header: str = ""

class ActionEngine:
    """声明式写行为引擎：只解释 Action 声明，不含任何业务动作知识。"""

    def __init__(self, registry, proposal_store, write_adapter):
        self.reg = registry
        self.store = proposal_store
        self.write = write_adapter

    def run(self, action_id: str, inputs: dict, ctx: ActionContext) -> dict:
        action = self.reg.actions[action_id]
        # 1) typed 输入强校验（input_schema）
        validated = self._validate_input(action, inputs)
        # 2) 定位目标（target.locator → query）
        target_row = self._locate(action, validated)
        # 3) 结构化规则：派生（derivation）+ 前置校验（validation），fail-closed
        derived = self._apply_rules(action, target_row, validated)
        # 4) 声明式组合写回载荷（JMESPath）
        payload = compose_effects(action, target_row, {**validated, **derived})
        # 5) 生成提案（授权恒在网关侧，引擎无权放行写操作）
        proposal = self._create_proposal(action, payload, validated, ctx)
        proposal.setdefault("writeback", action["writeback"])
        self.store.save(proposal)
        return proposal

    # 批准后由网关触发写回（对齐 Palantir WriteBack）
    def writeback_on_approval(self, proposal_id: str, ctx: ActionContext) -> dict:
        p = self.store.get(proposal_id)
        assert p.get("state") == "APPROVED", "仅已批准提案可写回"
        wb = p["writeback"]
        mi = self.reg.mis[wb["via"]]
        result = self.write.execute(mi, p["payload"], ctx.cookie_header)
        p["state"] = "EXECUTED"
        p["receipt"] = result
        self.store.update(proposal_id, state="EXECUTED", extra={"receipt": result})
        return result
```

关键点：`ActionEngine` 是**通用解释器**，新增业务对象只改 Action 声明（YAML），引擎代码零改动——这正是「本体模型不变、运行时底座」的落地。

### 5.4 结构化 M3 规则：when-then 替代中文自然语言

M3 从「`condition: subtable_type 不在禁止更新列表中`」升级为结构化（保留中文 `description` 给人看）：

```yaml
# models/examples/masterdata/m3-rule.yaml（结构化后）
model_id: masterdata.m3.allow-update-rule
description: { zh: "禁止更新列表内的子表类型不允许更新" }   # 给人看的业务口径
when:
  field: subtable_type          # 封闭：{field, op, value}，op ∈ RULE_OPS
  op: in
  value: ["ESN", "Tax_Rate", "Tax_Code", "Exchange_Rate"]
then:
  effect: block                 # block | warn | derive
  message: "该子表类型在禁止更新列表内，不允许更新"
```

现有 `_when_matches` / `_run_validation_rules` / `_apply_derivations` 已是「封闭词表解释器」的正确方向，只是词表内置在引擎代码里。改造为：**词表仍然封闭（`RULE_OPS`/`RULE_KINDS` 保留），但条件表达式从「中文文本」变为「结构化 when-then」，由现有求值器只做解释、不再维护业务取值**。业务取值全部进 YAML，引擎保持通用。

### 5.5 WriteBack 声明：复用现有 adapter，补「声明 + 补偿」

现有 `write_adapters.py` 的 adapter 模式已经正确（`LocalJson / DpaHttp` 切换、诚实区分 `LOCAL_SANDBOX_APPLIED` 与真实写）。改造点是**把「写回策略」从隐式 `.env` 开关提升为 Action 声明的 `writeback` 字段**，并补补偿语义：

```python
# gateway/action/writeback.py（示意，复用现有 write_adapters）
class WritebackPolicy:
    """解释 Action.writeback 声明，调度现有 adapter；不改变执行安全边界。"""
    def dispatch(self, wb: dict, mi: dict, payload: dict, ctx) -> dict:
        if wb["timing"] == "deferred":
            return {"status": "QUEUED", "state": "PENDING_WRITEBACK"}
        # on-approval：审批后立即经 MI 防腐层写回（复用 DpaHttp/LocalJson adapter）
        return self.adapter_for(mi).execute(mi, payload, ctx.cookie_header)
```

补偿：`writeback.compensation.ref` 指向另一个 Action（如 `restore-subtable-data`），写回失败时由引擎以受治理方式创建一个逆操作提案，而不是让 LLM 自由重试。

---

## 5b. Agent 如何调用 ActionEngine（唯一协议：MCP）

**核心原则**：Agent 连接层使用 **100% 标准的 MCP 协议**（`mcp` 官方 Python SDK），零自研 tool/事件协议。本体治理、HITL、规则求值、防腐层写回是 MCP Server 内部自研的价值层——MCP 不覆盖，也不该覆盖。

### 语义工具注册：本体 Action 声明 → MCP tool（唯一自研胶水，纯声明驱动）

```python
# gateway/mcp_server.py（示意，基于官方 mcp SDK）
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dpa-ontology-gateway")

for action_id, action in registry.actions.items():
    InputModel = pydantic_from_json_schema(action["input_schema"])  # JSON Schema → pydantic

    def make_handler(aid):
        async def handler(inputs: InputModel) -> dict:
            # MCP SDK 已按 inputSchema 强校验，inputs 到达即 typed —— 字符串协议彻底消失
            return engine.run(aid, inputs.model_dump(), ctx)
        return handler

    mcp.add_tool(
        make_handler(action_id),
        name=action_id.rsplit(".", 1)[-1],         # 语义名，非 Controller 名
        description=f"{action['name']['zh']}（写操作，生成提案，需审批）",
    )
```

**一份 `input_schema` 三处复用**：MCP tool 的 `inputSchema`、pydantic 校验契约、ActionEngine 的输入契约。新增写操作 = 只写 YAML，MCP Server 代码零改动。

### 交互流程（标准 MCP，任意客户端可接入）

```
MCP 客户端 ──tools/list──────────────────► 返回 [propose_update_subtable@input_schema, ...]
MCP 客户端 ──tools/call {name, arguments}──► 参数已是 typed JSON
                     │
                     ▼
              engine.run(action_id, inputs, ctx)
                     │ validate → locate → rules → compose
                     ▼
              返回 Proposal（提案卡）
                     │  HITL（见下）
                     ▼
              writeback_on_approval(proposal_id)  ← 网关触发，Agent 不可见 MI/Cookie
```

### HITL 的标准承载（二选一，均不破坏"授权在网关侧"）

| 方案 | MCP 机制 | 说明 |
|------|---------|------|
| 原生 elicitation | MCP elicit 原语（tool 执行中暂停询问用户） | 原生 HITL，需客户端支持 |
| confirm 两段式 | `tools/call propose_xxx` 返回提案卡 → 用户前端批准 → `tools/call confirm_xxx` | 兼容性最好，任意客户端可用 |

无论哪种，**Agent 全程只持有 `proposal_id` + 审批 token**；URL、Cookie、MI、参数映射全在引擎后的防腐层（边界 #4）。

### 对既有 LangGraph 的定位调整

LangGraph 不再是「Agent 编排主轴」，降级为「MCP Server 内部的可选多步工作流实现」（若单个 Action 不善编排、需跨 Action 组合时才用）。否则 MCP + ActionEngine 直连即可，无需引入图编排。

---

## 6. 迁移路径（从 mvp-vertical-slice.yaml 平滑升级）

不改动现有已跑通的读取链路，分三步迁移写链路：

1. **步骤 1（零破坏）**：引入 `action.schema.json` + `ActionEngine`，先只处理一个写行为（`update-subtable-data`），与旧 `create_proposal` 并存，跑同一条 smoke 验证。
2. **步骤 2（替换输入协议）**：`runtime.py` 的 `Plan.inputs` 从 `"参数名=值"` 字符串改为 typed `input_schema`，删除 `_parse_inputs`。此步是交互问题的直接修复。
3. **步骤 3（替换规则与映射）**：M3 条件结构化、MI 参数映射改 JMESPath，删除 `_when_matches`/`_dig`/`re` 三件套，保留 `_validate` 的 fail-fast 闭包校验（它本身是好的）。

**每一步都可独立验证**（沿袭项目「一次只改一个可验证 Task」的纪律），且不触碰「DPA 是最终执行系统 / Database MCP 只读 / 写走 DPA 原业务链」这三条不可违反边界。

---

## 7. 一句话总结

> 把「写行为」补成一份**声明式 Action Schema**（typed input + JMESPath effects + 结构化 when-then 规则 + declared writeback + HITL），交给一个**通用 ActionEngine** 解释执行——这就是 Palantir Action Type + WriteBack 在当前底座下的落法，也是把写链路从「手写字符串解释器」改成「本体模型声明 + 运行时底座」的关键一步。