from __future__ import annotations

import json
import uuid
from typing import Any, Generator

from flask import current_app

from ..db import get_db, write_audit_log
from ..services.conversation_context_service import (
    build_session_context_note,
    load_session_context,
    rewrite_message_with_context,
)
from ..services.domain_copilot_service import format_domain_explanation_payload, domain_explanation_query
from ..ontology.loader import OntologyRegistry
from ..services.ontology_knowledge_service import format_ontology_knowledge_payload, query_ontology_knowledge
from ..services.semantic_query_service import build_plan, execute_semantic_query, format_result_as_payload
from .deepseek_client import DeepSeekClient
from .tooling import build_tools, execute_tool, tool_result_message


MSG_THINKING = "正在理解您的问题..."
MSG_CHAT_FAILED = "对话处理失败"
MSG_LOCAL_FALLBACK = "已回退为本地处理模式"


def stream_chat(message: str, session_id: str | None, actor: str | None = None) -> Generator[str, None, None]:
    effective_session_id = session_id or str(uuid.uuid4())

    try:
        _ensure_chat_session(effective_session_id)

        yield _sse("message_start", {"sessionId": effective_session_id})
        yield _sse("delta", {"text": MSG_THINKING})

        payload, tool_trace = _run_orchestrator(message, session_id=effective_session_id, actor=actor)
        _save_message(effective_session_id, "user", message, "text")
        render_type = payload.get("render", {}).get("type", "text") if payload.get("render") else "text"
        _save_message(effective_session_id, "assistant", json.dumps(payload, ensure_ascii=False), render_type)

        for item in tool_trace:
            yield _sse("tool_call", item)

        yield _sse("assistant", payload)
        yield _sse("message_end", {"sessionId": effective_session_id})
    except Exception as exc:
        error_payload = {
            "message": f"{MSG_CHAT_FAILED}: {exc}",
            "render": None,
            "action": None,
        }
        try:
            _save_message(effective_session_id, "user", message, "text")
            _save_message(effective_session_id, "assistant", json.dumps(error_payload, ensure_ascii=False), "text")
        except Exception:
            pass
        yield _sse("error", {"message": str(exc), "sessionId": effective_session_id})
        yield _sse("assistant", error_payload)
        yield _sse("message_end", {"sessionId": effective_session_id})


def chat_once(message: str, actor: str | None = None, session_id: str | None = None):
    effective_session_id = session_id or str(uuid.uuid4())
    _ensure_chat_session(effective_session_id)
    payload, _tool_trace = _run_orchestrator(message, session_id=effective_session_id, actor=actor)
    _save_message(effective_session_id, "user", message, "text")
    render_type = payload.get("render", {}).get("type", "text") if payload.get("render") else "text"
    _save_message(effective_session_id, "assistant", json.dumps(payload, ensure_ascii=False), render_type)
    return payload


def _run_orchestrator(message: str, session_id: str | None = None, actor: str | None = None):
    client = DeepSeekClient()
    tool_trace: list[dict[str, Any]] = []
    session_context = load_session_context(session_id)

    if client.enabled:
        try:
            payload, tool_trace = _run_deepseek(message, client, session_context=session_context, actor=actor)
            write_audit_log("AI_CHAT", "chat", actor, {"message": message, "result": payload.get("message")})
            return _sanitize_payload(payload), tool_trace
        except Exception as exc:
            fallback_payload = _run_local_fallback(message, session_context=session_context)
            fallback_payload["message"] = f"{MSG_LOCAL_FALLBACK}，原因：{exc}。{fallback_payload['message']}"
            write_audit_log("AI_CHAT", "chat", actor, {"message": message, "result": fallback_payload.get("message")})
            return _sanitize_payload(fallback_payload), tool_trace

    payload = _run_local_fallback(message, session_context=session_context)
    write_audit_log("AI_CHAT", "chat", actor, {"message": message, "result": payload.get("message")})
    return _sanitize_payload(payload), tool_trace


