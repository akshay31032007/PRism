"""
Analysis Service — the single entry point for triggering a full PR analysis.

Responsibilities:
  1. Parse the PR URL
  2. Fetch GitHub data (PR context, repo context, git metadata, file diffs)
  3. Optionally trigger RAG indexing
  4. Build the initial GraphState
  5. Invoke the LangGraph pipeline
  6. Return a structured AnalysisResult to the API layer
"""

from __future__ import annotations

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from ai.models.graph_state import GraphState, MergeVerdict
from ai.models.agent_result import AgentResult
from ai.orchestrator.graph import get_graph
from backend.services.github_service import GitHubService, parse_pr_url
from backend.services.rag_service import RAGService

logger = logging.getLogger("prism.service.analysis")


# ── Response schema returned to the API layer ─────────────────────────────────

class AgentSummary(BaseModel):
    agent_name:    str
    status:        str
    score:         float
    confidence:    float
    issue_count:   int
    blocking:      int
    summary:       str
    recommendations: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    analysis_id:    str
    pr_url:         str
    owner:          str
    repo:           str
    pr_number:      int
    pr_title:       str
    verdict:        str
    confidence_score: float
    overall_risk_score: float
    primary_reasoning:  str
    executive_summary:  Optional[str]
    strengths:          list[str] = Field(default_factory=list)
    weaknesses:         list[str] = Field(default_factory=list)
    risks:              list[str] = Field(default_factory=list)
    blocking_issues:    list[str] = Field(default_factory=list)
    review_order:       list[str] = Field(default_factory=list)
    agent_summaries:    list[AgentSummary] = Field(default_factory=list)
    final_report:       Optional[str]
    total_tokens:       int = 0
    latency_seconds:    float = 0.0
    analysed_at:        str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    errors:             list[dict] = Field(default_factory=list)


