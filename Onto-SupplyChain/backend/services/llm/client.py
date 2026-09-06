from __future__ import annotations

import json
import logging
from typing import Any

import requests

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TEMPERATURE,
    DEEPSEEK_TIMEOUT,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是供应链ATP交期承诺分析助手。
你不会重新做数值计算，只基于给定的结构化ATP分析结果生成业务解释。
必须输出JSON对象，不要输出markdown代码块。
JSON字段必须包含:
recommended_commitment_type, recommended_date, confidence_score, risk_level,
reason_chain, impact_objects, alternatives, user_facing_reply, follow_up_questions
"""


class DeepSeekClient:
    def __init__(self) -> None:
        self.base_url = DEEPSEEK_BASE_URL.rstrip("/")
        self.api_key = DEEPSEEK_API_KEY
        self.model = DEEPSEEK_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _fallback_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        recommendation = payload["atp_summary"]["recommended"]
        return {
            "recommended_commitment_type": recommendation["commitment_type"],
            "recommended_date": recommendation["committed_date"],
            "confidence_score": recommendation["confidence_score"],
            "risk_level": recommendation["risk_level"],
            "reason_chain": recommendation["reason_chain"],
            "impact_objects": recommendation["impact_objects"],
            "alternatives": payload["atp_summary"]["alternatives"],
            "user_facing_reply": recommendation["narrative"],
            "follow_up_questions": payload["suggested_questions"],
            "llm_mode": "fallback",
        }

    def generate_atp_explanation(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured():
            logger.warning("[LLM] 未配置 API Key，使用回退模式（无真实 LLM 调用）")
            return self._fallback_response(payload)

        user_content = json.dumps(payload, ensure_ascii=False, indent=2)
        url = f"{self.base_url}/chat/completions"
        req_body = {
            "model": self.model,
            "temperature": DEEPSEEK_TEMPERATURE,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        logger.info(
            "[LLM] 真实调用开始 url=%s model=%s api_key=%s...",
            url, self.model, (self.api_key[:6] or "")
        )
        try:
            response = requests.post(
                url,
                headers=headers,
                json=req_body,
                timeout=DEEPSEEK_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed["llm_mode"] = "deepseek"
            usage = data.get("usage", {})
            logger.info(
                "[LLM] 调用成功 http=%s model=%s tokens=in:%s/out:%s/total:%s llm_mode=deepseek",
                response.status_code,
                data.get("model"),
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                usage.get("total_tokens"),
            )
            return parsed
        except Exception as exc:
            logger.warning("[LLM] 调用失败 type=%s err=%s，降级为回退模式", type(exc).__name__, exc)
            fallback = self._fallback_response(payload)
            fallback["llm_error"] = str(exc)
            return fallback
