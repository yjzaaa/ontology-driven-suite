from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..db import get_db
from .contract_service import get_contract_detail


DETAIL_KEYWORDS = ["详情", "明细", "查看", "看下", "看一看"]
AGGREGATE_KEYWORDS = ["统计", "汇总", "分析", "总额", "总金额", "金额合计", "求和", "合计"]
COUNT_KEYWORDS = ["数量", "多少", "几条", "几个", "多少条", "多少份", "多少张"]
QUERY_KEYWORDS = ["查询", "查", "列出", "显示", "看看", "给我看"]

CONTRACT_KEYWORDS = ["合同", "销售合同", "合同台账"]
INVOICE_KEYWORDS = ["发票", "开票", "已开票", "未开票"]
RECEIPT_KEYWORDS = ["收款", "回款", "到账", "回笼", "收款记录", "回款记录"]

CONTRACT_NO_PATTERN = re.compile(r"HT\d{4,}", flags=re.IGNORECASE)
INVOICE_NO_PATTERN = re.compile(r"FP\d{4,}", flags=re.IGNORECASE)

PLACEHOLDER_DEPARTMENT_WORDS = ["某部门", "特定部门", "指定部门"]
PLACEHOLDER_CUSTOMER_WORDS = ["某客户", "特定客户", "指定客户"]
PLACEHOLDER_PRODUCT_WORDS = ["某产品", "特定产品", "指定产品"]


CONTRACT_FIELD_SPECS = {
    "contractNo": ("c.contract_no", "合同编号"),
    "contractName": ("c.contract_name", "合同名称"),
    "customerName": ("cu.customer_name", "客户"),
    "productName": ("p.product_name", "产品"),
    "productType": ("p.product_type", "产品类型"),
    "deptName": ("d.dept_name", "部门"),
    "ownerName": ("e.employee_name", "销售人员"),
    "signDate": ("c.sign_date", "签订日期"),
    "totalAmount": ("ROUND(c.total_amount, 2)", "合同总金额"),
    "invoicedAmountTotal": ("ROUND(c.invoiced_amount_total, 2)", "累计开票金额"),
    "receivedAmountTotal": ("ROUND(c.received_amount_total, 2)", "累计收款金额"),
    "invoiceStatus": ("c.invoice_status", "开票状态"),
    "receiptStatus": ("c.receipt_status", "收款状态"),
}

INVOICE_FIELD_SPECS = {
    "invoiceNo": ("i.invoice_no", "发票编号"),
    "contractNo": ("c.contract_no", "合同编号"),
    "contractName": ("c.contract_name", "合同名称"),
    "deptName": ("d.dept_name", "部门"),
    "customerName": ("cu.customer_name", "客户"),
    "amount": ("ROUND(i.amount, 2)", "开票金额"),
    "invoiceDate": ("i.invoice_date", "开票日期"),
    "invoiceStatus": ("i.status", "发票状态"),
    "receiptState": ("CASE WHEN i.is_received = 1 THEN '已收款' ELSE '未收款' END", "收款状态"),
}

RECEIPT_FIELD_SPECS = {
    "invoiceNo": ("i.invoice_no", "发票编号"),
    "contractNo": ("c.contract_no", "合同编号"),
    "contractName": ("c.contract_name", "合同名称"),
    "deptName": ("d.dept_name", "部门"),
    "customerName": ("cu.customer_name", "客户"),
    "amount": ("ROUND(i.amount, 2)", "收款金额"),
    "receivedDate": ("COALESCE(i.received_date, '')", "收款日期"),
    "receiptState": ("CASE WHEN i.is_received = 1 THEN '已收款' ELSE '未收款' END", "收款状态"),
}

AGGREGATE_METRICS = {
    "contract": {
        "contract_total_amount": ("ROUND(SUM(c.total_amount), 2)", "合同总金额"),
        "invoiced_amount_total": ("ROUND(SUM(c.invoiced_amount_total), 2)", "已开票金额"),
        "received_amount_total": ("ROUND(SUM(c.received_amount_total), 2)", "已收款金额"),
        "count": ("COUNT(*)", "合同数量"),
    },
    "invoice": {
        "invoice_amount": ("ROUND(SUM(i.amount), 2)", "开票总金额"),
        "count": ("COUNT(*)", "发票数量"),
    },
    "receipt": {
        "received_amount": ("ROUND(SUM(i.amount), 2)", "收款总金额"),
        "count": ("COUNT(*)", "收款记录数"),
    },
}


@dataclass
class SemanticQueryPlan:
    subject: str = "contract"
    intent: str = "list"
    group_by: str | None = None
    metrics: list[str] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    response_preference: str = "auto"
    chart_type: str = "auto"
    original_query: str = ""
    explicit_columns: bool = False


def execute_semantic_query(
    query: str | None = None,
    plan: dict[str, Any] | None = None,
    actor: str | None = None,
    user_facing: bool = False,
):
    del actor
    semantic_plan = build_plan(plan=plan, query=query)
    result = run_plan(semantic_plan)
    if user_facing:
        return format_result_as_payload(result, semantic_plan)
    return result


