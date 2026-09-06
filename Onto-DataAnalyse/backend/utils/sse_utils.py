"""SSE (Server-Sent Events) 工具"""
import json
from typing import Any, Iterator

from flask import Response


def sse_pack(event_type: str, data: Any) -> str:
    """打包一条 SSE 消息。data 会被 JSON 序列化"""
    payload = json.dumps({"type": event_type, **(data if isinstance(data, dict) else {"data": data})}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def sse_pack_raw(payload: dict) -> str:
    """打包一条已经组装好的字典消息"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def sse_response(generator: Iterator[str]) -> Response:
    """把一个 yield SSE 字符串的生成器包装成 Flask Response"""
    resp = Response(generator, mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"   # 禁用 nginx 缓冲（如果部署到 nginx 后面）
    resp.headers["Connection"] = "keep-alive"
    return resp
