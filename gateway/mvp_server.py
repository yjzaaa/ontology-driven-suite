# -*- coding: utf-8 -*-
"""
MVP 竖切 Gateway（候选区原型，走真实测试库与真实 DPA 写路径）。

组成：
  registry   —— 加载 .build/candidates/masterdata/mvp-vertical-slice.yaml（PR 审批主数据）
  tools      —— 稳定语义工具（list/search/propose）；Agent 循环暂用关键词路由，
                真实 LLM 只需替换 agent_route() 一个函数
  policy     —— C0-C2 最小检查点（模型状态/对象存在/参数形状），fail-closed
  proposal   —— 提案存储 + 单次审批 Token
  execution  —— 读：本地库 gateway/data/localdb（由 sync_local.py 从测试库一次性只读引导）
                写：local_json 沙箱（默认）/ DPA HTTP 转发同源 Cookie（显式开启）
  audit      —— JSONL 审计收据
"""
import hashlib
import json
import re
import secrets
import threading
import time
import urllib.request
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from approval.proposal_store import JsonProposalStore, token_hash
from config import DPA_TEST_BASE_URL, GATEWAY_ROW_LIMIT, GATEWAY_WRITE_MODE, summary
from execution.write_adapters import get_write_adapter

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / ".build/candidates/masterdata/mvp-vertical-slice.yaml"
AUDIT_PATH = ROOT / "gateway/data/audit.jsonl"
LOCALDB_DIR = ROOT / "gateway/data/localdb"
DPA_BASE = DPA_TEST_BASE_URL                # 测试环境 DPA（.env → config.py）
COOKIE_NAME = "UserToken"                    # 事实：Operator.TokenName（T04.1）

app = FastAPI(title="DPA Ontology MVP Gateway")
print("[gateway] 配置加载：", summary(), flush=True)

# ---------------- registry ----------------
with open(MODEL_PATH, encoding="utf-8") as f:
    MODEL = yaml.safe_load(f)
OBJECTS = {o["id"]: o for o in MODEL["objects"]}
QUERIES = {q["id"]: q for o in MODEL["objects"] for q in o.get("queries", [])}
MIS = {m["id"]: m for m in MODEL["mis"]}
BEHAVIORS = {b["id"]: b for o in MODEL["objects"] for b in o.get("behaviors", [])}
COL_BY_FIELD = {o["id"]: {f["id"]: f.get("column", f["id"]) for f in o["fields"]}
                for o in MODEL["objects"]}
DISPLAY = {o["id"]: {f["id"]: f["display_name"] for f in o["fields"]}
           for o in MODEL["objects"]}

store = JsonProposalStore(ROOT / "gateway/data/proposals.json")  # 写操作台账：JSON 适配器，可换任意后端
_audit_lock = threading.Lock()

def audit(event: dict) -> None:
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock, open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def col(o: str, field: str) -> str:
    return COL_BY_FIELD[o][field]


# ---------------- 读执行器（本地库：由 sync_local.py 从测试库一次性只读引导） ----------------
def _load_local(name: str) -> list:
    path = LOCALDB_DIR / f"{name}.json"
    if not path.exists():
        raise RuntimeError(f"本地库缺失：{path}（先运行 gateway/sync_local.py 从测试库只读引导）")
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def run_query(mi_id: str, params: dict) -> list:
    mi = MIS[mi_id]
    assert mi["effect"] == "READ_ONLY", "非只读 MI 不得进入 run_query"
    rows = _load_local(mi["local_source"])
    kw = str(params.get("kw") or "").replace("%", "").strip().lower()
    fields = mi.get("local_search_fields", [])
    hits = [r for r in rows if not kw or any(kw in str(r.get(f) or "").lower() for f in fields)]
    hits = hits[:GATEWAY_ROW_LIMIT]  # 行数上限由 .env 统一控制
    audit({"kind": "governed_query", "mi": mi_id, "params": params,
           "rows": len(hits), "source": "localdb"})
    return hits


# ---------------- 写执行器调度（适配器模式：唯一知道 URL/Cookie/后端的地方） ----------------
WRITE_MODE = GATEWAY_WRITE_MODE  # 写模式由 .env 统一管理（config.py 映射）
WRITE_ADAPTER = get_write_adapter(WRITE_MODE, DPA_BASE,
                                  ROOT / "gateway/data/applied_writes.json", LOCALDB_DIR)

