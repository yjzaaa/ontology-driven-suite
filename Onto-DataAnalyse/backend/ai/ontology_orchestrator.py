"""阶段二 AI 编排器：

- 按顺序生成 5 个本体 YAML（M1 → M3 → M_Metric → M2 → M4）
- 每次生成后用 ontology_engine 校验；失败带错误提示让 LLM 自修复，最多重试 2 次
- 每个模型成功后立即推送 SSE 事件，前端实时构建知识图谱
- 5 个模型完成后再生成本体→数据库映射配置（同样的校验+重试）

SSE 消息类型：
  {"type":"phase","phase":"M1"|"M2"|...,"status":"start"}
  {"type":"phase_delta","phase":"M1","delta":"...片段..."}        # LLM 流式输出
  {"type":"phase_retry","phase":"M1","attempt":1,"reason":"..."} # 校验失败重试
  {"type":"phase_done","phase":"M1","summary":{...},"warnings":[...]}
  {"type":"graph_delta","added_nodes":[...],"added_edges":[...]} # 图谱增量
  {"type":"mapping_ready","stats":{...}}
  {"type":"error","message":"..."}
  {"type":"done"}
"""
from __future__ import annotations

import json
from typing import Iterator

from backend.ai.deepseek_client import get_client
from backend.ai.prompt_builder import load_prompt
from backend.config.settings import settings
from backend.core import graph_builder, mapping_engine, ontology_engine
from backend.db.database import system_db
from backend.utils.sse_utils import sse_pack_raw
from backend.utils.yaml_utils import extract_yaml_from_text

GENERATION_ORDER = ["M1", "M3", "M_Metric", "M2", "M4"]


def _get_project_inputs() -> tuple[str, str, dict | None]:
    """从数据库读取阶段一的产物（DB schema 文本 + 解析后的需求 JSON）"""
    with system_db() as conn:
        row = conn.execute(
            "SELECT db_schema_doc, requirement_doc_parsed FROM projects WHERE id = ?",
            (settings.PROJECT_ID,),
        ).fetchone()
        if not row:
            return "", "", None
        parsed = None
        if row["requirement_doc_parsed"]:
            try:
                parsed = json.loads(row["requirement_doc_parsed"])
            except (TypeError, json.JSONDecodeError):
                parsed = None
        return row["db_schema_doc"] or "", "", parsed


def _build_prompt(target_model: str, ontology_spec: str, db_schema: str,
                  parsed_req: dict | None, prior_models: dict[str, dict]) -> list[dict]:
    template = load_prompt("phase2_ontology.txt")
    # 把已有模型 dump 成简短 YAML（仅 ID/name 列表，避免 prompt 过长）
    prior_yaml = _summarize_prior_models(prior_models)
    system = template.format(
        target_model=target_model,
        ontology_spec=ontology_spec,
        db_schema_doc=db_schema.strip(),
        parsed_requirement_json=json.dumps(parsed_req or {}, ensure_ascii=False, indent=2),
        prior_models_yaml=prior_yaml or "（暂无）",
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"请生成 {target_model} 的完整 YAML 内容。"},
    ]


def _summarize_prior_models(prior_models: dict[str, dict]) -> str:
    """把已生成的模型转为精简清单：ID + name + (主要字段)，避免 prompt 过长"""
    if not prior_models:
        return ""
    out: list[str] = []
    if "M1" in prior_models:
        ents = prior_models["M1"].get("entities", [])
        out.append("# M1 已生成的实体（ID 列表，用于关系引用）")
        for e in ents:
            out.append(f"- {e.get('id')}: {e.get('name')} ({e.get('alias')})")
        rels = prior_models["M1"].get("relations", [])
        out.append(f"\n# M1 已有关系数: {len(rels)}")
    if "M3" in prior_models:
        out.append("\n# M3 已生成的规则 ID")
        for r in prior_models["M3"].get("rules", []):
            out.append(f"- {r.get('id')}: {r.get('name')}")
    if "M_Metric" in prior_models:
        out.append("\n# M_Metric 已生成的指标 ID")
        for m in prior_models["M_Metric"].get("metrics", []):
            out.append(f"- {m.get('id')}: {m.get('name')} ({m.get('computation_type')})")
    if "M2" in prior_models:
        out.append("\n# M2 已生成的行为 ID")
        for b in prior_models["M2"].get("behaviors", []):
            out.append(f"- {b.get('id')}: {b.get('name')}")
    return "\n".join(out)


