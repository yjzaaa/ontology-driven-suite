"""Demo DB 启动期自动初始化"""
from pathlib import Path

from backend.config.settings import settings


def ensure_demo_db() -> None:
    """Flask 启动时调用：若演示库不存在，自动生成"""
    db_path = Path(settings.DEMO_DB_PATH)
    if not db_path.is_absolute():
        db_path = settings.PROJECT_ROOT / db_path.as_posix().lstrip("./")
    if db_path.exists() and db_path.stat().st_size > 1024 * 1024:   # > 1MB 视为已生成
        return
    print("[bootstrap] 演示数据库不存在，开始生成（首次启动约 30-60 秒）...")
    from backend.db.demo_data.generate_demo_data import generate_all
    summary = generate_all()
    print("[bootstrap] 演示数据生成完成：")
    for k, v in summary.items():
        print(f"           {k}: {v:>7,} 条")