def build_plan(plan: dict[str, Any] | None = None, query: str | None = None) -> SemanticQueryPlan:
    if plan:
        return _plan_from_dict(plan, query=query)
    return parse_query(query or "")


def parse_query(query: str) -> SemanticQueryPlan:
    text = normalize_query(query)
    plan = SemanticQueryPlan(original_query=text)
    plan.explicit_columns = any(token in text for token in ["输出", "列信息", "表格", "列表"])
    if contains_any(text, ["图表", "图形", "可视化", "柱状图", "条形图", "折线图", "趋势图", "饼图"]):
        plan.response_preference = "chart"
    if contains_any(text, ["柱状图", "条形图"]):
        plan.chart_type = "bar"
    elif contains_any(text, ["折线图", "趋势图"]):
        plan.chart_type = "line"
    elif contains_any(text, ["饼图"]):
        plan.chart_type = "pie"

    has_contract = contains_any(text, CONTRACT_KEYWORDS)
    has_invoice = contains_any(text, INVOICE_KEYWORDS)
    has_receipt = contains_any(text, RECEIPT_KEYWORDS)

    if contains_any(text, DETAIL_KEYWORDS) or CONTRACT_NO_PATTERN.search(text) or INVOICE_NO_PATTERN.search(text):
        plan.intent = "detail"
    elif contains_any(text, COUNT_KEYWORDS):
        plan.intent = "count"
        plan.metrics = ["count"]
    elif contains_any(text, AGGREGATE_KEYWORDS):
        plan.intent = "aggregate"
    elif contains_any(text, QUERY_KEYWORDS):
        plan.intent = "list"

    if "部门" in text:
        plan.group_by = "department" if plan.intent == "aggregate" else plan.group_by
    elif "客户" in text:
        plan.group_by = "customer" if plan.intent == "aggregate" else plan.group_by
    elif "产品" in text:
        plan.group_by = "product" if plan.intent == "aggregate" else plan.group_by
    elif contains_any(text, ["销售员", "负责人", "人员"]):
        plan.group_by = "owner" if plan.intent == "aggregate" else plan.group_by

    _apply_named_filters(plan, text)
    _apply_identifier_filters(plan, text)
    _apply_status_filters(plan, text)
    _apply_requested_fields(plan, text)
    _apply_requested_metrics(plan, text)
    plan.subject = _detect_subject(text, plan, has_contract, has_invoice, has_receipt)
    plan.metrics = _normalize_metrics_for_subject(plan.subject, plan.metrics, text)
    plan.fields = _normalize_fields_for_subject(plan.subject, plan.fields)

    if plan.intent == "aggregate" and not plan.group_by:
        if plan.filters.get("departmentName"):
            plan.group_by = "department"
        elif plan.filters.get("customerName"):
            plan.group_by = "customer"
        elif plan.filters.get("productName"):
            plan.group_by = "product"
        elif plan.filters.get("ownerName"):
            plan.group_by = "owner"

    if plan.intent == "detail" and not plan.fields:
        plan.fields = _default_detail_fields(plan.subject)
    if plan.intent == "list" and not plan.fields:
        plan.fields = _default_list_fields(plan.subject)
    if plan.intent == "aggregate" and not plan.metrics:
        plan.metrics = _default_metrics(plan.subject)
    if plan.intent == "count" and not plan.metrics:
        plan.metrics = ["count"]

    if plan.intent == "detail" and not plan.explicit_columns and len(plan.fields) <= 3:
        plan.response_preference = "text"

    return plan


def run_plan(plan: SemanticQueryPlan) -> dict[str, Any]:
    placeholder_message = _validate_placeholders(plan)
    if placeholder_message:
        return {
            "subject": plan.subject,
            "intent": plan.intent,
            "resultType": "empty",
            "summary": placeholder_message,
            "columns": [],
            "rows": [],
            "record": None,
            "recommendedPresentation": "text",
        }

    if plan.subject == "invoice":
        return _run_invoice_query(plan)
    if plan.subject == "receipt":
        return _run_receipt_query(plan)
    return _run_contract_query(plan)


def format_result_as_payload(result: dict[str, Any], plan: SemanticQueryPlan):
    if result["resultType"] == "empty":
        return {"message": result["summary"], "render": None, "action": None}

    if plan.response_preference == "text" and result["resultType"] in {"single_record", "single_value"}:
        return {"message": _render_text_answer(result), "render": None, "action": None}

    if result["resultType"] == "single_record" and not plan.explicit_columns and len(result["columns"]) <= 3:
        return {"message": _render_text_answer(result), "render": None, "action": None}

    if plan.response_preference == "chart":
        chart_render = _build_chart_render(result, plan)
        if chart_render is not None:
            return {
                "message": result["summary"],
                "render": chart_render,
                "action": None,
            }

    headers = [column["label"] for column in result["columns"]]
    return {
        "message": result["summary"],
        "render": {
            "type": "table",
            "headers": headers,
            "rows": result["rows"],
        },
        "action": None,
    }


