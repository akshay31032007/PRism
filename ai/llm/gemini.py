"""
Gemini LLM wrapper — calls the Google Generative AI SDK directly.

Uses google-generativeai (the official SDK) rather than langchain-google-genai
for maximum compatibility. This avoids event-loop issues on Windows/Python 3.10
that occur with the langchain wrapper's async path.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.config import get_settings

logger = logging.getLogger("prism.llm.gemini")

T = TypeVar("T", bound=BaseModel)


def _get_client():
    """Build a configured GenerativeModel client."""
    import google.generativeai as genai  # type: ignore
    settings = get_settings()
    key = settings.google_api_key
    if not key:
        raise ValueError("GOOGLE_API_KEY is not set in backend/.env")
    genai.configure(api_key=key.get_secret_value())
    return genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={
            "temperature":     settings.llm_temperature,
            "max_output_tokens": settings.llm_max_tokens,
        },
    )


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        return fence.group(1).strip()
    if not text.startswith("{"):
        m = re.search(r"(\{[\s\S]*\})", text)
        if m:
            return m.group(1)
    return text


class GeminiWrapper:
    """
    Thin async wrapper around the Google Generative AI SDK.

    Exposes the same interface as OpenAIWrapper / _UniversalLLMWrapper
    so agents never need to know which provider is active.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._model_name = settings.gemini_model

    async def ainvoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], int, int]:
        """
        Invoke Gemini and return (parsed_dict, prompt_tokens, completion_tokens).
        Enforces JSON output via explicit instructions.
        """
        import asyncio

        combined = (
            system_prompt
            + "\n\nCRITICAL INSTRUCTION: Your response MUST be a single valid JSON object. "
            "Do not wrap it in markdown code fences. "
            "Do not include any text before or after the JSON. "
            "Start your response with '{' and end it with '}'.\n\n"
            + user_prompt
        )

        loop = asyncio.get_event_loop()
        model = _get_client()

        def _call():
            return model.generate_content(combined)

        response = await loop.run_in_executor(None, _call)
        raw_text = response.text.strip() if response.text else "{}"

        raw_text = _strip_fences(raw_text)

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            # Last resort: try to extract any JSON object
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if m:
                parsed = json.loads(m.group(0))
            else:
                raise ValueError(
                    f"Gemini returned non-JSON output: {raw_text[:200]}"
                )

        # Extract token usage if available
        p_tokens = 0
        c_tokens = 0
        try:
            usage = response.usage_metadata
            if usage:
                p_tokens = getattr(usage, "prompt_token_count",     0) or 0
                c_tokens = getattr(usage, "candidates_token_count", 0) or 0
        except Exception:
            pass

        return parsed, p_tokens, c_tokens

    async def ainvoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, int, int]:
        """Plain text invocation — returns the raw response string."""
        import asyncio

        combined = system_prompt + "\n\n" + user_prompt
        loop  = asyncio.get_event_loop()
        model = _get_client()

        def _call():
            return model.generate_content(combined)

        response = await loop.run_in_executor(None, _call)
        text = response.text or ""

        p_tokens = 0
        c_tokens = 0
        try:
            usage = response.usage_metadata
            if usage:
                p_tokens = getattr(usage, "prompt_token_count",     0) or 0
                c_tokens = getattr(usage, "candidates_token_count", 0) or 0
        except Exception:
            pass

        return text, p_tokens, c_tokens

    @property
    def model_name(self) -> str:
        return self._model_name
