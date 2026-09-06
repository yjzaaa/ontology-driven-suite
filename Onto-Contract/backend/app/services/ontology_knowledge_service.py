from __future__ import annotations

import re
from typing import Any

from flask import current_app


QUESTION_FOCUS_HINTS = {
    "流程": {"use_case", "behavior", "event"},
    "步骤": {"use_case", "behavior"},
    "规则": {"rule", "behavior"},
    "校验": {"rule", "behavior"},
    "事件": {"event"},
    "页面": {"page"},
    "界面": {"page"},
    "需求": {"document"},
    "本体": {"aggregate", "behavior", "rule", "event", "use_case", "page", "document"},
    "模型": {"aggregate", "behavior", "rule", "event", "use_case", "page", "document"},
}


def query_ontology_knowledge(question: str, focus: str | None = None, top_k: int = 6) -> dict[str, Any]:
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    normalized_question = _normalize(question)
    focus_types = _infer_focus_types(normalized_question, focus)
    scored_entries: list[tuple[float, dict[str, Any]]] = []

    for entry in registry.knowledge_entries:
        score = _score_entry(entry, normalized_question, focus_types)
        if score > 0:
            scored_entries.append((score, entry))

    scored_entries.sort(
        key=lambda item: (
            item[0],
            1 if item[1]["type"] in {"use_case", "behavior", "rule"} else 0,
            len(item[1]["content"]),
        ),
        reverse=True,
    )

    matches = [
        {
            "id": entry["id"],
            "type": entry["type"],
            "title": entry["title"],
            "source": entry["source"],
            "content": entry["content"],
            "score": round(score, 2),
        }
        for score, entry in scored_entries[: max(1, top_k)]
    ]
    summary = _build_summary(matches)
    return {
        "question": question,
        "summary": summary,
        "matches": matches,
    }


def format_ontology_knowledge_payload(result: dict[str, Any]) -> dict[str, Any]:
    matches = result.get("matches") or []
    if not matches:
        return {
            "message": "暂时没有从本体模型和需求文档中匹配到足够明确的信息。",
            "render": None,
            "action": None,
        }

    paragraphs = [result.get("summary", "")]
    for match in matches[:4]:
        paragraphs.append(f"{match['title']}：{match['content']}")
    return {
        "message": "\n\n".join(part for part in paragraphs if part),
        "render": None,
        "action": None,
    }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def _infer_focus_types(normalized_question: str, explicit_focus: str | None) -> set[str]:
    focus_types: set[str] = set()
    if explicit_focus:
        focus_types.add(explicit_focus)
    for hint, types in QUESTION_FOCUS_HINTS.items():
        if hint in normalized_question:
            focus_types.update(types)
    return focus_types


def _score_entry(entry: dict[str, Any], normalized_question: str, focus_types: set[str]) -> float:
    score = 0.0
    entry_type = entry.get("type", "")
    title = _normalize(entry.get("title", ""))
    content = _normalize(entry.get("content", ""))

    if focus_types and entry_type in focus_types:
        score += 5.0

    if title and title in normalized_question:
        score += 8.0
    if title and normalized_question in title:
        score += 4.0

    for keyword in entry.get("keywords", []):
        normalized_keyword = _normalize(keyword)
        if not normalized_keyword or len(normalized_keyword) < 2:
            continue
        if normalized_keyword in normalized_question:
            score += 3.0 + min(len(normalized_keyword), 10) * 0.15
        elif normalized_question and normalized_question in normalized_keyword:
            score += 1.5
        elif normalized_keyword in content:
            score += 0.3

    if "合同创建" in normalized_question and _contains_any(content, ["合同录入", "合同已创建", "contract_create"]):
        score += 6.0
    if "合同创建流程" in normalized_question and entry_type in {"use_case", "behavior", "event"}:
        score += 4.0
    if "开票流程" in normalized_question and _contains_any(content, ["开票录入", "invoice_create", "invoice.created"]):
        score += 4.0
    if "收款流程" in normalized_question and _contains_any(content, ["收款录入", "payment_receive", "payment.received"]):
        score += 4.0
    if "规则" in normalized_question and entry_type == "rule":
        score += 3.0
    if "需求" in normalized_question and entry_type == "document":
        score += 2.0

    return score


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _build_summary(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return ""
    top = matches[0]
    if top["type"] == "use_case":
        return "已根据本体场景模型、行为模型和需求文档匹配到最相关的业务流程信息。"
    if top["type"] == "rule":
        return "已根据本体规则模型匹配到最相关的业务规则信息。"
    if top["type"] == "event":
        return "已根据本体事件模型匹配到最相关的事件流转信息。"
    if top["type"] == "page":
        return "已根据 UI 模型匹配到最相关的页面职责信息。"
    if top["type"] == "document":
        return "已根据需求文档和架构文档匹配到最相关的背景说明。"
    return "已根据本体模型和需求文档匹配到最相关的信息。"
