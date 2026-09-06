"""SQL 执行器：在演示数据库上安全执行 SELECT 查询"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from backend.config.settings import settings
from backend.utils.sql_validator import validate_and_prepare_sql


def _connect() -> sqlite3.Connection:
    p = Path(settings.DEMO_DB_PATH)
    if not p.is_absolute():
        p = settings.PROJECT_ROOT / p.as_posix().lstrip("./")
    if not p.exists():
        raise RuntimeError(f"演示数据库不存在：{p}（请先启动 Flask 让 bootstrap 生成）")
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


class SqlExecutionResult:
    def __init__(self, sql: str, columns: list[str], rows: list[dict],
                 duration_ms: int, error: str = ""):
        self.sql = sql
        self.columns = columns
        self.rows = rows
        self.duration_ms = duration_ms
        self.error = error

    @property
    def ok(self) -> bool:
        return not self.error

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def to_dict(self) -> dict:
        return {
            "sql": self.sql,
            "ok": self.ok,
            "error": self.error,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "duration_ms": self.duration_ms,
        }


def execute_sql(sql: str) -> SqlExecutionResult:
    """安全校验 + 执行。所有异常都捕获并以 error 字段返回。"""
    ok, prepared, err = validate_and_prepare_sql(sql)
    if not ok:
        return SqlExecutionResult(sql=sql, columns=[], rows=[], duration_ms=0, error=err)

    start = time.perf_counter()
    try:
        conn = _connect()
        try:
            cursor = conn.execute(prepared)
            cols = [d[0] for d in (cursor.description or [])]
            rows = [dict(r) for r in cursor.fetchall()]
            return SqlExecutionResult(
                sql=prepared, columns=cols, rows=rows,
                duration_ms=int((time.perf_counter() - start) * 1000),
            )
        finally:
            conn.close()
    except sqlite3.Error as e:
        return SqlExecutionResult(
            sql=prepared, columns=[], rows=[],
            duration_ms=int((time.perf_counter() - start) * 1000),
            error=f"SQL 执行失败：{e}",
        )


def preview_rows(rows: list[dict], limit: int = 5) -> list[dict]:
    """截取前 N 行用于展示"""
    return rows[:limit]
