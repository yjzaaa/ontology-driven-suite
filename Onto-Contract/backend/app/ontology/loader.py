from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class OntologyRegistry:
    model_root: str
    raw_models: dict[str, Any] = field(default_factory=dict)
    aggregates: dict[str, Any] = field(default_factory=dict)
    behaviors: dict[str, Any] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)
    events: dict[str, Any] = field(default_factory=dict)
    use_cases: dict[str, Any] = field(default_factory=dict)
    quality_annotations: dict[str, Any] = field(default_factory=dict)
    pages: dict[str, Any] = field(default_factory=dict)
    navigation: list[dict[str, Any]] = field(default_factory=list)
    master_entities: dict[str, Any] = field(default_factory=dict)
    db_whitelist: dict[str, Any] = field(default_factory=dict)
    requirement_docs: dict[str, str] = field(default_factory=dict)
    knowledge_entries: list[dict[str, Any]] = field(default_factory=list)

    def load(self):
        root = Path(self.model_root)
        for file_path in sorted(root.glob("*.yaml")):
            self.raw_models[file_path.name] = yaml.safe_load(
                file_path.read_text(encoding="utf-8")
            )

        object_model = self.raw_models.get("m1-object-model.yaml", {})
        for aggregate in object_model.get("aggregates", []):
            alias = aggregate["rootEntity"]["alias"]
            self.aggregates[alias] = aggregate
        for master_entity in object_model.get("masterEntities", []):
            self.master_entities[master_entity["alias"]] = master_entity

        for behavior in self.raw_models.get("m2-behavior-model.yaml", {}).get("behaviors", []):
            self.behaviors[behavior["id"]] = behavior
        for rule in self.raw_models.get("m3-rule-model.yaml", {}).get("rules", []):
            self.rules[rule["id"]] = rule
        for event in self.raw_models.get("me-event-model.yaml", {}).get("events", []):
            self.events[event["eventId"]] = event
        for use_case in self.raw_models.get("m4-scenario-model.yaml", {}).get("use_cases", []):
            self.use_cases[use_case["id"]] = use_case
        for qa in self.raw_models.get("m7-quality-model.yaml", {}).get("quality_annotations", []):
            self.quality_annotations[qa["qaId"]] = qa

        ui_model = self.raw_models.get("m9-contract-ui-model.yaml", {})
        self.navigation = ui_model.get("navigation_model", {}).get("nodes", [])
        for page in ui_model.get("page_registry", []):
            self.pages[page["pageId"]] = page

        self.db_whitelist = {
            "tables": {
                "contracts": [
                    "id",
                    "contract_no",
                    "contract_name",
                    "status",
                    "product_id",
                    "customer_id",
                    "dept_id",
                    "owner_id",
                    "sign_date",
                    "total_amount",
                    "purchase_amount",
                    "tax_rate",
                    "invoiced_amount_total",
                    "received_amount_total",
                    "invoice_status",
                    "receipt_status",
                    "created_at",
                ],
                "contract_payment_terms": [
                    "id",
                    "contract_id",
                    "stage_no",
                    "stage_name",
                    "ratio",
                ],
                "invoices": [
                    "id",
                    "invoice_no",
                    "contract_id",
                    "amount",
                    "tax_rate",
                    "invoice_date",
                    "status",
                    "is_received",
                    "received_date",
                    "created_at",
                ],
                "invoice_term_mappings": [
                    "id",
                    "invoice_id",
                    "stage_no",
                    "stage_name",
                ],
                "products": ["id", "product_no", "product_type", "product_name"],
                "customers": ["id", "customer_no", "customer_type", "customer_name"],
                "departments": ["id", "dept_no", "dept_name"],
                "employees": ["id", "employee_no", "employee_name", "dept_id"],
            },
            "max_joins": 4,
        }

        self._load_requirement_docs(root)
        self._build_knowledge_entries()

    def page_summaries(self):
        return list(self.pages.values())

    def ontology_summary(self):
        return {
            "aggregates": list(self.aggregates.keys()),
            "behaviors": list(self.behaviors.keys()),
            "rules": list(self.rules.keys()),
            "events": list(self.events.keys()),
            "useCases": list(self.use_cases.keys()),
            "pages": list(self.pages.keys()),
        }

    def _load_requirement_docs(self, root: Path):
        # Resolve bundled documentation from this repository, independently of
        # the configured model path and any parent checkout directories.
        project_root = Path(__file__).resolve().parents[3]
        doc_candidates = [
            "合同管理原始需求.txt",
            "AI原生应用技术架构设计文档.md",
            "ontology_modeling_framework.md",
        ]
        for file_name in doc_candidates:
            file_path = project_root / file_name
            if file_path.exists():
                self.requirement_docs[file_name] = file_path.read_text(encoding="utf-8")

    def _build_knowledge_entries(self):
        self.knowledge_entries = []

        object_model = self.raw_models.get("m1-object-model.yaml", {})
        for aggregate in object_model.get("aggregates", []):
            root_entity = aggregate.get("rootEntity", {})
            children = aggregate.get("childEntities", [])
            refs = aggregate.get("references", [])
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"aggregate:{root_entity.get('alias', '')}",
                    entry_type="aggregate",
                    title=f"{root_entity.get('name', root_entity.get('alias', '聚合'))}聚合",
                    source="m1-object-model.yaml",
                    content="\n".join(
                        [
                            f"聚合根: {root_entity.get('alias', '')} / {root_entity.get('name', '')}",
                            f"子实体: {', '.join(item.get('alias', '') for item in children) or '无'}",
                            f"引用对象: {', '.join(item.get('targetAggregate', item.get('targetMasterEntity', '')) for item in refs) or '无'}",
                        ]
                    ),
                    keywords=[root_entity.get("alias", ""), root_entity.get("name", "")],
                )
            )

        for behavior in self.behaviors.values():
            lines = [
                f"行为ID: {behavior.get('id', '')}",
                f"行为名称: {behavior.get('name', '')}",
                f"所属对象: {behavior.get('ownerEntity', '')}",
                f"行为类型: {behavior.get('behaviorType', '')}",
                f"触发方式: {behavior.get('triggerType', '')}",
            ]
            if behavior.get("preconditions"):
                lines.append("前置条件: " + "；".join(behavior["preconditions"]))
            if behavior.get("postconditions"):
                postconditions = [f"{item.get('field', '')} -> {item.get('setValue', '')}" for item in behavior["postconditions"]]
                lines.append("后置结果: " + "；".join(postconditions))
            if behavior.get("appliedRules"):
                lines.append("应用规则: " + "、".join(behavior["appliedRules"]))
            if behavior.get("producedEvents"):
                lines.append("产生事件: " + "、".join(behavior["producedEvents"]))
            if behavior.get("requiredPermissions"):
                lines.append("权限要求: " + "、".join(behavior["requiredPermissions"]))
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"behavior:{behavior.get('id', '')}",
                    entry_type="behavior",
                    title=behavior.get("name", behavior.get("id", "行为")),
                    source="m2-behavior-model.yaml",
                    content="\n".join(lines),
                    keywords=[behavior.get("id", ""), behavior.get("name", ""), behavior.get("ownerEntity", "")],
                )
            )

        for rule in self.rules.values():
            lines = [
                f"规则ID: {rule.get('id', '')}",
                f"规则名称: {rule.get('name', '')}",
                f"规则类型: {rule.get('ruleType', '')}",
            ]
            if rule.get("description"):
                lines.append(f"规则说明: {rule['description']}")
            if rule.get("expression"):
                lines.append(f"规则表达式: {rule['expression'].strip()}")
            if rule.get("violationMessage"):
                lines.append(f"违规提示: {rule['violationMessage']}")
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"rule:{rule.get('id', '')}",
                    entry_type="rule",
                    title=rule.get("name", rule.get("id", "规则")),
                    source="m3-rule-model.yaml",
                    content="\n".join(lines),
                    keywords=[rule.get("id", ""), rule.get("name", ""), rule.get("ruleType", "")],
                )
            )

        for use_case in self.use_cases.values():
            lines = [
                f"用例ID: {use_case.get('id', '')}",
                f"用例名称: {use_case.get('name', '')}",
                "前置条件: " + "；".join(use_case.get("preconditions", []) or ["无"]),
                "后置条件: " + "；".join(use_case.get("postconditions", []) or ["无"]),
            ]
            primary_flow = []
            for step in use_case.get("primaryFlow", []):
                primary_flow.append(
                    f"{step.get('stepId', '')}:{step.get('behaviorRef') or step.get('eventRef') or step.get('waitForEvent') or step.get('stepType', '')}"
                )
            if primary_flow:
                lines.append("主流程: " + " -> ".join(primary_flow))
            for alt_flow in use_case.get("alternativeFlows", []):
                steps = [
                    step.get("behaviorRef") or step.get("eventRef") or step.get("stepType", "")
                    for step in alt_flow.get("steps", [])
                ]
                lines.append(
                    f"备选流程 {alt_flow.get('flowId', '')}: 条件={alt_flow.get('condition', '')}; 步骤={' -> '.join(steps)}"
                )
            for ex_flow in use_case.get("exceptionFlows", []):
                lines.append(
                    f"异常流程 {ex_flow.get('flowId', '')}: 条件={ex_flow.get('condition', '')}; 补偿={ex_flow.get('compensationRef', '')}"
                )
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"use_case:{use_case.get('id', '')}",
                    entry_type="use_case",
                    title=use_case.get("name", use_case.get("id", "用例")),
                    source="m4-scenario-model.yaml",
                    content="\n".join(lines),
                    keywords=[use_case.get("id", ""), use_case.get("name", "")],
                )
            )

        for event in self.events.values():
            lines = [
                f"事件ID: {event.get('eventId', '')}",
                f"事件名称: {event.get('eventName', '')}",
                f"生产行为: {event.get('producerBehaviorRef', '')}",
                f"订阅行为: {'、'.join(event.get('subscriberBehaviorRefs', []) or ['无'])}",
                f"载荷字段: {'、'.join(event.get('payload', []) or ['无'])}",
            ]
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"event:{event.get('eventId', '')}",
                    entry_type="event",
                    title=event.get("eventName", event.get("eventId", "事件")),
                    source="me-event-model.yaml",
                    content="\n".join(lines),
                    keywords=[event.get("eventId", ""), event.get("eventName", ""), event.get("producerBehaviorRef", "")],
                )
            )

        for page in self.pages.values():
            self.knowledge_entries.append(
                self._entry(
                    entry_id=f"page:{page.get('pageId', '')}",
                    entry_type="page",
                    title=page.get("pageName", page.get("pageId", "页面")),
                    source="m9-contract-ui-model.yaml",
                    content="\n".join(
                        [
                            f"页面ID: {page.get('pageId', '')}",
                            f"页面名称: {page.get('pageName', '')}",
                            f"页面描述: {page.get('description', '')}",
                            f"绑定用例: {'、'.join(page.get('useCaseIds', []) or ['无'])}",
                        ]
                    ),
                    keywords=[page.get("pageId", ""), page.get("pageName", "")],
                )
            )

        for file_name, content in self.requirement_docs.items():
            for index, paragraph in enumerate(self._split_paragraphs(content), start=1):
                self.knowledge_entries.append(
                    self._entry(
                        entry_id=f"doc:{file_name}:{index}",
                        entry_type="document",
                        title=f"{file_name}#{index}",
                        source=file_name,
                        content=paragraph,
                        keywords=[file_name],
                    )
                )

    def _entry(
        self,
        entry_id: str,
        entry_type: str,
        title: str,
        source: str,
        content: str,
        keywords: list[str],
    ) -> dict[str, Any]:
        return {
            "id": entry_id,
            "type": entry_type,
            "title": title,
            "source": source,
            "content": content.strip(),
            "keywords": self._expand_keywords(title, keywords, content),
        }

    def _expand_keywords(self, title: str, keywords: list[str], content: str) -> list[str]:
        result: list[str] = []
        seed_words = [title, *keywords]
        alias_map = {
            "录入": ["创建", "新增", "保存", "登记"],
            "创建": ["录入", "新增", "保存"],
            "收款": ["回款", "到账"],
            "查询": ["检索", "查找"],
            "开票": ["发票", "开具发票"],
            "流程": ["步骤", "过程"],
            "规则": ["校验", "约束"],
        }
        for word in seed_words:
            normalized = str(word).strip()
            if not normalized:
                continue
            if normalized not in result:
                result.append(normalized)
            for key, aliases in alias_map.items():
                if key in normalized:
                    for alias in aliases:
                        candidate = normalized.replace(key, alias)
                        if candidate and candidate not in result:
                            result.append(candidate)
        for term in ["合同", "开票", "收款", "发票", "流程", "规则", "事件", "需求", "页面", "本体模型"]:
            if term in content and term not in result:
                result.append(term)
        return result

    def _split_paragraphs(self, content: str) -> list[str]:
        paragraphs = [item.strip() for item in content.split("\n\n")]
        return [item for item in paragraphs if len(item) >= 12]
