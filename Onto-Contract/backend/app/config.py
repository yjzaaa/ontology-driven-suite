from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


BACKEND_DIR = Path(__file__).resolve().parents[1]
CODE_DIR = BACKEND_DIR.parent


DEFAULT_SETTINGS: dict[str, Any] = {
    "app": {
        "name": "ai-native-contract-system",
        "env": "dev",
        "host": "127.0.0.1",
        "port": 5000,
        "debug": True,
        "secret_key": "replace-with-your-secret-key",
    },
    "database": {
        "sqlite_path": str(CODE_DIR / "data" / "contract.db"),
        "timeout_seconds": 10,
    },
    "auth": {
        "enabled": True,
        "default_admin_username": "admin",
        "default_admin_password": "ChangeMe123!",
        "session_expire_minutes": 480,
    },
    "ai": {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key": "YOUR_DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "enable_function_calling": True,
        "request_timeout_seconds": 120,
        "max_context_messages": 20,
        "temperature": 0.1,
    },
    "sse": {
        "enabled": True,
        "heartbeat_seconds": 15,
    },
    "ontology": {
        "model_root": str(CODE_DIR / "models" / "contract"),
        "enable_runtime_registry": True,
        "fail_fast_on_invalid_model": True,
    },
    "readonly_sql": {
        "enabled": True,
        "select_only": True,
        "max_rows": 200,
        "default_limit": 50,
        "timeout_seconds": 8,
        "forbid_multi_statement": True,
        "audit_log_enabled": True,
    },
    "ui": {
        "chart_library": "echarts",
        "icon_library": "lucide",
        "hybrid_mode": True,
    },
}


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def load_settings() -> dict[str, Any]:
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    config_path = CODE_DIR / "deepseek.config.yaml"
    fallback_path = CODE_DIR / "deepseek.config.example.yaml"

    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        _deep_merge(settings, raw)
    elif fallback_path.exists():
        raw = yaml.safe_load(fallback_path.read_text(encoding="utf-8")) or {}
        _deep_merge(settings, raw)

    db_path = Path(settings["database"]["sqlite_path"])
    if not db_path.is_absolute():
        settings["database"]["sqlite_path"] = str((CODE_DIR / db_path).resolve())

    model_root = Path(settings["ontology"]["model_root"])
    if not model_root.is_absolute():
        settings["ontology"]["model_root"] = str((CODE_DIR / model_root).resolve())

    return settings
