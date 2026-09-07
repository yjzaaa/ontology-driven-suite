#!/usr/bin/env python3
"""从 MasterData 本体 YAML 生成 树(层级) + 图(引用关系) 自包含 HTML 可视化。

用法:
  python generate-ontology-view.py

输出:
  ontology-explorer/view.html  (离线可打开，无外部依赖)

原则: YAML 是事实源，HTML 是投影；图不成为第二事实源。
"""
import yaml, os, json, html, hashlib, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "models", "examples", "masterdata")
OUT = os.path.join(ROOT, "ontology-explorer", "view.html")

MODEL_TYPES = ["M1", "M2", "M3", "M5", "M6", "M7", "MU", "MI"]
TYPE_ZH = {
    "M1": "对象 Object", "M2": "行为 Behavior", "M3": "规则 Rule",
    "M5": "参与者/权限", "M6": "流程 Flow", "M7": "查询 Query",
    "MU": "展示 Presentation", "MI": "集成 Integration",
}
# 从各模型提取引用边（model_id -> 引用的 model_id 列表）
REF_FIELDS = {
    "M1": ["relations[].target"],
    "M2": ["target_object", "preconditions[]", "semantic_inputs[]?(ref)"],
    "M3": ["applies_to[]"],
    "M5": ["permissions[].applies_to"],
    "M6": ["trigger_behaviors[]", "guard_rules[]", "transitions[].trigger", "transitions[].guard[]"],
    "M7": ["target_object"],
    "MU": ["binds[]"],
    "MI": ["binds[]"],
}

def refs_of(d):
    """提取该模型的引用 model_id 列表。只扫描明确的引用承载字段，排除自身 ID、evidence_refs 与 Legacy View 回退。"""
    self_id = d.get("model_id", "")
    # 明确的引用承载字段：值为 model_id 或 列表/对象内嵌 model_id
    ref_carrying = ["target", "ref_model", "target_object", "preconditions", "applies_to",
                    "trigger_behaviors", "guard_rules", "trigger", "guard", "binds",
                    "relations", "attributes", "permissions", "transitions"]
    refs = []
    def walk(v):
        if isinstance(v, str) and v.startswith("masterdata.") and "@" not in v:
            r = v.split("@")[0]
            if r != self_id and not r.startswith("masterdata.mu.legacy"):
                refs.append(r)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if kk == "kind" or kk == "legacy_fallback":
                    continue
                walk(vv)
        elif isinstance(v, list):
            for it in v:
                walk(it)
    for key in ref_carrying:
        if key in d:
            walk(d[key])
    out = []
    for r in refs:
        if r not in out:
            out.append(r)
    return out

def load_models():
    models = []
    for fn in sorted(os.listdir(MODELS_DIR)):
        if not fn.endswith(".yaml"):
            continue
        if fn.startswith("publication") or fn == "m1-object.yaml" or fn == "m2-behavior.yaml" or True:
            pass
        p = os.path.join(MODELS_DIR, fn)
        if os.path.isdir(p):
            continue
        try:
            d = yaml.safe_load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "model_id" not in d:
            continue
        if d.get("model_type") not in MODEL_TYPES:
            continue
        d["_file"] = fn
        d["_refs"] = refs_of(d)
        models.append(d)
    return models

def esc(s):
    return html.escape(str(s))

