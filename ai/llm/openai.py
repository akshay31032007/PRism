"""
OpenAI LLM wrapper with JSON-mode enforcement and structured output parsing.

This module wraps langchain_openai.ChatOpenAI to add:
  - Guaranteed JSON responses via response_format={"type": "json_object"}
  - Pydantic model parsing via .with_structured_output()
  - Automatic system prompt injection
  - Token usage extraction from raw API responses
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration
from pydantic import BaseModel

from backend.config import get_settings
from .llm_factory import LLMFactory
from backend.config import LLMProvider

logger = logging.getLogger("prism.llm.openai")

T = TypeVar("T", bound=BaseModel)


class OpenAIWrapper:
    """
    Thin wrapper around ChatOpenAI that agents use directly.

    Features:
    - ainvoke_json(): returns parsed dict (JSON mode guaranteed)
    - ainvoke_structured(): returns typed Pydantic model via structured output
    - Records token usage from response metadata
    """

    def __init__(self) -> None:
        self._llm = LLMFactory.create(provider=LLMProvider.OPENAI)
        self._model_name = LLMFactory.get_model_name(LLMProvider.OPENAI)

    async def ainvoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], int, int]:
        """
        Invoke the model and parse the response as JSON.

        Returns:
            (parsed_dict, prompt_tokens, completion_tokens)

        Raises:
            json.JSONDecodeError: If the model returns non-JSON (should be rare with json_mode).
            RuntimeError: If the API call itself fails.
        """
        from langchain_openai import ChatOpenAI
        settings = get_settings()
        key = settings.openai_api_key
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set.")

        # Use JSON mode at the SDK level for guaranteed valid JSON output
        llm_json = ChatOpenAI(
            model=self._model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=key.get_secret_value(),
            model_kwargs={"response_format": {"type": "json_object"}},
            max_retries=0,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await llm_json.ainvoke(messages)

        # Extract token counts from response metadata
        usage    = getattr(response, "usage_metadata", {}) or {}
        p_tokens = usage.get("input_tokens",  0)
        c_tokens = usage.get("output_tokens", 0)

        content = response.content
        if not isinstance(content, str):
            content = str(content)

        parsed = json.loads(content)
        return parsed, p_tokens, c_tokens

    async def ainvoke_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
    ) -> tuple[T, int, int]:
        """
        Invoke the model with function-calling structured output.

        Returns:
            (pydantic_instance, prompt_tokens, completion_tokens)
        """
        structured_llm = self._llm.with_structured_output(output_schema)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        result = await structured_llm.ainvoke(messages)
        # Token counts unavailable in structured output path — return 0s
        return result, 0, 0

    async def ainvoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, int, int]:
        """
        Plain text invocation — returns the raw string response.
        Used by the documentation/summary agents that produce markdown prose.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await self._llm.ainvoke(messages)
        usage    = getattr(response, "usage_metadata", {}) or {}
        p_tokens = usage.get("input_tokens",  0)
        c_tokens = usage.get("output_tokens", 0)
        content  = response.content
        return str(content), p_tokens, c_tokens

    @property
    def model_name(self) -> str:
        return self._model_name
