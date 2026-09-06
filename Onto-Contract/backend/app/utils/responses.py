from __future__ import annotations

from flask import jsonify


def ok(data=None, message: str = "ok", status: int = 200):
    return jsonify(
        {
            "success": True,
            "message": message,
            "data": data,
            "errorCode": None,
        }
    ), status


def fail(message: str, error_code: str = "BAD_REQUEST", status: int = 400):
    return jsonify(
        {
            "success": False,
            "message": message,
            "data": None,
            "errorCode": error_code,
        }
    ), status
