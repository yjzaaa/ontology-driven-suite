from __future__ import annotations

import copy
from typing import Any

from flask import Flask

from .api.routes import register_blueprints
from .config import load_settings
from .db import close_db, init_app_database
from .ontology.loader import OntologyRegistry


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def create_app(settings_override: dict[str, Any] | None = None) -> Flask:
    settings = load_settings()
    if settings_override:
        settings = _deep_merge(copy.deepcopy(settings), settings_override)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings["app"]["secret_key"]
    app.config["APP_SETTINGS"] = settings

    registry = OntologyRegistry(settings["ontology"]["model_root"])
    registry.load()
    app.config["ONTOLOGY_REGISTRY"] = registry

    init_app_database(app)
    app.teardown_appcontext(close_db)
    register_blueprints(app)
    return app
