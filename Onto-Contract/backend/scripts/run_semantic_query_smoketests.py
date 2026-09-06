from __future__ import annotations

import sys
import tempfile
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.db import get_db


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = str(Path(temp_dir) / "semantic-test.db")
        app = create_app(
            {
                "database": {"sqlite_path": db_path},
                "ai": {"api_key": "YOUR_DEEPSEEK_API_KEY"},
            }
        )

        with app.app_context():
            seed_semantic_test_data()

        with app.test_client() as client:
            login = client.post("/api/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
            assert login.status_code == 200 and login.json["success"] is True, "登录失败"

            cases = [
                {
                    "query": "查询合同",
                    "expects": [
                        lambda data: data["render"]["type"] == "table",
                        lambda data: "合同编号" in data["render"]["headers"],
                        lambda data: len(data["render"]["rows"]) >= 5,
                    ],
                },
                {
                    "query": "帮我按部门统计销售合同总金额，输出部门，合同总金额两列信息。",
                    "expects": [
                        lambda data: data["render"]["headers"] == ["部门", "合同总金额"],
                        lambda data: len(data["render"]["rows"]) == 2,
                        lambda data: any(row[0] == "销售一部" and row[1] == 1480000.0 for row in data["render"]["rows"]),
                        lambda data: any(row[0] == "销售二部" and row[1] == 860000.0 for row in data["render"]["rows"]),
                    ],
                },
                {
                    "query": "查询收款记录",
                    "expects": [
                        lambda data: "收款金额" in data["render"]["headers"],
                        lambda data: len(data["render"]["rows"]) == 3,
                    ],
                },
                {
                    "query": "查询销售一部的收款",
                    "expects": [
                        lambda data: len(data["render"]["rows"]) == 2,
                        lambda data: all(row[3] == "销售一部" for row in data["render"]["rows"]),
                    ],
                },
                {
                    "query": "查询已经开票还未收款的发票",
                    "expects": [
                        lambda data: len(data["render"]["rows"]) == 2,
                        lambda data: all(row[-1] == "未收款" for row in data["render"]["rows"]),
                    ],
                },
                {
                    "query": "查询已经开票还未收款的合同",
                    "expects": [
                        lambda data: len(data["render"]["rows"]) == 2,
                        lambda data: all(row[-1] != "已收款" for row in data["render"]["rows"]),
                    ],
                },
                {
                    "query": "查询未开票合同",
                    "expects": [
                        lambda data: len(data["render"]["rows"]) == 1,
                        lambda data: data["render"]["rows"][0][0] == "HT2026041003",
                    ],
                },
                {
                    "query": "当前哪些合同既没有开票，也没有收款。给出合同编号，合同名称，客户名称和销售部门信息。",
                    "expects": [
                        lambda data: data["render"]["headers"] == ["合同编号", "合同名称", "客户", "部门"],
                        lambda data: len(data["render"]["rows"]) == 1,
                        lambda data: data["render"]["rows"][0] == [
                            "HT2026041003",
                            "远景数字科技运维支持项目",
                            "远景数字科技",
                            "销售一部",
                        ],
                    ],
                },
                {
                    "query": "查询华东能源集团已开票未收款合同",
                    "expects": [
                        lambda data: len(data["render"]["rows"]) == 1,
                        lambda data: data["render"]["rows"][0][2] == "华东能源集团",
                        lambda data: data["render"]["rows"][0][0] == "HT2026041001",
                    ],
                },
                {
                    "query": "统计华东能源集团收款总金额",
                    "expects": [
                        lambda data: data["render"]["rows"] == [["华东能源集团", 840000.0]],
                    ],
                },
                {
                    "query": "查看合同 HT2026041002 详情",
                    "expects": [
                        lambda data: data["render"]["rows"][0][0] == "HT2026041002",
                        lambda data: data["render"]["rows"][0][2] == "星河制造有限公司",
                    ],
                },
                {
                    "query": "查询某部门的收款",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "请补充具体部门名称" in data["message"],
                    ],
                },
                {
                    "query": "请删除 HT2026041002",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "只读查询和页面导航" in data["message"],
                    ],
                },
                {
                    "query": "当前系统里面的合同创建流程是如何的？",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "合同录入" in data["message"] or "Contract_Create" in data["message"],
                        lambda data: "Contract.Created" in data["message"] or "合同已创建" in data["message"],
                    ],
                },
                {
                    "query": "为什么 HT2026041003 既没有开票，也没有收款？",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "HT2026041003" in data["message"],
                        lambda data: "没有任何发票记录" in data["message"] or "未开票、未收款" in data["message"],
                    ],
                },
                {
                    "query": "合同创建有哪些关键规则？",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "付款比例" in data["message"] or "规则" in data["message"],
                        lambda data: "Contract_Create" in data["message"] or "合同录入" in data["message"],
                    ],
                },
                {
                    "query": "开票和收款的事件链路是什么？",
                    "expects": [
                        lambda data: data["render"] is None,
                        lambda data: "Invoice.Created" in data["message"] or "合同已开票" in data["message"],
                        lambda data: "Payment.Received" in data["message"] or "款项已收到" in data["message"],
                    ],
                },
                {
                    "query": "请用柱状图按部门统计合同总金额",
                    "expects": [
                        lambda data: data["render"]["type"] == "chart",
                        lambda data: data["render"]["option"]["series"][0]["type"] == "bar",
                    ],
                },
            ]

            for index, case in enumerate(cases, start=1):
                response = client.post("/api/ai/chat", json={"message": case["query"]})
                assert response.status_code == 200 and response.json["success"] is True, f"案例 {index} 接口失败"
                data = response.json["data"]
                for predicate in case["expects"]:
                    assert predicate(data), f"案例 {index} 断言失败：{case['query']} -> {data}"
                print(f"PASS {index}: {case['query']}")

            stream_response = client.post(
                "/api/ai/chat/stream",
                json={"message": "帮我按部门统计销售合同总金额，输出部门，合同总金额两列信息。"},
                buffered=True,
            )
            body = b"".join(stream_response.response).decode("utf-8", errors="replace")
            assert stream_response.status_code == 200, "SSE 接口失败"
            assert "event: assistant" in body, "SSE 未返回 assistant 事件"
            assert "部门" in body and "合同总金额" in body, "SSE 未返回预期表格字段"
            print("PASS SSE: 按部门统计销售合同总金额")

            context_session_id = "ctx-contract-follow-up"
            first_response = client.post(
                "/api/ai/chat",
                json={"sessionId": context_session_id, "message": "查看合同 HT2026041002 详情"},
            )
            assert first_response.status_code == 200 and first_response.json["success"] is True
            second_response = client.post(
                "/api/ai/chat",
                json={"sessionId": context_session_id, "message": "它的销售部门和合同总金额是什么？"},
            )
            assert second_response.status_code == 200 and second_response.json["success"] is True
            second_data = second_response.json["data"]
            assert second_data["render"] is None, "多轮上下文应返回自然语言"
            assert "HT2026041002" in second_data["message"], "多轮上下文未延续合同编号"
            assert "销售二部" in second_data["message"], "多轮上下文未解析销售部门"
            assert "500000" in second_data["message"], "多轮上下文未解析合同总金额"
            print("PASS CTX 1: 合同详情追问字段")

            reason_session_id = "ctx-status-follow-up"
            first_reason_response = client.post(
                "/api/ai/chat",
                json={"sessionId": reason_session_id, "message": "查看合同 HT2026041003 详情"},
            )
            assert first_reason_response.status_code == 200 and first_reason_response.json["success"] is True
            second_reason_response = client.post(
                "/api/ai/chat",
                json={"sessionId": reason_session_id, "message": "为什么它既没有开票，也没有收款？"},
            )
            assert second_reason_response.status_code == 200 and second_reason_response.json["success"] is True
            second_reason_data = second_reason_response.json["data"]
            assert second_reason_data["render"] is None, "状态追问应返回解释文本"
            assert "HT2026041003" in second_reason_data["message"], "状态追问未延续合同编号"
            assert "没有任何发票记录" in second_reason_data["message"] or "未开票、未收款" in second_reason_data["message"], "状态追问未解释原因"
            print("PASS CTX 2: 状态原因追问")

        print("ALL_SEMANTIC_SMOKETESTS_PASSED")


