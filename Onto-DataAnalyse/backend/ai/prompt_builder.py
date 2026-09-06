"""Prompt 构建器：加载 prompts/ 下的模板并填充变量"""
from pathlib import Path

from backend.config.settings import settings


def load_prompt(name: str) -> str:
    """读取 prompts/{name} 文件内容"""
    p = settings.prompts_dir() / name
    if not p.exists():
        raise FileNotFoundError(f"Prompt 文件不存在：{p}")
    return p.read_text(encoding="utf-8")


def build_phase1_messages(db_schema_doc: str, requirement_doc: str) -> list[dict]:
    """阶段一：把两份上传文档塞进 system prompt，产出 messages"""
    template = load_prompt("phase1_requirement.txt")
    system = template.format(
        db_schema_doc=db_schema_doc.strip(),
        requirement_doc=requirement_doc.strip(),
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "请基于以上两份文档生成结构化需求 JSON。"},
    ]
