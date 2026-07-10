"""
RAG Service — orchestrates repository indexing for the vector store.

This service is called:
  1. When a new repo is registered for analysis (full index)
  2. When a PR is analysed and the repo hasn't been indexed yet (lazy index)

It delegates to GitHubService for file fetching and RepositoryIndexer for
chunking + embedding. Results are cached by repo so re-analysis of the
same repo doesn't re-embed the full codebase on every request.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.services.github_service import GitHubService
from rag.retriever import RepositoryIndexer, PRismRetriever
from rag.vector_store import get_vector_store

logger = logging.getLogger("prism.service.rag")

# In-process set of repos already indexed this process lifetime.
# For a production deployment replace with a Redis set.
_indexed_repos: set[str] = set()


class RAGService:
    """
    Manages the RAG indexing lifecycle for repositories.
    """

    def __init__(self) -> None:
        self._github = GitHubService()

    async def ensure_indexed(
        self,
        owner:  str,
        repo:   str,
        branch: str = "main",
        force:  bool = False,
    ) -> bool:
        """
        Ensure the repository is indexed in the vector store.

        Skips indexing if:
          - The repo was already indexed in this process (unless force=True)
          - The vector store collection already exists (unless force=True)

        Returns True if indexing ran, False if skipped.
        """
        key = f"{owner}/{repo}"

        if not force and key in _indexed_repos:
            logger.debug("RAG: %s already indexed this session — skipping.", key)
            return False

        store = get_vector_store(owner, repo)
        if not force:
            try:
                exists = await store.collection_exists()
                if exists:
                    _indexed_repos.add(key)
                    logger.debug("RAG: collection for %s already exists — skipping.", key)
                    return False
            except Exception as exc:
                logger.warning("RAG: could not check collection existence: %s", exc)

        logger.info("RAG: indexing repository %s (branch=%s)...", key, branch)

        try:
            files = await self._github.fetch_repo_files_for_rag(
                owner=owner, repo=repo, branch=branch
            )
        except Exception as exc:
            logger.error("RAG: file fetch failed for %s: %s", key, exc)
            return False

        if not files:
            logger.warning("RAG: no indexable files found for %s.", key)
            return False

        indexer = RepositoryIndexer(owner=owner, repo=repo, store=store)
        try:
            count = await indexer.index(files)
            logger.info("RAG: indexed %d vectors for %s.", count, key)
            _indexed_repos.add(key)
            return True
        except Exception as exc:
            logger.error("RAG: indexing failed for %s: %s", key, exc, exc_info=True)
            return False

    async def retrieve_context(
        self,
        owner:       str,
        repo:        str,
        pr_title:    str,
        changed_files: list[str],
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Retrieve relevant context snippets for a PR.
        Ensures the repo is indexed before retrieval.
        """
        await self.ensure_indexed(owner, repo)
        retriever = PRismRetriever(owner=owner, repo=repo)
        return await retriever.retrieve_for_diff(
            changed_files=changed_files,
            pr_title=pr_title,
            pr_description=pr_description,
        )

    async def reindex(self, owner: str, repo: str, branch: str = "main") -> bool:
        """Force a full re-index of the repository."""
        key = f"{owner}/{repo}"
        _indexed_repos.discard(key)

        # Drop existing collection
        try:
            store = get_vector_store(owner, repo)
            await store.delete_collection()
        except Exception as exc:
            logger.warning("RAG: could not delete existing collection: %s", exc)

        return await self.ensure_indexed(owner, repo, branch=branch, force=True)
