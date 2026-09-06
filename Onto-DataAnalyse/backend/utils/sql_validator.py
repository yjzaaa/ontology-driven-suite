"""SQL 安全校验：仅允许 SELECT，禁止 DDL/DML，强制 LIMIT"""
import re
from typing import Tuple

from backend.config.settings import settings

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "REPLACE", "ATTACH", "PRAGMA",
]


def validate_and_prepare_sql(sql: str) -> Tuple[bool, str, str]:
    """
    校验并修整 SQL。
    返回: (is_valid, prepared_sql, error_message)
    """
    if not sql or not sql.strip():
        return False, "", "SQL 为空"

    sql_stripped = sql.strip().rstrip(";")
    sql_upper = sql_stripped.upper()

    if not sql_upper.lstrip("(").startswith("SELECT") and not sql_upper.startswith("WITH"):
        return False, "", "仅允许 SELECT / WITH 查询语句"

    # 用 \b 边界匹配，避免误伤诸如 'created_at' 这类含 'CREATE' 子串的字段
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", sql_upper):
            return False, "", f"禁止使用 {kw} 操作"

    # 多语句拦截
    if ";" in sql_stripped:
        return False, "", "禁止多语句执行"

    # 强制追加 LIMIT
    if not re.search(r"\bLIMIT\b", sql_upper):
        sql_stripped = f"{sql_stripped} LIMIT {settings.MAX_SQL_ROWS}"

    return True, sql_stripped, ""
