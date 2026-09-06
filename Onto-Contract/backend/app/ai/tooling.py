from __future__ import annotations

import json

from ..services import contract_service
from ..services.domain_copilot_service import domain_explanation_query
from ..services.ontology_knowledge_service import query_ontology_knowledge
from ..services.semantic_query_service import execute_semantic_query
from ..services.sql_readonly_service import execute_readonly_sql


def build_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "open_page",
                "description": "打开系统中的固定业务页面，例如合同录入、开票录入、收款录入、合同查询。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pageId": {
                            "type": "string",
                            "enum": [
                                "ContractEntryPage",
                                "InvoiceEntryPage",
                                "PaymentReceivePage",
                                "ContractSearchPage",
                            ],
                        }
                    },
                    "required": ["pageId"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "domain_explanation_query",
                "description": "面向领域 Copilot 的解释型工具。用于解释业务流程、规则、事件链路、对象关系，以及结合真实合同/发票数据解释当前状态为什么会这样。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "focus": {
                            "type": ["string", "null"],
                            "enum": ["process", "rule", "event", "page", "object", "status", "general", None],
                        },
                        "contractNo": {"type": "string"},
                        "invoiceNo": {"type": "string"},
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "ontology_knowledge_query",
                "description": "基于合同管理本体模型、需求文档和技术架构文档检索业务流程、规则、事件、页面职责和建模语义，用于回答解释性问题。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "focus": {
                            "type": ["string", "null"],
                            "enum": ["aggregate", "behavior", "rule", "event", "use_case", "page", "document", None],
                        },
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "semantic_query",
                "description": "基于合同管理本体模型执行结构化语义查询。适用于合同、发票、收款、部门/客户/产品/销售人员统计、已开票未收款、未开票、详情等业务问题。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "enum": ["contract", "invoice", "receipt"],
                        },
                        "intent": {
                            "type": "string",
                            "enum": ["list", "aggregate", "detail", "count"],
                        },
                        "groupBy": {
                            "type": ["string", "null"],
                            "enum": ["department", "customer", "product", "owner", None],
                        },
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "contract_total_amount",
                                    "invoiced_amount_total",
                                    "received_amount_total",
                                    "invoice_amount",
                                    "received_amount",
                                    "count",
                                ],
                            },
                        },
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "contractNo",
                                    "contractName",
                                    "customerName",
                                    "productName",
                                    "productType",
                                    "deptName",
                                    "ownerName",
                                    "signDate",
                                    "totalAmount",
                                    "invoicedAmountTotal",
                                    "receivedAmountTotal",
                                    "invoiceStatus",
                                    "receiptStatus",
                                    "invoiceNo",
                                    "amount",
                                    "invoiceDate",
                                    "receivedDate",
                                    "receiptState",
                                ],
                            },
                        },
                        "responsePreference": {
                            "type": "string",
                            "enum": ["auto", "text", "table", "chart"],
                        },
                        "chartType": {
                            "type": "string",
                            "enum": ["auto", "bar", "line", "pie"],
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "contractNo": {"type": "string"},
                                "invoiceNo": {"type": "string"},
                                "departmentName": {"type": "string"},
                                "customerName": {"type": "string"},
                                "productName": {"type": "string"},
                                "ownerName": {"type": "string"},
                                "invoiceState": {"type": "string", "enum": ["invoiced", "not_invoiced"]},
                                "receiptState": {"type": "string", "enum": ["received", "unreceived"]},
                                "invoiceReceiptState": {"type": "string", "enum": ["open_unreceived"]},
                                "contractState": {"type": "string", "enum": ["not_invoiced_unreceived"]},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["subject", "intent"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_contracts",
                "description": "执行合同信息模糊查询。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contractNo": {"type": "string"},
                        "contractName": {"type": "string"},
                        "productType": {"type": "string"},
                        "deptId": {"type": "integer"},
                        "signDateStart": {"type": "string"},
                        "signDateEnd": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_contract_detail",
                "description": "获取合同详情，包含付款条款、开票和收款信息。",
                "parameters": {
                    "type": "object",
                    "properties": {"contractId": {"type": "integer"}},
                    "required": ["contractId"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_open_invoices",
                "description": "查询待收款发票记录。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contractNo": {"type": "string"},
                        "contractName": {"type": "string"},
                        "invoiceNo": {"type": "string"},
                        "customerName": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "readonly_sql_query",
                "description": "当现成 API 或语义工具不能覆盖问题时，执行严格只读的 SELECT SQL 查询。",
                "parameters": {
                    "type": "object",
                    "properties": {"sql": {"type": "string"}},
                    "required": ["sql"],
                },
            },
        },
    ]


def execute_tool(name: str, arguments: dict, actor: str | None = None):
    if name == "open_page":
        return {"pageId": arguments["pageId"], "title": arguments["pageId"]}
    if name == "domain_explanation_query":
        return domain_explanation_query(
            arguments["question"],
            focus=arguments.get("focus"),
            contract_no=arguments.get("contractNo"),
            invoice_no=arguments.get("invoiceNo"),
        )
    if name == "ontology_knowledge_query":
        return query_ontology_knowledge(arguments["question"], focus=arguments.get("focus"))
    if name == "semantic_query":
        return execute_semantic_query(plan=arguments, actor=actor, user_facing=False)
    if name == "query_contracts":
        return contract_service.query_contracts(arguments)
    if name == "get_contract_detail":
        return contract_service.get_contract_detail(int(arguments["contractId"]))
    if name == "query_open_invoices":
        return contract_service.query_open_invoices(arguments)
    if name == "readonly_sql_query":
        return execute_readonly_sql(arguments["sql"], actor=actor)
    raise ValueError(f"不支持的工具: {name}")


def tool_result_message(tool_call_id: str, result):
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(result, ensure_ascii=False),
    }
