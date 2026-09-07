# -*- coding: utf-8 -*-
"""
MVP 竖切 Gateway（候选区原型，走真实测试库与真实 DPA 写路径）。

组成：
  registry   —— ModelRegistry：本体 YAML 统一视图 + 启动校验（借鉴 AppBuilder engine
                的 loader 模式：索引化访问、引用闭包校验、fail-fast）
  tools      —— 稳定语义工具（search/propose）；意图解析完全模型驱动
                （查询/行为/触发词/参数映射全部来自 YAML，见 agent/runtime.py）
  policy     —— C0-C2 最小检查点：解释 MI forbidden_params 的封闭规则词表，fail-closed
  proposal   —— 提案存储 + 单次审批 Token
  execution  —— 读：本地库 gateway/data/localdb（由 sync_local.py 从测试库一次性只读引导）
                写：local_json 沙箱（默认）/ DPA HTTP 转发同源 Cookie（显式开启）
  audit      —— JSONL 审计收据

引擎通用能力（新增业务对象 = 纯 YAML 提交，本文件零改动）：
  1. type_filter      —— MI 声明 dic_name 过滤，从 blob 表投影出类型化视图
  2. content_fields   —— MI 声明 dic_content JSON 字段投影
  3. ref 富化         —— 字段声明 ref{target,key,label} → 查询时自动带出目标显示名
                         （借鉴 AppBuilder engine query.enrich_row 的 __label 模式）
  4. 目录驱动意图     —— queries 的 keywords / behaviors 的 input_values 供 Agent 路由
"""
import json
import re
import secrets
import threading
import time
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