def _run_deepseek(
    message: str,
    client: DeepSeekClient,
    session_context: dict[str, Any] | None = None,
    actor: str | None = None,
):
    registry: OntologyRegistry = current_app.config["ONTOLOGY_REGISTRY"]
    tools = build_tools()
    session_context = session_context or {}
    effective_message = rewrite_message_with_context(message, session_context)
    messages = [{"role": "system", "content": _build_system_prompt(registry)}]
    context_note = build_session_context_note(session_context)
    if context_note:
        messages.append(
            {
                "role": "system",
                "content": f"当前会话最近上下文：{context_note}。如果用户本轮使用“这个合同”“它”“那一条”“上一条”等指代，请结合上下文理解。",
            }
        )
    messages.extend(session_context.get("llm_messages", []))
    messages.append({"role": "user", "content": effective_message})
    tool_trace: list[dict[str, Any]] = []
    semantic_tool_result: dict[str, Any] | None = None
    semantic_tool_args: dict[str, Any] | None = None
    explanation_tool_result: dict[str, Any] | None = None

    for _ in range(3):
        reply = client.chat_completion(messages, tools=tools)
        if reply.get("tool_calls"):
            messages.append(reply)
            for tool_call in reply["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"] or "{}")
                tool_trace.append({"name": function_name, "arguments": arguments})
                result = execute_tool(function_name, arguments, actor=actor)
                if function_name == "semantic_query":
                    semantic_tool_result = result
                    semantic_tool_args = arguments
                if function_name == "domain_explanation_query":
                    explanation_tool_result = result
                messages.append(tool_result_message(tool_call["id"], result))
            if (
                len(reply["tool_calls"]) == 1
                and semantic_tool_result is not None
                and semantic_tool_args is not None
                and reply["tool_calls"][0]["function"]["name"] == "semantic_query"
            ):
                semantic_plan = build_plan(plan=semantic_tool_args, query=effective_message)
                return format_result_as_payload(semantic_tool_result, semantic_plan), tool_trace
            if (
                len(reply["tool_calls"]) == 1
                and explanation_tool_result is not None
                and reply["tool_calls"][0]["function"]["name"] == "domain_explanation_query"
            ):
                return format_domain_explanation_payload(explanation_tool_result), tool_trace
            continue

        payload = _normalize_assistant_payload(reply.get("content", ""))
        if payload is not None:
            return payload, tool_trace
        break

    local_payload = _run_local_fallback(message, session_context=session_context)
    return local_payload, tool_trace


def _build_system_prompt(registry: OntologyRegistry) -> str:
    ontology_context = _build_ontology_context(registry)
    return f"""
你是“AI原生合同管理系统”的业务助手。
你的职责是：先理解用户自然语言，再结合本体模型选择合适工具，最后生成用户可直接阅读的中文结果。

{ontology_context}

严格遵守以下规则：
1. 优先使用函数调用理解和执行业务，不要把用户原话直接回显成内部语义。
2. 对合同、开票、收款、部门/客户/产品/销售人员统计、已开票未收款、未开票、合同详情等问题，优先调用 semantic_query。
3. 对流程、规则、事件链路、页面职责、本体模型含义、需求说明、系统设计说明等解释性问题，优先调用 domain_explanation_query；如只需要检索原始知识片段，再调用 ontology_knowledge_query。
4. 对“为什么这个合同/发票是某种状态”“为什么显示部分开票/部分收款”“这个编号为什么未开票未收款”这类问题，必须调用 domain_explanation_query，结合真实数据和本体规则回答。
5. 只有当现有 API/语义工具都不能覆盖时，才调用 readonly_sql_query。
6. readonly_sql_query 只能用于只读 SELECT。任何新增、修改、删除、作废类请求，都要明确告诉用户当前对话无权执行，并建议使用固定业务页面。
7. 如果用户问某个具体合同或发票的一两个字段，例如“合同总金额”“销售部门”，优先返回自然语言句子，不要强制渲染表格。
8. 如果用户明确要求“输出几列信息”“表格”“列表”，或者结果是多行多对象统计，再返回表格。
9. 如果用户明确要求图表、柱状图、条形图、折线图、趋势图、饼图，调用 semantic_query 时将 responsePreference 设为 chart，并根据图表类型设置 chartType。
10. 如果用户要求哪些列，就确保最终结果包含这些列。例如“部门、合同总金额、已开票金额三列”必须全部包含。
11. 永远不要向用户展示工具名、SQL、toolTrace、语义计划、内部参数。
12. 如果数据为空，直接清楚说明未查询到结果。
13. 如果问题是在问“怎么做”“流程如何”“规则是什么”，这属于解释性问题，不要误判为用户真的要执行创建、修改或删除操作。

你的最终输出必须是严格 JSON，不要输出 JSON 之外的任何文字：
{{
  "message": "面向用户的中文说明",
  "render": null 或 {{
    "type": "table" 或 "chart",
    "title": "标题",
    "headers": ["列1", "列2"],
    "rows": [["值1", "值2"]]
  }},
  "action": null 或 {{
    "type": "OPEN_PAGE",
    "pageId": "ContractEntryPage|InvoiceEntryPage|PaymentReceivePage|ContractSearchPage"
  }}
}}
""".strip()


