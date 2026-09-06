"""本体引擎：YAML 文件管理 + Schema 校验"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.config.settings import settings
from backend.utils.yaml_utils import dump_yaml, extract_yaml_from_text, load_yaml

# 五个本体模型的文件名约定
MODEL_FILES = {
    "M1": "m1_object_model.yaml",
    "M2": "m2_behavior_model.yaml",
    "M3": "m3_rule_model.yaml",
    "M4": "m4_scenario_model.yaml",
    "M_Metric": "m_metric_model.yaml",
}

MODEL_TYPE_EXPECTED = {
    "M1": "OBJECT",
    "M2": "BEHAVIOR",
    "M3": "RULE",
    "M4": "SCENARIO",
    "M_Metric": "METRIC",
}

# 每个模型的根集合字段名
MODEL_ROOT_KEY = {
    "M1": "entities",
    "M2": "behaviors",
    "M3": "rules",
    "M4": "scenarios",
    "M_Metric": "metrics",
}


def model_file_path(model_key: str) -> Path:
    fname = MODEL_FILES[model_key]
    return settings.project_models_dir() / fname


def save_model_yaml(model_key: str, data: dict) -> Path:
    """把模型 dict 写入磁盘并返回路径"""
    p = model_file_path(model_key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_yaml(data), encoding="utf-8")
    return p


def load_model_yaml(model_key: str) -> dict | None:
    p = model_file_path(model_key)
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def load_all_models() -> dict[str, dict]:
    """加载已存在的所有模型，缺失则跳过"""
    result = {}
    for k in MODEL_FILES:
        d = load_model_yaml(k)
        if d is not None:
            result[k] = d
    return result


class ValidationError(Exception):
    """YAML 校验错误"""


def validate_model_yaml(model_key: str, text: str) -> tuple[dict, list[str]]:
    """
    解析并校验 YAML 文本。
    返回 (parsed_dict, warnings)。结构性错误抛 ValidationError。
    """
    raw = extract_yaml_from_text(text)
    try:
        data = load_yaml(raw)
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML 解析失败：{e}") from e

    if not isinstance(data, dict):
        raise ValidationError("根节点必须是 dict")

    warnings: list[str] = []

    # 1. model_type 校验
    expected_type = MODEL_TYPE_EXPECTED[model_key]
    actual_type = data.get("model_type")
    if actual_type != expected_type:
        # 允许小写、大小写不一致
        if isinstance(actual_type, str) and actual_type.upper() == expected_type:
            data["model_type"] = expected_type
        else:
            raise ValidationError(
                f"model_type 应为 '{expected_type}'，实际为 '{actual_type}'"
            )

    # 2. 根集合校验
    root_key = MODEL_ROOT_KEY[model_key]
    root_list = data.get(root_key)
    if not isinstance(root_list, list) or len(root_list) == 0:
        raise ValidationError(f"缺失或为空的根集合字段 '{root_key}'")

    # 3. 各模型最小完整性校验
    _validate_specific(model_key, data, warnings)

    return data, warnings


def _validate_specific(model_key: str, data: dict, warnings: list[str]) -> None:
    if model_key == "M1":
        entities = data.get("entities", [])
        if len(entities) < 8:
            warnings.append(f"实体数量较少（{len(entities)} 个），建议至少 12 个")
        for ent in entities:
            if not ent.get("id") or not ent.get("name"):
                raise ValidationError(f"实体缺少 id 或 name：{ent}")
            if not isinstance(ent.get("attributes"), list):
                raise ValidationError(f"实体 {ent.get('id')} 缺少 attributes 列表")
        relations = data.get("relations", [])
        if len(relations) < 5:
            warnings.append(f"关系数量较少（{len(relations)} 条），建议至少 10 条")
        for rel in relations:
            for k in ("id", "type", "sourceEntity", "targetEntity"):
                if not rel.get(k):
                    raise ValidationError(f"关系缺少字段 {k}：{rel}")

    elif model_key == "M2":
        behaviors = data.get("behaviors", [])
        if len(behaviors) < 5:
            warnings.append(f"行为数量较少（{len(behaviors)} 个）")
        for b in behaviors:
            for k in ("id", "name", "computationType"):
                if not b.get(k):
                    raise ValidationError(f"行为缺少字段 {k}：{b.get('id')}")

    elif model_key == "M3":
        rules = data.get("rules", [])
        if len(rules) < 5:
            warnings.append(f"规则数量较少（{len(rules)} 条）")
        for r in rules:
            for k in ("id", "name", "ruleType"):
                if not r.get(k):
                    raise ValidationError(f"规则缺少字段 {k}：{r.get('id')}")

    elif model_key == "M4":
        scenarios = data.get("scenarios", [])
        if len(scenarios) < 1:
            raise ValidationError("场景数量不能为 0")
        for s in scenarios:
            for k in ("id", "name"):
                if not s.get(k):
                    raise ValidationError(f"场景缺少字段 {k}：{s.get('id')}")

    elif model_key == "M_Metric":
        metrics = data.get("metrics", [])
        if len(metrics) < 10:
            warnings.append(f"指标数量较少（{len(metrics)} 个），建议至少 20 个")
        for m in metrics:
            for k in ("id", "name", "computation_type"):
                if not m.get(k):
                    raise ValidationError(f"指标缺少字段 {k}：{m.get('id')}")


def model_summary(data: dict, model_key: str) -> dict:
    """返回模型简要摘要（用于前端进度面板）"""
    root_key = MODEL_ROOT_KEY[model_key]
    items = data.get(root_key, [])
    summary = {"model_key": model_key, "count": len(items)}
    if model_key == "M1":
        summary["relations"] = len(data.get("relations", []))
    return summary