# ============================================================
# 主流程：生成器（被 Flask SSE 路由消费）
# ============================================================
def orchestrate_ontology_generation() -> Iterator[str]:
    """整个阶段二的编排流程，逐条 yield SSE 消息字符串"""
    db_schema, _, parsed_req = _get_project_inputs()
    if not db_schema:
        yield sse_pack_raw({"type": "error", "message": "请先完成阶段一（上传 Schema + 需求）"})
        return
    if not parsed_req:
        yield sse_pack_raw({"type": "error", "message": "请先完成阶段一的 AI 需求解析"})
        return

    ontology_spec = load_prompt("ontology_spec.md")
    client = get_client()
    prior_models: dict[str, dict] = {}
    existing_node_ids: set[str] = set()

    for target in GENERATION_ORDER:
        yield sse_pack_raw({"type": "phase", "phase": target, "status": "start"})

        success = False
        last_error = ""
        full_text = ""
        for attempt in range(settings.AI_YAML_MAX_RETRIES + 1):
            full_text = ""
            messages = _build_prompt(target, ontology_spec, db_schema, parsed_req, prior_models)
            if attempt > 0:
                messages.append({
                    "role": "user",
                    "content": (
                        f"上次输出 YAML 校验失败，错误：{last_error}\n"
                        "请修正后**完整重新输出**符合规范的 YAML，不要解释、不要 Markdown 代码块包裹。"
                    ),
                })
                yield sse_pack_raw({
                    "type": "phase_retry", "phase": target,
                    "attempt": attempt, "reason": last_error[:200],
                })

            try:
                for chunk in client.chat_stream(messages, phase_key="phase2_ontology"):
                    full_text += chunk
                    yield sse_pack_raw({"type": "phase_delta", "phase": target, "delta": chunk})
            except Exception as e:
                yield sse_pack_raw({"type": "error", "message": f"LLM 调用失败：{e}"})
                return

            try:
                data, warnings = ontology_engine.validate_model_yaml(target, full_text)
            except ontology_engine.ValidationError as e:
                last_error = str(e)
                if attempt < settings.AI_YAML_MAX_RETRIES:
                    continue
                # 重试耗尽
                yield sse_pack_raw({
                    "type": "error",
                    "message": f"{target} 生成 {settings.AI_YAML_MAX_RETRIES + 1} 次仍校验失败：{last_error}",
                    "phase": target,
                })
                return

            # 校验通过：落盘 + 推图谱增量
            ontology_engine.save_model_yaml(target, data)
            prior_models[target] = data
            summary = ontology_engine.model_summary(data, target)
            yield sse_pack_raw({
                "type": "phase_done", "phase": target,
                "summary": summary, "warnings": warnings,
            })
            # 图谱增量
            delta = graph_builder.build_graph_delta(target, data, existing_node_ids)
            for n in delta["nodes"]:
                existing_node_ids.add(n["id"])
            yield sse_pack_raw({
                "type": "graph_delta",
                "phase": target,
                "added_nodes": delta["nodes"],
                "added_edges": delta["edges"],
            })

            # 把 ontology 摘要同步到系统库
            _persist_ontology_summary(prior_models)

            success = True
            break

        if not success:
            return

    # 5 个模型都好了，开始生成本体→数据库映射
    yield from _generate_mapping(db_schema, prior_models)
    yield sse_pack_raw({"type": "done"})


