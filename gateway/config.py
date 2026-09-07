# -*- coding: utf-8 -*-
"""Gateway 配置中心：.env → 配置项的唯一映射点。

纪律：
- 业务代码只允许从这里取配置，不得直接 os.environ 或手写连接串/URL；
- 配置缺失或非法时启动即失败（fail-fast），不猜测、不用空值伪装成功；
- 本文件不含任何环境事实值——真实值只在 .env（不入 git），模板见 .env.example；
- 按项目纪律不存放任何凭据：测试库走 Windows 集成认证（Trusted_Connection）。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path) -> dict:
    """最小 .env 解析：KEY=VALUE、# 注释、忽略空行、剥除值两端引号。"""
    if not path.exists():
        raise RuntimeError(f"缺少配置文件：{path}（请参照 .env.example 创建 .env）")
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        # 剥除行内注释：仅当 # 前有空白时视为注释起始，避免误伤值内 # 字符
        for marker in (" #", "\t#"):
            if marker in value:
                value = value.split(marker, 1)[0].rstrip()
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


_ENV = load_env(ROOT / ".env")


def _required(key: str) -> str:
    value = _ENV.get(key, "").strip()
    if not value:
        raise RuntimeError(f"配置缺失：{key}（请在 .env 中填写，参照 .env.example）")
    return value


def _int(key: str, default: int) -> int:
    raw = _ENV.get(key, "").strip() or str(default)
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError(f"配置非法：{key}={raw}（应为整数）") from None


# ---- 测试环境事实（与 DPA_TEST_* 对应）----
DPA_TEST_BASE_URL = _required("DPA_TEST_BASE_URL").rstrip("/")
DPA_TEST_DB_HOST = _required("DPA_TEST_DB_HOST")
DPA_TEST_DB_NAME = _required("DPA_TEST_DB_NAME")
DPA_TEST_DB_PORT = _ENV.get("DPA_TEST_DB_PORT", "").strip() or "1433"
DPA_TEST_REVISION = _ENV.get("DPA_TEST_REVISION", "").strip()

# ---- Gateway 行为 ----
GATEWAY_WRITE_MODE = _ENV.get("GATEWAY_WRITE_MODE", "").strip() or "local_json"
if GATEWAY_WRITE_MODE not in ("local_json", "dpa_http"):
    raise RuntimeError(
        f"配置非法：GATEWAY_WRITE_MODE={GATEWAY_WRITE_MODE}（可选 local_json / dpa_http）")
GATEWAY_PORT = _int("GATEWAY_PORT", 8000)
GATEWAY_QUERY_TIMEOUT_SECONDS = _int("GATEWAY_QUERY_TIMEOUT_SECONDS", 8)
GATEWAY_ROW_LIMIT = _int("GATEWAY_ROW_LIMIT", 50)

# ---- LLM（可选：不填则 Agent 退回关键词路由，降级在 route 事件中显式标注）----
LLM_BASE_URL = _ENV.get("LLM_BASE_URL", "").strip()
LLM_API_KEY = _ENV.get("LLM_API_KEY", "").strip()
LLM_MODEL = _ENV.get("LLM_MODEL", "").strip()
LLM_API_VERSION = _ENV.get("LLM_API_VERSION", "").strip()  # 可选：网关代理要求 api-version 查询参数时填
HAS_LLM = bool(LLM_BASE_URL and LLM_API_KEY and LLM_MODEL)

# ---- 派生值 ----
# 读连接串：只服务白名单 SELECT（run_query）；写路径永不使用该连接（读写分离）。
_DB_SERVER = (DPA_TEST_DB_HOST if DPA_TEST_DB_PORT in ("1433", "")
              else f"{DPA_TEST_DB_HOST},{DPA_TEST_DB_PORT}")
DB_CONN = (f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={_DB_SERVER};"
           f"DATABASE={DPA_TEST_DB_NAME};Trusted_Connection=yes;")


def summary() -> dict:
    """启动日志用配置摘要（不含任何敏感值——本配置按纪律不存放凭据）。"""
    return {
        "dpa_base_url": DPA_TEST_BASE_URL,
        "db_host": DPA_TEST_DB_HOST,
        "db_name": DPA_TEST_DB_NAME,
        "dpa_revision": DPA_TEST_REVISION or "(未填写)",
        "write_mode": GATEWAY_WRITE_MODE,
        "port": GATEWAY_PORT,
        "row_limit": GATEWAY_ROW_LIMIT,
        "query_timeout_s": GATEWAY_QUERY_TIMEOUT_SECONDS,
        "llm": LLM_MODEL if HAS_LLM else "(未配置→规则路由)",    }
