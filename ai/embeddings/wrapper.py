from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from ai.config import config
from ai.settings import settings


class EmbeddingWrapper:
    @staticmethod
    def get_embeddings(provider: str = None, model_name: str = None) -> Embeddings:
        provider = provider or config.default_embedding_provider

        if provider == "openai":
            return OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY, model=model_name or "text-embedding-3-small"
            )
        else:
            raise ValueError(f"Unsupported Embeddings provider: {provider}")