# ---------------- ModelRegistry（本体模型统一视图 + 启动校验） ----------------
class ModelRegistry:
    """本体 YAML 的一次性加载、索引与引用闭包校验（fail-fast）。

    借鉴 AppBuilder engine 的 OntologyModel：运行时只读模型文件并建索引，
    所有跨引用（query→MI、behavior→MI、ref→目标对象、forbidden 规则词表）
    在启动时验证，不合法直接拒绝启动，不带病运行。
    """

    # forbidden_params 的封闭规则词表（业务取值在 YAML，词表本身是引擎知识）
    RULE_VOCAB = ("nonempty_positive_ints", "nonempty", "in:")

    def __init__(self, model: dict):
        self.objects = {o["id"]: o for o in model.get("objects", [])}
        self.mis = {m["id"]: m for m in model.get("mis", [])}
        self.queries: dict = {}    # query_id -> (obj_id, q)
        self.behaviors: dict = {}  # behavior_id -> (obj_id, b)
        self.mi_refs: dict = {}    # mi_id -> [(field_id, target_obj, key, label)]
        for oid, o in self.objects.items():
            for q in o.get("queries") or []:
                self.queries[q["id"]] = (oid, q)
            for b in o.get("behaviors") or []:
                self.behaviors[b["id"]] = (oid, b)
        self._validate()

    def _field_ids(self, oid: str) -> set:
        o = self.objects[oid]
        return ({f["id"] for f in o.get("fields") or []}
                | {f["id"] for f in o.get("content_fields") or []})

    def all_field_ids(self, oid: str) -> list:
        """行投影字段全集：表头列 + 内容投影字段（提案参数构造需要完整行）。"""
        o = self.objects[oid]
        return ([f["id"] for f in o.get("fields") or []]
                + [f["id"] for f in o.get("content_fields") or []])

    def visible_fields(self, oid: str) -> list:
        """表格列（visible != False 的 fields + content_fields），含 ref 富化列。"""
        o = self.objects[oid]
        vis = [f for f in o.get("fields") or [] if f.get("visible", True)]
        vis += [f for f in o.get("content_fields") or [] if f.get("visible", True)]
        cols = [{"id": f["id"], "display_name": f["display_name"]} for f in vis]
        shown = {f["display_name"] for f in vis}   # 按 display_name 去重（id 大小写可能不同）
        for f in o.get("content_fields") or []:
            ref = f.get("ref")
            # 富化列：目标 label 的显示名未出现在列中时才追加（避免重复列）
            if ref and (lbl_dn := self._ref_label_display(ref)) not in shown:
                cols.append({"id": f["id"] + "__label", "display_name": lbl_dn})
                shown.add(lbl_dn)
        return cols

    def _ref_label_display(self, ref: dict) -> str:
        t = self.objects[ref["target"]]
        lbl = next((x for x in t.get("content_fields") or [] if x["id"] == ref["label"]), None)
        return (lbl or {}).get("display_name", ref["label"])

    def display_name(self, oid: str) -> str:
        return self.objects[oid]["display_name"]

    def _validate(self) -> None:
        errs: list = []
        for oid, o in self.objects.items():
            for q in o.get("queries") or []:
                if q.get("mi_ref") not in self.mis:
                    errs.append(f"查询 {q['id']} 引用不存在的 MI {q.get('mi_ref')}")
            for b in o.get("behaviors") or []:
                if b.get("mi_ref") not in self.mis:
                    errs.append(f"行为 {b['id']} 引用不存在的 MI {b.get('mi_ref')}")
                if b.get("kind") == "write" and not b.get("requires_approval"):
                    errs.append(f"写行为 {b['id']} 未声明 requires_approval")
                loc = (b.get("target_locator") or {}).get("query_ref")
                if loc is not None and loc not in self.queries:
                    errs.append(f"行为 {b['id']} target_locator 引用不存在的查询 {loc}")
                for field, mapping in (b.get("input_values") or {}).items():
                    if not isinstance(mapping, dict) or not mapping:
                        errs.append(f"行为 {b['id']} input_values.{field} 必须是非空映射")
                for tpl in (b.get("target_label"), b.get("change_label")):
                    for ph in re.findall(r"\{([\w.]+)\}", tpl or ""):
                        if ph.startswith("input."):
                            if ph[6:] not in (b.get("input_values") or {}):
                                errs.append(f"行为 {b['id']} 模板引用未声明的输入 {ph}")
                        elif ph not in self._field_ids(oid):
                            errs.append(f"行为 {b['id']} 模板引用未声明字段 {ph}")
        for qid, (oid, q) in self.queries.items():
            mi = self.mis[q["mi_ref"]]
            if mi.get("effect") != "READ_ONLY":
                continue
            if not mi.get("local_source"):
                errs.append(f"只读 MI {mi['id']} 缺少 local_source")
            tf = mi.get("type_filter")
            dt = self.objects[oid].get("doc_type")
            if tf and dt and tf != dt:
                errs.append(f"MI {mi['id']} type_filter={tf} 与对象 {oid} doc_type={dt} 不一致")
            if tf and not dt:
                errs.append(f"MI {mi['id']} 声明 type_filter 但对象 {oid} 缺少 doc_type")
            for f in mi.get("content_fields") or []:
                if f not in self._field_ids(oid):
                    errs.append(f"MI {mi['id']} 投影字段 {f} 未在对象 {oid} 声明")
            for fp in mi.get("forbidden_params") or []:
                rule = fp.get("rule", "")
                if not any(rule == v or rule.startswith(v) for v in self.RULE_VOCAB):
                    errs.append(f"MI {mi['id']} 禁止规则 {rule} 不在封闭词表 {self.RULE_VOCAB}")
        # ref 富化闭包：目标对象存在、key/label 字段存在；登记到本对象各只读 MI
        for oid, o in self.objects.items():
            for f in o.get("content_fields") or []:
                ref = f.get("ref")
                if not ref:
                    continue
                t = self.objects.get(ref.get("target"))
                if t is None:
                    errs.append(f"{oid}.{f['id']} ref 目标对象 {ref.get('target')} 未建模")
                    continue
                for side in ("key", "label"):
                    if ref.get(side) not in self._field_ids(ref["target"]):
                        errs.append(f"{oid}.{f['id']} ref.{side}={ref.get(side)} "
                                    f"未在 {t['id']} 声明")
                for q in o.get("queries") or []:
                    if self.mis[q["mi_ref"]].get("effect") == "READ_ONLY":
                        self.mi_refs.setdefault(q["mi_ref"], []).append(
                            (f["id"], ref["target"], ref["key"], ref["label"]))
        if errs:
            raise RuntimeError("本体模型校验失败（fail-fast）：\n  - " + "\n  - ".join(errs))


with open(MODEL_PATH, encoding="utf-8") as f:
    MODEL = yaml.safe_load(f)
REG = ModelRegistry(MODEL)
print(f"[gateway] 本体模型加载：{len(REG.objects)} 对象 / {len(REG.queries)} 查询 / "
      f"{len(REG.behaviors)} 行为 / {len(REG.mis)} MI", flush=True)

store = JsonProposalStore(ROOT / "gateway/data/proposals.json")  # 写操作台账：JSON 适配器，可换任意后端
_audit_lock = threading.Lock()


