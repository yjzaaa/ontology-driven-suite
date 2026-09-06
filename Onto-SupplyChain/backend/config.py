from __future__ import annotations

import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE_PATH = BASE_DIR / "config.local.json"


def _load_file_config() -> dict:
    if not CONFIG_FILE_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


FILE_CONFIG = _load_file_config()


def _get_config(name: str, default):
    if name in os.environ:
        return os.environ[name]
    return FILE_CONFIG.get(name, default)

_database_value = Path(str(_get_config("ATP_DATABASE_PATH", str(DATA_DIR / "atp_demo.sqlite3"))))
DATABASE_PATH = _database_value if _database_value.is_absolute() else BASE_DIR / _database_value
DEEPSEEK_BASE_URL = str(_get_config("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
DEEPSEEK_API_KEY = str(_get_config("DEEPSEEK_API_KEY", ""))
DEEPSEEK_MODEL = str(_get_config("DEEPSEEK_MODEL", "deepseek-chat"))
DEEPSEEK_TIMEOUT = int(_get_config("DEEPSEEK_TIMEOUT", "60"))
DEEPSEEK_TEMPERATURE = float(_get_config("DEEPSEEK_TEMPERATURE", "0.2"))
APP_HOST = str(_get_config("APP_HOST", "127.0.0.1"))
APP_PORT = int(_get_config("APP_PORT", "5000"))
DEBUG = str(_get_config("FLASK_DEBUG", "1")) == "1"