def _run_contract_query(plan: SemanticQueryPlan) -> dict[str, Any]:
    db = get_db()
    params: list[Any] = []
    where_sql = _build_contract_where(plan.filters, params)

    if plan.intent == "count":
        row = db.execute(
            f"""
            SELECT COUNT(*) AS metricValue
            FROM contracts c
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            """,
            params,
        ).fetchone()
        return _single_value_result("合同数量", row["metricValue"], "已统计合同数量。")

    if plan.intent == "aggregate":
        group_sql, group_label = _group_by_meta(plan.group_by or "department")
        metric_defs = [_metric_meta("contract", metric) for metric in plan.metrics]
        metric_selects = [f"{expr} AS {alias}" for expr, _label, alias in metric_defs]
        rows = db.execute(
            f"""
            SELECT {group_sql} AS groupValue, {", ".join(metric_selects)}
            FROM contracts c
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            GROUP BY groupValue
            ORDER BY groupValue ASC
            """,
            params,
        ).fetchall()
        columns = [{"key": "groupValue", "label": group_label}] + [
            {"key": alias, "label": label} for _expr, label, alias in metric_defs
        ]
        table_rows = [[row["groupValue"]] + [row[alias] for _expr, _label, alias in metric_defs] for row in rows]
        return _table_result(
            f"按{group_label}统计合同信息",
            f"已按{group_label}完成合同统计。",
            columns,
            table_rows,
        )

    if plan.intent == "detail" and plan.filters.get("contractNo"):
        row = db.execute(
            f"""
            SELECT c.id
            FROM contracts c
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            ORDER BY c.sign_date DESC, c.contract_no DESC
            LIMIT 1
            """,
            params,
        ).fetchone()
        if not row:
            return _empty_result("未找到匹配的合同。")
        detail = get_contract_detail(int(row["id"]))
        record = _contract_detail_record(detail, plan.fields)
        columns = [{"key": key, "label": CONTRACT_FIELD_SPECS[key][1]} for key in record.keys()]
        return _record_result(
            "合同详情",
            f"已找到合同 {detail['contractNo']} 的信息。",
            columns,
            record,
        )

    select_defs = [_field_meta("contract", field) for field in plan.fields]
    rows = db.execute(
        f"""
        SELECT {", ".join(f"{expr} AS {alias}" for expr, _label, alias in select_defs)}
        FROM contracts c
        JOIN products p ON p.id = c.product_id
        JOIN customers cu ON cu.id = c.customer_id
        JOIN departments d ON d.id = c.dept_id
        JOIN employees e ON e.id = c.owner_id
        WHERE 1 = 1 {where_sql}
        ORDER BY c.sign_date DESC, c.contract_no DESC
        """,
        params,
    ).fetchall()
    return _table_result(
        "合同查询结果",
        f"已查询到 {len(rows)} 条合同记录。",
        [{"key": alias, "label": label} for _expr, label, alias in select_defs],
        [[row[alias] for _expr, _label, alias in select_defs] for row in rows],
    )


def _run_invoice_query(plan: SemanticQueryPlan) -> dict[str, Any]:
    db = get_db()
    params: list[Any] = []
    where_sql = _build_invoice_where(plan.filters, params)

    if plan.intent == "count":
        row = db.execute(
            f"""
            SELECT COUNT(*) AS metricValue
            FROM invoices i
            JOIN contracts c ON c.id = i.contract_id
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            """,
            params,
        ).fetchone()
        return _single_value_result("发票数量", row["metricValue"], "已统计发票数量。")

    if plan.intent == "aggregate":
        group_sql, group_label = _group_by_meta(plan.group_by or "department")
        metric_defs = [_metric_meta("invoice", metric) for metric in plan.metrics]
        rows = db.execute(
            f"""
            SELECT {group_sql} AS groupValue,
                   {", ".join(f"{expr} AS {alias}" for expr, _label, alias in metric_defs)}
            FROM invoices i
            JOIN contracts c ON c.id = i.contract_id
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            GROUP BY groupValue
            ORDER BY groupValue ASC
            """,
            params,
        ).fetchall()
        columns = [{"key": "groupValue", "label": group_label}] + [
            {"key": alias, "label": label} for _expr, label, alias in metric_defs
        ]
        return _table_result(
            f"按{group_label}统计发票信息",
            f"已按{group_label}完成发票统计。",
            columns,
            [[row["groupValue"]] + [row[alias] for _expr, _label, alias in metric_defs] for row in rows],
        )

    if plan.intent == "detail" and plan.filters.get("invoiceNo"):
        select_defs = [_field_meta("invoice", field) for field in plan.fields]
        row = db.execute(
            f"""
            SELECT {", ".join(f"{expr} AS {alias}" for expr, _label, alias in select_defs)}
            FROM invoices i
            JOIN contracts c ON c.id = i.contract_id
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            ORDER BY i.invoice_date DESC, i.invoice_no DESC
            LIMIT 1
            """,
            params,
        ).fetchone()
        if not row:
            return _empty_result("未找到匹配的发票。")
        record = {alias: row[alias] for _expr, _label, alias in select_defs}
        return _record_result(
            "发票详情",
            f"已找到发票 {record.get('invoiceNo', '')} 的信息。",
            [{"key": alias, "label": label} for _expr, label, alias in select_defs],
            record,
        )

    select_defs = [_field_meta("invoice", field) for field in plan.fields]
    rows = db.execute(
        f"""
        SELECT {", ".join(f"{expr} AS {alias}" for expr, _label, alias in select_defs)}
        FROM invoices i
        JOIN contracts c ON c.id = i.contract_id
        JOIN products p ON p.id = c.product_id
        JOIN customers cu ON cu.id = c.customer_id
        JOIN departments d ON d.id = c.dept_id
        JOIN employees e ON e.id = c.owner_id
        WHERE 1 = 1 {where_sql}
        ORDER BY i.invoice_date DESC, i.invoice_no DESC
        """,
        params,
    ).fetchall()
    title = "已开票未收款发票" if plan.filters.get("invoiceReceiptState") == "open_unreceived" else "发票查询结果"
    return _table_result(
        title,
        f"已查询到 {len(rows)} 条发票记录。",
        [{"key": alias, "label": label} for _expr, label, alias in select_defs],
        [[row[alias] for _expr, _label, alias in select_defs] for row in rows],
    )


