"""
RAG Vector Store — abstraction layer over Qdrant, Chroma, and FAISS.

All callers use VectorStoreManager.get() and never interact with the
underlying client directly. This makes swapping providers a config change.

Collection naming convention:
    prism_{owner}_{repo}   — e.g. prism_facebook_react
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from ai.llm.embeddings import get_cached_embedding_model
from backend.config import VectorDBProvider, get_settings
from rag.chunker import CodeChunk

logger = logging.getLogger("prism.rag.vector_store")


# ── Document wrapper ──────────────────────────────────────────────────────────

class Document:
    """Minimal document container mirroring LangChain's Document interface."""

    def __init__(self, page_content: str, metadata: dict) -> None:
        self.page_content = page_content
        self.metadata     = metadata

    def __repr__(self) -> str:
        src = self.metadata.get("source", "?")
        return f"Document(source={src!r}, len={len(self.page_content)})"


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseVectorStore:
    """Interface all vector store backends must satisfy."""

    async def upsert(self, chunks: list[CodeChunk]) -> int:
        """Embed and upsert chunks. Returns number of vectors stored."""
        raise NotImplementedError

    async def similarity_search(
        self, query: str, k: int = 8, filter_metadata: Optional[dict] = None
    ) -> list[Document]:
        """Return the k most similar documents to query."""
        raise NotImplementedError

    async def delete_collection(self) -> None:
        """Drop this collection entirely."""
        raise NotImplementedError

    async def collection_exists(self) -> bool:
        raise NotImplementedError


# ── Qdrant backend ────────────────────────────────────────────────────────────

