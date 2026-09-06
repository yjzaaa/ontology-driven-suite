from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import DATABASE_PATH
from db.database import connection_scope
from db.schema import initialize_database


def seed() -> None:
    initialize_database(DATABASE_PATH)
    with connection_scope(DATABASE_PATH) as conn:
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("CUST_VIP_01", "华东终端集团", "VIP", 2, 0.08, 0.97, "High"),
                ("CUST_KEY_01", "华南渠道客户", "Key", 3, 0.05, 0.92, "Medium"),
                ("CUST_STD_01", "北方标准客户", "Standard", 5, 0.03, 0.9, "Low"),
                ("CUST_STD_02", "海外OEM客户", "Standard", 4, 0.04, 0.88, "Medium"),
            ],
        )
        conn.executemany(
            "INSERT INTO finished_items VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("FG_A100", "智能网关A100", "MTO", 20, 50, "Multiples", "A"),
                ("FG_B200", "控制器B200", "MTS", 30, 40, "Fixed", "B"),
                ("FG_C300", "边缘终端C300", "ATO", 10, 20, "Multiples", "A"),
                ("FG_D400", "工业采集器D400", "MTO", 15, 30, "Multiples", "B"),
            ],
        )
        conn.executemany(
            "INSERT INTO customer_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("SO1001", "CUST_VIP_01", "FG_A100", 180, "2026-04-10", "2026-04-10", 1, "Rush", "Confirmed", "2026-04-01 09:00:00"),
                ("SO1002", "CUST_KEY_01", "FG_A100", 200, "2026-04-12", "2026-04-12", 2, "Standard", "Confirmed", "2026-04-01 09:10:00"),
                ("SO1003", "CUST_STD_01", "FG_B200", 120, "2026-04-08", "2026-04-08", 3, "Standard", "InProgress", "2026-03-31 11:00:00"),
                ("SO1004", "CUST_STD_02", "FG_C300", 90, "2026-04-14", "2026-04-14", 4, "Frame", "Confirmed", "2026-04-01 14:00:00"),
            ],
        )
        conn.executemany(
            "INSERT INTO work_centers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("WC_SMT_01", "SMT-01贴片线", "Machine", "PLANT1", 16, 0.9, 4, 1, 0.85),
                ("WC_ASM_01", "组装线-01", "Mixed", "PLANT1", 18, 0.95, 3, 0, 0.88),
                ("WC_TEST_01", "测试线-01", "Machine", "PLANT1", 14, 0.92, 2, 0, 0.85),
                ("WC_PACK_01", "包装线-01", "Labor", "PLANT1", 20, 0.97, 2, 0, 0.9),
                ("WC_MANUAL_01", "手工替代线", "Labor", "PLANT1", 12, 0.82, 3, 0, 0.8),
            ],
        )
        work_dates = [
            "2026-04-02", "2026-04-03", "2026-04-04", "2026-04-05",
            "2026-04-06", "2026-04-07", "2026-04-08", "2026-04-09",
            "2026-04-10", "2026-04-11", "2026-04-12", "2026-04-13",
            "2026-04-14", "2026-04-15",
        ]
        calendar_rows = []
        for wc_id in ["WC_SMT_01", "WC_ASM_01", "WC_TEST_01", "WC_PACK_01", "WC_MANUAL_01"]:
            for idx, work_date in enumerate(work_dates, start=1):
                maintenance = 2 if wc_id == "WC_SMT_01" and work_date in {"2026-04-05", "2026-04-06"} else 0
                available = 16 if wc_id != "WC_PACK_01" else 18
                overtime = 4 if wc_id in {"WC_SMT_01", "WC_MANUAL_01"} else 2
                calendar_rows.append((f"{wc_id}_{idx}", wc_id, work_date, available, maintenance, overtime))
        conn.executemany("INSERT INTO work_center_calendar VALUES (?, ?, ?, ?, ?, ?)", calendar_rows)
        conn.executemany(
            "INSERT INTO production_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("WO1001", "SO1001", "FG_A100", 180, 40, "2026-04-02 08:00:00", "2026-04-09 18:00:00", "2026-04-02 08:00:00", None, "2026-04-10 18:00:00", 1, "InProgress", 0.32),
                ("WO1002", "SO1002", "FG_A100", 200, 0, "2026-04-03 08:00:00", "2026-04-11 18:00:00", None, None, "2026-04-12 18:00:00", 2, "Planned", 0.46),
                ("WO1003", "SO1003", "FG_B200", 120, 80, "2026-04-01 08:00:00", "2026-04-07 18:00:00", "2026-04-01 08:00:00", None, "2026-04-08 12:00:00", 3, "InProgress", 0.18),
                ("WO1004", "SO1004", "FG_C300", 90, 0, "2026-04-04 08:00:00", "2026-04-13 18:00:00", None, None, "2026-04-14 18:00:00", 4, "Planned", 0.29),
            ],
        )
        conn.executemany(
            "INSERT INTO operations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("OP1001", "WO1001", 10, "SMT贴片", "WC_SMT_01", 2.0, 0.035, 1.5, 0.5, 55, 0, 0),
                ("OP1002", "WO1001", 20, "总装", "WC_ASM_01", 1.0, 0.025, 1.0, 0.5, 30, 0, 0),
                ("OP1003", "WO1001", 30, "测试", "WC_TEST_01", 0.5, 0.02, 1.0, 0.2, 0, 0, 0),
                ("OP1004", "WO1001", 40, "包装", "WC_PACK_01", 0.3, 0.012, 0.5, 0.2, 0, 0, 0),
                ("OP2001", "WO1002", 10, "SMT贴片", "WC_SMT_01", 2.0, 0.035, 1.5, 0.5, 0, 0, 0),
                ("OP2002", "WO1002", 20, "总装", "WC_ASM_01", 1.0, 0.025, 1.0, 0.5, 0, 0, 0),
                ("OP2003", "WO1002", 30, "测试", "WC_TEST_01", 0.5, 0.02, 1.0, 0.2, 0, 0, 0),
                ("OP2004", "WO1002", 40, "包装", "WC_PACK_01", 0.3, 0.012, 0.5, 0.2, 0, 0, 0),
                ("OP3001", "WO1003", 10, "总装", "WC_ASM_01", 1.0, 0.02, 0.8, 0.2, 70, 0, 0),
                ("OP3002", "WO1003", 20, "测试", "WC_TEST_01", 0.5, 0.015, 0.6, 0.2, 40, 0, 0),
                ("OP4001", "WO1004", 10, "预装", "WC_MANUAL_01", 1.5, 0.03, 0.8, 0.3, 0, 0, 0),
                ("OP4002", "WO1004", 20, "测试", "WC_TEST_01", 0.5, 0.02, 0.8, 0.2, 0, 0, 1),
            ],
        )
        conn.executemany(
            "INSERT INTO operation_dependencies VALUES (?, ?, ?, ?)",
            [
                ("DEP1001", "OP1002", "OP1001", 1),
                ("DEP1002", "OP1003", "OP1002", 1),
                ("DEP1003", "OP1004", "OP1003", 1),
                ("DEP2001", "OP2002", "OP2001", 1),
                ("DEP2002", "OP2003", "OP2002", 1),
                ("DEP2003", "OP2004", "OP2003", 1),
                ("DEP3001", "OP3002", "OP3001", 1),
                ("DEP4001", "OP4002", "OP4001", 1),
            ],
        )
        conn.executemany(
            "INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("INV001", "FG_A100", "PLANT1", "FG", 40, 0, 20, 20, 20, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV002", "FG_B200", "PLANT1", "FG", 150, 0, 30, 120, 30, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV003", "FG_C300", "PLANT1", "FG", 30, 0, 10, 20, 15, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV004", "COMP_CHIP_X1", "PLANT1", "RM", 180, 100, 220, 60, 50, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV005", "COMP_BOARD_A", "PLANT1", "RM", 500, 0, 180, 320, 100, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV006", "COMP_CASE_A", "PLANT1", "RM", 380, 0, 120, 260, 80, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV007", "COMP_CHIP_X1_ALT", "PLANT1", "RM", 200, 0, 20, 180, 50, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV008", "COMP_TESTKIT", "PLANT1", "RM", 260, 0, 40, 220, 50, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
                ("INV009", "COMP_PANEL_C", "PLANT1", "RM", 110, 0, 30, 80, 40, "2026-04-02 08:00:00", "SAP_SNAPSHOT"),
            ],
        )
        conn.executemany(
            "INSERT INTO inventory_inbound VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("INB001", "COMP_CHIP_X1", "PO", "PO9001", "2026-04-07", 100, "Delayed"),
                ("INB002", "COMP_PANEL_C", "PO", "PO9002", "2026-04-05", 100, "Planned"),
            ],
        )
        conn.executemany(
            "INSERT INTO bom_headers VALUES (?, ?, ?, ?, ?)",
            [("BOM_A100", "V1", "FG_A100", "2026-01-01", None), ("BOM_B200", "V1", "FG_B200", "2026-01-01", None), ("BOM_C300", "V1", "FG_C300", "2026-01-01", None)],
        )
        conn.executemany(
            "INSERT INTO bom_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("BOMI_A100_1", "BOM_A100", "COMP_CHIP_X1", 1, 1, 1.02, 0, "Buy"),
                ("BOMI_A100_2", "BOM_A100", "COMP_BOARD_A", 1, 1, 1.01, 0, "Buy"),
                ("BOMI_A100_3", "BOM_A100", "COMP_CASE_A", 1, 1, 1.00, 0, "Buy"),
                ("BOMI_A100_4", "BOM_A100", "COMP_TESTKIT", 1, 1, 1.00, 0, "Buy"),
                ("BOMI_B200_1", "BOM_B200", "COMP_BOARD_A", 1, 1, 1.00, 0, "Buy"),
                ("BOMI_B200_2", "BOM_B200", "COMP_CASE_A", 1, 1, 1.00, 0, "Buy"),
                ("BOMI_C300_1", "BOM_C300", "COMP_PANEL_C", 1, 1, 1.05, 0, "Buy"),
                ("BOMI_C300_2", "BOM_C300", "COMP_CASE_A", 1, 1, 1.00, 0, "Buy"),
            ],
        )
        conn.executemany(
            "INSERT INTO bom_alternatives VALUES (?, ?, ?, ?, ?, ?)",
            [("ALT_A100_1", "BOMI_A100_1", "COMP_CHIP_X1_ALT", 1, 1, "Approved")],
        )
        conn.executemany(
            "INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("SUP001", "芯片核心供应商", "Tier1", 7, 3, 0.28, 100, 1000, 0.79, 0.95, 2.5, "Medium", 1),
                ("SUP002", "PCB板供应商", "Tier1", 5, 2, 0.12, 100, 3000, 0.94, 0.98, 0.6, "Low", 0),
                ("SUP003", "结构件供应商", "Approved", 4, 2, 0.09, 100, 2500, 0.96, 0.99, 0.3, "Low", 0),
                ("SUP004", "替代芯片供应商", "Backup", 6, 3, 0.18, 80, 900, 0.9, 0.94, 1.2, "Low", 0),
                ("SUP005", "面板供应商", "Tier2", 5, 3, 0.15, 100, 1200, 0.88, 0.97, 1.0, "Medium", 0),
            ],
        )
        conn.executemany(
            "INSERT INTO item_suppliers VALUES (?, ?, ?, ?)",
            [
                ("IS001", "COMP_CHIP_X1", "SUP001", 1),
                ("IS002", "COMP_BOARD_A", "SUP002", 1),
                ("IS003", "COMP_CASE_A", "SUP003", 1),
                ("IS004", "COMP_CHIP_X1_ALT", "SUP004", 1),
                ("IS005", "COMP_PANEL_C", "SUP005", 1),
                ("IS006", "COMP_TESTKIT", "SUP002", 0),
            ],
        )
        conn.executemany(
            "INSERT INTO routings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("RT_A100_STD", "FG_A100", "V1", "Standard", 5.5, "WC_SMT_01", 50, 500),
                ("RT_A100_ALT", "FG_A100", "V1", "Alternative", 6.2, "WC_MANUAL_01", 50, 300),
                ("RT_B200_STD", "FG_B200", "V1", "Standard", 3.5, "WC_ASM_01", 40, 300),
                ("RT_C300_STD", "FG_C300", "V1", "Standard", 4.5, "WC_TEST_01", 20, 200),
            ],
        )
        conn.executemany(
            "INSERT INTO routing_operations VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("RTO_A100_10", "RT_A100_STD", 10, "WC_SMT_01", 2.0, 0.035),
                ("RTO_A100_20", "RT_A100_STD", 20, "WC_ASM_01", 1.0, 0.025),
                ("RTO_A100_30", "RT_A100_STD", 30, "WC_TEST_01", 0.5, 0.02),
                ("RTO_A100_40", "RT_A100_STD", 40, "WC_PACK_01", 0.3, 0.012),
                ("RTO_A100_ALT_10", "RT_A100_ALT", 10, "WC_MANUAL_01", 2.5, 0.05),
                ("RTO_A100_ALT_20", "RT_A100_ALT", 20, "WC_ASM_01", 1.0, 0.028),
                ("RTO_A100_ALT_30", "RT_A100_ALT", 30, "WC_TEST_01", 0.5, 0.02),
                ("RTO_A100_ALT_40", "RT_A100_ALT", 40, "WC_PACK_01", 0.3, 0.012),
                ("RTO_B200_10", "RT_B200_STD", 10, "WC_ASM_01", 1.0, 0.02),
                ("RTO_B200_20", "RT_B200_STD", 20, "WC_TEST_01", 0.5, 0.015),
                ("RTO_C300_10", "RT_C300_STD", 10, "WC_MANUAL_01", 1.5, 0.03),
                ("RTO_C300_20", "RT_C300_STD", 20, "WC_TEST_01", 0.5, 0.02),
            ],
        )
        conn.executemany(
            "INSERT INTO routing_alternatives VALUES (?, ?, ?, ?)",
            [("RA001", "RT_A100_STD", "RT_A100_ALT", "SMT瓶颈负荷高于95%时启用")],
        )
        conn.executemany(
            "INSERT INTO atp_commitments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("ATP001", "SO1001", 1, "2026-04-10", "Standard", 91, "Low", json.dumps(["历史承诺样本"], ensure_ascii=False), 0, "AI_AUTO", "2026-04-01 10:00:00", None, None),
                ("ATP002", "SO1002", 1, "2026-04-12", "Standard", 84, "Medium", json.dumps(["历史承诺样本"], ensure_ascii=False), 0, "AI_AUTO", "2026-04-01 10:20:00", None, None),
            ],
        )
        conn.executemany(
            "INSERT INTO demo_scenarios VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("SC001", "urgent_insert_order", "客户加急插单", "urgent_insert_order", "VIP客户华东终端临时插单300台，最早什么时候能交？", "SO1001", json.dumps({"insert_quantity": 300}, ensure_ascii=False), 1),
                ("SC002", "demand_increase", "客户需求数量上调", "demand_increase", "订单SO1002数量从200提高到350，交期还能维持不变吗？", "SO1002", json.dumps({"new_quantity": 350}, ensure_ascii=False), 1),
                ("SC003", "material_delay", "关键物料缺料/在途延迟", "material_delay", "核心芯片来料延迟3天，这张订单还能按原承诺交付吗？", "SO1002", json.dumps({"delay_item_id": "COMP_CHIP_X1", "delay_days": 3, "new_quantity": 200}, ensure_ascii=False), 1),
                ("SC004", "capacity_bottleneck", "瓶颈工作中心产能不足", "capacity_bottleneck", "SMT-01本周产能爆满，这张单还能承诺4月12日吗？", "SO1002", json.dumps({"bottleneck_wc_id": "WC_SMT_01", "new_quantity": 200}, ensure_ascii=False), 1),
            ],
        )
        conn.executemany(
            "INSERT INTO scenario_conversation_notes VALUES (?, ?, ?, ?)",
            [
                ("NOTE001", "urgent_insert_order", "assistant_hint", "优先关注VIP客户罚款风险与瓶颈产能抢占。"),
                ("NOTE002", "demand_increase", "assistant_hint", "重点判断数量上调后的物料缺口和交期滑移。"),
                ("NOTE003", "material_delay", "assistant_hint", "重点检查芯片在途到货和替代料。"),
                ("NOTE004", "capacity_bottleneck", "assistant_hint", "重点比较标准路线、加班方案和替代路线。"),
            ],
        )


if __name__ == "__main__":
    seed()
    print(f"Seeded demo database at {Path(DATABASE_PATH).resolve()}")