def audit(event: dict) -> None:
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock, open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ---------------- 读执行器（本地库：由 sync_local.py 从测试库一次性只读引导） ----------------
def _load_local(name: str) -> list:
    path = LOCALDB_DIR / f"{name}.json"
    if not path.exists():
        raise RuntimeError(f"本地库缺失：{path}（先运行 gateway/sync_local.py 从测试库只读引导）")
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _parse_doc(row: dict) -> dict:
    """dic_content JSON 解析（数据边界校验，显式失败不静默）。"""
    raw = row.get("dic_content")
    if raw in (None, ""):
        return {}
    doc = json.loads(raw)  # 损坏数据直接抛错，由上层显式失败
    if not isinstance(doc, dict):
        raise ValueError(f"dic_content 非对象：id={row.get('id')}")
    return doc


def _label_index(reg: ModelRegistry, target_obj: str, key: str, label: str) -> dict:
    """ref 富化的标签索引：扫描目标 doc_type 行，key → label（模型驱动，无业务知识）。"""
    t = reg.objects[target_obj]
    src = None
    for q in t.get("queries") or []:
        mi = reg.mis[q["mi_ref"]]
        if mi.get("type_filter"):
            src = mi["local_source"]
            break
    if src is None:
        raise RuntimeError(f"ref 富化目标 {target_obj} 缺少带 type_filter 的查询 MI")
    out = {}
    for r in _load_local(src):
        if r.get("dic_name") != t.get("doc_type"):
            continue
        doc = _parse_doc(r)
        k, v = doc.get(key), doc.get(label)
        if k not in (None, ""):
            out[str(k)] = v
    return out


def _execute_query(reg: ModelRegistry, query_id: str, params: dict) -> list:
    """通用查询执行（可注入 registry，供引擎回归测试验证“纯 YAML 新增对象”）。"""
    _oid, q = reg.queries[query_id]
    mi = reg.mis[q["mi_ref"]]
    assert mi["effect"] == "READ_ONLY", "非只读 MI 不得进入 run_query"
    rows = _load_local(mi["local_source"])
    tf = mi.get("type_filter")
    if tf:
        rows = [r for r in rows if r.get("dic_name") == tf]
    kw = str(params.get("kw") or "").replace("%", "").strip().lower()
    fields = mi.get("local_search_fields", [])
    hits = [r for r in rows if not kw or any(kw in str(r.get(f) or "").lower() for f in fields)]
    hits = hits[:GATEWAY_ROW_LIMIT]  # 行数上限由 .env 统一控制
    cf = mi.get("content_fields") or []
    if cf:
        projected = []
        for r in hits:
            doc = _parse_doc(r)
            projected.append({**r, **{k: doc.get(k) for k in cf}})
        hits = projected
        # ref 富化：查询时带出目标显示名（AppBuilder engine __label 模式）
        for field, tobj, key, label in reg.mi_refs.get(mi["id"], []):
            labels = _label_index(reg, tobj, key, label)
            for r in hits:
                v = r.get(field)
                if v not in (None, ""):
                    r[field + "__label"] = labels.get(str(v))
    audit({"kind": "governed_query", "query": query_id, "mi": mi["id"], "params": params,
           "rows": len(hits), "source": "localdb"})
    return hits


def run_query(query_id: str, params: dict) -> list:
    return _execute_query(REG, query_id, params)


# ---------------- 写执行器调度（适配器模式：唯一知道 URL/Cookie/后端的地方） ----------------
WRITE_MODE = GATEWAY_WRITE_MODE  # 写模式由 .env 统一管理（config.py 映射）
WRITE_ADAPTER = get_write_adapter(WRITE_MODE, DPA_BASE,
                                  ROOT / "gateway/data/applied_writes.json", LOCALDB_DIR)

# 启动 fail-fast：所有只读 MI 依赖的本地库必须已引导
for _src in {mi["local_source"] for mi in REG.mis.values() if mi.get("effect") == "READ_ONLY"}:
    _load_local(_src)


def execute_write(mi_id: str, arguments: dict, cookie_header: str) -> dict:
    mi = REG.mis[mi_id]
    assert mi["effect"] == "WRITE", "非写 MI 不得进入执行器"
    return WRITE_ADAPTER.execute(mi, arguments, cookie_header)