def seed_semantic_test_data():
    db = get_db()

    dept_map = {row["dept_no"]: row["id"] for row in db.execute("SELECT id, dept_no FROM departments").fetchall()}
    employee_map = {
        row["employee_no"]: row["id"] for row in db.execute("SELECT id, employee_no FROM employees").fetchall()
    }
    product_map = {row["product_no"]: row["id"] for row in db.execute("SELECT id, product_no FROM products").fetchall()}
    customer_map = {
        row["customer_no"]: row["id"] for row in db.execute("SELECT id, customer_no FROM customers").fetchall()
    }

    contract_specs = [
        {
            "contract_no": "HT2026041001",
            "contract_name": "华东能源集团智能合同二期",
            "status": "生效",
            "product_id": product_map["P001"],
            "customer_id": customer_map["C001"],
            "dept_id": dept_map["D001"],
            "owner_id": employee_map["E001"],
            "sign_date": "2026-04-01",
            "total_amount": 800000,
            "purchase_amount": 260000,
            "tax_rate": 0.13,
            "invoiced_amount_total": 500000,
            "received_amount_total": 300000,
            "invoice_status": "部分开票",
            "receipt_status": "部分收款",
        },
        {
            "contract_no": "HT2026041002",
            "contract_name": "星河制造一体化交付项目",
            "status": "生效",
            "product_id": product_map["P002"],
            "customer_id": customer_map["C002"],
            "dept_id": dept_map["D002"],
            "owner_id": employee_map["E002"],
            "sign_date": "2026-04-02",
            "total_amount": 500000,
            "purchase_amount": 180000,
            "tax_rate": 0.13,
            "invoiced_amount_total": 500000,
            "received_amount_total": 0,
            "invoice_status": "已开票",
            "receipt_status": "未收款",
        },
        {
            "contract_no": "HT2026041003",
            "contract_name": "远景数字科技运维支持项目",
            "status": "生效",
            "product_id": product_map["P003"],
            "customer_id": customer_map["C003"],
            "dept_id": dept_map["D001"],
            "owner_id": employee_map["E001"],
            "sign_date": "2026-04-03",
            "total_amount": 200000,
            "purchase_amount": 60000,
            "tax_rate": 0.06,
            "invoiced_amount_total": 0,
            "received_amount_total": 0,
            "invoice_status": "未开票",
            "receipt_status": "未收款",
        },
        {
            "contract_no": "HT2026041004",
            "contract_name": "华东能源集团集成交付项目",
            "status": "生效",
            "product_id": product_map["P002"],
            "customer_id": customer_map["C001"],
            "dept_id": dept_map["D002"],
            "owner_id": employee_map["E002"],
            "sign_date": "2026-04-04",
            "total_amount": 360000,
            "purchase_amount": 120000,
            "tax_rate": 0.13,
            "invoiced_amount_total": 360000,
            "received_amount_total": 360000,
            "invoice_status": "已开票",
            "receipt_status": "已收款",
        },
    ]

    for spec in contract_specs:
        db.execute(
            """
            INSERT INTO contracts (
                contract_no, contract_name, status, product_id, customer_id, dept_id, owner_id,
                sign_date, total_amount, purchase_amount, tax_rate,
                invoiced_amount_total, received_amount_total, invoice_status, receipt_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec["contract_no"],
                spec["contract_name"],
                spec["status"],
                spec["product_id"],
                spec["customer_id"],
                spec["dept_id"],
                spec["owner_id"],
                spec["sign_date"],
                spec["total_amount"],
                spec["purchase_amount"],
                spec["tax_rate"],
                spec["invoiced_amount_total"],
                spec["received_amount_total"],
                spec["invoice_status"],
                spec["receipt_status"],
            ),
        )

    contract_id_map = {
        row["contract_no"]: row["id"] for row in db.execute("SELECT id, contract_no FROM contracts").fetchall()
    }

    payment_terms = [
        (contract_id_map["HT2026041001"], "S1", "预付款", 0.4),
        (contract_id_map["HT2026041001"], "S2", "验收款", 0.6),
        (contract_id_map["HT2026041002"], "S1", "首付款", 1.0),
        (contract_id_map["HT2026041003"], "S1", "尾款", 1.0),
        (contract_id_map["HT2026041004"], "S1", "项目款", 1.0),
    ]
    db.executemany(
        "INSERT INTO contract_payment_terms (contract_id, stage_no, stage_name, ratio) VALUES (?, ?, ?, ?)",
        payment_terms,
    )

    invoice_specs = [
        ("FP2026041001", contract_id_map["HT2026041001"], 300000, 0.13, "2026-04-01 10:00:00", "已收款", 1, "2026-04-05 16:00:00"),
        ("FP2026041002", contract_id_map["HT2026041001"], 200000, 0.13, "2026-04-08 11:00:00", "已开票", 0, None),
        ("FP2026041003", contract_id_map["HT2026041002"], 500000, 0.13, "2026-04-06 15:00:00", "已开票", 0, None),
        ("FP2026041004", contract_id_map["HT2026041004"], 360000, 0.13, "2026-04-07 09:30:00", "已收款", 1, "2026-04-09 12:00:00"),
    ]
    db.executemany(
        """
        INSERT INTO invoices (
            invoice_no, contract_id, amount, tax_rate, invoice_date, status, is_received, received_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        invoice_specs,
    )

    invoice_id_map = {row["invoice_no"]: row["id"] for row in db.execute("SELECT id, invoice_no FROM invoices").fetchall()}
    mappings = [
        (invoice_id_map["FP2026041001"], "S1", "预付款"),
        (invoice_id_map["FP2026041002"], "S2", "验收款"),
        (invoice_id_map["FP2026041003"], "S1", "首付款"),
        (invoice_id_map["FP2026041004"], "S1", "项目款"),
    ]
    db.executemany(
        "INSERT INTO invoice_term_mappings (invoice_id, stage_no, stage_name) VALUES (?, ?, ?)",
        mappings,
    )
    db.commit()


if __name__ == "__main__":
    main()
