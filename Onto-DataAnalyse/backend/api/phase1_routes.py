"""阶段一：需求探索

接口：
- POST /api/phase1/upload   上传两份 Markdown 文件（multipart 或 JSON 文本）
- POST /api/phase1/analyze  SSE 流式 AI 解析需求
- GET  /api/phase1/state    获取阶段一当前状态（已上传内容、已解析需求）
- POST /api/phase1/confirm  确认需求，推进到阶段二
"""
import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.ai.deepseek_client import get_client
from backend.ai.prompt_builder import build_phase1_messages
from backend.config.settings import settings
from backend.db.database import system_db
from backend.utils.sse_utils import sse_pack_raw, sse_response

bp = Blueprint("phase1", __name__, url_prefix="/api/phase1")


def _ok(data=None, message="ok"):
    return jsonify({"success": True, "data": data, "message": message})


def _err(message: str, status: int = 400):
    return jsonify({"success": False, "data": None, "message": message}), status


def _get_project_row():
    with system_db() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (settings.PROJECT_ID,)
        ).fetchone()
        return dict(row) if row else None


def _update_project(**fields) -> None:
    if not fields:
        return
    fields["updated_at"] = datetime.utcnow().isoformat()
    cols = ", ".join([f"{k} = ?" for k in fields])
    vals = list(fields.values()) + [settings.PROJECT_ID]
    with system_db() as conn:
        conn.execute(f"UPDATE projects SET {cols} WHERE id = ?", vals)


# ============================================================
# POST /api/phase1/upload
#   接受 multipart/form-data（fields: db_schema, requirement）
#   或 application/json（fields: db_schema_doc, requirement_doc）
# ============================================================
@bp.post("/upload")
def upload():
    db_schema_text = ""
    req_text = ""

    if request.content_type and "multipart/form-data" in request.content_type:
        f1 = request.files.get("db_schema")
        f2 = request.files.get("requirement")
        if not f1 or not f2:
            return _err("请同时上传 db_schema 与 requirement 两个文件")
        try:
            db_schema_text = f1.read().decode("utf-8")
            req_text = f2.read().decode("utf-8")
        except UnicodeDecodeError:
            return _err("仅支持 UTF-8 编码的文本文件（.md / .txt）")
    else:
        data = request.get_json(silent=True) or {}
        db_schema_text = (data.get("db_schema_doc") or "").strip()
        req_text = (data.get("requirement_doc") or "").strip()
        if not db_schema_text or not req_text:
            return _err("请提供 db_schema_doc 与 requirement_doc 两个字段")

    if len(db_schema_text) > 200_000 or len(req_text) > 200_000:
        return _err("单文件长度超过 200KB，请精简后重试")

    _update_project(
        db_schema_doc=db_schema_text,
        requirement_doc=req_text,
    )
    return _ok(
        {
            "db_schema_chars": len(db_schema_text),
            "requirement_chars": len(req_text),
        },
        "上传成功",
    )


# ============================================================
# GET /api/phase1/state
# ============================================================
@bp.get("/state")
def get_state():
    proj = _get_project_row()
    if not proj:
        return _err("默认项目未初始化", 500)
    parsed = None
    if proj.get("requirement_doc") and proj.get("ontology_data"):
        # ontology_data 在阶段二才用，这里我们用一个独立字段存 parsed requirement
        pass
    parsed_raw = proj.get("requirement_doc_parsed")
    try:
        parsed = json.loads(parsed_raw) if parsed_raw else None
    except (TypeError, json.JSONDecodeError):
        parsed = None
    return _ok({
        "has_db_schema": bool(proj.get("db_schema_doc")),
        "has_requirement": bool(proj.get("requirement_doc")),
        "db_schema_preview": (proj.get("db_schema_doc") or "")[:800],
        "requirement_preview": (proj.get("requirement_doc") or "")[:800],
        "parsed_requirement": parsed,
        "current_stage": proj.get("current_stage", 1),
    })


# ============================================================
# POST /api/phase1/analyze  (SSE)
#   把已上传的两份文档发给 DeepSeek，流式返回解析结果
#   消息类型：
#     {"type":"start"}
#     {"type":"delta","delta":"...片段..."}
#     {"type":"parsed","data":{...完整结构化需求...}}
#     {"type":"error","message":"..."}
#     {"type":"done"}
# ============================================================
@bp.post("/analyze")
def analyze():
    proj = _get_project_row()
    if not proj or not proj.get("db_schema_doc") or not proj.get("requirement_doc"):
        return _err("请先上传 DB Schema 与需求文档", 400)

    db_schema = proj["db_schema_doc"]
    req_text = proj["requirement_doc"]

    def gen():
        yield sse_pack_raw({"type": "start"})
        client = get_client()
        messages = build_phase1_messages(db_schema, req_text)
        full_text = ""
        try:
            for chunk in client.chat_stream(messages, phase_key="phase1_requirement"):
                full_text += chunk
                yield sse_pack_raw({"type": "delta", "delta": chunk})
        except Exception as e:
            yield sse_pack_raw({"type": "error", "message": str(e)})
            return

        parsed = _try_parse_json(full_text)
        if parsed is None:
            yield sse_pack_raw({
                "type": "error",
                "message": "AI 返回的内容无法解析为 JSON，请重试或修整上传文档",
                "raw_preview": full_text[:500],
            })
            return

        # 落盘 parsed requirement
        _persist_parsed_requirement(parsed)
        yield sse_pack_raw({"type": "parsed", "data": parsed})
        yield sse_pack_raw({"type": "done"})

    return sse_response(gen())


# ============================================================
# POST /api/phase1/confirm
#   推进到阶段二
# ============================================================
@bp.post("/confirm")
def confirm():
    proj = _get_project_row()
    if not proj:
        return _err("默认项目未初始化", 500)
    if not proj.get("requirement_doc_parsed"):
        return _err("请先完成 AI 需求解析", 400)
    _update_project(current_stage=2)
    return _ok({"current_stage": 2}, "已确认需求，进入阶段二")


# ============================================================
# 辅助
# ============================================================
def _try_parse_json(text: str) -> dict | None:
    """尽力解析 LLM 输出中的 JSON（容忍代码块包裹）"""
    text = text.strip()
    # 1) 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 2) 截取首个 { 到末尾最后一个 } 之间的内容
    l = text.find("{")
    r = text.rfind("}")
    if l == -1 or r == -1 or r <= l:
        return None
    snippet = text[l : r + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def _persist_parsed_requirement(parsed: dict) -> None:
    """把 parsed JSON 持久化到 projects.requirement_doc_parsed"""
    _update_project(requirement_doc_parsed=json.dumps(parsed, ensure_ascii=False))
