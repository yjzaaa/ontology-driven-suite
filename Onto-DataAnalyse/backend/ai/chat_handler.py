"""阶段四对话处理器：意图识别 + 场景调度 + 会话持久化"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Iterator

from backend.ai.deepseek_client import get_client
from backend.ai.prompt_builder import load_prompt
from backend.ai.scenario_executor import execute_scenario, load_scenario, scenarios_summary
from backend.config.settings import settings
from backend.db.database import system_db
from backend.utils.sse_utils import sse_pack_raw


# ============================================================
# 意图识别：先关键词匹配，未命中再调 AI
# ============================================================
def detect_intent(user_message: str) -> dict:
    """返回 {scenario_id, confidence, matched_keywords, reasoning, source}"""
    msg = (user_message or "").strip()
    if not msg:
        return {"scenario_id": None, "confidence": 0,
                "matched_keywords": [], "reasoning": "空输入", "source": "rule"}

    # 1. 关键词命中（快速路径）
    rule_match = _keyword_match(msg)
    if rule_match and rule_match["confidence"] >= 80:
        return {**rule_match, "source": "rule"}

    # 2. 关键词命中但置信度不够 → 用 AI 补判
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("sk-xxx"):
        # 无 API key 时回退用关键词结果
        if rule_match:
            return {**rule_match, "source": "rule"}
        return {"scenario_id": None, "confidence": 0,
                "matched_keywords": [], "reasoning": "无法匹配任何关键词，且 API 未配置",
                "source": "rule"}

    ai_result = _ai_intent(msg)
    return {**ai_result, "source": "ai"}


def _keyword_match(msg: str) -> dict | None:
    """简单关键词触发"""
    msg_lower = msg.lower()
    best: dict | None = None
    for sc in scenarios_summary():
        matched = []
        for kw in sc.get("triggers") or []:
            if kw.lower() in msg_lower:
                matched.append(kw)
        if matched:
            confidence = 80 + min(15, len(matched) * 5)
            candidate = {
                "scenario_id": sc["id"],
                "confidence": confidence,
                "matched_keywords": matched,
                "reasoning": f"匹配关键词 {matched}",
            }
            if best is None or candidate["confidence"] > best["confidence"]:
                best = candidate
    return best


def _ai_intent(msg: str) -> dict:
    summary_lines = [
        f"- {sc['id']}: {sc['name']} | 触发词: {', '.join(sc.get('triggers') or [])}"
        for sc in scenarios_summary()
    ]
    prompt = load_prompt("phase4_intent.txt").format(
        scenarios_summary="\n".join(summary_lines),
        user_message=msg,
    )
    try:
        raw = get_client().chat(
            [{"role": "system", "content": prompt},
             {"role": "user", "content": "请输出 JSON。"}],
            phase_key="intent_recognition",
        )
        parsed = _parse_json_loose(raw)
        if not parsed:
            return {"scenario_id": None, "confidence": 0,
                    "matched_keywords": [], "reasoning": "AI 输出无法解析"}
        return {
            "scenario_id": parsed.get("scenario_id"),
            "confidence": int(parsed.get("confidence") or 0),
            "matched_keywords": parsed.get("matched_keywords") or [],
            "reasoning": parsed.get("reasoning") or "",
            "alternatives": parsed.get("alternatives") or [],
        }
    except Exception as e:
        return {"scenario_id": None, "confidence": 0,
                "matched_keywords": [], "reasoning": f"AI 调用失败：{e}"}


def _parse_json_loose(text: str) -> dict | None:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```\w*\n", "", t)
        t = re.sub(r"\n```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        l, r = t.find("{"), t.rfind("}")
        if l == -1 or r == -1 or r <= l:
            return None
        try:
            return json.loads(t[l:r + 1])
        except json.JSONDecodeError:
            return None


# ============================================================
# 会话与消息持久化
# ============================================================
def ensure_default_session() -> str:
    """返回当前项目的默认会话 ID（不存在则创建）"""
    with system_db() as conn:
        row = conn.execute(
            """SELECT id FROM chat_sessions WHERE project_id = ?
               ORDER BY created_at DESC LIMIT 1""",
            (settings.PROJECT_ID,),
        ).fetchone()
        if row:
            return row["id"]
        sid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (sid, settings.PROJECT_ID, "默认对话", now, now),
        )
        return sid


def list_sessions() -> list[dict]:
    with system_db() as conn:
        rows = conn.execute(
            """SELECT s.id, s.title, s.created_at, s.updated_at,
                      (SELECT COUNT(*) FROM chat_messages WHERE session_id = s.id) AS msg_count
               FROM chat_sessions s
               WHERE s.project_id = ?
               ORDER BY s.updated_at DESC""",
            (settings.PROJECT_ID,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_messages(session_id: str) -> list[dict]:
    with system_db() as conn:
        rows = conn.execute(
            """SELECT * FROM chat_messages
               WHERE session_id = ? ORDER BY created_at ASC""",
            (session_id,),
        ).fetchall()
        result = []
        for r in rows:
            m = dict(r)
            for k in ("report_data", "reasoning_data"):
                if m.get(k):
                    try:
                        m[k] = json.loads(m[k])
                    except json.JSONDecodeError:
                        pass
            result.append(m)
        return result


def save_message(session_id: str, role: str, content: str,
                 message_type: str = "text", report_data: dict | None = None,
                 reasoning_data: dict | None = None) -> str:
    mid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with system_db() as conn:
        conn.execute(
            """INSERT INTO chat_messages
               (id, session_id, role, content, message_type, report_data, reasoning_data, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mid, session_id, role, content, message_type,
                json.dumps(report_data, ensure_ascii=False, default=str) if report_data else None,
                json.dumps(reasoning_data, ensure_ascii=False, default=str) if reasoning_data else None,
                now,
            ),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
    return mid


