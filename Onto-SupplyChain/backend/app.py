from __future__ import annotations

import logging

from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from config import APP_HOST, APP_PORT, DATABASE_PATH, DEBUG
from db.database import get_connection
from services.atp.engine import ATPService
from services.llm.client import DeepSeekClient
from services.ontology_graph import build_ontology_graph


app = Flask(__name__)


def _service() -> ATPService:
    return ATPService(get_connection(DATABASE_PATH))


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    llm = DeepSeekClient()
    conn = get_connection(DATABASE_PATH)
    try:
        conn.execute("SELECT 1")
        db_ok = True
    finally:
        conn.close()
    return jsonify(
        {
            "status": "ok",
            "database_path": str(DATABASE_PATH),
            "database_ready": db_ok,
            "deepseek_configured": llm.is_configured(),
        }
    )


@app.route("/api/ontology/graph", methods=["GET"])
def ontology_graph():
    return jsonify(build_ontology_graph())


@app.route("/api/scenarios", methods=["GET"])
def list_scenarios():
    service = _service()
    try:
        return jsonify({"items": service.list_scenarios()})
    finally:
        service.conn.close()


@app.route("/api/scenarios/<scenario_code>/run", methods=["POST"])
def run_scenario(scenario_code: str):
    body = request.get_json(silent=True) or {}
    service = _service()
    try:
        result = service.run_scenario(scenario_code, body.get("message"))
    finally:
        service.conn.close()
    assistant = DeepSeekClient().generate_atp_explanation(result)
    return jsonify({"scenario_result": result, "assistant": assistant})


@app.route("/api/atp/analyze", methods=["POST"])
def analyze_order():
    body = request.get_json(force=True)
    service = _service()
    try:
        result = service.analyze_order(
            order_id=body["order_id"],
            event_type=body.get("event_type"),
            event_payload=body.get("event_payload", {}),
            user_message=body.get("message"),
        )
    finally:
        service.conn.close()
    assistant = DeepSeekClient().generate_atp_explanation(result)
    return jsonify({"scenario_result": result, "assistant": assistant})


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True)
    service = _service()
    try:
        if body.get("scenario_code"):
            result = service.run_scenario(body["scenario_code"], body.get("message"))
        else:
            result = service.analyze_order(
                order_id=body["order_id"],
                event_type=body.get("event_type"),
                event_payload=body.get("event_payload", {}),
                user_message=body.get("message"),
            )
    finally:
        service.conn.close()

    message = (body.get("message") or "").lower()
    if "加班" in message or "overtime" in message:
        target = next(
            (item for item in result["atp_summary"]["alternatives"] if item["commitment_type"] == "Overtime"),
            result["atp_summary"]["recommended"],
        )
        result["atp_summary"]["recommended"] = {
            **target,
            "reason_chain": result["atp_summary"]["recommended"]["reason_chain"] + ["根据追问，优先展示加班方案。"],
            "impact_objects": result["atp_summary"]["recommended"]["impact_objects"],
            "narrative": f"如果允许加班，建议切换到 Overtime 方案，承诺日期 {target['committed_date']}。",
        }
    elif "替代" in message:
        target = next(
            (item for item in result["atp_summary"]["alternatives"] if item["commitment_type"] in {"AlternativeRouting", "AlternativeMaterial"}),
            result["atp_summary"]["recommended"],
        )
        result["atp_summary"]["recommended"] = {
            **target,
            "reason_chain": result["atp_summary"]["recommended"]["reason_chain"] + ["根据追问，优先展示替代方案。"],
            "impact_objects": result["atp_summary"]["recommended"]["impact_objects"],
            "narrative": f"如果启用替代方案，建议采用 {target['commitment_type']}，承诺日期 {target['committed_date']}。",
        }

    assistant = DeepSeekClient().generate_atp_explanation(result)
    return jsonify({"scenario_result": result, "assistant": assistant})


if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)
