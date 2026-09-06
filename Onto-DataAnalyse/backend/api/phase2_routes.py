"""阶段二：本体建模

接口：
- POST /api/phase2/generate           SSE 流式生成 5 个 YAML + 映射
- GET  /api/phase2/graph              获取当前已生成模型的完整图谱
- GET  /api/phase2/mapping            获取字段级映射可视化数据
- GET  /api/phase2/yaml/<model_key>   获取指定模型的 YAML 原文
- POST /api/phase2/confirm            确认本体并推进到阶段三
"""
import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.ai.ontology_orchestrator import GENERATION_ORDER, orchestrate_ontology_generation
from backend.config.settings import settings
from backend.core import graph_builder, mapping_engine, ontology_engine
from backend.db.database import system_db
from backend.utils.sse_utils import sse_response
from backend.utils.yaml_utils import dump_yaml

bp = Blueprint("phase2", __name__, url_prefix="/api/phase2")


def _ok(data=None, message="ok"):
    return jsonify({"success": True, "data": data, "message": message})


def _err(message: str, status: int = 400):
    return jsonify({"success": False, "data": None, "message": message}), status


# ============================================================
# POST /api/phase2/generate (SSE)
# ============================================================
@bp.post("/generate")
def generate():
    return sse_response(orchestrate_ontology_generation())


# ============================================================
# GET /api/phase2/graph
# ============================================================
@bp.get("/graph")
def get_graph():
    models = ontology_engine.load_all_models()
    if not models:
        return _ok({"nodes": [], "edges": [], "stats": {}}, "尚未生成本体")
    g = graph_builder.build_graph(models)
    return _ok(g)


# ============================================================
# GET /api/phase2/mapping
# ============================================================
@bp.get("/mapping")
def get_mapping():
    mapping = mapping_engine.load_mapping()
    if not mapping:
        return _ok({"entities": [], "tables": [], "links": [], "stats": {}}, "尚未生成映射")
    m1 = ontology_engine.load_model_yaml("M1")
    viz = mapping_engine.build_mapping_visualization(mapping, m1)
    return _ok(viz)


# ============================================================
# GET /api/phase2/yaml/<model_key>
# 返回指定模型的 YAML 原文
# ============================================================
@bp.get("/yaml/<model_key>")
def get_yaml(model_key: str):
    if model_key not in ontology_engine.MODEL_FILES:
        return _err(f"未知模型 key：{model_key}（合法值：{list(ontology_engine.MODEL_FILES.keys())}）")
    data = ontology_engine.load_model_yaml(model_key)
    if data is None:
        return _err(f"模型 {model_key} 尚未生成", 404)
    return _ok({
        "model_key": model_key,
        "filename": ontology_engine.MODEL_FILES[model_key],
        "yaml_text": dump_yaml(data),
        "summary": ontology_engine.model_summary(data, model_key),
    })


# ============================================================
# GET /api/phase2/state
# 综合状态：每个模型是否已生成、映射是否已生成
# ============================================================
@bp.get("/state")
def get_state():
    state = {
        "models": {},
        "has_mapping": False,
        "current_stage": 1,
    }
    for k in GENERATION_ORDER:
        d = ontology_engine.load_model_yaml(k)
        state["models"][k] = {
            "ready": d is not None,
            "summary": ontology_engine.model_summary(d, k) if d else None,
        }
    state["has_mapping"] = mapping_engine.load_mapping() is not None
    with system_db() as conn:
        row = conn.execute(
            "SELECT current_stage FROM projects WHERE id = ?", (settings.PROJECT_ID,)
        ).fetchone()
        if row:
            state["current_stage"] = row["current_stage"]
    return _ok(state)


# ============================================================
# POST /api/phase2/confirm
# ============================================================
@bp.post("/confirm")
def confirm():
    # 必须 5 个模型都已生成且 mapping 也已生成
    missing = [k for k in GENERATION_ORDER if ontology_engine.load_model_yaml(k) is None]
    if missing:
        return _err(f"以下模型尚未生成：{', '.join(missing)}")
    if not mapping_engine.load_mapping():
        return _err("数据库映射尚未生成")

    with system_db() as conn:
        conn.execute(
            "UPDATE projects SET current_stage = 3, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), settings.PROJECT_ID),
        )
    return _ok({"current_stage": 3}, "已确认本体，进入阶段三")