MAPPING_BATCH_SIZE = 3   # 每批映射几个实体（控制 LLM 单次输出长度 → 避免被截断）


def _generate_mapping(db_schema: str, prior_models: dict) -> Iterator[str]:
    """
    分批生成映射（核心修复）：

    - 把 M1 的全部实体按 MAPPING_BATCH_SIZE 切分
    - 每批独立调用 LLM 生成 entity_mappings 片段
    - 单批失败重试 2 次；仍失败则该批跳过（不阻塞整体）
    - 全部完成后合并并整体校验

    分批可以让单次 LLM 输出 ≤ 8K tokens，避开 DeepSeek 8192 上限导致的截断。
    """
    yield sse_pack_raw({"type": "phase", "phase": "mapping", "status": "start"})
    if "M1" not in prior_models:
        yield sse_pack_raw({"type": "error", "message": "M1 缺失，无法生成映射"})
        return

    m1 = prior_models["M1"]
    entities = m1.get("entities", []) or []
    if not entities:
        yield sse_pack_raw({"type": "error", "message": "M1 中没有实体，无法生成映射"})
        return

    client = get_client()
    template = load_prompt("phase2_mapping.txt")
    from backend.utils.yaml_utils import dump_yaml

    # 把实体切分成批次
    batches = [entities[i:i + MAPPING_BATCH_SIZE] for i in range(0, len(entities), MAPPING_BATCH_SIZE)]
    total_batches = len(batches)
    yield sse_pack_raw({
        "type": "mapping_plan",
        "total_entities": len(entities),
        "total_batches": total_batches,
        "batch_size": MAPPING_BATCH_SIZE,
    })

    all_entity_mappings: list[dict] = []
    skipped_entities: list[str] = []

    for batch_idx, batch in enumerate(batches):
        batch_ids = [e.get("id") for e in batch]
        yield sse_pack_raw({
            "type": "mapping_batch_start",
            "batch_idx": batch_idx + 1,
            "total_batches": total_batches,
            "entity_ids": batch_ids,
        })

        # 只把这一批的实体喂给 LLM
        batch_yaml = dump_yaml({"entities": batch})
        system = template.format(
            db_schema_doc=db_schema[:7000],     # schema 也截一下避免重复占用
            entities_yaml=batch_yaml,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"请为以上 {len(batch)} 个实体生成映射 JSON。"},
        ]

        success = False
        last_error = ""
        full_text = ""

        for attempt in range(settings.AI_YAML_MAX_RETRIES + 1):
            full_text = ""
            msgs = list(messages)
            if attempt > 0:
                msgs.append({
                    "role": "user",
                    "content": (
                        f"上次输出有问题：{last_error}\n"
                        "请重新只输出纯 JSON（不要 ```code block``` 包裹，不要解释），确保 JSON 完整闭合。"
                    ),
                })
                yield sse_pack_raw({
                    "type": "phase_retry", "phase": "mapping",
                    "batch_idx": batch_idx + 1, "attempt": attempt,
                    "reason": last_error[:200],
                })

            try:
                for chunk in client.chat_stream(msgs, phase_key="phase2_ontology"):
                    full_text += chunk
                    yield sse_pack_raw({
                        "type": "phase_delta", "phase": "mapping",
                        "batch_idx": batch_idx + 1, "delta": chunk,
                    })
            except Exception as e:
                last_error = f"LLM 调用失败：{e}"
                continue

            # 完整性快速检查：括号是否平衡
            if not _is_balanced_json_brackets(full_text):
                last_error = f"输出被截断（括号不平衡，{len(full_text)} 字）"
                if attempt < settings.AI_YAML_MAX_RETRIES:
                    continue

            parsed = _try_parse_json(full_text)
            if parsed is None:
                last_error = f"AI 输出无法解析为 JSON（{len(full_text)} 字）"
                if attempt < settings.AI_YAML_MAX_RETRIES:
                    continue
                break

            batch_mappings = parsed.get("entity_mappings") or []
            if not batch_mappings:
                last_error = "返回的 JSON 中 entity_mappings 为空"
                if attempt < settings.AI_YAML_MAX_RETRIES:
                    continue
                break

            # 批内校验：每个实体映射至少有 1 个主表 + 1 个字段映射
            valid_mappings = []
            for em in batch_mappings:
                if not em.get("entity_id"):
                    continue
                tables = em.get("tables") or []
                if not any(t.get("primary") for t in tables):
                    continue
                if not em.get("field_mappings"):
                    continue
                valid_mappings.append(em)

            if not valid_mappings:
                last_error = "本批所有实体映射都不符合最小结构要求"
                if attempt < settings.AI_YAML_MAX_RETRIES:
                    continue
                break

            all_entity_mappings.extend(valid_mappings)
            yield sse_pack_raw({
                "type": "mapping_batch_done",
                "batch_idx": batch_idx + 1,
                "mapped_count": len(valid_mappings),
                "entity_ids": [em["entity_id"] for em in valid_mappings],
            })
            success = True
            break

        if not success:
            # 单批彻底失败：记录但继续其他批次
            skipped_entities.extend(batch_ids)
            yield sse_pack_raw({
                "type": "mapping_batch_failed",
                "batch_idx": batch_idx + 1,
                "entity_ids": batch_ids,
                "reason": last_error[:200],
            })

    if not all_entity_mappings:
        yield sse_pack_raw({
            "type": "error", "phase": "mapping",
            "message": f"所有批次都失败，未能生成任何映射。最后错误：{last_error}",
        })
        return

    # 合并为最终 mapping
    final_mapping = {
        "version": "1.0",
        "source_db": {
            "type": "SQLite",
            "schema": "ecommerce",
            "timezone": "Asia/Shanghai",
        },
        "entity_mappings": all_entity_mappings,
    }
    ok, err = mapping_engine.validate_mapping(final_mapping)
    if not ok:
        yield sse_pack_raw({
            "type": "error", "phase": "mapping",
            "message": f"合并后的映射校验失败：{err}",
        })
        return

    mapping_engine.save_mapping(final_mapping)
    viz = mapping_engine.build_mapping_visualization(final_mapping, m1)
    yield sse_pack_raw({
        "type": "mapping_ready",
        "stats": {**viz["stats"], "skipped_entities": skipped_entities},
    })