def _build_ontology_context(registry: OntologyRegistry) -> str:
    aggregates = ", ".join(sorted(registry.aggregates.keys()))
    behaviors = ", ".join(sorted(registry.behaviors.keys()))
    pages = ", ".join(sorted(registry.pages.keys()))
    use_case_names = "；".join(item.get("name", "") for item in registry.use_cases.values())
    rule_names = "；".join(item.get("name", "") for item in registry.rules.values())
    requirement_excerpt = _pick_requirement_excerpt(registry)
    return (
        "本体模型摘要：\n"
        f"- 核心聚合: {aggregates}\n"
        f"- 已建模行为: {behaviors}\n"
        f"- 已建模用例: {use_case_names}\n"
        f"- 核心规则: {rule_names}\n"
        f"- 固定页面: {pages}\n"
        "- 业务对象关系: 合同关联客户、产品、部门、销售人员；发票隶属于合同；收款当前建模为对发票的收款确认。\n"
        "- 业务语义: “已开票未收款合同”表示合同下至少存在一张状态为已开票且未收款的发票；“未开票合同”表示合同下没有发票记录。\n"
        "- 合同常用字段: 合同编号、合同名称、客户、产品、部门、销售人员、签订日期、合同总金额、累计开票金额、累计收款金额、开票状态、收款状态。\n"
        "- 发票常用字段: 发票编号、合同编号、合同名称、部门、客户、开票金额、开票日期、发票状态、收款状态。\n"
        "- 收款常用字段: 发票编号、合同编号、合同名称、部门、客户、收款金额、收款日期、收款状态。\n"
        f"- 原始需求摘录: {requirement_excerpt}"
    )


def _normalize_assistant_payload(content: str):
    try:
        parsed = json.loads(content)
        return {
            "message": parsed.get("message") or "已完成处理。",
            "render": parsed.get("render"),
            "action": parsed.get("action"),
        }
    except Exception:
        return None


def _run_local_fallback(message: str, session_context: dict[str, Any] | None = None):
    text = (message or "").strip()
    session_context = session_context or {}
    effective_text = rewrite_message_with_context(text, session_context)
    lowered = text.lower()
    if not text:
        return {"message": "请先输入您的问题或指令。", "render": None, "action": None}

    if _is_explanatory_question(effective_text):
        return format_domain_explanation_payload(domain_explanation_query(effective_text))

    if _is_cud_request(lowered):
        return {
            "message": "当前 AI 对话仅支持只读查询和页面导航，不具备新增、修改、删除权限。请通过固定业务页面执行对应操作。",
            "render": None,
            "action": None,
        }

    if _looks_like_page_navigation(effective_text):
        if _contains_any(effective_text, ["合同录入", "新增合同", "创建合同"]):
            return _open_page_payload("ContractEntryPage", "已为您打开合同录入页面。")
        if _contains_any(effective_text, ["开票录入", "合同开票", "录入开票", "开发票", "去开票"]):
            return _open_page_payload("InvoiceEntryPage", "已为您打开开票录入页面。")
        if _contains_any(effective_text, ["收款录入", "确认收款", "合同收款", "去收款"]):
            return _open_page_payload("PaymentReceivePage", "已为您打开收款录入页面。")

    return execute_semantic_query(query=effective_text, user_facing=True)


def _sanitize_payload(payload: dict[str, Any]):
    return {
        "message": payload.get("message") or "已完成处理。",
        "render": payload.get("render"),
        "action": payload.get("action"),
    }


def _open_page_payload(page_id: str, message: str):
    return {"message": message, "render": None, "action": {"type": "OPEN_PAGE", "pageId": page_id}}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _looks_like_page_navigation(text: str) -> bool:
    return _contains_any(text, ["打开", "进入", "去", "跳转"]) and _contains_any(text, ["合同", "开票", "收款"])


def _is_cud_request(lowered: str) -> bool:
    if _is_explanatory_question(lowered):
        return False
    return any(keyword in lowered for keyword in ["新增", "创建", "修改", "删除", "作废", "insert", "update", "delete"])


def _is_explanatory_question(text: str) -> bool:
    return _contains_any(
        text,
        [
            "为什么",
            "为何",
            "原因",
            "状态",
            "流程",
            "步骤",
            "规则",
            "校验",
            "约束",
            "事件",
            "本体",
            "模型",
            "需求",
            "架构",
            "如何",
            "怎么",
            "是什么",
            "说明",
            "介绍",
            "含义",
            "逻辑",
            "原理",
        ],
    )


def _pick_requirement_excerpt(registry: OntologyRegistry) -> str:
    requirement = registry.requirement_docs.get("合同管理原始需求.txt", "")
    for line in requirement.splitlines():
        cleaned = line.strip()
        if cleaned and "合同系统只对销售合同进行管理" in cleaned:
            return cleaned
    return "系统管理销售合同、合同付款条款、开票信息和收款信息，并支持合同查询。"


def _ensure_chat_session(session_id: str):
    db = get_db()
    exists = db.execute("SELECT id FROM chat_sessions WHERE session_id = ?", (session_id,)).fetchone()
    if not exists:
        db.execute("INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)", (session_id, "新会话"))
        db.commit()


def _save_message(session_id: str, role: str, content: str, message_type: str):
    db = get_db()
    db.execute(
        """
        INSERT INTO chat_messages (session_id, role, content, message_type)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, role, content, message_type),
    )
    db.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
    db.commit()


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
