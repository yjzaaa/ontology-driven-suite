"""DeepSeek API 客户端（基于 openai SDK 兼容接口）"""
from typing import Iterable, Iterator

from openai import OpenAI

from backend.config.settings import settings


class DeepSeekClient:
    """对 DeepSeek API 的封装。所有 phase 通过 phase_key 取配置"""

    def __init__(self):
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY.startswith("sk-xxx"):
            self._client = None
            self._api_unconfigured = True
        else:
            self._client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            )
            self._api_unconfigured = False

    def _ensure_configured(self) -> None:
        if self._api_unconfigured or self._client is None:
            raise RuntimeError(
                "DeepSeek API Key 未配置。请在项目根目录的 .env 文件中填写 DEEPSEEK_API_KEY"
            )

    def chat(
        self,
        messages: list[dict],
        phase_key: str = "phase4_chat",
        stream: bool = False,
        model_override: str | None = None,
    ):
        """非流式调用，返回完整 content 字符串"""
        self._ensure_configured()
        cfg = settings.phase_ai_config(phase_key)
        model = model_override or cfg["model"]
        resp = self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
        )
        return resp.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: list[dict],
        phase_key: str = "phase4_chat",
        model_override: str | None = None,
    ) -> Iterator[str]:
        """流式调用，逐 chunk 产出文本"""
        self._ensure_configured()
        cfg = settings.phase_ai_config(phase_key)
        model = model_override or cfg["model"]
        stream: Iterable = self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content


# 全局单例
_client_instance: DeepSeekClient | None = None


def get_client() -> DeepSeekClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = DeepSeekClient()
    return _client_instance