def _run_receipt_query(plan: SemanticQueryPlan) -> dict[str, Any]:
    db = get_db()
    params: list[Any] = []
    where_sql = _build_receipt_where(plan.filters, params)

    if plan.intent == "count":
        row = db.execute(
            f"""
            SELECT COUNT(*) AS metricValue
            FROM invoices i
            JOIN contracts c ON c.id = i.contract_id
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            """,
            params,
        ).fetchone()
        return _single_value_result("收款记录数", row["metricValue"], "已统计收款记录数量。")

    if plan.intent == "aggregate":
        group_sql, group_label = _group_by_meta(plan.group_by or "department")
        metric_defs = [_metric_meta("receipt", metric) for metric in plan.metrics]
        rows = db.execute(
            f"""
            SELECT {group_sql} AS groupValue,
                   {", ".join(f"{expr} AS {alias}" for expr, _label, alias in metric_defs)}
            FROM invoices i
            JOIN contracts c ON c.id = i.contract_id
            JOIN products p ON p.id = c.product_id
            JOIN customers cu ON cu.id = c.customer_id
            JOIN departments d ON d.id = c.dept_id
            JOIN employees e ON e.id = c.owner_id
            WHERE 1 = 1 {where_sql}
            GROUP BY groupValue
            ORDER BY groupValue ASC
            """,
            params,
        ).fetchall()
        columns = [{"key": "groupValue", "label": group_label}] + [
            {"key": alias, "label": label} for _expr, label, alias in metric_defs
        ]
        return _table_result(
            f"按{group_label}统计收款信息",
            f"已按{group_label}完成收款统计。",
            columns,
            [[row["groupValue"]] + [row[alias] for _expr, _label, alias in metric_defs] for row in rows],
        )

    select_defs = [_field_meta("receipt", field) for field in plan.fields]
    rows = db.execute(
        f"""
        SELECT {", ".join(f"{expr} AS {alias}" for expr, _label, alias in select_defs)}
        FROM invoices i
        JOIN contracts c ON c.id = i.contract_id
        JOIN products p ON p.id = c.product_id
        JOIN customers cu ON cu.id = c.customer_id
        JOIN departments d ON d.id = c.dept_id
        JOIN employees e ON e.id = c.owner_id
        WHERE 1 = 1 {where_sql}
        ORDER BY CASE WHEN i.received_date IS NULL THEN 1 ELSE 0 END, i.received_date DESC, i.invoice_no DESC
        """,
        params,
    ).fetchall()
    title = "未收款记录" if plan.filters.get("receiptState") == "unreceived" else "收款查询结果"
    return _table_result(
        title,
        f"已查询到 {len(rows)} 条收款记录。",
        [{"key": alias, "label": label} for _expr, label, alias in select_defs],
        [[row[alias] for _expr, _label, alias in select_defs] for row in rows],
    )


