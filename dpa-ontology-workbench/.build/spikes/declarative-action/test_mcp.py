# -*- coding: utf-8 -*-
"""MCP 链路验证：tools/list → tools/call（typed 参数）→ 引擎执行。

验证三件事：
1. Action 声明能注册成标准 MCP tool（list_tools 里出现，且 inputSchema 是 typed）
2. typed 参数调用：合法参数 → 生成提案；非法参数 → MCP/引擎拦截
3. 参数不是字符串协议，而是结构化 JSON（呼应"交互协议协议化"）

运行：python test_mcp.py
"""
import asyncio
import json

from mcp_server import build_server

LOCALDB = {
    "pr_approval": [
        {"id": "9305733", "dic_name": "Vendor_type", "dic_type": "Vendor_type",
         "active_status": "Active", "ids": [9305733]},
    ]
}


async def main():
    mcp, engine = build_server("models", LOCALDB)

    # ① tools/list：Action 声明注册成了标准 MCP 工具
    tools = await mcp.list_tools() if asyncio.iscoroutinefunction(mcp.list_tools) else mcp.list_tools()
    assert len(tools) == 1, f"应有 1 个工具，实际 {len(tools)}"
    tool = tools[0]
    print(f"① tools/list -> {tool.name}")
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
    print(f"   inputSchema.properties: {list(schema.get('properties', {}).keys()) if schema else 'N/A'}")
    assert tool.name == "propose_update_subtable_data"
    assert schema and "active_status" in schema.get("properties", {})

    # ② 合法 typed 参数 → 引擎生成提案
    result = mcp.call_tool("propose_update_subtable_data",
                           {"record_id": "9305733", "active_status": "Inactive"})
    if asyncio.iscoroutine(result) or hasattr(result, "__await__"):
        result = await result
    text = _extract_text(result)
    assert "提案" in text or "PENDING" in text or "proposal" in text.lower(), text
    print(f"② tools/call 合法参数 -> {text[:80]}...")

    # ③ 非法参数（enum 越界）→ 被拦截（MCP 层或引擎层）
    blocked = False
    try:
        r = mcp.call_tool("propose_update_subtable_data",
                          {"record_id": "9305733", "active_status": "Enabled"})
        if asyncio.iscoroutine(r) or hasattr(r, "__await__"):
            r = await r
        t = _extract_text(r)
        blocked = "error" in t.lower() or "isError" in str(r) or "not" in t.lower()
        print(f"③ 非法参数被拦截 -> {t[:80]}...")
    except Exception as e:
        blocked = True
        print(f"③ 非法参数抛错（拦截）-> {str(e)[:80]}")
    assert blocked, "非法 enum 未被拦截"

    print("\n=== MCP 链路验证通过 ===")


def _extract_text(result) -> str:
    """从 CallToolResult 提取文本。"""
    s = str(result)
    if hasattr(result, "content"):
        try:
            return " ".join(getattr(c, "text", "") for c in result.content)
        except Exception:
            pass
    return s


if __name__ == "__main__":
    asyncio.run(main())