def build_tree_html(models):
    by_type = {t: [m for m in models if m["model_type"] == t] for t in MODEL_TYPES}
    parts = []
    for t in MODEL_TYPES:
        ms = by_type[t]
        if not ms:
            continue
        parts.append(f'<details open class="type-group"><summary><b>{esc(TYPE_ZH[t])}</b> <span class="count">({len(ms)})</span></summary>')
        parts.append('<ul class="tree">')
        for m in ms:
            name = m.get("name", {})
            zh = name.get("zh", "") if isinstance(name, dict) else ""
            en = name.get("en", "") if isinstance(name, dict) else ""
            status = m.get("status", "")
            status_cls = status.lower()
            parts.append(f'<li><details open class="model"><summary class="{status_cls}">'
                         f'<span class="mid">{esc(m["model_id"])}</span>'
                         f'<span class="name">{esc(zh)} / {esc(en)}</span>'
                         f'<span class="status">{esc(status)}</span></summary>')
            parts.append('<ul class="props">')
            for key in ("identity_fields", "attributes", "relations", "target_object",
                        "semantic_inputs", "semantic_outputs", "preconditions", "side_effect",
                        "risk", "applies_to", "severity", "condition", "result",
                        "actors", "permissions", "data_scope", "authority_source",
                        "states", "transitions", "trigger_behaviors", "guard_rules", "terminals",
                        "semantic_parameters", "return_shape", "filters", "ordering", "pagination",
                        "row_scope", "limits", "binds", "view_structure", "intent", "legacy_fallback",
                        "target_kind", "fixed_params", "forbidden_params", "side_effect_level",
                        "timeout_ms", "retry_policy", "idempotent", "error_map", "credential_policy"):
                if key in m:
                    val = m[key]
                    parts.append(f'<li><span class="k">{esc(key)}</span>: <span class="v">{esc(json.dumps(val, ensure_ascii=False))}</span></li>')
            if m.get("evidence_refs"):
                parts.append(f'<li><span class="k">evidence_refs</span>: <span class="v">{len(m["evidence_refs"])} 条</span></li>')
            if m.get("_refs"):
                parts.append(f'<li><span class="k">→ 引用</span>: <span class="v">{", ".join(esc(r) for r in m["_refs"])}</span></li>')
            parts.append('</ul></details></li>')
        parts.append('</ul></details>')
    return "\n".join(parts)

