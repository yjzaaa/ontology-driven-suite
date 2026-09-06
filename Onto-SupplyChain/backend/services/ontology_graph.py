from __future__ import annotations


def build_ontology_graph() -> dict:
    nodes = [
        {"id": "CustomerOrder", "label": "客户订单", "en": "CustomerOrder", "domain": "demand", "size": 42, "desc": "ATP分析中心对象。"},
        {"id": "Customer", "label": "客户", "en": "Customer", "domain": "demand", "size": 30, "desc": "客户等级与合同风险来源。"},
        {"id": "FinishedItem", "label": "成品物料", "en": "FinishedItem", "domain": "demand", "size": 28, "desc": "决定MTS/MTO/ATO路径。"},
        {"id": "WorkCenter", "label": "工作中心", "en": "WorkCenter", "domain": "production", "size": 32, "desc": "产能和瓶颈约束载体。"},
        {"id": "ProductionOrder", "label": "生产工单", "en": "ProductionOrder", "domain": "production", "size": 30, "desc": "订单触发的执行实体。"},
        {"id": "Operation", "label": "工序", "en": "Operation", "domain": "production", "size": 26, "desc": "ATP时间推演的最小粒度。"},
        {"id": "Inventory", "label": "库存", "en": "Inventory", "domain": "supply", "size": 28, "desc": "现货、在途、预留和可用量。"},
        {"id": "BOMLevel", "label": "BOM层级", "en": "BOMLevel", "domain": "supply", "size": 28, "desc": "物料依赖和替代料规则。"},
        {"id": "Supplier", "label": "供应商", "en": "Supplier", "domain": "supply", "size": 26, "desc": "提前期和供应风险来源。"},
        {"id": "Routing", "label": "工艺路线", "en": "Routing", "domain": "planning", "size": 28, "desc": "定义工序路径与替代路线。"},
        {"id": "ATPCommitment", "label": "交期承诺", "en": "ATPCommitment", "domain": "planning", "size": 34, "desc": "版本化的ATP输出。"},
    ]
    links = [
        {"source": "Customer", "target": "CustomerOrder", "label": "下达", "domain": "demand"},
        {"source": "CustomerOrder", "target": "FinishedItem", "label": "指定", "domain": "demand"},
        {"source": "CustomerOrder", "target": "ProductionOrder", "label": "触发", "domain": "production"},
        {"source": "CustomerOrder", "target": "Routing", "label": "遵循", "domain": "planning"},
        {"source": "CustomerOrder", "target": "Inventory", "label": "扣减", "domain": "supply"},
        {"source": "CustomerOrder", "target": "ATPCommitment", "label": "生成", "domain": "planning"},
        {"source": "FinishedItem", "target": "BOMLevel", "label": "定义", "domain": "supply"},
        {"source": "FinishedItem", "target": "Routing", "label": "适用", "domain": "planning"},
        {"source": "ProductionOrder", "target": "Operation", "label": "包含", "domain": "production"},
        {"source": "Operation", "target": "WorkCenter", "label": "执行于", "domain": "production"},
        {"source": "Routing", "target": "WorkCenter", "label": "分配", "domain": "planning"},
        {"source": "BOMLevel", "target": "Supplier", "label": "采购自", "domain": "supply"},
        {"source": "Supplier", "target": "Inventory", "label": "补充", "domain": "supply"},
        {"source": "Operation", "target": "Operation", "label": "前置依赖", "domain": "production"},
    ]
    return {"nodes": nodes, "links": links}
