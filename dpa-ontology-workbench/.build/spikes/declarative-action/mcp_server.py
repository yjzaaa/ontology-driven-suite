# -*- coding: utf-8 -*-
"""MCP Server：把声明式 Action 注册成标准 MCP 工具（唯一协议层，零自研协议）。

关键点：Action 的 input_schema（JSON Schema）→ pydantic 动态模型 → MCP tool 的 inputSchema。
这样 typed 参数契约只有一份（在 Action YAML 里），MCP 工具、服务端校验、LLM 全部复用。
"""
from typing import Literal
import inspect

from mcp.server.mcpserver import MCPServer
from pydantic import Field, create_model

from engine import load_engine

# JSON Schema type → Python type
_TYPE_MAP = {
    "string": str, "integer": int, "number": float,
    "boolean": bool, "object": dict, "array": list,
}


def _param_type(spec: dict):
    """enum → Literal 强约束；否则 JSON Schema type → Python type。"""
    if "enum" in spec:
        return Literal.__getitem__(tuple(spec["enum"]))
    return _TYPE_MAP.get(spec.get("type", "string"), str)


def build_tool_fn(action: dict, engine):
    """把 Action.input_schema 动态转成「顶层参数」的工具函数。

    MCP SDK 从函数 __signature__ 推导 typed inputSchema —— 这样 record_id/active_status
    是顶层工具参数（Agent/LLM 习惯），而不是嵌套的 input 对象。
    """
    props = action["input_schema"].get("properties", {})
    required = set(action["input_schema"].get("required", []))

    sig_params = []
    annotations = {}
    for name, spec in props.items():
        pytype = _param_type(spec)
        annotations[name] = pytype
        default = inspect.Parameter.empty if name in required else None
        sig_params.append(inspect.Parameter(
            name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=pytype))

    def tool_fn(**kwargs) -> dict:
        # kwargs 已被 MCP SDK 按 __signature__ 强校验（typed）
        return engine.run(kwargs, ctx={"actor": "mcp-client"})

    tool_fn.__signature__ = inspect.Signature(sig_params)
    tool_fn.__annotations__ = annotations
    tool_fn.__name__ = f"propose_{action['model_id'].rsplit('.', 1)[-1].replace('-', '_')}"
    tool_fn.__doc__ = f"{action['name']['zh']}（写操作，生成提案，需审批）"
    return tool_fn


def build_server(models_dir: str, localdb: dict):
    """从本体 Action 声明批量注册 MCP 工具（纯声明驱动）。"""
    engine = load_engine(models_dir, localdb)
    mcp = MCPServer(name="dpa-ontology-gateway")
    action = engine.action
    tool_fn = build_tool_fn(action, engine)
    mcp.add_tool(tool_fn, name=tool_fn.__name__, description=tool_fn.__doc__)
    return mcp, engine


if __name__ == "__main__":
    # stdio transport：供任意 MCP 客户端（Claude Desktop / Cursor / 自研宿主）接入
    mcp, _ = build_server("models", {})
    mcp.run_stdio_async()
