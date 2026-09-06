from __future__ import annotations

import re

from flask import current_app

from ..db import get_db, write_audit_log


FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "replace",
    "drop",
    "alter",
    "truncate",
    "create",
    "attach",
    "detach",
    "vacuum",
}


def execute_readonly_sql(sql: str, actor: str | None = None):
    settings = current_app.config["APP_SETTINGS"]["readonly_sql"]
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    normalized = sql.strip()
    lowered = normalized.lower()

    if settings["forbid_multi_statement"] and ";" in lowered.rstrip(";"):
        raise ValueError("只允许执行单条只读 SQL")
    if not lowered.startswith("select"):
        raise ValueError("当前 AI 对话仅允许只读 SELECT 查询")
    if any(keyword in lowered for keyword in FORBIDDEN_KEYWORDS):
        raise ValueError("当前 AI 对话不具备新增、修改、删除或结构变更权限")

    allowed_tables = set(registry.db_whitelist["tables"].keys())
    referenced_tables = {
        match.group(1)
        for match in re.finditer(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered)
    }
    if not referenced_tables.issubset(allowed_tables):
        raise ValueError("SQL 访问了未授权的数据表")

    if " limit " not in lowered:
        normalized = f"{normalized.rstrip(';')} LIMIT {int(settings['default_limit'])}"

    db = get_db()
    cursor = db.execute(normalized)
    rows = cursor.fetchall()
    if len(rows) > settings["max_rows"]:
        rows = rows[: settings["max_rows"]]

    headers = list(rows[0].keys()) if rows else [col[0] for col in cursor.description or []]
    write_audit_log("AI_READONLY_SQL", "readonly_sql_query", actor, {"sql": normalized})
    return {"sql": normalized, "headers": headers, "rows": rows}
