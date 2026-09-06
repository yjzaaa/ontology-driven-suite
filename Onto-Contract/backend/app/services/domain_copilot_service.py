from __future__ import annotations

import re
from typing import Any

from flask import current_app

from ..db import get_db
from .contract_service import get_contract_detail
from .ontology_knowledge_service import query_ontology_knowledge


CONTRACT_NO_PATTERN = re.compile(r"HT\d{4,}", flags=re.IGNORECASE)
INVOICE_NO_PATTERN = re.compile(r"FP\d{4,}", flags=re.IGNORECASE)


def domain_explanation_query(
    question: str,
    focus: str | None = None,
    contract_no: str | None = None,
    invoice_no: str | None = None,
) -> dict[str, Any]:
    inferred_focus = _infer_focus(question, focus)
    contract_no = contract_no or _extract_contract_no(question)
    invoice_no = invoice_no or _extract_invoice_no(question)

    if contract_no and inferred_focus in {"status", "reason", "general"}:
        contract_result = _explain_contract(contract_no, question)
        if contract_result:
            return contract_result

    if invoice_no and inferred_focus in {"status", "reason", "general"}:
        invoice_result = _explain_invoice(invoice_no, question)
        if invoice_result:
            return invoice_result

    return _compose_knowledge_answer(question, inferred_focus)


def format_domain_explanation_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": result.get("answer") or "暂时没有匹配到足够明确的解释信息。",
        "render": None,
        "action": None,
    }


