"""
LLMFactory — single entry point for constructing any supported LLM.

Usage:
    llm = LLMFactory.create()                        # uses DEFAULT_LLM_PROVIDER
    llm = LLMFactory.create(provider=LLMProvider.OPENAI)
    response = await llm.ainvoke("your prompt")

The factory never touches API keys directly — it reads from Settings,
which reads from .env.  Nothing is hardcoded.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel

from backend.config import LLMProvider, get_settings

logger = logging.getLogger("prism.llm.factory")


class LLMFactory:
    """
    Creates fully-configured LangChain chat model instances.

    Provider instantiation is deferred until first call so that
    missing keys only raise at construction time, not at import time.
    """

    @staticmethod
    def create(
        provider: Optional[LLMProvider] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
    ) -> BaseChatModel:
        """
        Return a configured LangChain BaseChatModel.

        Args:
            provider:    Override the default provider from Settings.
            temperature: Override the default temperature.
            max_tokens:  Override the default max_tokens.
            streaming:   Enable token streaming (for future UI use).

        Returns:
            A provider-specific BaseChatModel ready for ainvoke/invoke.

        Raises:
            ValueError: If the provider is unknown or its key is missing.
        """
        settings = get_settings()
        active_provider = provider or settings.default_llm_provider
        temp  = temperature if temperature is not None else settings.llm_temperature
        maxtk = max_tokens  if max_tokens  is not None else settings.llm_max_tokens

        logger.debug("Creating LLM: provider=%s temp=%s", active_provider.value, temp)

        builders = {
            LLMProvider.OPENAI:     lambda: LLMFactory._build_openai(temp, maxtk, streaming),
            LLMProvider.ANTHROPIC:  lambda: LLMFactory._build_anthropic(temp, maxtk, streaming),
            LLMProvider.GEMINI:     lambda: LLMFactory._build_gemini(temp, maxtk, streaming),
            LLMProvider.GROQ:       lambda: LLMFactory._build_groq(temp, maxtk, streaming),
            LLMProvider.OPENROUTER: lambda: LLMFactory._build_openrouter(temp, maxtk, streaming),
            LLMProvider.AZURE:      lambda: LLMFactory._build_azure(temp, maxtk, streaming),
            LLMProvider.OLLAMA:     lambda: LLMFactory._build_ollama(temp, maxtk, streaming),
        }

        builder = builders.get(active_provider)
        if builder is None:
            raise ValueError(
                f"Unknown LLM provider: '{active_provider}'. "
                f"Valid options: {[p.value for p in LLMProvider]}"
            )

        return builder()

    # ── Provider builders ─────────────────────────────────────────────────────

    @staticmethod
    def _build_openai(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        settings = get_settings()
        key = settings.openai_api_key
        if not key:
            raise ValueError("OPENAI_API_KEY is not set in .env")
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=temp,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=key.get_secret_value(),
            timeout=settings.llm_timeout_secs,
            max_retries=0,  # Retries handled by our tenacity wrapper
        )

    @staticmethod
    def _build_anthropic(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic
        settings = get_settings()
        key = settings.anthropic_api_key
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=temp,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=key.get_secret_value(),
            timeout=settings.llm_timeout_secs,
            max_retries=0,
        )

    @staticmethod
    def _build_gemini(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        settings = get_settings()
        key = settings.google_api_key
        if not key:
            raise ValueError("GOOGLE_API_KEY is not set in .env")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=temp,
            max_output_tokens=max_tokens,
            streaming=streaming,
            google_api_key=key.get_secret_value(),
        )

    @staticmethod
    def _build_groq(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_groq import ChatGroq  # type: ignore[import-untyped]
        settings = get_settings()
        key = settings.groq_api_key
        if not key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        return ChatGroq(
            model=settings.groq_model,
            temperature=temp,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=key.get_secret_value(),
            timeout=settings.llm_timeout_secs,
            max_retries=0,
        )

    @staticmethod
    def _build_openrouter(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        settings = get_settings()
        key = settings.openrouter_api_key
        if not key:
            raise ValueError("OPENROUTER_API_KEY is not set in .env")
        return ChatOpenAI(
            model="openai/gpt-4o",          # Default; override via env if needed
            temperature=temp,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=key.get_secret_value(),
            base_url="https://openrouter.ai/api/v1",
            timeout=settings.llm_timeout_secs,
            max_retries=0,
        )

    @staticmethod
    def _build_azure(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_openai import AzureChatOpenAI
        settings = get_settings()
        key      = settings.azure_openai_api_key
        endpoint = settings.azure_openai_endpoint
        if not key or not endpoint:
            raise ValueError(
                "Both AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set."
            )
        return AzureChatOpenAI(
            azure_deployment=settings.openai_model,
            azure_endpoint=endpoint,
            api_version="2024-10-21",
            temperature=temp,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=key.get_secret_value(),
            timeout=settings.llm_timeout_secs,
            max_retries=0,
        )

    @staticmethod
    def _build_ollama(temp: float, max_tokens: int, streaming: bool) -> BaseChatModel:
        from langchain_community.chat_models import ChatOllama  # type: ignore[import-untyped]
        return ChatOllama(
            model="llama3.2",          # Override with OLLAMA_MODEL in env if needed
            temperature=temp,
            num_predict=max_tokens,
        )

    @staticmethod
    def get_model_name(provider: Optional[LLMProvider] = None) -> str:
        """Return the configured model name string for the given provider."""
        settings = get_settings()
        p = provider or settings.default_llm_provider
        mapping = {
            LLMProvider.OPENAI:     settings.openai_model,
            LLMProvider.ANTHROPIC:  settings.anthropic_model,
            LLMProvider.GEMINI:     settings.gemini_model,
            LLMProvider.GROQ:       settings.groq_model,
            LLMProvider.OPENROUTER: "openai/gpt-4o",
            LLMProvider.AZURE:      settings.openai_model,
            LLMProvider.OLLAMA:     "llama3.2",
        }
        return mapping.get(p, "unknown")
