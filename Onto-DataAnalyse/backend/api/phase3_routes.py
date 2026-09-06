"""阶段三：场景执行

- GET  /api/phase3/scenarios       获取场景列表
- POST /api/phase3/execute         执行场景（SSE 流式）
- GET  /api/phase3/records         获取执行历史
- GET  /api/phase3/records/<id>    单次执行详情
- POST /api/phase3/confirm         推进到阶段四
"""
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.ai.scenario_executor import (
    execute_scenario, get_execution_detail, get_execution_records, load_scenario, scenarios_summary,
)
from backend.config.settings import settings
from backend.db.database import system_db
from backend.utils.sse_utils import sse_response

bp = Blueprint("phase3", __name__, url_prefix="/api/phase3")


def _ok(data=None, message="ok"):
    return jsonify({"success": True, "data": data, "message": message})


def _err(message: str, status: int = 400):
    return jsonify({"success": False, "data": None, "message": message}), status


@bp.get("/scenarios")
def list_scenarios():
    return _ok(scenarios_summary())


@bp.get("/scenarios/<scenario_id>")
def get_scenario(scenario_id: str):
    sc = load_scenario(scenario_id)
    if not sc:
        return _err(f"未找到场景 {scenario_id}", 404)
    # 移除内部字段
    sc.pop("_file", None)
    return _ok(sc)


@bp.post("/execute")
def execute():
    body = request.get_json(silent=True) or {}
    scenario_id = body.get("scenario_id")
    if not scenario_id:
        return _err("缺少 scenario_id 参数")
    if not load_scenario(scenario_id):
        return _err(f"未找到场景 {scenario_id}", 404)
    return sse_response(execute_scenario(scenario_id))


@bp.get("/records")
def list_records():
    return _ok(get_execution_records(limit=30))


@bp.get("/records/<execution_id>")
def get_record(execution_id: str):
    rec = get_execution_detail(execution_id)
    if not rec:
        return _err("记录不存在", 404)
    return _ok(rec)


@bp.post("/confirm")
def confirm():
    with system_db() as conn:
        conn.execute(
            "UPDATE projects SET current_stage = 4, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), settings.PROJECT_ID),
        )
    return _ok({"current_stage": 4}, "已确认场景执行，进入阶段四")