def _compose_knowledge_answer(question: str, inferred_focus: str) -> dict[str, Any]:
    focus_mapping = {
        "process": "use_case",
        "rule": "rule",
        "event": "event",
        "page": "page",
        "object": "aggregate",
    }
    knowledge = query_ontology_knowledge(question, focus=focus_mapping.get(inferred_focus))
    matches = knowledge.get("matches") or []
    if not matches:
        return {
            "kind": "knowledge_answer",
            "answer": "暂时没有从本体模型和需求文档中匹配到足够明确的信息。",
            "evidence": [],
        }

    lines = [knowledge.get("summary", "已从本体模型中整理出相关信息。")]
    top_groups = _group_matches(matches)

    if inferred_focus == "process":
        use_case = top_groups.get("use_case")
        behavior = top_groups.get("behavior")
        rule_matches = [item for item in matches if item["type"] == "rule"][:2]
        event_matches = [item for item in matches if item["type"] == "event"][:2]
        page_match = top_groups.get("page")
        if use_case:
            lines.append(f"对应业务用例：{use_case['title']}。{use_case['content']}")
        if behavior:
            lines.append(f"核心行为：{behavior['title']}。{behavior['content']}")
        if rule_matches:
            lines.append("关键规则：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in rule_matches))
        if event_matches:
            lines.append("事件链路：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in event_matches))
        if page_match:
            lines.append(f"承载页面：{page_match['title']}。{_trim_content(page_match['content'])}")
    elif inferred_focus == "rule":
        lines.append(_build_rule_answer(question, matches))
    elif inferred_focus == "event":
        lines.append(_build_event_chain_answer(question, matches))
    elif inferred_focus == "page":
        page_matches = [item for item in matches if item["type"] == "page"][:3]
        if page_matches:
            lines.append("相关页面职责如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in page_matches))
    elif inferred_focus == "object":
        object_matches = [item for item in matches if item["type"] == "aggregate"][:3]
        if object_matches:
            lines.append("相关业务对象如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in object_matches))
    else:
        for match in matches[:4]:
            lines.append(f"{match['title']}：{_trim_content(match['content'])}")

    return {
        "kind": "knowledge_answer",
        "answer": "\n\n".join(line for line in lines if line),
        "evidence": matches[:4],
    }


def _explain_contract(contract_no: str, question: str) -> dict[str, Any] | None:
    db = get_db()
    contract = db.execute(
        """
        SELECT c.id,
               c.contract_no AS contractNo,
               c.contract_name AS contractName,
               c.status,
               c.total_amount AS totalAmount,
               c.invoiced_amount_total AS invoicedAmountTotal,
               c.received_amount_total AS receivedAmountTotal,
               c.invoice_status AS invoiceStatus,
               c.receipt_status AS receiptStatus,
               c.sign_date AS signDate,
               cu.customer_name AS customerName,
               d.dept_name AS deptName,
               e.employee_name AS ownerName
        FROM contracts c
        JOIN customers cu ON cu.id = c.customer_id
        JOIN departments d ON d.id = c.dept_id
        JOIN employees e ON e.id = c.owner_id
        WHERE c.contract_no = ?
        """,
        (contract_no.upper(),),
    ).fetchone()
    if not contract:
        return None

    detail = get_contract_detail(int(contract["id"]))
    invoices = detail.get("invoices", []) if detail else []
    invoice_count = len(invoices)
    received_invoice_count = len([item for item in invoices if int(item.get("isReceived") or 0) == 1])
    open_invoice_count = len([item for item in invoices if int(item.get("isReceived") or 0) == 0])

    registry = current_app.config["ONTOLOGY_REGISTRY"]
    invoice_rule = registry.behaviors.get("Contract_UpdateInvoiceSummary", {})
    receipt_rule = registry.behaviors.get("Contract_UpdateReceiptSummary", {})

    normalized_question = _normalize(question)
    explain_invoice = _contains_any(normalized_question, ["开票", "发票", "未开票", "已开票"])
    explain_receipt = _contains_any(normalized_question, ["收款", "回款", "到账"])
    if not explain_invoice and not explain_receipt:
        explain_invoice = True
        explain_receipt = True

    lines = [
        f"合同 {contract['contractNo']}《{contract['contractName']}》当前客户是 {contract['customerName']}，销售部门是 {contract['deptName']}，责任人是 {contract['ownerName']}。"
    ]

    total_amount = float(contract["totalAmount"])
    invoiced_total = float(contract["invoicedAmountTotal"])
    received_total = float(contract["receivedAmountTotal"])

    if explain_invoice:
        lines.append(
            f"当前开票状态显示为“{contract['invoiceStatus']}”，因为合同总金额是 {total_amount:.2f}，累计开票金额是 {invoiced_total:.2f}。"
        )
        if invoice_count == 0:
            lines.append("该合同下目前没有任何发票记录，所以从本体语义上属于未开票合同。")
        elif invoiced_total >= total_amount:
            lines.append(
                f"根据行为 Contract_UpdateInvoiceSummary 的规则，累计开票金额达到或超过合同总金额时，合同开票状态应为“已开票”。当前合同下共有 {invoice_count} 张发票。"
            )
        else:
            lines.append(
                f"根据行为 Contract_UpdateInvoiceSummary 的规则，累计开票金额尚未达到合同总金额时，合同开票状态应为“部分开票”。当前合同下共有 {invoice_count} 张发票。"
            )

    if explain_receipt:
        lines.append(
            f"当前收款状态显示为“{contract['receiptStatus']}”，因为合同总金额是 {total_amount:.2f}，累计收款金额是 {received_total:.2f}。"
        )
        if invoice_count == 0 and received_total == 0:
            lines.append("该合同下没有发票记录，累计收款金额也为 0，因此它同时符合“未开票、未收款”的业务语义。")
        elif received_total >= total_amount:
            lines.append(
                f"根据行为 Contract_UpdateReceiptSummary 的规则，累计收款金额达到或超过合同总金额时，合同收款状态应为“已收款”。当前合同下共有 {received_invoice_count} 张已收款发票。"
            )
        else:
            lines.append(
                f"根据行为 Contract_UpdateReceiptSummary 的规则，累计收款金额尚未达到合同总金额时，合同收款状态应为“部分收款”或“未收款”。当前合同下已收款发票 {received_invoice_count} 张，未收款发票 {open_invoice_count} 张。"
            )

    if detail and detail.get("paymentTerms"):
        payment_term_count = len(detail["paymentTerms"])
        lines.append(f"该合同还配置了 {payment_term_count} 条付款条款，后续开票会基于这些付款阶段进行映射。")

    evidence = [invoice_rule, receipt_rule]
    return {
        "kind": "contract_status_explanation",
        "answer": "\n\n".join(lines),
        "evidence": [item for item in evidence if item],
    }


def _explain_invoice(invoice_no: str, question: str) -> dict[str, Any] | None:
    db = get_db()
    invoice = db.execute(
        """
        SELECT i.id,
               i.invoice_no AS invoiceNo,
               i.amount,
               i.tax_rate AS taxRate,
               i.invoice_date AS invoiceDate,
               i.status,
               i.is_received AS isReceived,
               i.received_date AS receivedDate,
               c.contract_no AS contractNo,
               c.contract_name AS contractName,
               cu.customer_name AS customerName
        FROM invoices i
        JOIN contracts c ON c.id = i.contract_id
        JOIN customers cu ON cu.id = c.customer_id
        WHERE i.invoice_no = ?
        """,
        (invoice_no.upper(),),
    ).fetchone()
    if not invoice:
        return None

    lines = [
        f"发票 {invoice['invoiceNo']} 关联合同 {invoice['contractNo']}《{invoice['contractName']}》，客户是 {invoice['customerName']}。"
    ]
    lines.append(
        f"该发票开票金额为 {float(invoice['amount']):.2f}，开票日期为 {invoice['invoiceDate']}，当前发票状态是“{invoice['status']}”。"
    )
    if int(invoice["isReceived"] or 0) == 1:
        lines.append(f"因为该发票已经确认收款，收款时间是 {invoice['receivedDate']}，所以收款状态为“已收款”。")
    else:
        lines.append("因为该发票尚未确认收款，所以收款状态为“未收款”。")

    return {
        "kind": "invoice_status_explanation",
        "answer": "\n\n".join(lines),
        "evidence": [invoice],
    }


def _group_matches(matches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for match in matches:
        match_type = match.get("type", "")
        if match_type not in result:
            result[match_type] = match
    return result


def _build_event_chain_answer(question: str, matches: list[dict[str, Any]]) -> str:
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    normalized = _normalize(question)
    chains: list[str] = []

    if _contains_any(normalized, ["开票", "发票"]):
        invoice_created = registry.events.get("Invoice.Created")
        if invoice_created:
            chains.append(
                "开票链路：Invoice_Create 执行后发布 Invoice.Created，随后由 Contract_UpdateInvoiceSummary 订阅处理，并进一步形成 Contract.InvoiceSummaryUpdated。"
            )
    if _contains_any(normalized, ["收款", "回款", "到账"]):
        payment_received = registry.events.get("Payment.Received")
        if payment_received:
            chains.append(
                "收款链路：Payment_Receive 执行后发布 Payment.Received，随后由 Contract_UpdateReceiptSummary 订阅处理，并进一步形成 Contract.ReceiptSummaryUpdated。"
            )

    if chains:
        return "相关事件流如下：" + "；".join(chains)

    event_matches = [item for item in matches if item["type"] == "event"][:4]
    if event_matches:
        return "相关事件流如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in event_matches)
    return "当前没有匹配到明确的事件链信息。"


def _build_rule_answer(question: str, matches: list[dict[str, Any]]) -> str:
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    normalized = _normalize(question)

    if _contains_any(normalized, ["合同创建", "创建合同", "合同录入", "新增合同"]):
        behavior = registry.behaviors.get("Contract_Create", {})
        if behavior:
            preconditions = "；".join(behavior.get("preconditions", []) or ["无"])
            postconditions = "；".join(
                f"{item.get('field', '')} -> {item.get('setValue', '')}" for item in behavior.get("postconditions", [])
            )
            return (
                "合同创建的关键规则主要定义在行为 Contract_Create 上。"
                f"前置约束包括：{preconditions}。"
                f"创建成功后的核心结果包括：{postconditions}。"
                "从业务语义上看，这意味着合同必须先补齐基础信息和付款条款，系统保存后会自动初始化生效、未开票、未收款等状态。"
            )

    if _contains_any(normalized, ["开票", "发票"]):
        rule_matches = [item for item in matches if item["type"] == "rule"][:3]
        if rule_matches:
            return "开票相关规则如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in rule_matches)

    if _contains_any(normalized, ["收款", "回款", "到账"]):
        behavior = registry.behaviors.get("Payment_Receive", {})
        if behavior:
            preconditions = "；".join(behavior.get("preconditions", []) or ["无"])
            postconditions = "；".join(
                f"{item.get('field', '')} -> {item.get('setValue', '')}" for item in behavior.get("postconditions", [])
            )
            return (
                "收款确认的关键规则主要定义在行为 Payment_Receive 上。"
                f"前置约束包括：{preconditions}。"
                f"执行后的结果包括：{postconditions}。"
            )

    rule_matches = [item for item in matches if item["type"] == "rule"][:3]
    behavior_matches = [item for item in matches if item["type"] == "behavior"][:2]
    parts: list[str] = []
    if rule_matches:
        parts.append("相关业务规则如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in rule_matches))
    if behavior_matches:
        parts.append("相关行为约束如下：" + "；".join(f"{item['title']}，{_trim_content(item['content'])}" for item in behavior_matches))
    return " ".join(parts) if parts else "当前没有匹配到明确的业务规则信息。"


def _trim_content(content: str, max_len: int = 180) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 1] + "…"


def _infer_focus(question: str, explicit_focus: str | None) -> str:
    if explicit_focus:
        return explicit_focus
    normalized = _normalize(question)
    if _contains_any(normalized, ["为什么", "为何", "原因", "状态", "怎么来的"]):
        return "status"
    if _contains_any(normalized, ["流程", "步骤", "过程", "如何", "怎么做"]):
        return "process"
    if _contains_any(normalized, ["规则", "校验", "约束"]):
        return "rule"
    if _contains_any(normalized, ["事件", "链路", "流转"]):
        return "event"
    if _contains_any(normalized, ["页面", "界面", "入口"]):
        return "page"
    if _contains_any(normalized, ["对象", "聚合", "实体", "关系"]):
        return "object"
    return "general"


def _extract_contract_no(question: str) -> str | None:
    match = CONTRACT_NO_PATTERN.search(question or "")
    return match.group(0).upper() if match else None


def _extract_invoice_no(question: str) -> str | None:
    match = INVOICE_NO_PATTERN.search(question or "")
    return match.group(0).upper() if match else None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)
