"""
Embeddings factory and wrapper.

Supports:
  - OpenAI text-embedding-3-small / large
  - Sentence Transformers (local, no API key needed)
  - Voyage AI
  - Jina AI

All providers expose the same interface:
    embed_texts(texts: list[str]) -> list[list[float]]
    embed_query(text: str) -> list[float]
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol, runtime_checkable

from backend.config import EmbeddingProvider, get_settings

logger = logging.getLogger("prism.llm.embeddings")


# ── Protocol for duck-typing ───────────────────────────────────────────────────

@runtime_checkable
class EmbeddingModel(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


# ── Public helpers ────────────────────────────────────────────────────────────

def get_embedding_model(
    provider: EmbeddingProvider | None = None,
) -> EmbeddingModel:
    """
    Return a configured embedding model for the given provider.
    Defaults to settings.default_embedding_provider.
    """
    settings = get_settings()
    active = provider or settings.default_embedding_provider

    builders = {
        EmbeddingProvider.OPENAI:               _build_openai_embeddings,
        EmbeddingProvider.SENTENCE_TRANSFORMERS: _build_sentence_transformers,
        EmbeddingProvider.VOYAGE:               _build_voyage,
        EmbeddingProvider.JINA:                 _build_jina,
    }
    builder = builders.get(active)
    if builder is None:
        raise ValueError(f"Unknown embedding provider: '{active}'")

    logger.debug("Creating embedding model: provider=%s", active.value)
    return builder()


# ── Provider builders ─────────────────────────────────────────────────────────

def _build_openai_embeddings() -> EmbeddingModel:
    from langchain_openai import OpenAIEmbeddings
    settings = get_settings()
    key = settings.openai_api_key
    if not key:
        raise ValueError("OPENAI_API_KEY required for OpenAI embeddings.")
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=key.get_secret_value(),
    )


def _build_sentence_transformers() -> EmbeddingModel:
    """
    Local Sentence Transformers — works with no API key.
    Model is downloaded on first use and cached by the library.
    """
    from langchain_community.embeddings import SentenceTransformerEmbeddings  # type: ignore
    settings = get_settings()
    return SentenceTransformerEmbeddings(model_name=settings.st_embedding_model)


def _build_voyage() -> EmbeddingModel:
    from langchain_community.embeddings import VoyageEmbeddings  # type: ignore
    settings = get_settings()
    key = settings.voyage_api_key
    if not key:
        raise ValueError("VOYAGE_API_KEY required for Voyage embeddings.")
    return VoyageEmbeddings(
        voyage_api_key=key.get_secret_value(),
        model="voyage-3",
    )


def _build_jina() -> EmbeddingModel:
    from langchain_community.embeddings import JinaEmbeddings  # type: ignore
    settings = get_settings()
    key = settings.jina_api_key
    if not key:
        raise ValueError("JINA_API_KEY required for Jina embeddings.")
    return JinaEmbeddings(
        jina_api_key=key.get_secret_value(),
        model_name="jina-embeddings-v3",
    )


# ── Async-compatible embed helper ─────────────────────────────────────────────

class AsyncEmbeddingWrapper:
    """
    Thin async wrapper around any EmbeddingModel.

    langchain embedding models expose sync methods;
    this wrapper runs them in asyncio's default executor.
    """

    def __init__(self, model: EmbeddingModel) -> None:
        self._model = model

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._model.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._model.embed_query, text)

    # Sync pass-throughs
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)


@lru_cache(maxsize=1)
def get_cached_embedding_model() -> AsyncEmbeddingWrapper:
    """
    Return a singleton AsyncEmbeddingWrapper using the configured provider.
    Cached so the model is only loaded once per process.
    """
    model = get_embedding_model()
    return AsyncEmbeddingWrapper(model)
