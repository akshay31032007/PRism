"""
Gemini LLM wrapper.

Google Gemini supports JSON-constrained generation via
response_mime_type="application/json" and optional response_schema.
We use that path when requesting structured agent output.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.config import get_settings, LLMProvider
from .llm_factory import LLMFactory

logger = logging.getLogger("prism.llm.gemini")

T = TypeVar("T", bound=BaseModel)


class GeminiWrapper:
    """
    Wrapper around ChatGoogleGenerativeAI adding JSON enforcement
    and structured output helpers, mirroring OpenAIWrapper's interface.
    """

    def __init__(self) -> None:
        self._llm = LLMFactory.create(provider=LLMProvider.GEMINI)
        self._model_name = LLMFactory.get_model_name(LLMProvider.GEMINI)

    async def ainvoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], int, int]:
        """
        Invoke Gemini and return a parsed JSON dict.

        Gemini does not have a dedicated json_mode parameter in
        langchain-google-genai, so we instruct the model explicitly
        in the system prompt and parse robustly.

        Returns:
            (parsed_dict, prompt_tokens, completion_tokens)
        """
        json_system = (
            system_prompt
            + "\n\nIMPORTANT: Your response MUST be a single, valid JSON object. "
            "No markdown fences, no explanation text outside the JSON. "
            "Start your response with '{' and end it with '}'."
        )
        messages = [
            SystemMessage(content=json_system),
            HumanMessage(content=user_prompt),
        ]
        response = await self._llm.ainvoke(messages)

        content = response.content
        if not isinstance(content, str):
            content = str(content)

        # Strip any accidental markdown fences
        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(
                l for l in lines if not l.strip().startswith("```")
            ).strip()

        parsed = json.loads(content)

        usage    = getattr(response, "usage_metadata", {}) or {}
        p_tokens = usage.get("input_tokens",  0)
        c_tokens = usage.get("output_tokens", 0)

        return parsed, p_tokens, c_tokens

    async def ainvoke_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
    ) -> tuple[T, int, int]:
        """
        Use Gemini's native structured output (function-calling path).
        Falls back to JSON parse if structured output is unavailable.
        """
        try:
            structured_llm = self._llm.with_structured_output(output_schema)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            result = await structured_llm.ainvoke(messages)
            return result, 0, 0
        except Exception as exc:
            logger.warning(
                "Gemini structured output failed (%s), falling back to JSON parse.", exc
            )
            raw, pt, ct = await self.ainvoke_json(system_prompt, user_prompt)
            instance = output_schema.model_validate(raw)
            return instance, pt, ct

    async def ainvoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, int, int]:
        """Plain text invocation for prose-generating agents."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await self._llm.ainvoke(messages)
        usage    = getattr(response, "usage_metadata", {}) or {}
        p_tokens = usage.get("input_tokens",  0)
        c_tokens = usage.get("output_tokens", 0)
        return str(response.content), p_tokens, c_tokens

    @property
    def model_name(self) -> str:
        return self._model_name
