# -*- coding: utf-8 -*-
"""MVP 竖切端到端验收：六个测试问题 → 逐步断言。

覆盖：LLM 意图解析 → 治理读 → HITL 提案/批准 → 读写自洽 → 语义护栏。

运行前提：
1. 网关已启动：uvicorn mvp_server:app --app-dir gateway --port 8000
2. .env 已配置 LLM_*（未配置时以规则路由降级——场景 1/3/4 的输入措辞
   同时兼容两种路由；场景 5/6 的断言对两种路由均成立）
3. 安全护栏：GATEWAY_WRITE_MODE 必须为 local_json（本脚本会产生写提案，
   绝不允许在未经 E2E_ALLOW_DPA=1 显式授权时打到真实 DPA）。

运行：
  gateway/.venv/Scripts/python.exe -X utf8 tests/e2e_mvp_vertical_slice.py

可选环境变量：
  GATEWAY_E2E_BASE_URL  默认 http://localhost:8000
  GATEWAY_E2E_TIMEOUT   单请求超时秒数，默认 180（gpt-5 推理约 5-10s/次）
  GATEWAY_E2E_DOC       演示文档关键词，默认 9305733
"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.environ.get("GATEWAY_E2E_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = int(os.environ.get("GATEWAY_E2E_TIMEOUT", "180"))
DOC = os.environ.get("GATEWAY_E2E_DOC", "9305733")

PASS: list[str] = []
FAIL: list[tuple[str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name if cond else f"{name}：{detail}")
    print(f"  {'✓' if cond else '✗'} {name}" + ("" if cond else f" —— {detail}"))


def http(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        method=method, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=TIMEOUT).read())


def chat(message: str) -> list[dict]:
    return http("POST", "/api/chat", {"message": message})["events"]


def first(events: list[dict], kind: str) -> dict | None:
    return next((e for e in events if e["type"] == kind), None)


def table_row(events: list[dict], retry_message: str | None = None) -> dict:
    """取首个非空结果表；LLM 关键词提取有非确定性，允许用兜底措辞重试一次。"""
    tbl = first(events, "object_table")
    if not (tbl and tbl.get("rows")) and retry_message:
        tbl = first(chat(retry_message), "object_table")
    assert tbl and tbl.get("rows"), "未返回非空 object_table 事件"
    return tbl["rows"][0]


def approve(card: dict) -> dict:
    return http("POST", "/api/approve",
                {"proposal_id": card["proposal_id"], "decision": "approve",
                 "token": card["token"]})


def main() -> int:
    print(f"端到端验收 @ {BASE}（演示文档：{DOC}）\n")

    # ── 0 安全护栏：绝不无意写真实 DPA ──
    session = http("GET", "/api/session")
    mode = session.get("write_mode")
    check("写模式护栏", mode == "local_json" or os.environ.get("E2E_ALLOW_DPA") == "1",
          f"write_mode={mode}（dpa_http 需 E2E_ALLOW_DPA=1 显式授权）")

    route_note = ""
    print("\n[场景1] LLM 检索：「帮我查一下 9305733 这个主数据文档」")
    ev = chat(f"帮我查一下 {DOC} 这个主数据文档")
    route_note = (first(ev, "route") or {}).get("note", "")
    check("LangGraph 编排生效", "LangGraph 编排" in route_note, f"note={route_note!r}")
    check("返回非空结果表", bool((first(ev, "object_table") or {}).get("rows")))
    row = table_row(ev)
    check("结果字段完整", bool(row.get("id") and row.get("dic_name")), f"row={row!r}")
    baseline_status = row.get("active_status")

    print("\n[场景2] 写提案+批准：「请把 9305733 停用」")
    ev = chat(f"请把 {DOC} 停用")
    card = first(ev, "proposal_card")
    check("产生 HIGH 提案卡", bool(card and card.get("risk") == "HIGH"),
          f"events={[e['type'] for e in ev]}")
    if card:
        r = approve(card)
        check("批准执行成功", r.get("status") == "SUCCEEDED", f"resp={r}")
        if mode == "local_json":
            check("诚实执行码（未伪装真实写）", r.get("code") == "LOCAL_SANDBOX_APPLIED",
                  f"code={r.get('code')}")

    print("\n[场景3] 读写自洽：「9305733 这条文档现在什么状态？」")
    row = table_row(chat(f"{DOC} 这条文档现在什么状态？"), DOC)
    check("状态已变为 Inactive", row.get("active_status") == "Inactive",
          f"actual={row.get('active_status')}")

    print("\n[场景4] 口语化恢复：「帮我把 9305733 重新启用了」")
    card = first(chat(f"帮我把 {DOC} 重新启用了"), "proposal_card")
    check("口语化意图解析为启用", bool(card and "Active" in card.get("change", "")),
          "未产生 Active 提案")
    if card:
        r = approve(card)
        check("批准执行成功", r.get("status") == "SUCCEEDED", f"resp={r}")
    row = table_row(chat(f"查审批主数据 {DOC}"), DOC)
    check("基线恢复为 Active", row.get("active_status") == "Active",
          f"actual={row.get('active_status')}（初始 {baseline_status}）")

    print("\n[场景5] 语义护栏：「把 9305733 删掉」（删除不在可用动作内）")
    ev = chat(f"把 {DOC} 删掉")
    check("不得产生提案", first(ev, "proposal_card") is None,
          f"events={[e['type'] for e in ev]}")
    check("返回未识别意图", bool(first(ev, "error")))

    print("\n[场景6] 越界输入：「今天天气怎么样」")
    ev = chat("今天天气怎么样")
    check("不得产生提案", first(ev, "proposal_card") is None)
    check("返回未识别意图", bool(first(ev, "error")))

    print(f"\n──── 结论：{len(PASS)} 通过 / {len(FAIL)} 失败 ────")
    for f in FAIL:
        print(f"  ✗ {f}")
    print(f"路由模式：{route_note}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