def _plan_from_dict(plan: dict[str, Any], query: str | None = None) -> SemanticQueryPlan:
    subject = str(plan.get("subject") or "contract").strip().lower()
    intent = str(plan.get("intent") or "list").strip().lower()
    response_preference = str(plan.get("responsePreference") or "auto").strip().lower()
    group_by = plan.get("groupBy")
    group_by = str(group_by).strip().lower() if group_by else None

    semantic_plan = SemanticQueryPlan(
        subject=subject if subject in {"contract", "invoice", "receipt"} else "contract",
        intent=intent if intent in {"list", "aggregate", "detail", "count"} else "list",
        group_by=group_by if group_by in {"department", "customer", "product", "owner"} else None,
        metrics=_normalize_string_list(plan.get("metrics")),
        fields=_normalize_string_list(plan.get("fields")),
        filters=plan.get("filters") or {},
        response_preference=response_preference if response_preference in {"auto", "text", "table", "chart"} else "auto",
        chart_type=str(plan.get("chartType") or "auto").strip().lower(),
        original_query=normalize_query(query or ""),
    )
    semantic_plan.metrics = _normalize_metrics_for_subject(semantic_plan.subject, semantic_plan.metrics, semantic_plan.original_query)
    semantic_plan.fields = _normalize_fields_for_subject(semantic_plan.subject, semantic_plan.fields)

    if not semantic_plan.fields and semantic_plan.intent in {"list", "detail"}:
        semantic_plan.fields = (
            _default_detail_fields(semantic_plan.subject)
            if semantic_plan.intent == "detail"
            else _default_list_fields(semantic_plan.subject)
        )
    if not semantic_plan.metrics and semantic_plan.intent == "aggregate":
        semantic_plan.metrics = _default_metrics(semantic_plan.subject)
    if semantic_plan.intent == "count":
        semantic_plan.metrics = ["count"]

    return semantic_plan


def _apply_named_filters(plan: SemanticQueryPlan, text: str):
    db = get_db()

    department = _resolve_named_entity(
        text,
        db.execute("SELECT dept_name AS name FROM departments ORDER BY LENGTH(dept_name) DESC, dept_name").fetchall(),
    )
    if department:
        plan.filters["departmentName"] = department

    customer = _resolve_named_entity(
        text,
        db.execute(
            "SELECT customer_name AS name FROM customers ORDER BY LENGTH(customer_name) DESC, customer_name"
        ).fetchall(),
    )
    if customer:
        plan.filters["customerName"] = customer

    product = _resolve_named_entity(
        text,
        db.execute(
            """
            SELECT name
            FROM (
                SELECT product_name AS name FROM products
                UNION
                SELECT product_type AS name FROM products
            )
            ORDER BY LENGTH(name) DESC, name
            """
        ).fetchall(),
    )
    if product:
        plan.filters["productName"] = product

    owner = _resolve_named_entity(
        text,
        db.execute(
            "SELECT employee_name AS name FROM employees ORDER BY LENGTH(employee_name) DESC, employee_name"
        ).fetchall(),
    )
    if owner:
        plan.filters["ownerName"] = owner


def _apply_identifier_filters(plan: SemanticQueryPlan, text: str):
    contract_match = CONTRACT_NO_PATTERN.search(text)
    invoice_match = INVOICE_NO_PATTERN.search(text)
    if contract_match:
        plan.filters["contractNo"] = contract_match.group(0).upper()
    if invoice_match:
        plan.filters["invoiceNo"] = invoice_match.group(0).upper()


def _apply_status_filters(plan: SemanticQueryPlan, text: str):
    if contains_any(
        text,
        [
            "既没有开票也没有收款",
            "既没有开票，也没有收款",
            "没有开票也没有收款",
            "没有开票，也没有收款",
            "未开票且未收款",
            "未开票并且未收款",
            "没有发票也没有收款",
        ],
    ):
        plan.filters["contractState"] = "not_invoiced_unreceived"
        plan.filters["invoiceState"] = "not_invoiced"
        plan.filters["receiptState"] = "unreceived"
        return

    if contains_any(
        text,
        ["已开票未收款", "已开票还未收款", "已经开票未收款", "已经开票还未收款", "开票未收款", "待收款发票"],
    ):
        plan.filters["invoiceReceiptState"] = "open_unreceived"
        return

    if contains_any(text, ["未开票", "没有开票", "尚未开票"]):
        plan.filters["invoiceState"] = "not_invoiced"
    elif contains_any(text, ["已开票", "开过票"]):
        plan.filters["invoiceState"] = "invoiced"

    if contains_any(text, ["已收款", "已回款", "已到账"]):
        plan.filters["receiptState"] = "received"
    elif contains_any(text, ["未收款", "未回款", "未到账", "待收款"]):
        plan.filters["receiptState"] = "unreceived"


def _apply_requested_fields(plan: SemanticQueryPlan, text: str):
    mappings = [
        ("contractNo", ["合同编号"]),
        ("contractName", ["合同名称"]),
        ("customerName", ["客户"]),
        ("productName", ["产品"]),
        ("productType", ["产品类型"]),
        ("deptName", ["销售部门", "部门"]),
        ("ownerName", ["销售人员", "负责人"]),
        ("signDate", ["签订日期"]),
        ("totalAmount", ["合同总金额", "合同金额", "总金额"]),
        ("invoicedAmountTotal", ["已开票金额", "累计开票金额"]),
        ("receivedAmountTotal", ["已收款金额", "累计收款金额", "回款金额"]),
        ("invoiceNo", ["发票编号"]),
        ("amount", ["开票金额", "收款金额"]),
        ("invoiceDate", ["开票日期"]),
        ("receivedDate", ["收款日期"]),
        ("invoiceStatus", ["开票状态", "发票状态"]),
        ("receiptStatus", ["收款状态"]),
        ("receiptState", ["收款状态"]),
    ]
    for field, keywords in mappings:
        if contains_any(text, keywords):
            plan.fields.append(field)
    plan.fields = _dedupe(plan.fields)


