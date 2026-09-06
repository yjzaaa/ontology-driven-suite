from __future__ import annotations

import json
import re
from typing import Any

from ..db import get_db


CONTRACT_NO_PATTERN = re.compile(r"HT\d{4,}", flags=re.IGNORECASE)
INVOICE_NO_PATTERN = re.compile(r"FP\d{4,}", flags=re.IGNORECASE)


def load_session_context(session_id: str | None, limit: int = 10) -> dict[str, Any]:
    if not session_id:
        return _empty_context()

    db = get_db()
    rows = db.execute(
        """
        SELECT role, content, message_type, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()
    messages = list(reversed(rows))
    if not messages:
        return _empty_context()

    parsed_messages = [_parse_chat_message(row) for row in messages]
    context = _empty_context()
    context["messages"] = parsed_messages
    context["llm_messages"] = _build_llm_messages(parsed_messages)

    _extract_entity_context(context, parsed_messages)
    _extract_result_context(context, parsed_messages)
    _extract_topic_context(context, parsed_messages)
    return context


def build_session_context_note(context: dict[str, Any]) -> str:
    fragments: list[str] = []
    if context.get("last_contract_no"):
        fragments.append(f"最近关注合同: {context['last_contract_no']}")
    if context.get("last_invoice_no"):
        fragments.append(f"最近关注发票: {context['last_invoice_no']}")
    if context.get("last_department_name"):
        fragments.append(f"最近关注部门: {context['last_department_name']}")
    if context.get("last_customer_name"):
        fragments.append(f"最近关注客户: {context['last_customer_name']}")
    if context.get("last_subject"):
        fragments.append(f"最近主题对象: {context['last_subject']}")
    if context.get("last_topic"):
        fragments.append(f"最近问题类型: {context['last_topic']}")
    return "；".join(fragments)


def rewrite_message_with_context(message: str, context: dict[str, Any]) -> str:
    text = (message or "").strip()
    if not text:
        return text

    additions: list[str] = []
    normalized = _normalize(text)
    has_contract_no = bool(CONTRACT_NO_PATTERN.search(text))
    has_invoice_no = bool(INVOICE_NO_PATTERN.search(text))

    if _contains_any(normalized, ["第一张", "第一条", "第一个", "上一个", "上一条", "那一条", "那一个"]):
        if not has_invoice_no and context.get("last_result_invoice_no"):
            additions.append(f"本轮延续的发票编号是 {context['last_result_invoice_no']}")
            has_invoice_no = True
        if not has_contract_no and context.get("last_result_contract_no"):
            additions.append(f"本轮延续的合同编号是 {context['last_result_contract_no']}")
            has_contract_no = True

    if _contains_any(normalized, ["这个合同", "该合同", "这份合同", "它"]) and not has_contract_no and context.get("last_contract_no"):
        additions.append(f"当前延续的合同编号是 {context['last_contract_no']}")
        has_contract_no = True

    if _contains_any(normalized, ["这个发票", "该发票", "这张发票", "它"]) and not has_invoice_no and context.get("last_invoice_no"):
        additions.append(f"当前延续的发票编号是 {context['last_invoice_no']}")
        has_invoice_no = True

    if _contains_any(normalized, ["这个部门", "该部门", "上个部门", "上一部门"]) and context.get("last_department_name"):
        additions.append(f"当前延续的部门是 {context['last_department_name']}")

    if _contains_any(normalized, ["这个客户", "该客户", "上个客户", "上一客户"]) and context.get("last_customer_name"):
        additions.append(f"当前延续的客户是 {context['last_customer_name']}")

    if not additions:
        return text
    return f"{text}。{'；'.join(additions)}"


def _empty_context() -> dict[str, Any]:
    return {
        "messages": [],
        "llm_messages": [],
        "last_contract_no": None,
        "last_invoice_no": None,
        "last_department_name": None,
        "last_customer_name": None,
        "last_subject": None,
        "last_topic": None,
        "last_result_contract_no": None,
        "last_result_invoice_no": None,
    }


def _parse_chat_message(row: dict[str, Any]) -> dict[str, Any]:
    role = row["role"]
    content = row["content"]
    payload = None
    visible_text = content
    render = None
    if role == "assistant":
        try:
            payload = json.loads(content)
            visible_text = payload.get("message") or ""
            render = payload.get("render")
        except Exception:
            payload = None
    return {
        "role": role,
        "content": content,
        "visible_text": visible_text,
        "payload": payload,
        "render": render,
        "message_type": row.get("message_type") or "text",
        "created_at": row.get("created_at"),
    }


def _build_llm_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    llm_messages: list[dict[str, str]] = []
    for item in messages[-8:]:
        content = item["visible_text"]
        if item["role"] == "assistant" and item.get("render"):
            render_summary = _summarize_render(item["render"])
            if render_summary:
                content = f"{content}\n{render_summary}".strip()
        llm_messages.append({"role": item["role"], "content": content})
    return llm_messages


def _summarize_render(render: dict[str, Any]) -> str:
    if not render:
        return ""
    if render.get("type") == "table":
        headers = render.get("headers") or []
        rows = render.get("rows") or []
        if rows:
            return f"上轮结果表头: {headers}；首行: {rows[0]}"
        return f"上轮结果表头: {headers}"
    if render.get("type") == "chart" and render.get("table"):
        table = render["table"]
        rows = table.get("rows") or []
        if rows:
            return f"上轮图表对应表格首行: {rows[0]}"
    return ""


def _extract_entity_context(context: dict[str, Any], messages: list[dict[str, Any]]):
    db = get_db()
    departments = [row["dept_name"] for row in db.execute("SELECT dept_name FROM departments ORDER BY LENGTH(dept_name) DESC").fetchall()]
    customers = [row["customer_name"] for row in db.execute("SELECT customer_name FROM customers ORDER BY LENGTH(customer_name) DESC").fetchall()]

    for item in reversed(messages):
        text = item["visible_text"] or ""
        if context["last_contract_no"] is None:
            match = CONTRACT_NO_PATTERN.search(text)
            if match:
                context["last_contract_no"] = match.group(0).upper()
        if context["last_invoice_no"] is None:
            match = INVOICE_NO_PATTERN.search(text)
            if match:
                context["last_invoice_no"] = match.group(0).upper()
        if context["last_department_name"] is None:
            context["last_department_name"] = _find_named_entity(text, departments)
        if context["last_customer_name"] is None:
            context["last_customer_name"] = _find_named_entity(text, customers)
        if all(context[key] is not None for key in ["last_contract_no", "last_invoice_no", "last_department_name", "last_customer_name"]):
            break


def _extract_result_context(context: dict[str, Any], messages: list[dict[str, Any]]):
    for item in reversed(messages):
        render = item.get("render")
        if not render or render.get("type") != "table":
            continue
        headers = render.get("headers") or []
        rows = render.get("rows") or []
        if not headers or not rows:
            continue
        first_row = rows[0]
        header_map = {str(header): index for index, header in enumerate(headers)}
        if context["last_result_contract_no"] is None and "合同编号" in header_map:
            context["last_result_contract_no"] = str(first_row[header_map["合同编号"]]).strip()
        if context["last_result_invoice_no"] is None and "发票编号" in header_map:
            context["last_result_invoice_no"] = str(first_row[header_map["发票编号"]]).strip()
        if context["last_department_name"] is None and "部门" in header_map:
            context["last_department_name"] = str(first_row[header_map["部门"]]).strip()
        if context["last_customer_name"] is None and "客户" in header_map:
            context["last_customer_name"] = str(first_row[header_map["客户"]]).strip()
        if context["last_result_contract_no"] or context["last_result_invoice_no"]:
            break


def _extract_topic_context(context: dict[str, Any], messages: list[dict[str, Any]]):
    for item in reversed(messages):
        if item["role"] != "user":
            continue
        normalized = _normalize(item["visible_text"])
        if context["last_subject"] is None:
            if _contains_any(normalized, ["发票", "开票"]):
                context["last_subject"] = "invoice"
            elif _contains_any(normalized, ["收款", "回款", "到账"]):
                context["last_subject"] = "receipt"
            elif "合同" in normalized:
                context["last_subject"] = "contract"
        if context["last_topic"] is None:
            if _contains_any(normalized, ["为什么", "为何", "原因", "状态"]):
                context["last_topic"] = "explanation"
            elif _contains_any(normalized, ["流程", "步骤", "规则", "事件", "架构", "模型"]):
                context["last_topic"] = "knowledge"
            elif _contains_any(normalized, ["统计", "汇总", "图表"]):
                context["last_topic"] = "aggregate"
            elif _contains_any(normalized, ["详情", "明细", "什么", "是多少"]):
                context["last_topic"] = "detail"
            else:
                context["last_topic"] = "query"
        if context["last_subject"] and context["last_topic"]:
            break


def _find_named_entity(text: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate and candidate in text:
            return candidate
    return None


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())
