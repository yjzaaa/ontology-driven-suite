"""YAML 解析与序列化辅助"""
import re
from pathlib import Path
from typing import Any

import yaml


class _IndentDumper(yaml.SafeDumper):
    """让列表项相对父键缩进，可读性更好"""

    def increase_indent(self, flow=False, indentless=False):  # noqa: D401
        return super().increase_indent(flow, False)


def dump_yaml(data: Any) -> str:
    return yaml.dump(
        data,
        Dumper=_IndentDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )


def load_yaml(text: str) -> Any:
    return yaml.safe_load(text)


def load_yaml_file(path: Path | str) -> Any:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml_file(path: Path | str, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(dump_yaml(data))


_CODE_BLOCK_RE = re.compile(r"```(?:yaml|yml)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def extract_yaml_from_text(text: str) -> str:
    """从 LLM 输出中提取 YAML 内容。若包含 ```yaml ... ``` 代码块则只取代码块内文本"""
    if not text:
        return ""
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()