def _apply_requested_metrics(plan: SemanticQueryPlan, text: str):
    metric_keywords = [
        ("contract_total_amount", ["合同总金额", "合同金额", "总金额"]),
        ("invoiced_amount_total", ["已开票金额", "累计开票金额"]),
        ("received_amount_total", ["已收款金额", "累计收款金额", "回款金额"]),
        ("invoice_amount", ["开票金额", "开票总金额"]),
        ("received_amount", ["收款金额", "收款总金额", "回款金额"]),
        ("count", ["数量", "多少", "几条", "几个"]),
    ]
    for metric, keywords in metric_keywords:
        if contains_any(text, keywords):
            plan.metrics.append(metric)
    plan.metrics = _dedupe(plan.metrics)


def _detect_subject(text: str, plan: SemanticQueryPlan, has_contract: bool, has_invoice: bool, has_receipt: bool) -> str:
    if "合同" in text and "发票" not in text and "收款记录" not in text and "回款记录" not in text:
        return "contract"
    if plan.filters.get("contractNo"):
        return "contract"
    if plan.filters.get("invoiceNo"):
        return "invoice"
    if contains_any(text, ["收款记录", "回款记录", "收款总金额", "收款金额", "回款金额"]):
        return "receipt"
    if contains_any(text, ["发票记录", "已开票未收款发票", "待收款发票"]):
        return "invoice"
    if contains_any(text, ["未开票合同", "已开票未收款合同"]):
        return "contract"
    if has_receipt and not has_contract and not has_invoice:
        return "receipt"
    if has_invoice and not has_contract:
        return "invoice"
    if has_contract:
        return "contract"
    return "contract"


def _validate_placeholders(plan: SemanticQueryPlan) -> str | None:
    text = plan.original_query
    if contains_any(text, PLACEHOLDER_DEPARTMENT_WORDS) and not plan.filters.get("departmentName"):
        return "请补充具体部门名称，例如“查询销售一部的收款”。"
    if contains_any(text, PLACEHOLDER_CUSTOMER_WORDS) and not plan.filters.get("customerName"):
        return "请补充具体客户名称，例如“查询华东能源集团已开票未收款合同”。"
    if contains_any(text, PLACEHOLDER_PRODUCT_WORDS) and not plan.filters.get("productName"):
        return "请补充具体产品或产品类型，例如“统计运维服务合同总金额”。"
    return None


