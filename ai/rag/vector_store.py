from langchain_core.vectorstores import VectorStore
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from ai.config import config
from ai.embeddings.wrapper import EmbeddingWrapper
from ai.settings import settings


class VectorStoreWrapper:
    @staticmethod
    def get_vector_store(collection_name: str) -> VectorStore:
        provider = config.default_vector_db
        embeddings = EmbeddingWrapper.get_embeddings()

        if provider == "qdrant":
            # Using in-memory or local if URL is not set for simpler execution,
            # but usually it connects to Qdrant Cloud / Docker.
            url = settings.QDRANT_URL
            api_key = settings.QDRANT_API_KEY

            if url:
                client = QdrantClient(url=url, api_key=api_key)
            else:
                client = QdrantClient(path="local_qdrant")

            return QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
            )
        else:
            raise ValueError(f"Unsupported Vector Store provider: {provider}")
