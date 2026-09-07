# -*- coding: utf-8 -*-
"""Agent Runtime：LangGraph 编排 + HITL 中断（Runtime Interface 隐藏框架细节）。

设计纪律：
- mvp_server 只见 AgentRuntime.run()/resume()，LangGraph 细节不外泄；
- HITL 双轨制：图的 interrupt() 负责**编排暂停/恢复**；**授权**始终在网关侧
  （ProposalStore + 单次审批 Token + 状态机），图恢复只携带已裁决的结果，
  图本身无权放行任何写操作；
- 意图解析完全模型驱动：可用查询/行为/触发词/参数取值全部来自 bindings.catalog()
  （本体 YAML 声明），本文件不含任何业务动作知识——新增业务对象只改 YAML；
- LLM 可选：.env 配置 LLM_* 走模型结构化决策；未配置退回目录驱动的确定性路由，
  降级在 route 事件中显式标注，不静默伪装；
- 刻意零中间件：DeepAgents 的 todo/虚拟文件系统/子代理/摘要等中间件对本网关
  均非必要——全部禁用后剩下的就是 LangGraph 本身，故直接用 LangGraph。
"""
import json
from typing import Callable, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from config import HAS_LLM, LLM_API_KEY, LLM_API_VERSION, LLM_BASE_URL, LLM_MODEL

# 语言填充词（通用语言处理，非业务知识）：提取检索词时剔除
_FILLERS = {"查", "帮我", "一下", "看看", "请", "把", "吧", "了", "的",
            "这个", "那个", "一下下", "相应"}


class GatewayBindings:
    """网关能力注入：Agent 图只依赖这组回调，不导入 mvp_server（避免循环依赖）。"""

    def __init__(self, *, catalog: Callable, run_query: Callable,
                 build_arguments: Callable, create_proposal: Callable,
                 build_table_event: Callable, route_note: Callable):
        self.catalog = catalog                # () -> {queries:[...], behaviors:[...]}（本体 YAML 推导）
        self.run_query = run_query            # (query_id, params) -> rows
        self.build_arguments = build_arguments  # (behavior_id, row, inputs) -> 提案参数（param_mapping 驱动）
        self.create_proposal = create_proposal  # (behavior_id, args, thread_id) -> card
        self.build_table_event = build_table_event  # (obj_id, rows) -> object_table 事件
        self.route_note = route_note          # (mode) -> str


class AgentState(TypedDict):
    message: str
    thread_id: str
    steps: list        # [(kind, obj_id, ref, params)]；propose 的 params = inputs
    events: list       # UI 事件流
    proposal: dict     # 已创建的提案卡（None = 本次无写提案）


def _kw_token(message: str, consumed: set) -> str:
    """提取检索词：剔除已命中触发词与填充词后取最长 token。

    通用语言处理（切词粗粒度），不含业务知识；复杂口语由 LLM 路径处理。
    """
    text = message
    for kw in sorted(consumed, key=len, reverse=True):
        text = text.replace(kw, " ")
    toks = [t for t in text.split() if t and t not in _FILLERS]
    if not toks:
        return ""
    return max(toks, key=len)


def _fallback_steps(message: str, cat: dict) -> list:
    """目录驱动的确定性路由（无 LLM 回退）：触发词全部来自本体 YAML 声明。"""
    # 1) 行为触发：任一 input_values 触发词命中 → 先定位后提案
    for b in cat["behaviors"]:
        for field, mapping in (b.get("input_values") or {}).items():
            hit = next((trig for trig in mapping if trig in message), None)
            if hit is None:
                continue
            consumed = set(mapping) | {hit}
            loc = b.get("target_locator") or {}
            steps = []
            if loc.get("query_ref"):
                kw = _kw_token(message, consumed)
                steps.append(("lookup", b["object"], loc["query_ref"], {"kw": f"%{kw}%"}))
            steps.append(("propose", b["object"], b["id"], {field: mapping[hit]}))
            return steps
    # 2) 查询触发：最长命中关键词优先
    matched = []
    for q in cat["queries"]:
        kws = [kw for kw in q.get("keywords", []) if kw in message]
        if kws:
            matched.append((q, max(kws, key=len)))
    if not matched:
        return []
    q, kw = max(matched, key=lambda p: len(p[1]))
    consumed = {k for _, k in matched} | set(q.get("keywords", []))
    rest = _kw_token(message, consumed)
    return [("search", q["object"], q["id"], {"kw": f"%{rest}%"})]


def _catalog_prompt(cat: dict) -> str:
    """从本体目录生成意图解析提示词：模型即工具目录，不在代码里枚举业务动作。"""
    lines = ["你是主数据网关的意图解析器，只能从下列模型声明的动作中选择。", "", "可用查询："]
    for q in cat["queries"]:
        kws = "/".join(q.get("keywords", []))
        lines.append(f"- {q['id']}：{q['display_name']}（触发词：{kws}）")
    lines += ["", "可用行为（先按 keyword 定位目标文档，再创建提案）："]
    for bh in cat["behaviors"]:
        iv = "; ".join(f"{k} 取值映射 {json.dumps(m, ensure_ascii=False)}"
                       for k, m in (bh.get("input_values") or {}).items())
        lines.append(f"- {bh['id']}：{bh['display_name']}（参数：{iv or '无'}）")
    lines += ["",
              "规则：action_id 必须取自上面列表；用户动词不在范围内（如删除、导出、新增）"
              "时 action_id 返回 none，禁止猜测近似动作；",
              "keyword 只填文档编号或名称原文（如 9305733），不要包含'查''停用'等指令词。",
              "inputs 按行为的参数取值映射填写，格式：参数名=值，多个用分号分隔（如 active_status=Inactive）；不适用时留空。只输出 Plan。"]
    return "\n".join(lines)