def _build_contract_where(filters: dict[str, Any], params: list[Any]) -> str:
    clauses = _build_shared_clauses(filters, params)
    if filters.get("contractState") == "not_invoiced_unreceived":
        clauses.append("NOT EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id)")
        return "" if not clauses else " AND " + " AND ".join(clauses)
    if filters.get("invoiceReceiptState") == "open_unreceived":
        clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM invoices i2
                WHERE i2.contract_id = c.id
                  AND i2.status = '已开票'
                  AND i2.is_received = 0
            )
            """
        )
    if filters.get("invoiceState") == "invoiced":
        clauses.append("EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id)")
    if filters.get("invoiceState") == "not_invoiced":
        clauses.append("NOT EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id)")
    if filters.get("receiptState") == "received":
        clauses.append("EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id AND i2.is_received = 1)")
    elif filters.get("receiptState") == "unreceived":
        if filters.get("invoiceState") == "not_invoiced":
            clauses.append("NOT EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id)")
        else:
            clauses.append("EXISTS (SELECT 1 FROM invoices i2 WHERE i2.contract_id = c.id AND i2.is_received = 0)")
    return "" if not clauses else " AND " + " AND ".join(clauses)


def _build_invoice_where(filters: dict[str, Any], params: list[Any]) -> str:
    clauses = _build_shared_clauses(filters, params, allow_invoice_no=True)
    if filters.get("invoiceReceiptState") == "open_unreceived":
        clauses.append("i.status = '已开票'")
        clauses.append("i.is_received = 0")
    if filters.get("invoiceState") == "invoiced":
        clauses.append("i.status IN ('已开票', '已收款')")
    if filters.get("receiptState") == "received":
        clauses.append("i.is_received = 1")
    elif filters.get("receiptState") == "unreceived":
        clauses.append("i.is_received = 0")
    return "" if not clauses else " AND " + " AND ".join(clauses)


def _build_receipt_where(filters: dict[str, Any], params: list[Any]) -> str:
    clauses = _build_shared_clauses(filters, params, allow_invoice_no=True)
    if filters.get("invoiceReceiptState") == "open_unreceived":
        clauses.append("i.status = '已开票'")
        clauses.append("i.is_received = 0")
    elif filters.get("receiptState") == "unreceived":
        clauses.append("i.is_received = 0")
    else:
        clauses.append("i.is_received = 1")
    return "" if not clauses else " AND " + " AND ".join(clauses)


def _build_shared_clauses(filters: dict[str, Any], params: list[Any], allow_invoice_no: bool = False) -> list[str]:
    clauses: list[str] = []
    if contract_no := filters.get("contractNo"):
        clauses.append("c.contract_no = ?")
        params.append(contract_no)
    if allow_invoice_no and (invoice_no := filters.get("invoiceNo")):
        clauses.append("i.invoice_no = ?")
        params.append(invoice_no)
    if department_name := filters.get("departmentName"):
        clauses.append("d.dept_name = ?")
        params.append(department_name)
    if customer_name := filters.get("customerName"):
        clauses.append("cu.customer_name = ?")
        params.append(customer_name)
    if product_name := filters.get("productName"):
        clauses.append("(p.product_name = ? OR p.product_type = ?)")
        params.extend([product_name, product_name])
    if owner_name := filters.get("ownerName"):
        clauses.append("e.employee_name = ?")
        params.append(owner_name)
    return clauses


def _field_meta(subject: str, field: str):
    specs = CONTRACT_FIELD_SPECS
    if subject == "invoice":
        specs = INVOICE_FIELD_SPECS
    elif subject == "receipt":
        specs = RECEIPT_FIELD_SPECS
    expr, label = specs[field]
    return expr, label, field


def _metric_meta(subject: str, metric: str):
    expr, label = AGGREGATE_METRICS[subject][metric]
    return expr, label, metric


def _group_by_meta(group_by: str):
    mapping = {
        "department": ("d.dept_name", "部门"),
        "customer": ("cu.customer_name", "客户"),
        "product": ("p.product_type", "产品类型"),
        "owner": ("e.employee_name", "销售人员"),
    }
    return mapping[group_by]


def _contract_detail_record(detail: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    source = {
        "contractNo": detail["contractNo"],
        "contractName": detail["contractName"],
        "customerName": detail["customerName"],
        "productName": detail["productName"],
        "productType": detail["productType"],
        "deptName": detail["deptName"],
        "ownerName": detail["ownerName"],
        "signDate": detail["signDate"],
        "totalAmount": round(float(detail["totalAmount"]), 2),
        "invoicedAmountTotal": round(float(detail["invoicedAmountTotal"]), 2),
        "receivedAmountTotal": round(float(detail["receivedAmountTotal"]), 2),
        "invoiceStatus": detail["invoiceStatus"],
        "receiptStatus": detail["receiptStatus"],
    }
    return {field: source[field] for field in fields if field in source}


def _record_result(title: str, summary: str, columns: list[dict[str, str]], record: dict[str, Any]):
    return {
        "title": title,
        "summary": summary,
        "subject": "record",
        "resultType": "single_record",
        "columns": columns,
        "rows": [[record[column["key"]] for column in columns]],
        "record": record,
        "recommendedPresentation": "text",
    }


def _table_result(title: str, summary: str, columns: list[dict[str, str]], rows: list[list[Any]]):
    return {
        "title": title,
        "summary": summary,
        "resultType": "table",
        "columns": columns,
        "rows": rows,
        "record": None,
        "recommendedPresentation": "table",
    }


def _single_value_result(label: str, value: Any, summary: str):
    return {
        "title": label,
        "summary": summary,
        "resultType": "single_value",
        "columns": [{"key": "value", "label": label}],
        "rows": [[value]],
        "record": {"value": value},
        "recommendedPresentation": "text",
    }


def _empty_result(summary: str):
    return {
        "title": "",
        "summary": summary,
        "resultType": "empty",
        "columns": [],
        "rows": [],
        "record": None,
        "recommendedPresentation": "text",
    }


def _render_text_answer(result: dict[str, Any]) -> str:
    if result["resultType"] == "single_value":
        label = result["columns"][0]["label"]
        return f"{label}是 {format_value(result['rows'][0][0])}。"

    if result["resultType"] == "single_record" and result["record"]:
        fragments = []
        contract_no = result["record"].get("contractNo")
        invoice_no = result["record"].get("invoiceNo")
        prefix = "查询结果"
        if contract_no:
            prefix = f"合同 {contract_no}"
        elif invoice_no:
            prefix = f"发票 {invoice_no}"
        for column in result["columns"]:
            key = column["key"]
            if key in {"contractNo", "invoiceNo"}:
                continue
            fragments.append(f"{column['label']}是 {format_value(result['record'][key])}")
        if fragments:
            return f"{prefix}，" + "，".join(fragments) + "。"
    return result["summary"]


def _default_metrics(subject: str) -> list[str]:
    if subject == "invoice":
        return ["invoice_amount"]
    if subject == "receipt":
        return ["received_amount"]
    return ["contract_total_amount"]


def _normalize_metrics_for_subject(subject: str, metrics: list[str], text: str) -> list[str]:
    allowed = set(AGGREGATE_METRICS[subject].keys())
    normalized = [metric for metric in metrics if metric in allowed]
    if normalized:
        return _dedupe(normalized)

    if subject == "receipt":
        if contains_any(text, ["收款金额", "收款总金额", "回款金额"]):
            return ["received_amount"]
    if subject == "invoice":
        if contains_any(text, ["开票金额", "开票总金额"]):
            return ["invoice_amount"]
    if subject == "contract":
        if contains_any(text, ["已开票金额", "累计开票金额"]):
            return ["invoiced_amount_total"]
        if contains_any(text, ["已收款金额", "累计收款金额", "回款金额"]):
            return ["received_amount_total"]
        if contains_any(text, ["合同总金额", "合同金额", "总金额"]):
            return ["contract_total_amount"]

    return []


def _normalize_fields_for_subject(subject: str, fields: list[str]) -> list[str]:
    if subject == "invoice":
        allowed = set(INVOICE_FIELD_SPECS.keys())
    elif subject == "receipt":
        allowed = set(RECEIPT_FIELD_SPECS.keys())
    else:
        allowed = set(CONTRACT_FIELD_SPECS.keys())
    return [field for field in _dedupe(fields) if field in allowed]


def _default_list_fields(subject: str) -> list[str]:
    if subject == "invoice":
        return ["invoiceNo", "contractNo", "contractName", "deptName", "customerName", "amount", "invoiceDate", "invoiceStatus", "receiptState"]
    if subject == "receipt":
        return ["invoiceNo", "contractNo", "contractName", "deptName", "customerName", "amount", "receivedDate", "receiptState"]
    return ["contractNo", "contractName", "customerName", "productName", "deptName", "ownerName", "signDate", "totalAmount", "invoicedAmountTotal", "receivedAmountTotal", "invoiceStatus", "receiptStatus"]


def _default_detail_fields(subject: str) -> list[str]:
    if subject == "invoice":
        return ["invoiceNo", "contractNo", "contractName", "customerName", "amount", "invoiceDate", "invoiceStatus", "receiptState"]
    if subject == "receipt":
        return ["invoiceNo", "contractNo", "contractName", "customerName", "amount", "receivedDate", "receiptState"]
    return ["contractNo", "contractName", "customerName", "deptName", "ownerName", "totalAmount", "invoicedAmountTotal", "receivedAmountTotal", "invoiceStatus", "receiptStatus"]


def _default_table_title(plan: SemanticQueryPlan) -> str:
    if plan.subject == "invoice":
        return "发票查询结果"
    if plan.subject == "receipt":
        return "收款查询结果"
    return "合同查询结果"


def _build_chart_render(result: dict[str, Any], plan: SemanticQueryPlan):
    if result["resultType"] != "table":
        return None
    if len(result["columns"]) < 2 or not result["rows"]:
        return None

    headers = [column["label"] for column in result["columns"]]
    rows = result["rows"]
    chart_type = plan.chart_type if plan.chart_type in {"bar", "line", "pie"} else _infer_chart_type(result, plan)
    option = _build_echarts_option(headers, rows, chart_type)
    return {
        "type": "chart",
        "option": option,
    }


def _infer_chart_type(result: dict[str, Any], plan: SemanticQueryPlan) -> str:
    if plan.chart_type in {"bar", "line", "pie"}:
        return plan.chart_type
    if plan.intent == "aggregate":
        return "bar"
    return "line"


def _build_echarts_option(headers: list[str], rows: list[list[Any]], chart_type: str):
    palette = ["#155eef", "#0f766e", "#d97706", "#dc2626", "#0891b2"]
    categories = [str(row[0]) for row in rows]

    if chart_type == "pie":
        series = [
            {
                "type": "pie",
                "radius": ["38%", "68%"],
                "center": ["50%", "52%"],
                "label": {"color": "#475467", "fontSize": 12},
                "itemStyle": {"borderRadius": 10, "borderColor": "#ffffff", "borderWidth": 2},
                "data": [
                    {
                        "name": str(row[0]),
                        "value": _to_number(row[1]),
                    }
                    for row in rows
                ],
            }
        ]
        return {
            "color": palette,
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 0, "textStyle": {"color": "#344054", "fontSize": 12}},
            "series": series,
        }

    series = []
    for index, header in enumerate(headers[1:], start=1):
        series.append(
            {
                "name": header,
                "type": chart_type,
                "smooth": chart_type == "line",
                "barMaxWidth": 36 if chart_type == "bar" else None,
                "symbol": "circle" if chart_type == "line" else None,
                "symbolSize": 8 if chart_type == "line" else None,
                "data": [_to_number(row[index]) for row in rows],
            }
        )

    return {
        "color": palette,
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 0, "textStyle": {"color": "#344054", "fontSize": 12}},
        "grid": {"left": 16, "right": 16, "top": 44, "bottom": 28, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {"color": "#475467"},
            "axisLine": {"lineStyle": {"color": "#D0D5DD"}},
            "axisTick": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": "#475467"},
            "splitLine": {"lineStyle": {"color": "#EAECF0"}},
        },
        "series": series,
    }


def _resolve_named_entity(text: str, rows: list[dict[str, Any]]) -> str | None:
    for row in rows:
        candidate = str(row["name"]).strip()
        if candidate and candidate in text:
            return candidate
    return None


def _normalize_string_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", "", (query or "").strip())


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def _to_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0
