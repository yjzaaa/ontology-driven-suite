"""Flask 应用入口

启动方式：
    cd ecommerce-ontology-analytics
    python -m backend.app

或通过 start_backend.bat
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify  # noqa: E402
from flask_cors import CORS  # noqa: E402

from backend.api import (  # noqa: E402
    phase1_routes,
    phase2_routes,
    phase3_routes,
    phase4_routes,
    system_routes,
)
from backend.config.settings import settings  # noqa: E402
from backend.db.database import init_system_db  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    CORS(app, resources={r"/api/*": {"origins": [settings.FRONTEND_ORIGIN, "http://127.0.0.1:5173"]}})

    # 轻量初始化：系统库（projects/chat/execution_records）
    init_system_db()

    app.register_blueprint(system_routes.bp)
    app.register_blueprint(phase1_routes.bp)
    app.register_blueprint(phase2_routes.bp)
    app.register_blueprint(phase3_routes.bp)
    app.register_blueprint(phase4_routes.bp)

    @app.errorhandler(404)
    def _404(_e):
        return jsonify({"success": False, "message": "接口不存在"}), 404

    @app.errorhandler(500)
    def _500(e):
        return jsonify({"success": False, "message": f"服务器内部错误：{str(e)}"}), 500

    return app


def _bootstrap() -> None:
    """重型启动前置：演示库（首次约 30-60s）"""
    from backend.db.demo_data.bootstrap import ensure_demo_db
    ensure_demo_db()


if __name__ == "__main__":
    _bootstrap()
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=settings.FLASK_PORT,
        debug=settings.FLASK_DEBUG,
        threaded=True,
    )