def build_graph_svg(models):
    """按 model_type 分列布局的有向引用图。"""
    nodes = []
    for i, m in enumerate(models):
        nodes.append({
            "id": m["model_id"], "type": m["model_type"],
            "zh": m.get("name", {}).get("zh", "") if isinstance(m.get("name"), dict) else "",
            "status": m.get("status", ""),
        })
    id2node = {n["id"]: n for n in nodes}
    # 收集边 + 悬空引用
    edges = []
    dangling_ids = []
    for m in models:
        for r in m.get("_refs", []):
            if r in id2node:
                edges.append((m["model_id"], r))
            else:
                dangling_ids.append((m["model_id"], r))
    # 悬空引用节点（虚线红框，示意闭包缺口）
    dangling_nodes = []
    for src, r in dangling_ids:
        if r not in id2node:
            dangling_nodes.append({"id": r, "type": "dangling", "zh": "未建模", "status": "dangling"})
            id2node[r] = {"id": r, "type": "dangling", "zh": "未建模", "status": "dangling"}
            edges.append((src, r))
    # 布局：列 = model_type 顺序（dangling 放最后）
    col_w = 230
    row_h = 150
    node_w = 200
    node_h = 46
    all_nodes = nodes + dangling_nodes
    types_ordered = [t for t in MODEL_TYPES if any(n["type"] == t for n in all_nodes)]
    if any(n["type"] == "dangling" for n in all_nodes):
        types_ordered.append("dangling")
    col_of = {t: i for i, t in enumerate(types_ordered)}
    rows = {t: 0 for t in types_ordered}
    pos = {}
    for n in all_nodes:
        t = n["type"]
        if t not in col_of:
            t = "dangling"
        x = col_of[t] * col_w + 20
        y = rows[t] * row_h + 30
        rows[t] += 1
        pos[n["id"]] = (x, y, t)
    W = len(types_ordered) * col_w + 40
    H = max(rows.values()) * row_h + 90
    parts = []
    parts.append(f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">')
    parts.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#7c7c9c"/></marker></defs>')
    # 边
    for src, dst in edges:
        sx, sy, _ = pos[src]
        dx, dy, _ = pos[dst]
        x1 = sx + node_w
        y1 = sy + node_h / 2
        x2 = dx
        y2 = dy + node_h / 2
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#7c7c9c" stroke-width="1.6" marker-end="url(#arrow)" opacity="0.75"/>')
    # 节点
    colors = {"M1": "#4c78a8", "M2": "#f58518", "M3": "#54a24b", "M5": "#e45756",
              "M6": "#72b7b2", "M7": "#b279a2", "MU": "#ff9da6", "MI": "#9d755d",
              "dangling": "#c0392b"}
    for n in all_nodes:
        x, y, t = pos[n["id"]]
        c = colors.get(t, "#888")
        if t == "dangling":
            parts.append(f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="8" fill="none" stroke="{c}" stroke-width="1.8" stroke-dasharray="6 4"/>')
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="8" fill="{c}" opacity="0.92"/>')
        label = n["id"].split(".")[-1]
        zh = n["zh"]
        if t == "dangling":
            parts.append(f'<text x="{x+8}" y="{y+18}" fill="{c}" font-size="12" font-weight="bold">{esc(label)}</text>')
            parts.append(f'<text x="{x+8}" y="{y+35}" fill="{c}" font-size="10">(未建模/悬空引用)</text>')
        else:
            parts.append(f'<text x="{x+8}" y="{y+18}" fill="#fff" font-size="12" font-weight="bold">{esc(label)}</text>')
            if zh:
                parts.append(f'<text x="{x+8}" y="{y+35}" fill="#fff" font-size="10" opacity="0.9">{esc(zh)}</text>')
    parts.append('</svg>')
    return "\n".join(parts)

def main():
    models = load_models()
    tree = build_tree_html(models)
    graph = build_graph_svg(models)
    digest = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
    html_doc = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DPA 本体 YAML — 树与图（投影）</title>
<style>
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 0; background: #f6f7fb; color: #222; }}
  header {{ background: #1f2d3d; color: #fff; padding: 16px 24px; }}
  header h1 {{ margin: 0; font-size: 18px; }}
  header p {{ margin: 4px 0 0; color: #b8c4d0; font-size: 12px; }}
  nav.tabs {{ display: flex; gap: 8px; padding: 12px 24px; background: #fff; border-bottom: 1px solid #e3e6ee; }}
  nav.tabs button {{ padding: 8px 16px; border: 1px solid #d0d6e0; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }}
  nav.tabs button.active {{ background: #1f2d3d; color: #fff; border-color: #1f2d3d; }}
  main {{ padding: 20px 24px; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  .type-group {{ margin-bottom: 12px; background: #fff; border: 1px solid #e3e6ee; border-radius: 8px; padding: 10px 14px; }}
  .type-group summary {{ cursor: pointer; font-size: 14px; }}
  .count {{ color: #888; }}
  ul.tree {{ list-style: none; padding-left: 18px; margin: 6px 0 0; }}
  ul.props {{ list-style: none; padding-left: 16px; margin: 4px 0 8px; font-size: 12px; color: #444; }}
  ul.props li {{ padding: 1px 0; }}
  .model summary {{ cursor: pointer; padding: 4px 0; }}
  .mid {{ font-family: Consolas, monospace; color: #1a5c9e; font-weight: bold; margin-right: 10px; }}
  .name {{ color: #333; margin-right: 10px; }}
  .status {{ font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #f0f2f7; }}
  .status.review_required {{ background: #fff3cd; color: #856404; }}
  .k {{ color: #7a7f8a; }}
  .v {{ font-family: Consolas, monospace; font-size: 11px; color: #2c3e50; }}
  .graph-wrap {{ background: #fff; border: 1px solid #e3e6ee; border-radius: 8px; padding: 12px; overflow: auto; }}
  .legend {{ font-size: 12px; color: #555; margin: 8px 0; }}
  .legend span {{ margin-right: 12px; }}
  footer {{ padding: 12px 24px; color: #999; font-size: 11px; }}
</style>
</head>
<body>
<header>
  <h1>DPA 本体 YAML — 树与图（投影视图）</h1>
  <p>事实源：<code>models/examples/masterdata/*.yaml</code>（{len(models)} 个模型）｜ 本视图是只读投影，不成为第二事实源 ｜ 生成器 digest: {digest[:16]}</p>
</header>
<nav class="tabs">
  <button class="active" data-tab="tree">🌲 树（模型层级）</button>
  <button data-tab="graph">🕸 图（引用关系）</button>
</nav>
<main>
  <section id="tab-tree" class="tab-panel active">
    {tree}
  </section>
  <section id="tab-graph" class="tab-panel">
    <div class="legend">节点 = 本体模型（按模型类型分列）；箭头 = 引用关系（引用目标 model_id）。</div>
    <div class="graph-wrap">
      {graph}
    </div>
  </section>
</main>
<footer>YAML 是事实源，图是 Registry 生成的投影。本页由 ontology-explorer/generate-ontology-view.py 生成。</footer>
<script>
  document.querySelectorAll("nav.tabs button").forEach(function(btn){{
    btn.addEventListener("click", function(){{
      document.querySelectorAll("nav.tabs button").forEach(function(b){{ b.classList.remove("active"); }});
      document.querySelectorAll(".tab-panel").forEach(function(p){{ p.classList.remove("active"); }});
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    }});
  }});
</script>
</body>
</html>"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"生成完成: {OUT}")
    print(f"模型数: {len(models)}")
    for m in models:
        print(f"  {m['model_type']} {m['model_id']}  ->  {', '.join(m['_refs']) or '-'}")

if __name__ == "__main__":
    main()
