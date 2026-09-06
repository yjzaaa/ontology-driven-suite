"""配置加载：合并 .env + yaml 配置"""
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _load_yaml(rel_path: str) -> dict:
    full = PROJECT_ROOT / rel_path
    if not full.exists():
        return {}
    with full.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_env_refs(node: Any) -> Any:
    """递归把形如 'env:DEEPSEEK_MODEL' 的值替换为环境变量真实值"""
    if isinstance(node, dict):
        return {k: _resolve_env_refs(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_env_refs(v) for v in node]
    if isinstance(node, str) and node.startswith("env:"):
        return os.getenv(node[4:], "")
    return node


_APP_CONFIG = _resolve_env_refs(_load_yaml("config/app_config.yaml"))
_AI_CONFIG = _resolve_env_refs(_load_yaml("config/ai_config.yaml"))


class Settings:
    PROJECT_ROOT: Path = PROJECT_ROOT
    PROJECT_ID: str = _APP_CONFIG.get("app", {}).get("project_id", "default")

    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_REASONING_MODEL: str = os.getenv("DEEPSEEK_REASONING_MODEL", "deepseek-reasoner")

    SYSTEM_DB_PATH: str = os.getenv("SYSTEM_DB_PATH", "./backend/data/system.db")
    DEMO_DB_PATH: str = os.getenv("DEMO_DB_PATH", "./backend/data/demo_ecommerce.db")

    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    MAX_SQL_ROWS: int = int(os.getenv("MAX_SQL_ROWS", "10000"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "4096"))
    AI_YAML_MAX_RETRIES: int = int(os.getenv("AI_YAML_MAX_RETRIES", "2"))
    AI_SQL_MAX_RETRIES: int = int(os.getenv("AI_SQL_MAX_RETRIES", "2"))

    APP_CONFIG: dict = _APP_CONFIG
    AI_CONFIG: dict = _AI_CONFIG

    @classmethod
    def models_dir(cls) -> Path:
        rel = cls.APP_CONFIG.get("paths", {}).get("models_dir", "./backend/models")
        p = (cls.PROJECT_ROOT / rel.lstrip("./")).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def project_models_dir(cls) -> Path:
        p = cls.models_dir() / cls.PROJECT_ID
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def prompts_dir(cls) -> Path:
        rel = cls.APP_CONFIG.get("paths", {}).get("prompts_dir", "./backend/prompts")
        return (cls.PROJECT_ROOT / rel.lstrip("./")).resolve()

    @classmethod
    def scenarios_dir(cls) -> Path:
        rel = cls.APP_CONFIG.get("paths", {}).get("scenarios_dir", "./backend/scenarios")
        return (cls.PROJECT_ROOT / rel.lstrip("./")).resolve()

    @classmethod
    def demo_files_dir(cls) -> Path:
        rel = cls.APP_CONFIG.get("paths", {}).get("demo_files_dir", "./demo_files")
        return (cls.PROJECT_ROOT / rel.lstrip("./")).resolve()

    @classmethod
    def data_dir(cls) -> Path:
        p = cls.PROJECT_ROOT / "backend" / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def phase_ai_config(cls, phase_key: str) -> dict:
        """获取指定阶段的 AI 调用配置（model 已解析为真实 ID）"""
        cfg = cls.AI_CONFIG.get("phase_configs", {}).get(phase_key, {})
        model_ref = cfg.get("model_ref", "default")
        model_id = cls.AI_CONFIG.get("models", {}).get(model_ref, cls.DEEPSEEK_MODEL)
        return {
            "model": model_id or cls.DEEPSEEK_MODEL,
            "temperature": cfg.get("temperature", cls.AI_TEMPERATURE),
            "max_tokens": cfg.get("max_tokens", cls.AI_MAX_TOKENS),
        }


settings = Settings()