def _is_balanced_json_brackets(text: str) -> bool:
    """快速检查 JSON 的 {} [] 是否平衡（避免被截断的 JSON 进入慢速解析）"""
    if not text or not text.strip():
        return False
    # 忽略字符串内的括号（简化处理：用栈 + 引号状态）
    open_curly = 0
    open_square = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            open_curly += 1
        elif ch == "}":
            open_curly -= 1
            if open_curly < 0:
                return False
        elif ch == "[":
            open_square += 1
        elif ch == "]":
            open_square -= 1
            if open_square < 0:
                return False
    return open_curly == 0 and open_square == 0


def _try_parse_json(text: str) -> dict | None:
    text = text.strip()
    # 去除可能的代码块包裹
    if text.startswith("```"):
        # 简单去掉 fence
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        l = text.find("{")
        r = text.rfind("}")
        if l == -1 or r == -1 or r <= l:
            return None
        try:
            return json.loads(text[l : r + 1])
        except json.JSONDecodeError:
            return None


def _persist_ontology_summary(prior_models: dict) -> None:
    """把每个模型的摘要存到 projects.ontology_data 字段"""
    summary = {
        k: {
            "count": len(v.get(ontology_engine.MODEL_ROOT_KEY[k], [])),
            "relation_count": len(v.get("relations", [])) if k == "M1" else None,
        }
        for k, v in prior_models.items()
    }
    with system_db() as conn:
        conn.execute(
            "UPDATE projects SET ontology_data = ? WHERE id = ?",
            (json.dumps(summary, ensure_ascii=False), settings.PROJECT_ID),
        )
