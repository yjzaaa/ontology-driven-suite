from __future__ import annotations

from functools import wraps

from flask import Blueprint, Response, current_app, request, stream_with_context

from ..ai.orchestrator import chat_once, stream_chat
from ..services import auth_service, contract_service, meta_service
from ..services.domain_copilot_service import domain_explanation_query
from ..services.semantic_query_service import execute_semantic_query
from ..utils.responses import fail, ok


api_bp = Blueprint("api", __name__, url_prefix="/api")


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_app.config["APP_SETTINGS"]["auth"]["enabled"] and not auth_service.current_user():
            return fail("请先登录", "UNAUTHORIZED", 401)
        return func(*args, **kwargs)

    return wrapper


@api_bp.get("/health")
def health():
    return ok({"status": "UP", "app": current_app.config["APP_SETTINGS"]["app"]["name"]})


@api_bp.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return fail("用户名和密码不能为空")

    user = auth_service.login(username, password)
    if not user:
        return fail("用户名或密码错误", "AUTH_FAILED", 401)
    return ok(user, "登录成功")


@api_bp.post("/auth/logout")
def logout():
    auth_service.logout()
    return ok({}, "已退出登录")


@api_bp.get("/auth/me")
def current_user():
    user = auth_service.current_user()
    if not user:
        return fail("未登录", "UNAUTHORIZED", 401)
    return ok(user)


@api_bp.get("/meta/navigation")
@login_required
def navigation():
    return ok(meta_service.get_navigation())


@api_bp.get("/meta/pages")
@login_required
def pages():
    return ok(meta_service.get_pages())


@api_bp.get("/meta/page/<page_id>")
@login_required
def page_detail(page_id: str):
    page = meta_service.get_page(page_id)
    if not page:
        return fail("页面不存在", "NOT_FOUND", 404)
    return ok(page)


@api_bp.get("/meta/ontology-summary")
@login_required
def ontology_summary():
    return ok(meta_service.get_ontology_summary())


@api_bp.get("/meta/reference-data")
@login_required
def reference_data():
    return ok(meta_service.get_reference_data())


@api_bp.post("/behaviors/Contract_Create/execute")
@login_required
def contract_create():
    payload = request.get_json(silent=True) or {}
    try:
        result = contract_service.create_contract(payload, actor=auth_service.current_user()["username"])
        return ok(result, "合同录入成功")
    except ValueError as exc:
        return fail(str(exc))


@api_bp.post("/behaviors/Invoice_Create/execute")
@login_required
def invoice_create():
    payload = request.get_json(silent=True) or {}
    try:
        result = contract_service.create_invoice(payload, actor=auth_service.current_user()["username"])
        return ok(result, "开票录入成功")
    except ValueError as exc:
        return fail(str(exc))


@api_bp.post("/behaviors/Payment_Receive/execute")
@login_required
def payment_receive():
    payload = request.get_json(silent=True) or {}
    try:
        result = contract_service.receive_payment(
            int(payload["invoiceId"]),
            payload.get("receivedDate"),
            actor=auth_service.current_user()["username"],
        )
        return ok(result, "收款确认成功")
    except (ValueError, KeyError) as exc:
        return fail(str(exc))


@api_bp.post("/queries/Contract_Query/execute")
@login_required
def contract_query():
    payload = request.get_json(silent=True) or {}
    return ok(contract_service.query_contracts(payload))


@api_bp.get("/queries/Contract_GetDetail/execute")
@login_required
def contract_get_detail():
    contract_id = request.args.get("contractId", type=int)
    if not contract_id:
        return fail("contractId 不能为空")
    detail = contract_service.get_contract_detail(contract_id)
    if not detail:
        return fail("合同不存在", "NOT_FOUND", 404)
    return ok(detail)


@api_bp.post("/support/open-invoices")
@login_required
def open_invoices():
    payload = request.get_json(silent=True) or {}
    return ok(contract_service.query_open_invoices(payload))


@api_bp.get("/ai/tools")
@login_required
def ai_tools():
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    return ok(
        {
            "behaviors": list(registry.behaviors.keys()),
            "queries": [key for key, item in registry.behaviors.items() if item["behaviorType"] == "QUERY"],
            "pages": list(registry.pages.keys()),
        }
    )


@api_bp.post("/ai/semantic-query")
@login_required
def ai_semantic_query():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return fail("query 不能为空")
    return ok(
        execute_semantic_query(
            query=query,
            actor=auth_service.current_user()["username"],
            user_facing=True,
        )
    )


@api_bp.post("/ai/domain-explain")
@login_required
def ai_domain_explain():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return fail("question 不能为空")
    return ok(
        domain_explanation_query(
            question=question,
            focus=payload.get("focus"),
            contract_no=payload.get("contractNo"),
            invoice_no=payload.get("invoiceNo"),
        )
    )


@api_bp.post("/ai/chat")
@login_required
def ai_chat_once():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("sessionId")
    if not message:
        return fail("message 不能为空")
    result = chat_once(message, actor=auth_service.current_user()["username"], session_id=session_id)
    return ok(result)


@api_bp.post("/ai/chat/stream")
@login_required
def ai_chat_stream():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("sessionId")
    if not message:
        return fail("message 不能为空")

    actor = auth_service.current_user()["username"]

    def event_stream():
        yield from stream_chat(
            message=message,
            session_id=session_id,
            actor=actor,
        )

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def register_blueprints(app):
    app.register_blueprint(api_bp)