def _llm_steps(message: str, cat: dict) -> tuple[list | None, str]:
    """LLM 结构化决策：自然语言 → 本体动作。失败显式退回目录路由（标注原因）。"""
    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field

        class Plan(BaseModel):
            action_id: str = Field(description="选择的动作 id；均不适用时为 none")
            keyword: str = Field(default="", description="检索词：文档编号或名称原文")
            # 注：gpt-5 结构化输出不支持自由 dict，故用「参数名=值」串（分号分隔）
            inputs: str = Field(default="", description="参数取值：参数名=值，多个用分号分隔")

        def _parse_inputs(s: str) -> dict:
            out = {}
            for part in (s or "").split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    if k.strip() and v.strip():
                        out[k.strip()] = v.strip()
            return out

        # Siemens APIM 实证：需 api-key 头（订阅键）+ api-version 查询参数同时存在；
        # OpenAI 官方/DeepSeek 等端点会忽略未知头，不影响直连
        extra = {"default_query": {"api-version": LLM_API_VERSION}} if LLM_API_VERSION else {}
        llm = ChatOpenAI(model=LLM_MODEL, base_url=LLM_BASE_URL, api_key=LLM_API_KEY,
                         default_headers={"api-key": LLM_API_KEY}, **extra)
        plan = llm.with_structured_output(Plan).invoke([
            {"role": "system", "content": _catalog_prompt(cat)},
            {"role": "user", "content": message}])
        by_bh = {b["id"]: b for b in cat["behaviors"]}
        by_q = {q["id"]: q for q in cat["queries"]}
        aid = (plan.action_id or "").strip()
        if aid in by_bh:
            bh = by_bh[aid]
            steps, loc = [], bh.get("target_locator") or {}
            if loc.get("query_ref"):
                steps.append(("lookup", bh["object"], loc["query_ref"],
                              {"kw": f"%{plan.keyword}%"})
                             )
            steps.append(("propose", bh["object"], aid, _parse_inputs(plan.inputs)))
            return steps, "LLM"
        if aid in by_q:
            q = by_q[aid]
            return [("search", q["object"], aid,
                     {"kw": f"%{(plan.keyword or '').strip()}%"})], "LLM"
        return [], "LLM(未识别意图)"
    except Exception as e:  # 显式降级：原因进 route 事件，不静默
        return None, f"LLM 不可用({type(e).__name__})→目录路由"


def build_runtime(b: GatewayBindings):
    def plan(state: AgentState) -> dict:
        cat = b.catalog()
        steps, mode = None, "目录路由"
        if HAS_LLM:
            steps, mode = _llm_steps(state["message"], cat)
        if steps is None:
            steps = _fallback_steps(state["message"], cat)
        return {"steps": steps,
                "events": [{"type": "route", "note": b.route_note(mode)}]}

    def act(state: AgentState) -> dict:
        events, proposal = [], None
        if not state["steps"]:
            return {"events": list(state["events"]) +
                    [{"type": "error", "message":
                        "未识别意图。可用示例：查审批主数据 9305733 / 查厂商 9305733 / "
                        "查商品 芝士 / 查预算 FY23 / 停用 9305733 / 启用 …"}]}
        for kind, obj_id, ref, params in state["steps"]:
            if kind in ("search", "lookup"):
                rows = b.run_query(ref, params)
                events.append(b.build_table_event(obj_id, rows))
            elif kind == "propose":
                target = next((e for e in state["events"] + events
                               if e["type"] == "object_table"
                               and e["object"] == obj_id and e["rows"]), None)
                if not target:
                    events.append({"type": "error", "message": "未找到匹配文档，拒绝创建提案"})
                    continue
                row = target["rows"][0]
                # 提案参数由 param_mapping + 目标模板统一推导（模型驱动，代码不含接口字段知识）
                args = b.build_arguments(ref, row, params)
                card = b.create_proposal(ref, args, state["thread_id"])
                proposal = card
                events.append({"type": "proposal_card", **card})
        return {"events": list(state["events"]) + events, "proposal": proposal}

    def wait_approval(state: AgentState) -> dict:
        card = state["proposal"]
        # HITL：图在此暂停；恢复值必须携带网关已完成的裁决结果（图无权自行放行）
        payload = interrupt({"proposal_id": card["proposal_id"],
                             "state": card["state"], "risk": card["risk"]})
        events = list(state["events"]) + [{"type": "hitl",
                                           "decision": payload.get("decision"),
                                           "result": payload.get("result")}]
        return {"events": events}

    g = StateGraph(AgentState)
    g.add_node("plan", plan)
    g.add_node("act", act)
    g.add_node("wait_approval", wait_approval)
    g.add_edge(START, "plan")
    g.add_edge("plan", "act")
    g.add_conditional_edges("act", lambda s: "wait_approval" if s.get("proposal") else END)
    g.add_edge("wait_approval", END)
    app = g.compile(checkpointer=InMemorySaver())  # 正式环境换 PG Checkpointer

    class AgentRuntime:
        def run(self, message: str, thread_id: str) -> list:
            final = app.invoke({"message": message, "thread_id": thread_id},
                               config={"configurable": {"thread_id": thread_id}})
            return final["events"]

        def resume(self, thread_id: str, payload: dict) -> None:
            """人工裁决后恢复图线程（仅补齐事件流；授权已由网关状态机完成）。"""
            app.invoke(Command(resume=payload),
                       config={"configurable": {"thread_id": thread_id}})

    return AgentRuntime()
