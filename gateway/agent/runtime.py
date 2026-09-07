# -*- coding: utf-8 -*-
"""Agent Runtime：LangGraph 编排 + HITL 中断（Runtime Interface 隐藏框架细节）。

设计纪律：
- mvp_server 只见 AgentRuntime.run()/resume()，LangGraph 细节不外泄；
- HITL 双轨制：图的 interrupt() 负责**编排暂停/恢复**；**授权**始终在网关侧
  （ProposalStore + 单次审批 Token + 状态机），图恢复只携带已裁决的结果，
  图本身无权放行任何写操作；
- LLM 可选：.env 配置 LLM_* 走模型结构化决策；未配置退回关键词路由
  （演示不依赖外部服务），降级在 route 事件中显式标注，不静默伪装；
- 刻意零中间件：DeepAgents 的 todo/虚拟文件系统/子代理/摘要等中间件对本网关
  均非必要——全部禁用后剩下的就是 LangGraph 本身，故直接用 LangGraph。
"""
from typing import Callable, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from config import HAS_LLM, LLM_API_KEY, LLM_API_VERSION, LLM_BASE_URL, LLM_MODEL


class GatewayBindings:
    """网关能力注入：Agent 图只依赖这组回调，不导入 mvp_server（避免循环依赖）。"""

    def __init__(self, *, fallback_route: Callable, run_query: Callable,
                 create_proposal: Callable, build_table_event: Callable,
                 route_note: Callable):
        self.fallback_route = fallback_route          # message -> steps
        self.run_query = run_query                    # (mi_id, params) -> rows
        self.create_proposal = create_proposal        # (behavior_id, args, thread_id) -> card
        self.build_table_event = build_table_event    # (obj_id, rows) -> object_table 事件
        self.route_note = route_note                  # (mode) -> str


class AgentState(TypedDict):
    message: str
    thread_id: str
    steps: list        # [(kind, obj_id, ref, params)]
    events: list       # UI 事件流
    proposal: dict     # 已创建的提案卡（None = 本次无写提案）


def _llm_steps(message: str) -> tuple[list | None, str]:
    """LLM 结构化决策：自然语言 → 本体动作。失败显式退回规则路由（标注原因）。"""
    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel

        class Plan(BaseModel):
            action: Literal["search_docs", "change_status", "other"]
            keyword: str = ""
            target_status: Literal["Active", "Inactive", ""] = ""

        # Siemens APIM 实证：需 api-key 头（订阅键）+ api-version 查询参数同时存在；
        # OpenAI 官方/DeepSeek 等端点会忽略未知头，不影响直连
        extra = {"default_query": {"api-version": LLM_API_VERSION}} if LLM_API_VERSION else {}
        llm = ChatOpenAI(model=LLM_MODEL, base_url=LLM_BASE_URL, api_key=LLM_API_KEY,
                         default_headers={"api-key": LLM_API_KEY}, **extra)
        plan = llm.with_structured_output(Plan).invoke([
            {"role": "system", "content":
                "你是 PR 审批主数据网关的意图解析器。可用动作只有两个："
                "search_docs=按关键词检索主数据文档；change_status=按关键词定位文档并"
                "启用(target_status=Active)或停用(Inactive)。"
                "keyword 只填文档编号或名称原文（如 9305733），不要包含'查''停用'等指令词。"
                "若用户动词不在上述范围内（如删除、导出、新增），一律返回 action=other，"
                "禁止猜测近似动作。只输出 Plan。"},
            {"role": "user", "content": message}])
        if plan.action == "search_docs":
            return [("search", "pr_approval_doc", "pr_doc_search",
                     {"kw": f"%{plan.keyword}%"})], "LLM"
        if plan.action == "change_status":
            act = "Inactive" if plan.target_status == "Inactive" else "Active"
            return [("lookup", "pr_approval_doc", "pr_doc_search",
                     {"kw": f"%{plan.keyword}%"}),
                    ("propose", "pr_approval_doc", "change_doc_status",
                     {"active_status": act})], "LLM"
        return [], "LLM(未识别意图)"
    except Exception as e:  # 显式降级：原因进 route 事件，不静默
        return None, f"LLM 不可用({type(e).__name__})→规则路由"


def build_runtime(b: GatewayBindings):
    def plan(state: AgentState) -> dict:
        steps, mode = None, "规则路由"
        if HAS_LLM:
            steps, mode = _llm_steps(state["message"])
        if steps is None:
            steps = b.fallback_route(state["message"])
        return {"steps": steps,
                "events": [{"type": "route", "note": b.route_note(mode)}]}

    def act(state: AgentState) -> dict:
        events, proposal = [], None
        if not state["steps"]:
            return {"events": list(state["events"]) +
                    [{"type": "error", "message": "未识别意图。可用示例：查审批主数据 9305733 / 停用 FY23_One-time Tooling / 启用 …"}]}
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
                args = {"target": {"ids": [int(row["id"])], "dic_type": row.get("dic_type"),
                                   "dic_name": row.get("dic_name")},
                        "input": dict(params)}
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
