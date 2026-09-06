"""SQLite 连接管理"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterator

from backend.config.settings import settings


def _connect(path: str) -> sqlite3.Connection:
    p = Path(path)
    if not p.is_absolute():
        p = settings.PROJECT_ROOT / p.as_posix().lstrip("./")
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def system_db() -> sqlite3.Connection:
    """系统库连接（projects/chat/execution_records）"""
    return _connect(settings.SYSTEM_DB_PATH)


def demo_db() -> sqlite3.Connection:
    """演示电商业务库连接"""
    return _connect(settings.DEMO_DB_PATH)


def init_system_db() -> None:
    """初始化系统库 schema 并确保 default 项目存在"""
    schema_path = settings.PROJECT_ROOT / "backend" / "db" / "schema.sql"
    with system_db() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        cur = conn.execute("SELECT id FROM projects WHERE id = ?", (settings.PROJECT_ID,))
        if cur.fetchone() is None:
            now = datetime.utcnow().isoformat()
            conn.execute(
                """INSERT INTO projects
                   (id, name, description, current_stage, created_at, updated_at, stage_status)
                   VALUES (?, ?, ?, 1, ?, ?, ?)""",
                (
                    settings.PROJECT_ID,
                    "电商经营数据智能分析（默认项目）",
                    "本体模型驱动的电商数据分析演示项目",
                    now,
                    now,
                    json.dumps({"1": False, "2": False, "3": False, "4": False}),
                ),
            )


def iter_rows(cursor: sqlite3.Cursor) -> Iterator[dict]:
    for row in cursor.fetchall():
        yield dict(row)
