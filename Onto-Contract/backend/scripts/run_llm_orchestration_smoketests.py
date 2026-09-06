from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.ai.deepseek_client import DeepSeekClient
from scripts.run_semantic_query_smoketests import seed_semantic_test_data


def fake_chat_completion(self, messages, tools=None):
    user_messages = [item["content"] for item in messages if item["role"] == "user"]
    user_message = user_messages[-1] if user_messages else ""
    tool_messages = [item for item in messages if item["role"] == "tool"]
    conversation_text = "\n".join(str(item.get("content", "")) for item in messages)

    if not tool_messages:
        if "它的销售部门和合同总金额是什么" in user_message and "HT2026041002" in conversation_text:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool-6",
                        "type": "function",
                        "function": {
                            "name": "semantic_query",
                            "arguments": json.dumps(
                                {
                                    "subject": "contract",
                                    "intent": "detail",
                                    "fields": ["contractNo", "totalAmount", "deptName"],
                                    "filters": {"contractNo": "HT2026041002"},
                                    "responsePreference": "text",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

        if "为什么" in user_message and "HT2026041003" in user_message:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool-5",
                        "type": "function",
                        "function": {
                            "name": "domain_explanation_query",
                            "arguments": json.dumps(
                                {
                                    "question": user_message,
                                    "focus": "status",
                                    "contractNo": "HT2026041003",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

        if "流程" in user_message:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool-4",
                        "type": "function",
                        "function": {
                            "name": "domain_explanation_query",
                            "arguments": json.dumps(
                                {
                                    "question": user_message,
                                    "focus": "process",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

        if "HT2026041002" in user_message:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool-2",
                        "type": "function",
                        "function": {
                            "name": "semantic_query",
                            "arguments": json.dumps(
                                {
                                    "subject": "contract",
                                    "intent": "detail",
                                    "fields": ["contractNo", "totalAmount", "deptName"],
                                    "filters": {"contractNo": "HT2026041002"},
                                    "responsePreference": "text",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

        if "柱状图" in user_message:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool-3",
                        "type": "function",
                        "function": {
                            "name": "semantic_query",
                            "arguments": json.dumps(
                                {
                                    "subject": "contract",
                                    "intent": "aggregate",
                                    "groupBy": "department",
                                    "metrics": ["contract_total_amount"],
                                    "responsePreference": "chart",
                                    "chartType": "bar",
                                },
                                ensure_ascii=False,
                            ),
                        },
                    }
                ],
            }

        return {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "tool-1",
                    "type": "function",
                    "function": {
                        "name": "semantic_query",
                        "arguments": json.dumps(
                            {
                                "subject": "contract",
                                "intent": "aggregate",
                                "groupBy": "department",
                                "metrics": ["contract_total_amount", "invoiced_amount_total"],
                                "responsePreference": "table",
                            },
                            ensure_ascii=False,
                        ),
                    },
                }
            ],
        }

    tool_payload = json.loads(tool_messages[-1]["content"])
    if "为什么" in user_message and "HT2026041003" in user_message:
        return {
            "role": "assistant",
            "content": json.dumps(
                {
                    "message": tool_payload["answer"],
                    "render": None,
                    "action": None,
                },
                ensure_ascii=False,
            ),
        }

    if "流程" in user_message:
        return {
            "role": "assistant",
            "content": json.dumps(
                {
                    "message": tool_payload["answer"],
                    "render": None,
                    "action": None,
                },
                ensure_ascii=False,
            ),
        }

    if tool_payload["resultType"] == "single_record":
        record = tool_payload["record"]
        return {
            "role": "assistant",
            "content": json.dumps(
                {
                    "message": f"合同 {record['contractNo']} 的合同总金额是 {int(record['totalAmount'])}，销售部门是 {record['deptName']}。",
                    "render": None,
                    "action": None,
                },
                ensure_ascii=False,
            ),
        }

    if tool_payload["columns"][1]["label"] == "合同总金额" and len(tool_payload["columns"]) == 2:
        return {
            "role": "assistant",
            "content": json.dumps(
                {
                    "message": "已按部门生成合同总金额柱状图。",
                    "render": None,
                    "action": None,
                },
                ensure_ascii=False,
            ),
        }

    return {
        "role": "assistant",
        "content": json.dumps(
            {
                "message": "已按部门统计合同总金额和已开票金额。",
                "render": None,
                "action": None,
            },
            ensure_ascii=False,
        ),
    }


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = str(Path(temp_dir) / "llm-orchestrator-test.db")
        app = create_app(
            {
                "database": {"sqlite_path": db_path},
                "ai": {"api_key": "sk-test", "model": "deepseek-chat"},
            }
        )

        with app.app_context():
            seed_semantic_test_data()

        with patch.object(DeepSeekClient, "chat_completion", new=fake_chat_completion):
            with app.test_client() as client:
                login = client.post("/api/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
                assert login.status_code == 200 and login.json["success"] is True, "登录失败"

                aggregate_response = client.post(
                    "/api/ai/chat",
                    json={"message": "帮我按部门统计合同总金额，输出部门，合同总金额，已经开票金额三列信息。"},
                )
                assert aggregate_response.status_code == 200 and aggregate_response.json["success"] is True
                aggregate_data = aggregate_response.json["data"]
                assert aggregate_data["render"]["headers"] == ["部门", "合同总金额", "已开票金额"]
                assert aggregate_data["render"]["rows"][0] == ["销售一部", 1480000.0, 680000.0]
                assert aggregate_data["render"]["rows"][1] == ["销售二部", 860000.0, 860000.0]
                print("PASS LLM 1: 多指标按部门统计")

                detail_response = client.post(
                    "/api/ai/chat",
                    json={"message": "HT2026041002 的合同总金额和销售部门是什么？"},
                )
                assert detail_response.status_code == 200 and detail_response.json["success"] is True
                detail_data = detail_response.json["data"]
                assert detail_data["render"] is None
                assert "合同 HT2026041002" in detail_data["message"]
                assert "合同总金额是 500000" in detail_data["message"]
                assert "销售二部" in detail_data["message"]
                print("PASS LLM 2: 单合同字段改为自然语言")

                chart_response = client.post(
                    "/api/ai/chat",
                    json={"message": "请用柱状图按部门统计合同总金额"},
                )
                assert chart_response.status_code == 200 and chart_response.json["success"] is True
                chart_data = chart_response.json["data"]
                assert chart_data["render"]["type"] == "chart"
                assert chart_data["render"]["option"]["series"][0]["type"] == "bar"
                print("PASS LLM 3: 图表意图输出 ECharts")

                knowledge_response = client.post(
                    "/api/ai/chat",
                    json={"message": "当前系统里面的合同创建流程是如何的？"},
                )
                assert knowledge_response.status_code == 200 and knowledge_response.json["success"] is True
                knowledge_data = knowledge_response.json["data"]
                assert knowledge_data["render"] is None
                assert "Contract_Create" in knowledge_data["message"]
                assert "Contract.Created" in knowledge_data["message"]
                print("PASS LLM 4: 本体流程问题走知识查询")

                status_reason_response = client.post(
                    "/api/ai/chat",
                    json={"message": "为什么 HT2026041003 既没有开票，也没有收款？"},
                )
                assert status_reason_response.status_code == 200 and status_reason_response.json["success"] is True
                status_reason_data = status_reason_response.json["data"]
                assert status_reason_data["render"] is None
                assert "HT2026041003" in status_reason_data["message"]
                assert "没有任何发票记录" in status_reason_data["message"] or "未开票、未收款" in status_reason_data["message"]
                print("PASS LLM 5: 合同状态原因解释")

                context_first_response = client.post(
                    "/api/ai/chat",
                    json={"sessionId": "llm-ctx-1", "message": "查看合同 HT2026041002 详情"},
                )
                assert context_first_response.status_code == 200 and context_first_response.json["success"] is True
                context_second_response = client.post(
                    "/api/ai/chat",
                    json={"sessionId": "llm-ctx-1", "message": "它的销售部门和合同总金额是什么？"},
                )
                assert context_second_response.status_code == 200 and context_second_response.json["success"] is True
                context_second_data = context_second_response.json["data"]
                assert context_second_data["render"] is None
                assert "HT2026041002" in context_second_data["message"]
                assert "合同总金额是 500000" in context_second_data["message"]
                assert "销售二部" in context_second_data["message"]
                print("PASS LLM 6: 多轮上下文追问字段")

        print("ALL_LLM_ORCHESTRATION_SMOKETESTS_PASSED")


if __name__ == "__main__":
    main()