class AnalysisService:
    """
    Orchestrates the full end-to-end PR analysis pipeline.

    Usage:
        service = AnalysisService()
        result  = await service.analyse(pr_url="https://github.com/owner/repo/pull/42")
    """

    def __init__(self) -> None:
        self._github = GitHubService()
        self._rag    = RAGService()

    async def analyse(
        self,
        pr_url:           str,
        enable_rag:       bool = True,
        skip_rag_indexing: bool = False,
    ) -> AnalysisResult:
        """
        Run a full multi-agent analysis on the given PR URL.

        Args:
            pr_url:             Full GitHub PR URL.
            enable_rag:         Whether to include RAG context in agent prompts.
            skip_rag_indexing:  Skip the indexing step (use existing index or no context).

        Returns:
            AnalysisResult with all agent findings and final verdict.

        Raises:
            ValueError: If the PR URL cannot be parsed.
            RuntimeError: If critical GitHub API calls fail.
        """
        analysis_id = str(uuid.uuid4())[:8]
        t_start     = time.perf_counter()
        logger.info("Starting analysis %s for %s", analysis_id, pr_url)

        # ── 1. Parse URL ───────────────────────────────────────────────────────
        owner, repo, pr_number = parse_pr_url(pr_url)

        # ── 2. Fetch GitHub data (parallel where possible) ────────────────────
        import asyncio
        pr_context, repo_context, git_metadata = await asyncio.gather(
            self._github.fetch_pull_request(owner, repo, pr_number),
            self._github.fetch_repository_context(owner, repo),
            self._github.fetch_git_metadata(owner, repo, pr_number),
            return_exceptions=False,
        )

        if pr_context is None:
            raise RuntimeError(
                f"Failed to fetch PR #{pr_number} from {owner}/{repo}. "
                "Check that the PR URL is correct and your GITHUB_TOKEN has read access."
            )

        # ── 3. RAG indexing (non-blocking — failure is acceptable) ────────────
        if enable_rag and not skip_rag_indexing:
            branch = repo_context.default_branch if repo_context else "main"
            try:
                await self._rag.ensure_indexed(owner, repo, branch=branch)
            except Exception as exc:
                logger.warning("RAG indexing failed (non-fatal): %s", exc)

        # ── 4. Retrieve RAG context for this PR ───────────────────────────────
        rag_context = ""
        if enable_rag:
            try:
                changed_files = [
                    f.get("filename", "")
                    for f in pr_context.__dict__.get("_raw_files", [])
                ]
                rag_context = await self._rag.retrieve_context(
                    owner=owner,
                    repo=repo,
                    pr_title=pr_context.title,
                    changed_files=changed_files,
                    pr_description=pr_context.body,
                )
            except Exception as exc:
                logger.warning("RAG context retrieval failed (non-fatal): %s", exc)

        # ── 5. Build initial GraphState ───────────────────────────────────────
        state = GraphState(
            pr_url=pr_url,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            analysis_id=analysis_id,
            pull_request_context=pr_context,
            repository_context=repo_context,
            git_metadata=git_metadata,
            rag_context=rag_context or None,
        )
        state.execution_metrics.start()

        # ── 6. Run LangGraph pipeline ─────────────────────────────────────────
        graph = get_graph()
        try:
            raw_result = await graph.ainvoke(state)
            # LangGraph returns a dict when using Pydantic models as state
            if isinstance(raw_result, dict):
                # Carefully merge — only update fields that are actually set
                merged = state.model_dump()
                for k, v in raw_result.items():
                    if v is not None:
                        merged[k] = v
                final_state = GraphState.model_validate(merged)
            else:
                final_state = raw_result

            # If pipeline produced no verdict, log all errors for diagnosis
            if final_state.final_verdict is None:
                logger.error(
                    "Pipeline completed but produced no verdict. Errors: %s",
                    final_state.errors,
                )
                if final_state.errors:
                    first_error = final_state.errors[0].get("error", "unknown")
                    raise RuntimeError(
                        f"Analysis pipeline failed: {first_error}. "
                        f"Check that GITHUB_TOKEN has 'repo' scope and the PR URL is accessible."
                    )

        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Graph execution failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Analysis pipeline failed: {exc}") from exc

        latency = time.perf_counter() - t_start
        logger.info(
            "Analysis %s complete in %.2fs — verdict=%s",
            analysis_id,
            latency,
            final_state.final_verdict.verdict if final_state.final_verdict else "UNKNOWN",
        )

        # ── 7. Build response ─────────────────────────────────────────────────
        return self._build_result(
            final_state, pr_url, owner, repo, pr_number,
            pr_context.title, analysis_id, latency,
        )

    def _build_result(
        self,
        state:       GraphState,
        pr_url:      str,
        owner:       str,
        repo:        str,
        pr_number:   int,
        pr_title:    str,
        analysis_id: str,
        latency:     float,
    ) -> AnalysisResult:
        verdict: MergeVerdict = state.final_verdict or MergeVerdict(
            verdict="CAUTION",
            confidence_score=0.3,
            overall_risk_score=0.7,
            primary_reasoning="Verdict not produced — pipeline may have encountered errors.",
        )

        agent_summaries = [
            AgentSummary(
                agent_name=r.agent_name,
                status=r.status.value,
                score=round(r.score, 3),
                confidence=round(r.confidence, 3),
                issue_count=r.total_issue_count,
                blocking=r.blocking_issue_count,
                summary=r.summary,
                recommendations=r.recommendations[:5],
            )
            for r in state.collect_all_agent_results()
        ]

        return AnalysisResult(
            analysis_id=analysis_id,
            pr_url=pr_url,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            pr_title=pr_title,
            verdict=verdict.verdict,
            confidence_score=verdict.confidence_score,
            overall_risk_score=verdict.overall_risk_score,
            primary_reasoning=verdict.primary_reasoning,
            executive_summary=verdict.executive_summary,
            strengths=verdict.strengths,
            weaknesses=verdict.weaknesses,
            risks=verdict.risks,
            blocking_issues=verdict.blocking_issues,
            review_order=verdict.review_order,
            agent_summaries=agent_summaries,
            final_report=state.final_report,
            total_tokens=state.token_usage.total_tokens,
            latency_seconds=round(latency, 2),
            errors=state.errors,
        )