# ============================================================
# 主流程：处理一次对话
# ============================================================
def handle_chat(session_id: str, user_message: str) -> Iterator[str]:
    """整个对话流程：意图识别 → 复用 scenario_executor 跑场景 → 持久化"""
    # 1. 落库用户消息
    save_message(session_id, "user", user_message)
    yield sse_pack_raw({"type": "user_saved"})

    # 2. 意图识别
    intent = detect_intent(user_message)
    yield sse_pack_raw({"type": "intent", **intent})

    scenario_id = intent.get("scenario_id")
    confidence = intent.get("confidence") or 0
    if not scenario_id or confidence < 30:
        # 兜底回复
        fallback = (
            "抱歉，我未能识别你的分析意图。\n\n"
            "本系统目前支持以下三个预设分析场景：\n"
            + "\n".join([f"- 🚨 经营异常分析（如：发现什么异常）",
                        f"- 📈 GMV 分析（如：分析销售额）",
                        f"- 👥 客户流失分析（如：用户流失情况）"])
            + "\n\n请用包含上述任一关键词的自然语言重新描述。"
        )
        save_message(session_id, "assistant", fallback)
        yield sse_pack_raw({"type": "assistant_fallback", "content": fallback})
        yield sse_pack_raw({"type": "done"})
        return

    # 3. 复用阶段三的场景执行器
    sc = load_scenario(scenario_id)
    if not sc:
        msg = f"未找到场景：{scenario_id}"
        save_message(session_id, "assistant", msg)
        yield sse_pack_raw({"type": "error", "message": msg})
        return

    yield sse_pack_raw({
        "type": "execution_start",
        "scenario": {"id": sc["id"], "name": sc["name"], "icon": sc.get("icon")},
    })

    # 透传 scenario_executor 的所有事件
    final_report = None
    reasoning_data = []
    for ev_str in execute_scenario(scenario_id):
        yield ev_str
        # 顺手解析关键事件用于持久化
        try:
            payload = ev_str.replace("data: ", "").strip()
            ev = json.loads(payload)
            if ev.get("type") == "report_ready":
                final_report = ev.get("report")
            elif ev.get("type") == "ai_complete":
                reasoning_data.append({
                    "step_id": ev.get("step_id"),
                    "thinking": ev.get("thinking"),
                    "conclusion": ev.get("conclusion"),
                    "recommendations": ev.get("recommendations"),
                    "confidence": ev.get("confidence"),
                })
        except json.JSONDecodeError:
            pass

    # 4. 持久化助手回复（含完整报告）
    summary_text = _make_summary(sc, final_report)
    save_message(
        session_id, "assistant", summary_text,
        message_type="report",
        report_data=final_report,
        reasoning_data={"steps": reasoning_data},
    )


def _make_summary(sc: dict, report: dict | None) -> str:
    if not report:
        return f"已尝试执行场景 {sc['name']}，但未能生成完整报告。"
    n_sql = len(report.get("sql_steps") or [])
    n_stat = len(report.get("stat_steps") or [])
    n_ai = len(report.get("ai_steps") or [])
    return f"已完成 {sc.get('icon', '')} {sc['name']}：采集 {n_sql} 个数据集，{n_stat} 次统计计算，{n_ai} 次 AI 推理。完整报告见下。"
