from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from ai.config import config
from ai.settings import settings


class LLMWrapper:
    @staticmethod
    def get_llm(provider: str = None, model_name: str = None) -> BaseChatModel:
        provider = provider or config.default_llm_provider

        if provider == "openai":
            return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=model_name or "gpt-4o")
        elif provider == "anthropic":
            return ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY, model=model_name or "claude-3-opus-20240229"
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY, model=model_name or "gemini-1.5-pro"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
