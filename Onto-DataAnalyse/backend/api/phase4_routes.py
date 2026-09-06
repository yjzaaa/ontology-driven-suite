"""阶段四：对话与报告"""
from flask import Blueprint, jsonify, request

from backend.ai.chat_handler import (
    detect_intent, ensure_default_session, handle_chat,
    list_messages, list_sessions,
)
from backend.ai.scenario_executor import scenarios_summary
from backend.utils.sse_utils import sse_response

bp = Blueprint("phase4", __name__, url_prefix="/api/phase4")


def _ok(data=None, message="ok"):
    return jsonify({"success": True, "data": data, "message": message})


def _err(message: str, status: int = 400):
    return jsonify({"success": False, "data": None, "message": message}), status


@bp.post("/chat")
def chat():
    body = request.get_json(silent=True) or {}
    user_message = (body.get("message") or "").strip()
    if not user_message:
        return _err("缺少 message")
    session_id = body.get("session_id") or ensure_default_session()
    return sse_response(handle_chat(session_id, user_message))


@bp.get("/sessions")
def sessions_list():
    sid = ensure_default_session()    # 确保至少有默认会话
    return _ok({"default_session_id": sid, "sessions": list_sessions()})


@bp.get("/messages/<session_id>")
def messages(session_id: str):
    return _ok(list_messages(session_id))


@bp.post("/intent")
def intent():
    """单纯做意图识别（前端可在用户输入时实时显示）"""
    body = request.get_json(silent=True) or {}
    msg = (body.get("message") or "").strip()
    if not msg:
        return _err("缺少 message")
    return _ok(detect_intent(msg))


@bp.get("/scenarios")
def quick_scenarios():
    """前端快捷入口的场景列表（与 phase3 复用一致）"""
    return _ok(scenarios_summary())
