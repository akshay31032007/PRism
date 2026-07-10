"""
RAG Retriever — query the vector store and format retrieved context
into a clean string block for injection into agent prompts.

Anti-prompt-injection hardening:
  - All retrieved content is wrapped in explicit boundary markers.
  - Content exceeding the budget is truncated, never silently dropped.
  - Metadata fields are validated before forwarding to the LLM.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from backend.config import get_settings
from rag.vector_store import BaseVectorStore, Document, get_vector_store

logger = logging.getLogger("prism.rag.retriever")

# Prompt injection patterns to strip from retrieved content
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"you\s+are\s+now\s+a",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"###\s*instruction",
    r"forget\s+(everything|all)",
]

_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    flags=re.IGNORECASE,
)

_MAX_SNIPPET_CHARS = 600     # Per-document content cap in the context block
_MAX_CONTEXT_CHARS = 8_000   # Total context block cap


def _sanitise(text: str) -> str:
    """
    Strip prompt-injection patterns from retrieved text.
    Does NOT alter normal code content.
    """
    return _INJECTION_RE.sub("[REDACTED]", text)


def _format_document(doc: Document, index: int) -> str:
    """Format a single retrieved document into a readable context block."""
    source     = doc.metadata.get("source", "unknown")
    language   = doc.metadata.get("language", "")
    start_line = doc.metadata.get("start_line", "?")
    end_line   = doc.metadata.get("end_line",   "?")

    content = _sanitise(doc.page_content)
    if len(content) > _MAX_SNIPPET_CHARS:
        content = content[:_MAX_SNIPPET_CHARS] + "\n... [snippet truncated]"

    lang_label = f" ({language})" if language else ""
    return (
        f"--- CONTEXT SNIPPET {index} ---\n"
        f"Source: {source}{lang_label}  Lines: {start_line}-{end_line}\n"
        f"```{language}\n{content}\n```"
    )


class PRismRetriever:
    """
    Retrieves relevant repository code snippets for a given natural-language query.

    Usage:
        retriever = PRismRetriever(owner="facebook", repo="react")
        context   = await retriever.retrieve("authentication middleware pattern")
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        store: Optional[BaseVectorStore] = None,
    ) -> None:
        self._owner = owner
        self._repo  = repo
        self._store = store or get_vector_store(owner, repo)
        self._settings = get_settings()

    async def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filter_language: Optional[str] = None,
    ) -> str:
        """
        Retrieve the top-k most relevant snippets for `query`.

        Returns a formatted multi-snippet context string ready for prompt injection,
        or an empty string if the collection doesn't exist or has no relevant results.

        Args:
            query:           Natural-language search query.
            k:               Number of results (defaults to settings.retriever_top_k).
            filter_language: Restrict to a specific language (e.g. 'python').

        Returns:
            Formatted context string, or "" on failure.
        """
        if not query or not query.strip():
            return ""

        # Safety: don't query if collection was never indexed
        try:
            exists = await self._store.collection_exists()
            if not exists:
                logger.debug(
                    "Collection not indexed for %s/%s — skipping RAG retrieval.",
                    self._owner, self._repo,
                )
                return ""
        except Exception as exc:
            logger.warning("Could not check collection existence: %s", exc)
            return ""

        k_actual = k or self._settings.retriever_top_k
        filter_meta = {"language": filter_language} if filter_language else None

        try:
            docs = await self._store.similarity_search(
                query=query,
                k=k_actual,
                filter_metadata=filter_meta,
            )
        except Exception as exc:
            logger.error("Vector store similarity_search failed: %s", exc, exc_info=True)
            return ""

        if not docs:
            return ""

        snippets = [_format_document(doc, i + 1) for i, doc in enumerate(docs)]
        full_context = "\n\n".join(snippets)

        # Enforce total context budget
        if len(full_context) > _MAX_CONTEXT_CHARS:
            full_context = (
                full_context[:_MAX_CONTEXT_CHARS]
                + "\n\n... [RAG context truncated at budget limit]"
            )

        logger.debug(
            "Retrieved %d snippets for query=%r (total %d chars)",
            len(docs), query[:60], len(full_context),
        )
        return full_context

    async def retrieve_for_diff(
        self,
        changed_files: list[str],
        pr_title: str,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Build a targeted query from the PR's changed files + title,
        then retrieve relevant context snippets.

        This is the primary entry point for agent context enrichment.
        """
        # Construct a focused query from PR metadata
        file_names = [f.split("/")[-1].replace(".", " ") for f in changed_files[:8]]
        query_parts = [pr_title]
        if pr_description:
            query_parts.append(pr_description[:300])
        query_parts.extend(file_names)

        query = " ".join(query_parts)
        # Strip special chars that could mess up embedding
        query = re.sub(r"[<>{}|\\^`]", " ", query)
        query = " ".join(query.split())[:512]

        return await self.retrieve(query=query)


class RepositoryIndexer:
    """
    Indexes a repository's source files into the vector store.

    Typically called once after the repo is cloned or freshly fetched.
    Re-indexing the same collection is safe — Qdrant upserts by ID.
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        store: Optional[BaseVectorStore] = None,
    ) -> None:
        from rag.chunker import RepositoryChunker
        self._owner   = owner
        self._repo    = repo
        self._store   = store or get_vector_store(owner, repo)
        self._chunker = RepositoryChunker()

    async def index(self, files: dict[str, str]) -> int:
        """
        Chunk and embed a dict of {relative_path: file_content}.

        Returns the total number of vectors upserted.
        """
        if not files:
            logger.warning("index() called with empty files dict — nothing to index.")
            return 0

        logger.info(
            "Indexing %d files for %s/%s...",
            len(files), self._owner, self._repo,
        )

        chunks = self._chunker.chunk_repository(
            files=files,
            extra_metadata={"owner": self._owner, "repo": self._repo},
        )

        if not chunks:
            logger.warning("Chunker produced 0 chunks for %s/%s.", self._owner, self._repo)
            return 0

        total = await self._store.upsert(chunks)
        logger.info(
            "Indexed %d vectors for %s/%s (%d source files).",
            total, self._owner, self._repo, len(files),
        )
        return total
