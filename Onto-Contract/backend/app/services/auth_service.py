from __future__ import annotations

from flask import session
from werkzeug.security import check_password_hash

from ..db import get_db


def login(username: str, password: str):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username,),
    ).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return None

    session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "displayName": user["display_name"],
    }
    return session["user"]


def logout():
    session.pop("user", None)


def current_user():
    return session.get("user")
