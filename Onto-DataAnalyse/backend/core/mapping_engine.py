"""映射引擎：本体实体 → 数据库表/字段 映射的生成与查询"""
from __future__ import annotations

import json

from backend.config.settings import settings
from backend.db.database import system_db
from backend.utils.yaml_utils import dump_yaml, save_yaml_file


MAPPING_FILE = "data_mapping.yaml"      # 落盘在 models/{pid}/data_mapping.yaml


def save_mapping(mapping: dict) -> str:
    """把 mapping JSON 同时写到 YAML 文件 + 系统库 projects.mapping_data"""
    out_path = settings.project_models_dir() / MAPPING_FILE
    save_yaml_file(out_path, mapping)
    with system_db() as conn:
        conn.execute(
            "UPDATE projects SET mapping_data = ? WHERE id = ?",
            (json.dumps(mapping, ensure_ascii=False), settings.PROJECT_ID),
        )
    return str(out_path)


def load_mapping() -> dict | None:
    """从系统库读取"""
    with system_db() as conn:
        row = conn.execute(
            "SELECT mapping_data FROM projects WHERE id = ?", (settings.PROJECT_ID,)
        ).fetchone()
        if not row or not row["mapping_data"]:
            return None
        try:
            return json.loads(row["mapping_data"])
        except (TypeError, json.JSONDecodeError):
            return None


def validate_mapping(mapping: dict) -> tuple[bool, str]:
    """轻量校验 mapping 结构"""
    if not isinstance(mapping, dict):
        return False, "映射根节点必须是 dict"
    ems = mapping.get("entity_mappings")
    if not isinstance(ems, list) or not ems:
        return False, "缺少 entity_mappings 列表"
    for em in ems:
        if not em.get("entity_id"):
            return False, f"映射缺少 entity_id：{em}"
        tables = em.get("tables") or []
        if not tables:
            return False, f"实体 {em['entity_id']} 缺少 tables 配置"
        if not any(t.get("primary") for t in tables):
            return False, f"实体 {em['entity_id']} 没有指定主表（primary: true）"
        fms = em.get("field_mappings") or []
        for fm in fms:
            if not fm.get("ontology_field") or not fm.get("db_column"):
                return False, f"实体 {em['entity_id']} 有字段映射缺少 ontology_field 或 db_column"
            if not isinstance(fm.get("confidence"), (int, float)):
                return False, f"实体 {em['entity_id']} 字段 {fm.get('ontology_field')} 缺少 confidence"
    return True, ""


def build_mapping_visualization(mapping: dict, m1_yaml: dict | None) -> dict:
    """
    把 mapping 整理为前端可视化友好的结构：
    {
      "entities": [
        {
          "entity_id": "ENT-ORD-001",
          "entity_name": "订单",
          "fields": [{name, label}, ...]                      # 本体侧字段
        }
      ],
      "tables": [
        {"table": "t_order", "columns": [{name, mapped: bool}, ...]}
      ],
      "links": [
        {
          "entity_id": "ENT-ORD-001",
          "ontology_field": "orderId",
          "table": "t_order",
          "db_column": "order_id",
          "confidence": 1.0,
          "color": "#22C55E",
          "note": null,
          "value_mapping": {...}
        }
      ]
    }
    """
    if not mapping:
        return {"entities": [], "tables": [], "links": []}

    # 1. 实体侧 ── 从 M1 拿全部字段 + 与映射对齐
    entities_view: list[dict] = []
    if m1_yaml:
        for ent in m1_yaml.get("entities", []):
            entities_view.append({
                "entity_id": ent["id"],
                "entity_name": ent.get("name", ent["id"]),
                "fields": [
                    {"name": a.get("name"), "label": a.get("label", a.get("name"))}
                    for a in (ent.get("attributes") or [])
                ],
            })

    # 2. 表侧 ── 收集所有出现的表，列出每张表被映射的列
    table_col_map: dict[str, set[str]] = {}
    for em in mapping.get("entity_mappings", []):
        for fm in (em.get("field_mappings") or []):
            t = fm.get("db_table") or _primary_table(em)
            if not t:
                continue
            table_col_map.setdefault(t, set()).add(fm["db_column"])

    tables_view = [
        {
            "table": t,
            "columns": sorted([{"name": c, "mapped": True} for c in cols], key=lambda x: x["name"]),
        }
        for t, cols in sorted(table_col_map.items())
    ]

    # 3. 连线
    links: list[dict] = []
    for em in mapping.get("entity_mappings", []):
        for fm in (em.get("field_mappings") or []):
            conf = float(fm.get("confidence") or 0)
            links.append({
                "entity_id": em["entity_id"],
                "ontology_field": fm["ontology_field"],
                "table": fm.get("db_table") or _primary_table(em),
                "db_column": fm["db_column"],
                "db_expression": fm.get("db_expression"),
                "confidence": conf,
                "color": _confidence_color(conf),
                "note": fm.get("note"),
                "value_mapping": fm.get("value_mapping"),
            })

    return {
        "entities": entities_view,
        "tables": tables_view,
        "links": links,
        "stats": {
            "entity_count": len(entities_view),
            "table_count": len(tables_view),
            "link_count": len(links),
            "low_confidence_count": sum(1 for l in links if l["confidence"] < 0.7),
        },
    }


def _primary_table(em: dict) -> str | None:
    for t in (em.get("tables") or []):
        if t.get("primary"):
            return t.get("table")
    return (em.get("tables") or [{}])[0].get("table")


def _confidence_color(c: float) -> str:
    if c >= 0.90:
        return "#22C55E"   # 绿
    if c >= 0.70:
        return "#F59E0B"   # 橙
    return "#EF4444"       # 红
