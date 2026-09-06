"""阶段三场景执行编排器

按场景 YAML 中定义的步骤顺序执行：
  - SQL 步骤：AI 优先生成 SQL → 校验 → 执行；失败重试 2 次仍失败则用 fallback_sql
  - STAT 步骤：调用 stats_engine 的算法
  - AI_REASONING 步骤：组装上下文 → DeepSeek 流式推理

所有事件流式推送 SSE 给前端实时显示。
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Iterator

import yaml

from backend.ai.deepseek_client import get_client
from backend.ai.prompt_builder import load_prompt
from backend.config.settings import settings
from backend.core import mapping_engine, ontology_engine, sql_executor, stats_engine
from backend.db.database import system_db
from backend.utils.sse_utils import sse_pack_raw


# ============================================================
# 场景加载
# ============================================================
def load_all_scenarios() -> list[dict]:
    out: list[dict] = []
    for p in sorted(settings.scenarios_dir().glob("scenario_*.yaml")):
        try:
            sc = yaml.safe_load(p.read_text(encoding="utf-8"))
            sc["_file"] = p.name
            out.append(sc)
        except yaml.YAMLError:
            continue
    return out


def load_scenario(scenario_id: str) -> dict | None:
    for sc in load_all_scenarios():
        if sc.get("id") == scenario_id:
            return sc
    return None


def scenarios_summary() -> list[dict]:
    """前端列表接口用：精简字段"""
    out = []
    for sc in load_all_scenarios():
        out.append({
            "id": sc["id"],
            "name": sc["name"],
            "icon": sc.get("icon", ""),
            "description": sc.get("description", ""),
            "key_metrics": sc.get("key_metrics", []),
            "triggers": sc.get("triggers", []),
            "step_count": len(sc.get("steps", [])),
        })
    return out


# ============================================================
# 主执行流程（生成器：yield SSE 字符串）
# ============================================================
def execute_scenario(scenario_id: str) -> Iterator[str]:
    sc = load_scenario(scenario_id)
    if not sc:
        yield sse_pack_raw({"type": "error", "message": f"未找到场景：{scenario_id}"})
        return

    execution_id = str(uuid.uuid4())
    yield sse_pack_raw({
        "type": "scenario_start",
        "execution_id": execution_id,
        "scenario": {
            "id": sc["id"], "name": sc["name"], "icon": sc.get("icon"),
            "description": sc.get("description"), "step_count": len(sc.get("steps", [])),
        },
    })

    # 初始化执行记录
    _create_execution_record(execution_id, scenario_id)

    step_results: dict[str, dict] = {}    # step_id → 结果
    steps_data: list[dict] = []

    db_schema = _get_db_schema()
    mapping = mapping_engine.load_mapping() or {}
    mapping_summary = _build_mapping_summary(mapping)

    for step in sc.get("steps", []):
        sid = step["id"]
        stype = step["type"]
        yield sse_pack_raw({
            "type": "step_start",
            "step_id": sid,
            "step_type": stype,
            "description": step.get("description", ""),
        })

        try:
            if stype == "SQL":
                result = yield from _execute_sql_step(step, db_schema, mapping_summary)
            elif stype == "STAT":
                result = _execute_stat_step(step, step_results)
                yield sse_pack_raw({
                    "type": "step_result", "step_id": sid, "step_type": stype,
                    "stats": result.get("stats"), "ok": True,
                })
            elif stype == "AI_REASONING":
                result = yield from _execute_ai_reasoning_step(step, sc, step_results)
            else:
                result = {"ok": False, "error": f"未知步骤类型 {stype}"}
        except Exception as e:
            yield sse_pack_raw({
                "type": "step_error", "step_id": sid, "error": str(e),
            })
            result = {"ok": False, "error": str(e)}

        step_results[sid] = result
        steps_data.append({
            "step_id": sid, "type": stype,
            "description": step.get("description"),
            **{k: v for k, v in result.items() if k != "rows" or len(result.get("rows") or []) <= 20},
            # 只在结果中保留前 20 行预览，避免存档过大
            "rows_preview": (result.get("rows") or [])[:20] if result.get("rows") else None,
            "row_count": len(result.get("rows") or []) if result.get("rows") else None,
        })
        yield sse_pack_raw({"type": "step_done", "step_id": sid})

    # 最终报告组装事件
    yield sse_pack_raw({
        "type": "report_ready",
        "scenario_id": scenario_id,
        "execution_id": execution_id,
        "report": _assemble_report(sc, step_results),
    })
    _finalize_execution_record(execution_id, steps_data, _assemble_report(sc, step_results))
    yield sse_pack_raw({"type": "done", "execution_id": execution_id})


# ============================================================
# SQL 步骤：AI 优先生成 + fallback 兜底
# ============================================================
def _execute_sql_step(step: dict, db_schema: str, mapping_summary: str) -> Iterator[str]:
    sid = step["id"]
    sql_intent = step.get("sql_intent", "")
    fallback_sql = step.get("fallback_sql", "")

    used_fallback = False
    final_sql = ""
    last_error = ""

    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("sk-xxx"):
        # API Key 未配置时直接用 fallback（避免演示中断）
        used_fallback = True
        final_sql = fallback_sql
        yield sse_pack_raw({
            "type": "step_sql_attempt", "step_id": sid,
            "source": "fallback", "reason": "DeepSeek API Key 未配置，使用 fallback SQL",
            "sql": final_sql,
        })
    else:
        # AI 生成 + 重试
        client = get_client()
        template = load_prompt("phase3_sql_gen.txt")
        for attempt in range(settings.AI_SQL_MAX_RETRIES + 1):
            yield sse_pack_raw({
                "type": "step_sql_attempt", "step_id": sid,
                "source": "ai", "attempt": attempt + 1,
            })
            try:
                system = template.format(
                    db_schema_doc=db_schema[:8000],
                    mapping_summary=mapping_summary,
                    sql_intent=sql_intent,
                )
                # 非流式调用，等到完整 SQL 再校验
                ai_sql = client.chat(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": "请直接输出 SQL。"},
                    ],
                    phase_key="phase3_sql_gen",
                )
                ai_sql = _strip_code_fence(ai_sql).strip().rstrip(";")
            except Exception as e:
                last_error = f"LLM 调用失败：{e}"
                continue

            # 试运行
            res = sql_executor.execute_sql(ai_sql)
            if res.ok and res.row_count > 0:
                final_sql = ai_sql
                yield sse_pack_raw({
                    "type": "step_sql", "step_id": sid, "source": "ai",
                    "sql": ai_sql,
                })
                yield sse_pack_raw({
                    "type": "step_result", "step_id": sid, "step_type": "SQL",
                    "ok": True, "source": "ai",
                    "rows_preview": res.rows[:5], "row_count": res.row_count,
                    "columns": res.columns, "duration_ms": res.duration_ms,
                })
                return {
                    "ok": True, "source": "ai", "sql": ai_sql,
                    "rows": res.rows, "columns": res.columns,
                    "duration_ms": res.duration_ms,
                }
            else:
                last_error = res.error or "SQL 返回 0 行结果"
                # 提示重试时附带错误（这里我们不在 prompt 中加入，下次重试是新对话）
        # AI 全部失败 → 用 fallback
        used_fallback = True
        final_sql = fallback_sql
        yield sse_pack_raw({
            "type": "step_sql_attempt", "step_id": sid,
            "source": "fallback", "reason": f"AI 生成失败 {settings.AI_SQL_MAX_RETRIES + 1} 次，最后错误：{last_error}",
            "sql": final_sql,
        })

    # 执行最终 SQL（fallback 路径）
    yield sse_pack_raw({
        "type": "step_sql", "step_id": sid,
        "source": "fallback" if used_fallback else "ai",
        "sql": final_sql,
    })
    res = sql_executor.execute_sql(final_sql)
    yield sse_pack_raw({
        "type": "step_result", "step_id": sid, "step_type": "SQL",
        "ok": res.ok, "source": "fallback" if used_fallback else "ai",
        "rows_preview": res.rows[:5] if res.ok else [],
        "row_count": res.row_count, "columns": res.columns,
        "duration_ms": res.duration_ms,
        "error": res.error,
    })
    return {
        "ok": res.ok,
        "source": "fallback" if used_fallback else "ai",
        "sql": final_sql,
        "rows": res.rows,
        "columns": res.columns,
        "duration_ms": res.duration_ms,
        "error": res.error,
    }


# ============================================================
# STAT 步骤
# ============================================================
def _execute_stat_step(step: dict, step_results: dict[str, dict]) -> dict:
    algo = step.get("algorithm")
    input_step_id = step.get("input_step")
    input_result = step_results.get(input_step_id)
    if not input_result or not input_result.get("ok"):
        return {"ok": False, "error": f"依赖的步骤 {input_step_id} 未完成或失败"}
    rows = input_result.get("rows") or []
    params = step.get("params") or {}
    try:
        stats = stats_engine.run_algorithm(algo, rows, **params)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "algorithm": algo, "stats": stats, "rows": rows}


# ============================================================
# AI_REASONING 步骤（流式）
# ============================================================
def _execute_ai_reasoning_step(step: dict, scenario: dict, step_results: dict) -> Iterator[str]:
    sid = step["id"]
    task = step.get("task", "")
    input_step_ids = step.get("input_steps", [])
    # 收集上下文数据（精简版，避免 token 爆炸）
    collected = {}
    for src_sid in input_step_ids:
        res = step_results.get(src_sid) or {}
        if res.get("rows"):
            collected[src_sid] = {
                "description": _step_description(scenario, src_sid),
                "row_count": len(res["rows"]),
                "columns": res.get("columns"),
                "rows": res["rows"][:30],   # 截前 30 行
            }
        elif res.get("stats"):
            collected[src_sid] = {
                "description": _step_description(scenario, src_sid),
                "stats": res["stats"],
            }

    ontology_ctx = _build_ontology_context(scenario)
    template = load_prompt("phase3_reasoning.txt")
    system = template.format(
        ontology_context=ontology_ctx,
        collected_data_json=json.dumps(collected, ensure_ascii=False, default=str)[:20000],
        task_description=task,
    )

    full_text = ""
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("sk-xxx"):
        yield sse_pack_raw({
            "type": "step_error", "step_id": sid,
            "error": "DeepSeek API Key 未配置，无法进行 AI 推理",
        })
        return {"ok": False, "error": "DeepSeek API Key 未配置"}

    client = get_client()
    try:
        for chunk in client.chat_stream(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": "请按 XML 标签格式输出完整推理与建议。"},
            ],
            phase_key="phase3_reasoning",
        ):
            full_text += chunk
            yield sse_pack_raw({"type": "ai_thinking", "step_id": sid, "delta": chunk})
    except Exception as e:
        yield sse_pack_raw({"type": "step_error", "step_id": sid, "error": str(e)})
        return {"ok": False, "error": str(e)}

    parsed = _parse_reasoning_output(full_text)
    # 兜底：如果 LLM 没按 XML 标签格式输出（标签全空），把全文塞到 conclusion 里
    if not parsed.get("thinking") and not parsed.get("conclusion") \
       and not parsed.get("recommendations") and full_text.strip():
        parsed = {"conclusion": full_text.strip(), "parse_fallback": True}
    yield sse_pack_raw({
        "type": "ai_complete", "step_id": sid,
        "thinking": parsed.get("thinking"),
        "conclusion": parsed.get("conclusion"),
        "recommendations": parsed.get("recommendations"),
        "charts": parsed.get("charts"),
        "charts_parsed": parsed.get("charts_parsed"),
        "confidence": parsed.get("confidence"),
        "parse_fallback": parsed.get("parse_fallback", False),
        "raw_text": full_text[:6000],
    })
    parsed["raw_text"] = full_text
    return {"ok": True, "ai_output": parsed, "raw_text": full_text}


# ============================================================
# 辅助函数
# ============================================================
def _get_db_schema() -> str:
    """从系统库读取阶段一上传的 DB Schema 文档"""
    with system_db() as conn:
        row = conn.execute(
            "SELECT db_schema_doc FROM projects WHERE id = ?", (settings.PROJECT_ID,)
        ).fetchone()
        return row["db_schema_doc"] if row and row["db_schema_doc"] else ""


def _build_mapping_summary(mapping: dict) -> str:
    """把映射配置压成"实体名→主表 + 关键字段"清单，供 SQL 生成 prompt 使用"""
    if not mapping:
        return "（映射未生成）"
    out = []
    for em in mapping.get("entity_mappings", []):
        primary = next((t for t in (em.get("tables") or []) if t.get("primary")), None)
        if not primary:
            continue
        cols = []
        for fm in (em.get("field_mappings") or [])[:8]:
            cols.append(f"{fm['ontology_field']}={fm.get('db_table', primary['table'])}.{fm['db_column']}")
        line = f"- {em['entity_name']} ({em['entity_id']}) → {primary['table']}：{', '.join(cols)}"
        if em.get("default_filter"):
            line += f"  [filter: {em['default_filter']}]"
        out.append(line)
    return "\n".join(out)


def _step_description(scenario: dict, step_id: str) -> str:
    for s in scenario.get("steps", []):
        if s.get("id") == step_id:
            return s.get("description", step_id)
    return step_id


def _build_ontology_context(scenario: dict) -> str:
    """从已生成的本体里抽取与当前场景相关的实体/指标定义"""
    parts = []
    m1 = ontology_engine.load_model_yaml("M1")
    if m1:
        parts.append("# 涉及实体（M1）")
        for ent in m1.get("entities", [])[:12]:
            parts.append(f"- {ent.get('id')}: {ent.get('name')} ({ent.get('domain', '')})")
    mm = ontology_engine.load_model_yaml("M_Metric")
    if mm:
        parts.append("\n# 涉及指标（M_Metric）")
        wanted = set(scenario.get("key_metrics") or [])
        for m in mm.get("metrics", []):
            if not wanted or m.get("id") in wanted:
                parts.append(f"- {m.get('id')}: {m.get('name')} — {m.get('formula_description', '')}")
    m3 = ontology_engine.load_model_yaml("M3")
    if m3:
        parts.append("\n# 关键业务规则（M3）")
        for r in m3.get("rules", [])[:6]:
            parts.append(f"- {r.get('id')}: {r.get('name')} — {r.get('description', '')}")
    return "\n".join(parts) or "（本体尚未生成）"


_TAG_RE = {
    "thinking": re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL),
    "conclusion": re.compile(r"<conclusion>(.*?)</conclusion>", re.DOTALL),
    "recommendations": re.compile(r"<recommendations>(.*?)</recommendations>", re.DOTALL),
    "charts": re.compile(r"<charts>(.*?)</charts>", re.DOTALL),
}
_CONF_RE = re.compile(r"置信度[:：]?\s*(\d+)\s*%")


def _parse_reasoning_output(text: str) -> dict:
    out: dict = {}
    for k, pat in _TAG_RE.items():
        m = pat.search(text)
        if m:
            out[k] = m.group(1).strip()
    # 提取置信度数字列表
    confidences = [int(m.group(1)) for m in _CONF_RE.finditer(text)]
    if confidences:
        out["confidence"] = {
            "values": confidences,
            "avg": round(sum(confidences) / len(confidences)),
        }
    # 尝试解析 charts JSON
    if "charts" in out:
        try:
            cleaned = _strip_code_fence(out["charts"])
            out["charts_parsed"] = json.loads(cleaned)
        except json.JSONDecodeError:
            out["charts_parsed"] = []
    return out


def _strip_code_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()
        lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s


def _assemble_report(scenario: dict, step_results: dict[str, dict]) -> dict:
    """组装最终报告（前端用一次性渲染）"""
    sql_steps = []
    stat_steps = []
    ai_steps = []
    for step in scenario.get("steps", []):
        sid = step["id"]
        res = step_results.get(sid) or {}
        if step["type"] == "SQL":
            sql_steps.append({
                "step_id": sid,
                "description": step.get("description"),
                "sql": res.get("sql"),
                "source": res.get("source"),
                "row_count": len(res.get("rows") or []),
                "columns": res.get("columns"),
                "rows_preview": (res.get("rows") or [])[:10],
                "ok": res.get("ok"),
            })
        elif step["type"] == "STAT":
            stat_steps.append({
                "step_id": sid,
                "description": step.get("description"),
                "algorithm": res.get("algorithm"),
                "stats": res.get("stats"),
            })
        elif step["type"] == "AI_REASONING":
            ai_steps.append({
                "step_id": sid,
                "description": step.get("description"),
                "ai_output": res.get("ai_output", {}),
            })
    return {
        "scenario": {
            "id": scenario["id"], "name": scenario["name"],
            "icon": scenario.get("icon"), "description": scenario.get("description"),
        },
        "sql_steps": sql_steps,
        "stat_steps": stat_steps,
        "ai_steps": ai_steps,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# 执行记录持久化
# ============================================================
def _create_execution_record(execution_id: str, scenario_id: str) -> None:
    with system_db() as conn:
        conn.execute(
            """INSERT INTO execution_records (id, project_id, scenario_id, status, started_at)
               VALUES (?, ?, ?, 'running', datetime('now', 'localtime'))""",
            (execution_id, settings.PROJECT_ID, scenario_id),
        )


def _finalize_execution_record(execution_id: str, steps_data: list, report: dict) -> None:
    with system_db() as conn:
        conn.execute(
            """UPDATE execution_records
               SET status = 'completed', steps_data = ?, report_data = ?,
                   completed_at = datetime('now', 'localtime')
               WHERE id = ?""",
            (
                json.dumps(steps_data, ensure_ascii=False, default=str),
                json.dumps(report, ensure_ascii=False, default=str),
                execution_id,
            ),
        )


def get_execution_records(limit: int = 20) -> list[dict]:
    with system_db() as conn:
        rows = conn.execute(
            """SELECT id, scenario_id, status, started_at, completed_at
               FROM execution_records WHERE project_id = ?
               ORDER BY started_at DESC LIMIT ?""",
            (settings.PROJECT_ID, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_execution_detail(execution_id: str) -> dict | None:
    with system_db() as conn:
        row = conn.execute(
            "SELECT * FROM execution_records WHERE id = ?", (execution_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        for k in ("steps_data", "report_data"):
            if d.get(k):
                try:
                    d[k] = json.loads(d[k])
                except json.JSONDecodeError:
                    pass
        return d
