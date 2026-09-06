"""系统接口：健康检查、演示文件下载"""
from flask import Blueprint, jsonify, send_from_directory

from backend.config.settings import settings

bp = Blueprint("system", __name__, url_prefix="/api/system")


def _ok(data=None, message="ok"):
    return jsonify({"success": True, "data": data, "message": message})


def _err(message: str, status: int = 400):
    return jsonify({"success": False, "data": None, "message": message}), status


@bp.get("/health")
def health():
    return _ok({
        "project_id": settings.PROJECT_ID,
        "deepseek_configured": bool(
            settings.DEEPSEEK_API_KEY and not settings.DEEPSEEK_API_KEY.startswith("sk-xxx")
        ),
        "model": settings.DEEPSEEK_MODEL,
        "reasoning_model": settings.DEEPSEEK_REASONING_MODEL,
    })


@bp.get("/demo-files/<path:filename>")
def download_demo_file(filename: str):
    demo_dir = settings.demo_files_dir()
    target = demo_dir / filename
    if not target.exists():
        return _err(f"演示文件不存在：{filename}", 404)
    return send_from_directory(str(demo_dir), filename, as_attachment=True)


@bp.get("/demo-files")
def list_demo_files():
    demo_dir = settings.demo_files_dir()
    if not demo_dir.exists():
        return _ok([])
    files = []
    for p in sorted(demo_dir.iterdir()):
        if p.is_file():
            files.append({
                "name": p.name,
                "size": p.stat().st_size,
                "download_url": f"/api/system/demo-files/{p.name}",
            })
    return _ok(files)