# 启动 fail-fast：所有只读 MI 依赖的本地库必须已引导
for _mi in MIS.values():
    if _mi.get("effect") == "READ_ONLY":
        _load_local(_mi["local_source"])


def execute_write(mi_id: str, arguments: dict, cookie_header: str) -> dict:
    mi = MIS[mi_id]
    assert mi["effect"] == "WRITE", "非写 MI 不得进入执行器"
    return WRITE_ADAPTER.execute(mi, arguments, cookie_header)


# ---------------- 最小 Policy（fail-closed） ----------------
def policy_check(behavior_id: str, arguments: dict) -> None:
    """C0-C2 最小检查：与 MI forbidden_params 声明一致，规则引擎留待正式实现。"""
    b = BEHAVIORS[behavior_id]
    if b["kind"] != "write":
        return
    if not b.get("requires_approval"):
        raise ValueError("写行为必须声明 requires_approval")
    ids = arguments.get("target", {}).get("ids") or []
    if not ids or not all(int(i) > 0 for i in ids):  # forbidden: len(JsonIds) > 0
        raise ValueError("必须选中至少一个既有文档（JsonIds 非空且为正）")
    status = str(arguments.get("input", {}).get("active_status", ""))
    if status not in ("Active", "Inactive"):  # forbidden: ActiveStatu ∈ {Active, Inactive}
        raise ValueError("目标状态只允许 Active / Inactive")


# ---------------- 提案 ----------------
def _dig(obj: dict, path: str):
    """按 a.b.c 点路径取值（MI param_mapping 解析用）。"""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def create_proposal(behavior_id: str, arguments: dict, thread_id: str = "") -> dict:
    policy_check(behavior_id, arguments)
    b = BEHAVIORS[behavior_id]
    mi = MIS[b["mi_ref"]]
    pid = "P" + secrets.token_hex(4)
    token = secrets.token_urlsafe(24)
    # form 由 MI param_mapping 统一推导：代码不含任何接口字段知识（模型不可选技术接口）
    form = {k: _dig(arguments, v.strip("{}").strip())
            for k, v in mi.get("param_mapping", {}).items()}
    tgt = arguments.get("target", {})
    store.save({"proposal_id": pid, "behavior": behavior_id, "arguments": arguments,
                "form": form, "token_hash": token_hash(token), "state": "PENDING_APPROVAL",
                "mi": b["mi_ref"], "risk": b["risk"], "created": time.time(),
                "thread_id": thread_id,  # LangGraph 线程：批准后用于 resume 补齐事件流
                "history": [{"event": "created"}]})
    audit({"kind": "proposal_created", "proposal_id": pid, "behavior": behavior_id,
           "target": tgt, "risk": b["risk"]})
    return {"proposal_id": pid, "state": "PENDING_APPROVAL", "risk": b["risk"],
            "token": token,  # MVP：单人演示随提案卡下发；正式 T07 改为仅授权审批人通道可见
            "display": f"{b['display_name']}：{tgt.get('dic_name', tgt.get('id'))}（id={','.join(map(str, tgt.get('ids', [])))}）",
            "change": f"状态 → {arguments['input'].get('active_status')}"}


def approve_proposal(pid: str, decision: str, token: str, cookie_header: str) -> dict:
    p = store.get(pid)
    if p is None or p["state"] != "PENDING_APPROVAL":
        raise ValueError("提案不存在或已处理")
    if not secrets.compare_digest(token_hash(token), p["token_hash"]):  # 单次 Token 绑定（只存哈希）
        raise ValueError("审批 Token 无效")
    if decision == "reject":
        store.update(pid, state="REJECTED", history_event={"event": "rejected"})
        audit({"kind": "proposal_rejected", "proposal_id": pid})
        _resume_graph(p, decision, {"status": "REJECTED", "code": "REJECTED"})
        return {"state": "REJECTED"}
    store.update(pid, state="EXECUTING", history_event={"event": "approved"})
    # 同时携带映射后的 form（DPA 用）与原始 target/input（local_update 叠加用）
    result = execute_write(p["mi"], {"form": p["form"], **(p.get("arguments") or {})}, cookie_header)
    store.update(pid, state=result["status"],
                 extra={"execution": {"status": result["status"], "code": result["code"]}},
                 history_event={"event": "executed",
                                "result": {"status": result["status"], "code": result["code"]}})
    audit({"kind": "execution", "proposal_id": pid, "mi": p["mi"],
           "result": {"status": result["status"], "code": result["code"]}})
    _resume_graph(p, decision, {"status": result["status"], "code": result["code"]})
    return result