# ---------------- 点路径取值（MI param_mapping / 禁止规则 / 文案模板共用） ----------------
def _dig(obj, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


# ---------------- 最小 Policy（fail-closed：封闭规则词表解释器） ----------------
def policy_check(behavior_id: str, arguments: dict) -> None:
    """C0-C2 最小检查：解释 MI forbidden_params 声明（封闭词表），未知规则 fail-closed。"""
    _oid, b = REG.behaviors[behavior_id]
    if b["kind"] != "write":
        return
    if not b.get("requires_approval"):
        raise ValueError("写行为必须声明 requires_approval")
    for fp in REG.mis[b["mi_ref"]].get("forbidden_params") or []:
        val = _dig(arguments, fp["param"])
        rule = fp["rule"]
        if rule == "nonempty_positive_ints":
            ok = (isinstance(val, list) and bool(val)
                  and all(str(x).lstrip("-").isdigit() and int(x) > 0 for x in val))
        elif rule == "nonempty":
            ok = bool(val)
        elif rule.startswith("in:"):
            ok = str(val) in rule[3:].split(",")
        else:
            raise RuntimeError(f"未知禁止规则类型，fail-closed：{rule}")
        if not ok:
            raise ValueError(fp.get("reason") or f"参数违反禁止规则：{fp['param']} {rule}")


# ---------------- 提案 ----------------
def _render(tpl: str, row: dict, inputs: dict) -> str:
    """渲染模型声明的文案模板：{字段} / {input.参数} 占位。"""
    env = dict(row or {})
    if inputs:
        env["input"] = dict(inputs)  # 嵌套结构，供 _dig 按 input.x 路径取值

    def rep(m: re.Match) -> str:
        v = _dig(env, m.group(1))
        return "—" if v is None else str(v)

    return re.sub(r"\{([\w.]+)\}", rep, tpl)


def build_arguments(behavior_id: str, row: dict, inputs: dict) -> dict:
    """提案参数构造：由 MI param_mapping 与行为文案模板统一推导，代码不含接口字段知识。"""
    _oid, b = REG.behaviors[behavior_id]
    mi = REG.mis[b["mi_ref"]]
    tfields: set = set()
    for v in (mi.get("param_mapping") or {}).values():
        for ph in re.findall(r"\{([\w.]+)\}", str(v)):
            if ph.startswith("target."):
                tfields.add(ph.split(".", 1)[1])
    for tpl in (b.get("target_label"), b.get("change_label")):
        for ph in re.findall(r"\{([\w.]+)\}", tpl or ""):
            if not ph.startswith("input."):
                tfields.add(ph)
    target = {}
    for f in tfields:
        if f == "ids":
            target["ids"] = [int(row["id"])]
        else:
            target[f] = row.get(f)
    return {"target": target, "input": dict(inputs)}


def create_proposal(behavior_id: str, arguments: dict, thread_id: str = "") -> dict:
    policy_check(behavior_id, arguments)
    _oid, b = REG.behaviors[behavior_id]
    mi = REG.mis[b["mi_ref"]]
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
    label = _render(b.get("target_label") or "（id={id}）", tgt, arguments.get("input") or {})
    change = _render(b.get("change_label") or "", tgt, arguments.get("input") or {})
    return {"proposal_id": pid, "state": "PENDING_APPROVAL", "risk": b["risk"],
            "token": token,  # MVP：单人演示随提案卡下发；正式 T07 改为仅授权审批人通道可见
            "display": f"{b['display_name']}：{label}",
            "change": change}


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


# ---------------- Agent Runtime（LangGraph + HITL，框架藏于 Runtime Interface 后） ----------------
from agent.runtime import GatewayBindings, build_runtime  # noqa: E402


def _build_table_event(obj_id: str, rows: list) -> dict:
    """表格事件完全由模型投影：列=visible 字段（含 ref 富化列），行=声明字段全集。"""
    cols = REG.visible_fields(obj_id)
    keep = REG.all_field_ids(obj_id)
    proj = [{k: r.get(k) for k in keep} for r in rows]
    return {"type": "object_table", "object": obj_id,
            "display": REG.display_name(obj_id),
            "columns": [c["display_name"] for c in cols],
            "rows": proj}


def _catalog() -> dict:
    """工具目录：从本体 YAML 推导查询/行为清单（意图解析与 fallback 路由共用）。"""
    qs, bs = [], []
    for oid, o in REG.objects.items():
        for q in o.get("queries") or []:
            qs.append({"id": q["id"], "display_name": q["display_name"], "object": oid,
                       "keywords": q.get("keywords", [])})
        for b in o.get("behaviors") or []:
            bs.append({"id": b["id"], "display_name": b["display_name"], "object": oid,
                       "target_locator": b.get("target_locator") or {},
                       "input_values": b.get("input_values") or {}})
    return {"queries": qs, "behaviors": bs}


agent_rt = build_runtime(GatewayBindings(
    catalog=_catalog,
    run_query=run_query,
    build_arguments=build_arguments,
    create_proposal=create_proposal,
    build_table_event=_build_table_event,
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