class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant-backed vector store.

    Creates the collection on first upsert with cosine distance.
    Uses batch upserts of 100 vectors at a time to avoid memory spikes.
    """

    VECTOR_DIM = 384  # all-MiniLM-L6-v2 dimension; updated on first upsert

    def __init__(self, collection_name: str) -> None:
        self._collection = collection_name
        self._settings   = get_settings()
        self._embedder   = get_cached_embedding_model()
        self._client     = self._build_client()

    def _build_client(self):
        from qdrant_client import QdrantClient
        settings = self._settings
        key = settings.qdrant_api_key
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=key.get_secret_value() if key else None,
            timeout=30,
        )

    async def _ensure_collection(self, vector_size: int) -> None:
        from qdrant_client.models import Distance, VectorParams
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self._collection)

    async def upsert(self, chunks: list[CodeChunk]) -> int:
        if not chunks:
            return 0

        from qdrant_client.models import PointStruct

        texts = [c.content for c in chunks]
        vectors = await self._embedder.aembed_documents(texts)

        await self._ensure_collection(len(vectors[0]))

        batch_size = 100
        total = 0
        for i in range(0, len(chunks), batch_size):
            batch_chunks  = chunks[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={
                        "page_content": chunk.content,
                        **chunk.to_document_dict()["metadata"],
                    },
                )
                for chunk, vec in zip(batch_chunks, batch_vectors)
            ]
            self._client.upsert(
                collection_name=self._collection,
                points=points,
            )
            total += len(points)

        logger.info("Upserted %d vectors to '%s'", total, self._collection)
        return total

    async def similarity_search(
        self, query: str, k: int = 8, filter_metadata: Optional[dict] = None
    ) -> list[Document]:
        query_vector = await self._embedder.aembed_query(query)

        from qdrant_client.models import Filter, FieldCondition, MatchValue
        qdrant_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_metadata.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=k,
            query_filter=qdrant_filter,
        )

        return [
            Document(
                page_content=hit.payload.get("page_content", ""),
                metadata={
                    k: v
                    for k, v in hit.payload.items()
                    if k != "page_content"
                },
            )
            for hit in results
        ]

    async def delete_collection(self) -> None:
        self._client.delete_collection(self._collection)
        logger.info("Deleted Qdrant collection: %s", self._collection)

    async def collection_exists(self) -> bool:
        existing = {c.name for c in self._client.get_collections().collections}
        return self._collection in existing


# ── FAISS backend (local, no server) ─────────────────────────────────────────

class FAISSVectorStore(BaseVectorStore):
    """
    In-process FAISS store. Good for local dev / CI where Qdrant is unavailable.
    NOT persistent across process restarts.
    """

    def __init__(self, collection_name: str) -> None:
        self._collection = collection_name
        self._embedder   = get_cached_embedding_model()
        self._index: Any = None
        self._documents: list[Document] = []

    async def upsert(self, chunks: list[CodeChunk]) -> int:
        import numpy as np

        try:
            import faiss  # type: ignore
        except ImportError:
            raise ImportError("Install faiss-cpu to use the FAISS vector store.")

        texts   = [c.content for c in chunks]
        vectors = await self._embedder.aembed_documents(texts)
        arr     = np.array(vectors, dtype="float32")

        if self._index is None:
            self._index = faiss.IndexFlatIP(arr.shape[1])

        # Normalise for cosine similarity via inner product
        faiss.normalize_L2(arr)
        self._index.add(arr)

        for chunk, vec in zip(chunks, vectors):
            doc_dict = chunk.to_document_dict()
            self._documents.append(Document(
                page_content=doc_dict["page_content"],
                metadata=doc_dict["metadata"],
            ))

        logger.info("FAISS: upserted %d vectors for '%s'", len(chunks), self._collection)
        return len(chunks)

    async def similarity_search(
        self, query: str, k: int = 8, filter_metadata: Optional[dict] = None
    ) -> list[Document]:
        if self._index is None or not self._documents:
            return []

        import numpy as np
        import faiss  # type: ignore

        q_vec = await self._embedder.aembed_query(query)
        arr   = np.array([q_vec], dtype="float32")
        faiss.normalize_L2(arr)

        actual_k = min(k, len(self._documents))
        _, indices = self._index.search(arr, actual_k)

        results = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            if filter_metadata:
                if not all(doc.metadata.get(fk) == fv for fk, fv in filter_metadata.items()):
                    continue
            results.append(doc)
        return results

    async def delete_collection(self) -> None:
        self._index     = None
        self._documents = []

    async def collection_exists(self) -> bool:
        return self._index is not None


# ── Chroma backend ────────────────────────────────────────────────────────────

class ChromaVectorStore(BaseVectorStore):
    """Chroma in-process vector store. Persistent via local SQLite."""

    def __init__(self, collection_name: str) -> None:
        self._collection_name = collection_name
        self._embedder = get_cached_embedding_model()
        self._client   = None
        self._coll     = None

    def _get_client(self):
        if self._client is None:
            import chromadb  # type: ignore
            self._client = chromadb.Client()
        return self._client

    def _get_collection(self):
        if self._coll is None:
            client = self._get_client()
            self._coll = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._coll

    async def upsert(self, chunks: list[CodeChunk]) -> int:
        if not chunks:
            return 0

        coll    = self._get_collection()
        texts   = [c.content for c in chunks]
        vectors = await self._embedder.aembed_documents(texts)

        coll.upsert(
            ids=[str(uuid.uuid4()) for _ in chunks],
            embeddings=vectors,
            documents=texts,
            metadatas=[c.to_document_dict()["metadata"] for c in chunks],
        )
        logger.info("Chroma: upserted %d vectors", len(chunks))
        return len(chunks)

    async def similarity_search(
        self, query: str, k: int = 8, filter_metadata: Optional[dict] = None
    ) -> list[Document]:
        coll    = self._get_collection()
        q_vec   = await self._embedder.aembed_query(query)
        results = coll.query(
            query_embeddings=[q_vec],
            n_results=min(k, coll.count()),
            where=filter_metadata,
        )
        docs = []
        for text, meta in zip(
            results["documents"][0], results["metadatas"][0]
        ):
            docs.append(Document(page_content=text, metadata=meta))
        return docs

    async def delete_collection(self) -> None:
        client = self._get_client()
        client.delete_collection(self._collection_name)
        self._coll = None

    async def collection_exists(self) -> bool:
        try:
            client = self._get_client()
            client.get_collection(self._collection_name)
            return True
        except Exception:
            return False


# ── Factory ───────────────────────────────────────────────────────────────────

def collection_name_for(owner: str, repo: str) -> str:
    """Derive a safe Qdrant/Chroma collection name from owner + repo."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{owner}_{repo}")
    return f"prism_{safe}"[:64]


def get_vector_store(
    owner: str,
    repo: str,
    provider: Optional[VectorDBProvider] = None,
) -> BaseVectorStore:
    """
    Return a configured vector store for the given repository.

    Provider selection order:
      1. `provider` argument
      2. settings.default_vector_db
    """
    settings = get_settings()
    active   = provider or settings.default_vector_db
    name     = collection_name_for(owner, repo)

    if active == VectorDBProvider.QDRANT:
        return QdrantVectorStore(name)
    elif active == VectorDBProvider.CHROMA:
        return ChromaVectorStore(name)
    elif active == VectorDBProvider.FAISS:
        return FAISSVectorStore(name)
    else:
        raise ValueError(f"Unknown vector DB provider: '{active}'")


import re  # noqa: E402 — placed here to avoid circular at module top