def _resume_graph(p: dict, decision: str, result: dict) -> None:
    """恢复 LangGraph 线程（仅补齐事件流）；线程丢失（如服务重启）不影响裁决效力。"""
    if not p.get("thread_id"):
        return
    try:
        agent_rt.resume(p["thread_id"], {"decision": decision, "result": result})
    except Exception as e:
        audit({"kind": "graph_resume_skipped", "proposal_id": p.get("proposal_id"),
               "reason": f"{type(e).__name__}: {e}"})


# ---------------- Agent 工具与循环（LLM 插槽：只换这一个函数） ----------------
def fallback_route(message: str) -> list:
    """关键词路由（无 LLM 时的确定性回退）：message → 工具调用序列。"""
    steps, m = [], message.strip()
    mstatus = re.search(r"(停用|启用)\s*(.+)", m)
    if mstatus:  # 停用/启用 <关键词>：先检索定位文档，再创建状态变更提案
        action = "Inactive" if mstatus.group(1) == "停用" else "Active"
        kw = f"%{mstatus.group(2).strip()}%"
        steps.append(("lookup", "pr_approval_doc", "pr_doc_search", {"kw": kw}))
        steps.append(("propose", "pr_approval_doc", "change_doc_status",
                      {"active_status": action}))
        return steps
    if "审批" in m or "主数据" in m or "文档" in m:
        kw = f"%{m.replace('查', '').replace('审批', '').replace('主数据', '').replace('文档', '').strip()}%"
        steps.append(("search", "pr_approval_doc", "pr_doc_search", {"kw": kw}))
        return steps
    return steps


# ---------------- Agent Runtime（LangGraph + HITL，框架藏于 Runtime Interface 后） ----------------
from agent.runtime import GatewayBindings, build_runtime

agent_rt = build_runtime(GatewayBindings(
    fallback_route=fallback_route,
    run_query=lambda query_id, params: run_query(QUERIES[query_id]["mi_ref"], params),  # 查询→MI 映射属注册表知识，注入而非硬编码
    create_proposal=create_proposal,
    build_table_event=lambda obj_id, rows: {
        "type": "object_table", "object": obj_id,
        "display": OBJECTS[obj_id]["display_name"],
        "columns": [DISPLAY[obj_id].get(c, c) for c in rows[0]] if rows else [],
        "rows": rows},
    route_note=lambda mode: f"LangGraph 编排 · {mode} · HITL 中断就绪",
))


# ---------------- HTTP 层 ----------------
@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/session")
def session(request: Request):
    ck = request.headers.get("cookie", "")
    return {"dpa_session_bound": COOKIE_NAME in ck, "write_mode": WRITE_MODE}


@app.post("/api/chat")
async def chat(request: Request):
    msg = (await request.json()).get("message", "")
    thread_id = "t" + secrets.token_hex(6)
    try:
        return {"thread_id": thread_id, "events": agent_rt.run(msg, thread_id)}
    except Exception as e:
        return JSONResponse({"events": [{"type": "error", "message": f"平台错误：{e}"}]},
                            status_code=200)


@app.get("/api/proposals")
def list_proposals():
    """写操作台账（JSON 适配器当前内容），换后端后本端点不变。"""
    return [{k: v for k, v in p.items() if k not in ("form", "arguments", "token_hash")}
            for p in store.list()]


@app.post("/api/approve")
async def approve(request: Request):
    body = await request.json()
    try:
        return approve_proposal(body["proposal_id"], body["decision"],
                                body["token"], request.headers.get("cookie", ""))
    except Exception as e:
        return {"status": "FAILED", "code": "APPROVAL_INVALID", "message": str(e)}
