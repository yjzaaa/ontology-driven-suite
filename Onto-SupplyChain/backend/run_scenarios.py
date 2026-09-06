import json, time, urllib.request

BASE = "http://127.0.0.1:5002/api"

def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def show(name, resp):
    a = resp.get("assistant", {})
    sr = resp.get("scenario_result", {})
    rec = (sr.get("atp_summary") or {}).get("recommended", {})
    print(f"\n### {name}")
    print(f"  llm_mode={a.get('llm_mode')}  llm_error={a.get('llm_error','(none)')}")
    print(f"  recommended={rec.get('commitment_type')} date={rec.get('committed_date')} conf={rec.get('confidence_score')}")
    print(f"  AI回复: {(a.get('user_facing_reply') or '')[:110]}")
    print(f"  reason_chain[0]: {(a.get('reason_chain') or [''])[0][:90]}")

req = urllib.request.Request(BASE + "/scenarios");
with urllib.request.urlopen(req, timeout=30) as r:
    scenarios = json.loads(r.read().decode())
scenarios = scenarios["items"]
for s in scenarios:
    body = {"scenario_code": s["scenario_code"], "message": s["user_prompt"]}
    print(f">>> 运行场景: {s['scenario_name']} ({s['scenario_code']}) 目标单 {s['target_order_id']}")
    resp = post(f"/scenarios/{s['scenario_code']}/run", body)
    show(s["scenario_code"], resp)
    time.sleep(0.5)

# 一次自然语言对话
print("\n>>> /api/chat 自然语言对话: 订单SO1002物料延迟，推荐加班吗？")
resp = post("/chat", {"scenario_code": "material_delay", "message": "核心芯片延迟了，这单还能按原承诺交付吗？如果加班呢？"})
show("chat-material_delay", resp)
