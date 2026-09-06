from __future__ import annotations

from typing import Any

import requests
from flask import current_app


class DeepSeekClient:
    def __init__(self):
        settings = current_app.config["APP_SETTINGS"]["ai"]
        self.base_url = settings["base_url"].rstrip("/")
        self.api_key = settings["api_key"]
        self.model = settings["model"]
        self.timeout = settings["request_timeout_seconds"]
        self.temperature = settings["temperature"]

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and "YOUR_DEEPSEEK_API_KEY" not in self.api_key

    def chat_completion(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None):
        if not self.enabled:
            raise RuntimeError("DeepSeek API Key 未配置")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]
