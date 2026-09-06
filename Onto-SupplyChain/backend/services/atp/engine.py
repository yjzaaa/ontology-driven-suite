from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any


DATE_FMT = "%Y-%m-%d"


def _parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FMT).date()


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def _load_inventory(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute("SELECT * FROM inventory").fetchall()
    return {row["item_id"]: dict(row) for row in rows}


def _load_suppliers(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT i.item_id, s.*
        FROM item_suppliers i
        JOIN suppliers s ON s.supplier_id = i.supplier_id
        ORDER BY i.item_id, i.is_primary DESC
        """
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["item_id"]].append(dict(row))
    return grouped


def _load_bom(conn: sqlite3.Connection, parent_item_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT bi.*, ba.alt_item_id, ba.usage_priority, ba.substitution_ratio, ba.approval_status
        FROM bom_headers bh
        JOIN bom_items bi ON bi.bom_id = bh.bom_id
        LEFT JOIN bom_alternatives ba ON ba.bom_item_id = bi.bom_item_id
        WHERE bh.parent_item_id = ?
        ORDER BY bi.level, bi.bom_item_id
        """,
        (parent_item_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _load_routing(conn: sqlite3.Connection, item_id: str, routing_type: str = "Standard") -> dict[str, Any] | None:
    routing = conn.execute(
        "SELECT * FROM routings WHERE item_id = ? AND routing_type = ? ORDER BY routing_version DESC LIMIT 1",
        (item_id, routing_type),
    ).fetchone()
    if not routing:
        return None
    ops = conn.execute(
        """
        SELECT ro.*, wc.wc_name, wc.standard_capacity_per_day, wc.efficiency_factor,
               wc.overtime_capacity_per_day, wc.bottleneck_flag, wc.utilization_target
        FROM routing_operations ro
        JOIN work_centers wc ON wc.wc_id = ro.wc_id
        WHERE ro.routing_id = ?
        ORDER BY ro.op_sequence
        """,
        (routing["routing_id"],),
    ).fetchall()
    result = dict(routing)
    result["operations"] = [dict(op) for op in ops]
    result["alternatives"] = [
        dict(row)
        for row in conn.execute(
            """
            SELECT ra.*, r.routing_type
            FROM routing_alternatives ra
            JOIN routings r ON r.routing_id = ra.alternative_routing_id
            WHERE ra.routing_id = ?
            """,
            (routing["routing_id"],),
        ).fetchall()
    ]
    return result


def _existing_load(conn: sqlite3.Connection, wc_id: str, work_date: str) -> float:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(
            o.setup_time_hours + (o.process_time_per_unit_hours * (po.planned_quantity - po.confirmed_quantity))
            + o.queue_time_hours + o.move_time_hours
        ), 0) AS load_hours
        FROM operations o
        JOIN production_orders po ON po.wo_id = o.wo_id
        WHERE o.wc_id = ?
          AND date(po.forecast_end) = date(?)
          AND po.status IN ('Planned', 'InProgress')
        """,
        (wc_id, work_date),
    ).fetchone()
    return float(row["load_hours"] or 0.0)


def _next_calendar_day(conn: sqlite3.Connection, wc_id: str, start_date: date, include_overtime: bool) -> tuple[date, dict[str, Any]] | None:
    rows = conn.execute(
        """
        SELECT * FROM work_center_calendar
        WHERE wc_id = ? AND date(work_date) >= date(?)
        ORDER BY work_date
        """,
        (wc_id, start_date.strftime(DATE_FMT)),
    ).fetchall()
    for row in rows:
        calendar = dict(row)
        available = float(calendar["available_hours"]) - float(calendar["maintenance_hours"])
        if include_overtime:
            available += float(calendar["overtime_hours"])
        if available > 0:
            return _parse_date(calendar["work_date"]), calendar
    return None


def _estimate_material_ready_date(
    conn: sqlite3.Connection,
    item_id: str,
    short_qty: float,
    inventory_map: dict[str, dict[str, Any]],
    supplier_map: dict[str, list[dict[str, Any]]],
    bom_rows: list[dict[str, Any]],
    reason_chain: list[str],
    impact_objects: list[dict[str, str]],
) -> tuple[date, list[dict[str, Any]], list[dict[str, Any]]]:
    today = date(2026, 4, 2)
    candidate_dates = [today]
    shortages: list[dict[str, Any]] = []
    alternatives_used: list[dict[str, Any]] = []
    by_child: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bom_rows:
        by_child[row["child_item_id"]].append(row)

    for child_item_id, entries in by_child.items():
        entry = entries[0]
        needed = short_qty * float(entry["quantity_per"]) * float(entry["scrap_factor"])
        inventory = inventory_map.get(child_item_id)
        available = float(inventory["available_qty"]) if inventory else 0.0
        if available >= needed:
            continue

        gap = round(needed - available, 2)
        used_alternative = False
        for alt in entries:
            if alt["alt_item_id"] and alt["approval_status"] == "Approved":
                alt_inventory = inventory_map.get(alt["alt_item_id"])
                alt_available = float(alt_inventory["available_qty"]) if alt_inventory else 0.0
                alt_needed = gap * float(alt["substitution_ratio"] or 1.0)
                if alt_available >= alt_needed:
                    alternatives_used.append(
                        {
                            "component": child_item_id,
                            "alternative_item_id": alt["alt_item_id"],
                            "qty": round(alt_needed, 2),
                        }
                    )
                    reason_chain.append(f"关键物料 {child_item_id} 库存不足，但可用已批准替代料 {alt['alt_item_id']} 补足缺口。")
                    impact_objects.append({"type": "item", "id": alt["alt_item_id"], "label": alt["alt_item_id"]})
                    used_alternative = True
                    break

        if used_alternative:
            continue

        inbound = conn.execute(
            """
            SELECT * FROM inventory_inbound
            WHERE item_id = ? AND status IN ('Planned', 'Delayed')
            ORDER BY expected_arrival_date
            LIMIT 1
            """,
            (child_item_id,),
        ).fetchone()
        if inbound:
            arrival_date = _parse_date(inbound["expected_arrival_date"])
            candidate_dates.append(arrival_date)
            reason_chain.append(
                f"物料 {child_item_id} 缺口 {gap:.0f}，最早依赖在途到货 {arrival_date.strftime(DATE_FMT)}。"
            )
        else:
            suppliers = supplier_map.get(child_item_id, [])
            lead_days = int(suppliers[0]["standard_lt_days"]) if suppliers else 7
            arrival_date = today + timedelta(days=lead_days)
            candidate_dates.append(arrival_date)
            reason_chain.append(f"物料 {child_item_id} 无在途库存，需要按标准采购提前期 {lead_days} 天补料。")
        impact_objects.append({"type": "item", "id": child_item_id, "label": child_item_id})
        shortages.append(
            {
                "item_id": child_item_id,
                "needed_qty": round(needed, 2),
                "available_qty": round(available, 2),
                "gap_qty": gap,
                "material_ready_date": arrival_date.strftime(DATE_FMT),
            }
        )

    return max(candidate_dates), shortages, alternatives_used


def _estimate_routing_finish(
    conn: sqlite3.Connection,
    routing: dict[str, Any],
    quantity: float,
    start_date: date,
    include_overtime: bool,
    reason_chain: list[str],
    impact_objects: list[dict[str, str]],
) -> tuple[date, dict[str, Any]]:
    current_date = start_date
    bottleneck_pressure = 0.0
    wc_load_snapshot: list[dict[str, Any]] = []
    for operation in routing["operations"]:
        remaining_hours = float(operation["standard_setup_hours"]) + float(operation["standard_process_hours"]) * quantity
        while remaining_hours > 0:
            next_day = _next_calendar_day(conn, operation["wc_id"], current_date, include_overtime)
            if not next_day:
                raise RuntimeError(f"工作中心 {operation['wc_id']} 无可用日历")
            work_date, calendar = next_day
            base_hours = float(calendar["available_hours"]) - float(calendar["maintenance_hours"])
            if include_overtime:
                base_hours += float(calendar["overtime_hours"])
            existing = _existing_load(conn, operation["wc_id"], work_date.strftime(DATE_FMT))
            effective_capacity = max(base_hours * float(operation["efficiency_factor"]) - existing, 0.0)
            if effective_capacity <= 0:
                current_date = work_date + timedelta(days=1)
                continue
            used = min(remaining_hours, effective_capacity)
            remaining_hours -= used
            util = 0.0 if base_hours == 0 else (existing + used) / max(base_hours, 0.1)
            wc_load_snapshot.append(
                {
                    "wc_id": operation["wc_id"],
                    "wc_name": operation["wc_name"],
                    "work_date": work_date.strftime(DATE_FMT),
                    "existing_load_hours": round(existing, 2),
                    "used_hours": round(used, 2),
                    "utilization": round(util, 2),
                }
            )
            bottleneck_pressure = max(bottleneck_pressure, util)
            current_date = work_date
            if remaining_hours > 0:
                current_date = work_date + timedelta(days=1)
        impact_objects.append({"type": "work_center", "id": operation["wc_id"], "label": operation["wc_name"]})

    finish_date = current_date
    reason_chain.append(f"按 {routing['routing_type']} 路线排产，最早完工日期为 {finish_date.strftime(DATE_FMT)}。")
    return finish_date, {"wc_load_snapshot": wc_load_snapshot, "bottleneck_pressure": round(bottleneck_pressure, 2)}


def _score_confidence(
    customer: dict[str, Any],
    shortages: list[dict[str, Any]],
    supplier_risks: list[dict[str, Any]],
    bottleneck_pressure: float,
    include_overtime: bool,
    uses_alternative: bool,
) -> tuple[float, str]:
    score = 85.0
    if not shortages:
        score += 5
    if include_overtime:
        score -= 3
    if uses_alternative:
        score -= 5
    if customer["priority_level"] == "VIP":
        score += 2
    for risk in supplier_risks:
        if risk["single_source_flag"]:
            score -= 10
        if risk["on_time_rate"] < 0.85:
            score -= 8
    if bottleneck_pressure > 0.95:
        score -= 8
    elif bottleneck_pressure > 0.85:
        score -= 5
    score = max(40.0, min(98.0, score))
    risk_level = "Low" if score >= 90 else "Medium" if score >= 75 else "High"
    return round(score, 1), risk_level


def _collect_supplier_risks(supplier_map: dict[str, list[dict[str, Any]]], bom_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = sorted({row["child_item_id"] for row in bom_rows})
    risks: list[dict[str, Any]] = []
    for item_id in items:
        supplier = supplier_map.get(item_id, [])
        if not supplier:
            continue
        primary = supplier[0]
        risks.append(
            {
                "item_id": item_id,
                "supplier_id": primary["supplier_id"],
                "supplier_name": primary["supplier_name"],
                "on_time_rate": float(primary["on_time_rate"]),
                "single_source_flag": bool(primary["single_source_flag"]),
            }
        )
    return risks


def _serialize_scenario(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["payload"] = json.loads(data.pop("payload_json"))
    data["is_default"] = bool(data["is_default"])
    return data


class ATPService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_scenarios(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM demo_scenarios ORDER BY scenario_name").fetchall()
        return [_serialize_scenario(row) for row in rows]

    def get_scenario(self, scenario_code: str) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM demo_scenarios WHERE scenario_code = ?", (scenario_code,)).fetchone()
        if not row:
            raise KeyError(f"Unknown scenario: {scenario_code}")
        return _serialize_scenario(row)

    def run_scenario(self, scenario_code: str, user_message: str | None = None) -> dict[str, Any]:
        scenario = self.get_scenario(scenario_code)
        return self.analyze_order(
            order_id=scenario["target_order_id"],
            scenario=scenario,
            event_type=scenario["scenario_type"],
            event_payload=scenario["payload"],
            user_message=user_message or scenario["user_prompt"],
        )

    def analyze_order(
        self,
        order_id: str,
        scenario: dict[str, Any] | None = None,
        event_type: str | None = None,
        event_payload: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> dict[str, Any]:
        event_payload = event_payload or {}
        trace: list[dict[str, Any]] = []

        def log(step: str, title: str, details: list[str], rule_ids: list[str] | None = None, objects: list[str] | None = None) -> None:
            trace.append(
                {
                    "step": step,
                    "title": title,
                    "details": details,
                    "rule_ids": rule_ids or [],
                    "objects": objects or [],
                }
            )

        order = _row_dict(
            self.conn.execute(
                """
                SELECT co.*, c.customer_name, c.priority_level, c.penalty_threshold_days, c.penalty_rate,
                       c.delivery_reliability, c.complaint_sensitivity,
                       fi.item_name, fi.item_category, fi.safety_stock, fi.min_order_quantity
                FROM customer_orders co
                JOIN customers c ON c.customer_id = co.customer_id
                JOIN finished_items fi ON fi.item_id = co.item_id
                WHERE co.order_id = ?
                """,
                (order_id,),
            ).fetchone()
        )
        if not order:
            raise KeyError(f"Unknown order: {order_id}")
        log(
            "S1",
            "识别场景对象",
            [
                f"定位订单 {order['order_id']}，客户 {order['customer_name']}，成品 {order['item_id']} / {order['item_name']}。",
                f"事件类型为 {event_type or 'manual_analysis'}，客户要求交期 {order['requested_date']}。",
            ],
            rule_ids=["Ontology:CustomerOrder", "Ontology:Customer", "Ontology:FinishedItem"],
            objects=[order["order_id"], order["customer_id"], order["item_id"]],
        )

        inventory_map = _load_inventory(self.conn)
        supplier_map = _load_suppliers(self.conn)
        bom_rows = _load_bom(self.conn, order["item_id"])
        routing = _load_routing(self.conn, order["item_id"], "Standard")
        alt_routing = _load_routing(self.conn, order["item_id"], "Alternative")
        log(
            "S2",
            "加载基础对象数据",
            [
                f"读取库存对象 {len(inventory_map)} 条，用于计算 available_qty。",
                f"读取 BOM 组件 {len(bom_rows)} 条，用于展开物料需求。",
                f"读取供应商映射 {sum(len(v) for v in supplier_map.values())} 条，用于判断提前期和风险。",
                f"读取标准工艺路线 {'1 条' if routing else '0 条'}，替代路线 {'1 条' if alt_routing else '0 条'}。",
            ],
            rule_ids=["CR-01", "CR-02", "CR-03", "ALT-01"],
            objects=[order["item_id"]],
        )

        requested_date = _parse_date(order["requested_date"])
        target_quantity = float(event_payload.get("new_quantity", order["quantity"] + event_payload.get("insert_quantity", 0)))
        inventory = inventory_map.get(order["item_id"])
        available_finished = float(inventory["available_qty"]) if inventory else 0.0
        stock_cover_qty = min(target_quantity, available_finished)
        required_production_qty = max(target_quantity - stock_cover_qty, 0.0)
        log(
            "S3",
            "执行成品库存可承诺判断",
            [
                f"目标需求数量 {target_quantity:.0f}，成品可用库存 {available_finished:.0f}。",
                f"库存可直接覆盖 {stock_cover_qty:.0f}，剩余需生产补足 {required_production_qty:.0f}。",
                "这里应用的是 Inventory.available_qty 语义，而不是 on_hand_qty。",
            ],
            rule_ids=["CR-01", "Inventory.available_qty"],
            objects=[order["item_id"]],
        )

        reason_chain: list[str] = []
        impact_objects: list[dict[str, str]] = [
            {"type": "order", "id": order["order_id"], "label": order["order_id"]},
            {"type": "customer", "id": order["customer_id"], "label": order["customer_name"]},
            {"type": "item", "id": order["item_id"], "label": order["item_name"]},
        ]

        if stock_cover_qty > 0:
            reason_chain.append(f"成品 {order['item_id']} 当前可用库存 {available_finished:.0f}，可先覆盖 {stock_cover_qty:.0f}。")
        else:
            reason_chain.append(f"成品 {order['item_id']} 当前无足够可用库存，需要完全走生产补足。")

        material_ready_date = date(2026, 4, 2)
        shortages: list[dict[str, Any]] = []
        alternatives_used: list[dict[str, Any]] = []
        if required_production_qty > 0:
            material_ready_date, shortages, alternatives_used = _estimate_material_ready_date(
                self.conn, order["item_id"], required_production_qty, inventory_map, supplier_map, bom_rows, reason_chain, impact_objects
            )
            bom_details = [
                f"展开 BOM 子项 {row['child_item_id']}：单位用量 {row['quantity_per']}，损耗系数 {row['scrap_factor']}。"
                for row in bom_rows[:6]
            ]
            log(
                "S4",
                "展开 BOM 并计算物料缺口",
                [
                    f"针对需生产数量 {required_production_qty:.0f} 展开物料需求。",
                    *bom_details,
                    f"识别短缺项目 {len(shortages)} 条，物料最晚齐套日期推演为 {material_ready_date.strftime(DATE_FMT)}。",
                ],
                rule_ids=["BOMLevel.quantity_per", "BOMLevel.scrap_factor", "CR-03"],
                objects=[row["child_item_id"] for row in bom_rows[:6]],
            )
        if event_payload.get("delay_item_id") and event_payload.get("delay_days"):
            delay_days = int(event_payload["delay_days"])
            material_ready_date = material_ready_date + timedelta(days=delay_days)
            reason_chain.append(
                f"场景设定为关键物料 {event_payload['delay_item_id']} 延迟 {delay_days} 天，物料齐套时间顺延。"
            )
            log(
                "S5",
                "应用场景事件修正",
                [
                    f"关键物料 {event_payload['delay_item_id']} 延迟 {delay_days} 天。",
                    f"物料齐套日期顺延到 {material_ready_date.strftime(DATE_FMT)}。",
                ],
                rule_ids=["ScenarioOverride:material_delay"],
                objects=[str(event_payload["delay_item_id"])],
            )

        supplier_risks = _collect_supplier_risks(supplier_map, bom_rows)
        if supplier_risks:
            log(
                "S6",
                "评估供应风险",
                [
                    f"识别供应风险对象 {risk['item_id']} -> {risk['supplier_name']}，准时率 {risk['on_time_rate']:.2f}，单一来源 {risk['single_source_flag']}。"
                    for risk in supplier_risks
                ],
                rule_ids=["RISK-01"],
                objects=[risk["supplier_id"] for risk in supplier_risks],
            )
        standard_finish_date = material_ready_date
        standard_detail = {"wc_load_snapshot": [], "bottleneck_pressure": 0.0}
        if required_production_qty > 0 and routing:
            standard_finish_date, standard_detail = _estimate_routing_finish(
                self.conn, routing, required_production_qty, material_ready_date, False, reason_chain, impact_objects
            )
            route_log = [
                f"工序工作中心 {item['wc_name']} 在 {item['work_date']} 使用 {item['used_hours']} 小时，利用率 {item['utilization']}。"
                for item in standard_detail["wc_load_snapshot"][:8]
            ]
            log(
                "S7",
                "按标准路线进行产能排程",
                [
                    f"标准路线最早完工日期 {standard_finish_date.strftime(DATE_FMT)}。",
                    *route_log,
                    f"瓶颈压力系数 {standard_detail['bottleneck_pressure']}。",
                ],
                rule_ids=["C-01", "C-02", "C-03", "ALT-01"],
                objects=[item["wc_id"] for item in standard_detail["wc_load_snapshot"][:8]],
            )
        if event_payload.get("bottleneck_wc_id"):
            standard_finish_date = standard_finish_date + timedelta(days=2)
            standard_detail["bottleneck_pressure"] = max(standard_detail["bottleneck_pressure"], 1.02)
            reason_chain.append(
                f"场景设定中 {event_payload['bottleneck_wc_id']} 产能爆满，标准路线额外顺延 2 天。"
            )
            log(
                "S8",
                "应用瓶颈产能场景修正",
                [
                    f"工作中心 {event_payload['bottleneck_wc_id']} 设定为爆满状态。",
                    f"标准方案额外顺延 2 天，瓶颈压力提升到 {standard_detail['bottleneck_pressure']}。",
                ],
                rule_ids=["ScenarioOverride:capacity_bottleneck"],
                objects=[str(event_payload["bottleneck_wc_id"])],
            )

        standard_confidence, standard_risk = _score_confidence(
            order, shortages, supplier_risks, standard_detail["bottleneck_pressure"], False, bool(alternatives_used)
        )
        standard_date = standard_finish_date if required_production_qty > 0 else date(2026, 4, 2)
        standard_candidate = {
            "commitment_type": "Standard",
            "committed_date": standard_date.strftime(DATE_FMT),
            "confidence_score": standard_confidence,
            "risk_level": standard_risk,
            "cost_impact": 0,
            "summary": "按标准库存与标准路线承诺。",
        }

        overtime_candidate = dict(standard_candidate)
        if required_production_qty > 0 and routing:
            overtime_finish, overtime_detail = _estimate_routing_finish(
                self.conn, routing, required_production_qty, material_ready_date, True, [], []
            )
            overtime_confidence, overtime_risk = _score_confidence(
                order, shortages, supplier_risks, overtime_detail["bottleneck_pressure"], True, bool(alternatives_used)
            )
            overtime_candidate.update(
                {
                    "commitment_type": "Overtime",
                    "committed_date": overtime_finish.strftime(DATE_FMT),
                    "confidence_score": overtime_confidence,
                    "risk_level": overtime_risk,
                    "cost_impact": round(required_production_qty * 8, 2),
                    "summary": "启用加班产能后，可压缩瓶颈工作中心等待时间。",
                }
            )
            if event_payload.get("bottleneck_wc_id"):
                overtime_candidate["committed_date"] = (overtime_finish + timedelta(days=1)).strftime(DATE_FMT)
                overtime_candidate["summary"] = "启用加班后可部分缓解瓶颈，但仍需额外协调关键工作中心。"

        alternative_candidate = dict(standard_candidate)
        if alt_routing:
            alt_finish, alt_detail = _estimate_routing_finish(
                self.conn, alt_routing, required_production_qty, material_ready_date, False, [], []
            )
            alt_confidence, alt_risk = _score_confidence(
                order, shortages, supplier_risks, alt_detail["bottleneck_pressure"], False, True
            )
            alternative_candidate.update(
                {
                    "commitment_type": "AlternativeRouting",
                    "committed_date": alt_finish.strftime(DATE_FMT),
                    "confidence_score": alt_confidence,
                    "risk_level": alt_risk,
                    "cost_impact": round(required_production_qty * 5, 2),
                    "summary": "切换替代工艺路线，可绕开主瓶颈工作中心。",
                }
            )
        elif alternatives_used:
            alternative_candidate.update(
                {
                    "commitment_type": "AlternativeMaterial",
                    "committed_date": standard_date.strftime(DATE_FMT),
                    "confidence_score": max(standard_confidence - 3, 60),
                    "risk_level": standard_risk,
                    "cost_impact": round(required_production_qty * 2, 2),
                    "summary": "使用替代料补足缺口，维持当前完工节奏。",
                }
            )
        else:
            alternative_candidate["summary"] = "当前无可用替代路线或替代料。"

        candidates = [standard_candidate, overtime_candidate, alternative_candidate]
        recommended = min(candidates, key=lambda item: (item["committed_date"], -item["confidence_score"], item["cost_impact"]))
        log(
            "S9",
            "生成候选 ATP 方案并比较",
            [
                f"标准方案：{standard_candidate['committed_date']}，置信度 {standard_candidate['confidence_score']}，成本 {standard_candidate['cost_impact']}。",
                f"加班方案：{overtime_candidate['committed_date']}，置信度 {overtime_candidate['confidence_score']}，成本 {overtime_candidate['cost_impact']}。",
                f"替代方案：{alternative_candidate['committed_date']}，置信度 {alternative_candidate['confidence_score']}，成本 {alternative_candidate['cost_impact']}。",
                f"当前推荐方案为 {recommended['commitment_type']}。",
            ],
            rule_ids=["AUTO-01", "ALT-01"],
            objects=[order["order_id"]],
        )

        if recommended["commitment_type"] == "Overtime":
            reason_chain.append("若允许加班，可进一步压缩等待时间，但会增加额外成本。")
        if recommended["commitment_type"] in {"AlternativeRouting", "AlternativeMaterial"}:
            reason_chain.append("替代方案可以绕开当前主要约束，但会引入切换成本或认证风险。")
        if requested_date < _parse_date(recommended["committed_date"]):
            reason_chain.append(f"客户要求交期 {requested_date.strftime(DATE_FMT)} 早于系统可承诺日期，需要主动沟通交期差异。")

        narrative = (
            f"建议采用 {recommended['commitment_type']} 方案，当前可承诺日期为 {recommended['committed_date']}，"
            f"置信度 {recommended['confidence_score']}，风险等级 {recommended['risk_level']}。"
        )
        log(
            "S10",
            "生成最终承诺结论",
            [
                f"最终承诺日期 {recommended['committed_date']}。",
                f"承诺类型 {recommended['commitment_type']}，风险等级 {recommended['risk_level']}，置信度 {recommended['confidence_score']}。",
                "系统已汇总原因链、影响对象与备选方案，交由 LLM 输出业务化解释。",
            ],
            rule_ids=["ATPCommitment", "LEARN-01"],
            objects=[order["order_id"], order["item_id"]],
        )

        atp_summary = {
            "order": order,
            "event_type": event_type or "manual_analysis",
            "requested_date": order["requested_date"],
            "target_quantity": target_quantity,
            "available_finished_qty": round(available_finished, 2),
            "required_production_qty": round(required_production_qty, 2),
            "material_ready_date": material_ready_date.strftime(DATE_FMT),
            "shortages": shortages,
            "supplier_risks": supplier_risks,
            "alternatives_used": alternatives_used,
            "standard_detail": standard_detail,
            "recommended": {
                **recommended,
                "reason_chain": reason_chain,
                "impact_objects": impact_objects,
                "narrative": narrative,
            },
            "alternatives": candidates,
        }

        return {
            "scenario": scenario,
            "user_message": user_message,
            "atp_summary": atp_summary,
            "reasoning_trace": trace,
            "suggested_questions": [
                "如果允许加班，最早能提前到哪一天？",
                "如果启用替代料，风险会怎么变化？",
                "哪些对象是这次承诺变化的主要影响因素？",
            ],
        }
