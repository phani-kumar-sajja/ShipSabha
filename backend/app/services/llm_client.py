"""
Thin wrapper around the Anthropic API.

Every agent in this system (domain validator, planner, literature agent,
etc.) should call the LLM through this module rather than importing the
SDK directly, so retry/timeout/error behavior and prompt-logging stay in
one place.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import anthropic

from app.core.config import get_settings

logger = logging.getLogger("research_assistant.llm")


class LLMError(RuntimeError):
    """Raised when the LLM call fails or returns an unusable response."""


class LLMClient:
    def __init__(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            logger.warning(
                "ANTHROPIC_API_KEY is not set. LLM-backed agents will raise "
                "LLMError until it is configured (see .env.example)."
            )
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or None)
        self._model = settings.anthropic_model

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Call the model and parse a strict-JSON response.

        Raises LLMError on any transport failure or on unparsable output,
        so callers can record the failure in research state (Section 22)
        instead of silently proceeding on a bad/empty result.
        """
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            raise LLMError(f"Anthropic API call failed: {exc}") from exc

        text_parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        raw_text = "".join(text_parts).strip()

        cleaned = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model did not return valid JSON: {exc}. Raw output: {raw_text[:500]}") from exc


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
