"""知识图谱构建器：从五个本体模型 YAML 提取图谱节点和边

节点类型：entity / behavior / rule / scenario / metric
边类型：composition / aggregation / association / dependency / rule_ref / metric_dep / scenario_call / behavior_call

关键算法（从 M1 提取关系的 3 个来源）：
1. relations[] 列表中显式定义的关系
2. entities[].attributes[] 中 type=Reference 的字段
3. entities[].constraints[] 中 FOREIGN_KEY 类型（可选）

为保证关系完整性，三个来源会去重合并。
"""
from __future__ import annotations

from typing import Any


# ============================================================
# 节点视觉配置
# ============================================================
NODE_VISUAL = {
    "entity": {
        "core":    {"radius": 28, "color": "#5B4FBB"},
        "support": {"radius": 20, "color": "#3B9A80"},
    },
    "behavior": {"radius": 16, "color": "#CB6A2A"},
    "rule":     {"radius": 14, "color": "#BA7517"},
    "scenario": {"radius": 22, "color": "#3B78C0"},
    "metric":   {"radius": 15, "color": "#3B9A80", "shape": "diamond"},
}


# ============================================================
# 主入口
# ============================================================
def build_graph(models: dict[str, dict]) -> dict:
    """
    输入：models = {"M1": {...}, "M2": {...}, ...}
    输出：{"nodes": [...], "edges": [...], "stats": {...}}
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    node_ids: set[str] = set()
    edge_keys: set[tuple] = set()    # 用于去重边（source, target, type）

    if m1 := models.get("M1"):
        _add_entities(m1, nodes, node_ids)
        _add_relations(m1, edges, edge_keys, node_ids)

    if m2 := models.get("M2"):
        _add_behaviors(m2, nodes, edges, edge_keys, node_ids)

    if m3 := models.get("M3"):
        _add_rules(m3, nodes, edges, edge_keys, node_ids)

    if m_metric := models.get("M_Metric"):
        _add_metrics(m_metric, nodes, edges, edge_keys, node_ids)

    if m4 := models.get("M4"):
        _add_scenarios(m4, nodes, edges, edge_keys, node_ids)

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": _stats(nodes, edges),
    }


# ============================================================
# 增量构建 (用于阶段二的 SSE 流式推送)
# ============================================================
def build_graph_delta(model_key: str, model_data: dict, existing_node_ids: set[str]) -> dict:
    """生成单个模型新增的节点和边（用于 SSE 增量推送）"""
    nodes: list[dict] = []
    edges: list[dict] = []
    node_ids = set(existing_node_ids)
    edge_keys: set[tuple] = set()

    if model_key == "M1":
        _add_entities(model_data, nodes, node_ids)
        _add_relations(model_data, edges, edge_keys, node_ids)
    elif model_key == "M2":
        _add_behaviors(model_data, nodes, edges, edge_keys, node_ids)
    elif model_key == "M3":
        _add_rules(model_data, nodes, edges, edge_keys, node_ids)
    elif model_key == "M4":
        _add_scenarios(model_data, nodes, edges, edge_keys, node_ids)
    elif model_key == "M_Metric":
        _add_metrics(model_data, nodes, edges, edge_keys, node_ids)

    return {"nodes": nodes, "edges": edges, "added_node_ids": [n["id"] for n in nodes]}


# ============================================================
# 节点添加：M1 实体
# ============================================================
_CORE_DOMAINS = {"交易域", "用户域", "商品域"}


def _add_entities(m1: dict, nodes: list[dict], node_ids: set[str]) -> None:
    for ent in m1.get("entities", []):
        eid = ent.get("id")
        if not eid or eid in node_ids:
            continue
        subtype = "core" if (ent.get("domain") in _CORE_DOMAINS or "核心" in (ent.get("tags") or [])) else "support"
        visual = NODE_VISUAL["entity"][subtype]
        nodes.append({
            "id": eid,
            "label": ent.get("name", eid),
            "type": "entity",
            "subtype": subtype,
            "description": ent.get("description", ""),
            "domain": ent.get("domain"),
            "radius": visual["radius"],
            "color": visual["color"],
            "raw_ref": {"model": "M1", "key": "entities"},
        })
        node_ids.add(eid)


# ============================================================
# 边添加：M1 关系
# ============================================================
_REL_TYPE_NORMALIZE = {
    "COMPOSITION": "composition",
    "AGGREGATION": "aggregation",
    "ASSOCIATION": "association",
    "DEPENDENCY": "dependency",
}
_EDGE_VISUAL = {
    "composition": {"color": "#D05538", "width": 2.0, "dashArray": None},
    "aggregation": {"color": "#CB6A2A", "width": 1.5, "dashArray": None},
    "association": {"color": "#5B78C0", "width": 1.2, "dashArray": None},
    "dependency":  {"color": "#888780", "width": 1.0, "dashArray": "4 3"},
    "rule_ref":    {"color": "#BA7517", "width": 1.0, "dashArray": "4 3"},
    "metric_dep":  {"color": "#3B9A80", "width": 0.8, "dashArray": "3 3"},
    "scenario_call": {"color": "#3B78C0", "width": 1.0, "dashArray": None},
    "behavior_call": {"color": "#CB6A2A", "width": 1.0, "dashArray": "4 2"},
}


def _add_edge(edges: list[dict], edge_keys: set[tuple], source: str, target: str,
              etype: str, label: str = "", cardinality: str = "") -> bool:
    """添加边（自动去重）。返回是否新增"""
    if source == target:
        return False
    key = (source, target, etype)
    if key in edge_keys:
        return False
    visual = _EDGE_VISUAL.get(etype, {"color": "#888", "width": 1.0, "dashArray": None})
    edges.append({
        "id": f"E-{len(edges) + 1:04d}",
        "source": source,
        "target": target,
        "type": etype,
        "label": label,
        "cardinality": cardinality,
        "color": visual["color"],
        "width": visual["width"],
        "dashArray": visual["dashArray"],
    })
    edge_keys.add(key)
    return True


def _add_relations(m1: dict, edges: list[dict], edge_keys: set[tuple],
                   node_ids: set[str]) -> None:
    # 来源 1：显式 relations 列表
    for rel in m1.get("relations", []):
        src = rel.get("sourceEntity")
        tgt = rel.get("targetEntity")
        if not src or not tgt:
            continue
        # 若引用了未声明的实体，跳过以避免悬空连线
        if src not in node_ids or tgt not in node_ids:
            continue
        rtype = _REL_TYPE_NORMALIZE.get(str(rel.get("type", "")).upper(), "association")
        label = rel.get("targetRole") or rel.get("description") or ""
        cardinality = f"{rel.get('sourceCardinality', '')} → {rel.get('targetCardinality', '')}".strip()
        _add_edge(edges, edge_keys, src, tgt, rtype, label, cardinality)

    # 来源 2：属性中的 Reference 类型字段（兜底，避免关系遗漏）
    for ent in m1.get("entities", []):
        src = ent.get("id")
        if not src or src not in node_ids:
            continue
        for attr in (ent.get("attributes") or []):
            if attr.get("type") == "Reference":
                tgt = attr.get("refEntity")
                if tgt and tgt in node_ids:
                    label = attr.get("label") or attr.get("name", "")
                    cardinality = attr.get("refCardinality", "")
                    _add_edge(edges, edge_keys, src, tgt, "association", label, cardinality)

    # 来源 3：constraints 中的 FOREIGN_KEY 类型
    for ent in m1.get("entities", []):
        src = ent.get("id")
        if not src or src not in node_ids:
            continue
        for c in (ent.get("constraints") or []):
            if str(c.get("constraintType", "")).upper() == "FOREIGN_KEY":
                # 表达式可能形如 "buyerId REFERENCES ENT-USR-001"
                expr = c.get("expression", "")
                for token in expr.replace(",", " ").split():
                    if token in node_ids and token != src:
                        _add_edge(edges, edge_keys, src, token, "dependency", "FK")


# ============================================================
# M2 行为节点 + 连接到所属实体/相关指标
# ============================================================
def _add_behaviors(m2: dict, nodes: list[dict], edges: list[dict],
                   edge_keys: set[tuple], node_ids: set[str]) -> None:
    visual = NODE_VISUAL["behavior"]
    for b in m2.get("behaviors", []):
        bid = b.get("id")
        if not bid or bid in node_ids:
            continue
        nodes.append({
            "id": bid,
            "label": b.get("name", bid),
            "type": "behavior",
            "subtype": str(b.get("computationType", "")).lower(),
            "description": b.get("description", ""),
            "radius": visual["radius"],
            "color": visual["color"],
            "raw_ref": {"model": "M2", "key": "behaviors"},
        })
        node_ids.add(bid)
        # 连到所属实体
        owner = b.get("ownerEntity")
        if owner and owner in node_ids:
            _add_edge(edges, edge_keys, bid, owner, "behavior_call", "作用于")
        # 连到相关指标
        for m_ref in (b.get("relatedMetrics") or []):
            if m_ref in node_ids:
                _add_edge(edges, edge_keys, bid, m_ref, "metric_dep", "依赖指标")
        # 连到引用规则
        for r_ref in (b.get("appliedRules") or []):
            if r_ref in node_ids:
                _add_edge(edges, edge_keys, bid, r_ref, "rule_ref", "应用规则")


# ============================================================
# M3 规则节点 + 反向连接
# ============================================================
def _add_rules(m3: dict, nodes: list[dict], edges: list[dict],
               edge_keys: set[tuple], node_ids: set[str]) -> None:
    visual = NODE_VISUAL["rule"]
    for r in m3.get("rules", []):
        rid = r.get("id")
        if not rid or rid in node_ids:
            continue
        nodes.append({
            "id": rid,
            "label": r.get("name", rid),
            "type": "rule",
            "subtype": str(r.get("ruleType", "")).lower(),
            "description": r.get("description", ""),
            "radius": visual["radius"],
            "color": visual["color"],
            "raw_ref": {"model": "M3", "key": "rules"},
        })
        node_ids.add(rid)
        # 规则被哪些行为引用（反向连线 — 但 M2 已经连过去了，这里检测 reusedBy 字段）
        for b_ref in (r.get("reusedBy") or []):
            if b_ref in node_ids:
                _add_edge(edges, edge_keys, b_ref, rid, "rule_ref", "应用规则")


# ============================================================
# M_Metric 指标节点
# ============================================================
def _add_metrics(mm: dict, nodes: list[dict], edges: list[dict],
                 edge_keys: set[tuple], node_ids: set[str]) -> None:
    visual = NODE_VISUAL["metric"]
    for m in mm.get("metrics", []):
        mid = m.get("id")
        if not mid or mid in node_ids:
            continue
        nodes.append({
            "id": mid,
            "label": m.get("name", mid),
            "type": "metric",
            "subtype": str(m.get("computation_type", "")).lower(),
            "description": m.get("description") or m.get("formula_description", ""),
            "unit": m.get("unit"),
            "radius": visual["radius"],
            "color": visual["color"],
            "shape": "diamond",
            "raw_ref": {"model": "M_Metric", "key": "metrics"},
        })
        node_ids.add(mid)
        # 指标依赖实体
        for e_ref in (m.get("depends_on_entities") or []):
            if e_ref in node_ids:
                _add_edge(edges, edge_keys, mid, e_ref, "metric_dep", "依赖实体")
        # 指标引用规则
        for r_ref in (m.get("rule_refs") or []):
            if r_ref in node_ids:
                _add_edge(edges, edge_keys, mid, r_ref, "rule_ref", "应用规则")


# ============================================================
# M4 场景节点
# ============================================================
def _add_scenarios(m4: dict, nodes: list[dict], edges: list[dict],
                   edge_keys: set[tuple], node_ids: set[str]) -> None:
    visual = NODE_VISUAL["scenario"]
    for s in m4.get("scenarios", []):
        sid = s.get("id")
        if not sid or sid in node_ids:
            continue
        nodes.append({
            "id": sid,
            "label": s.get("name", sid),
            "type": "scenario",
            "description": s.get("description", ""),
            "radius": visual["radius"],
            "color": visual["color"],
            "raw_ref": {"model": "M4", "key": "scenarios"},
        })
        node_ids.add(sid)
        # 场景依赖行为
        for b_ref in (s.get("relatedBehaviors") or []):
            if b_ref in node_ids:
                _add_edge(edges, edge_keys, sid, b_ref, "scenario_call", "调用行为")
        # 场景关键指标
        for m_ref in (s.get("keyMetrics") or []):
            if m_ref in node_ids:
                _add_edge(edges, edge_keys, sid, m_ref, "metric_dep", "关键指标")


# ============================================================
# 统计
# ============================================================
def _stats(nodes: list[dict], edges: list[dict]) -> dict:
    by_type: dict[str, int] = {}
    for n in nodes:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    edge_by_type: dict[str, int] = {}
    for e in edges:
        edge_by_type[e["type"]] = edge_by_type.get(e["type"], 0) + 1
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes_by_type": by_type,
        "edges_by_type": edge_by_type,
    }
