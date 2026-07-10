"""
GraphState — the single mutable object that flows through every LangGraph node.

Rules:
- Every node receives GraphState and returns GraphState.
- Nodes only write their own fields; they never mutate fields owned by other nodes.
- All fields default to None / empty so the graph can execute partial pipelines.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .pr_context import (
    PullRequestContext,
    RepositoryContext,
    ParsedDiff,
    GitMetadata,
)
from .agent_result import AgentResult


# ── Token / cost telemetry ────────────────────────────────────────────────────

class TokenUsage(BaseModel):
    """Cumulative token counters for the entire pipeline run."""
    prompt_tokens:     int   = Field(default=0, ge=0)
    completion_tokens: int   = Field(default=0, ge=0)
    total_tokens:      int   = Field(default=0, ge=0)

    def add(self, prompt: int, completion: int) -> None:
        self.prompt_tokens     += prompt
        self.completion_tokens += completion
        self.total_tokens      += prompt + completion


class ExecutionMetrics(BaseModel):
    """Wall-clock timings for each node."""
    node_timings:    dict[str, float] = Field(
        default_factory=dict,
        description="node_name → seconds.",
    )
    total_latency_s: float = Field(default=0.0, ge=0.0)
    started_at:      Optional[datetime] = Field(default=None)
    finished_at:     Optional[datetime] = Field(default=None)

    def record(self, node: str, elapsed_s: float) -> None:
        self.node_timings[node] = round(elapsed_s, 4)
        self.total_latency_s   += elapsed_s

    def start(self) -> None:
        self.started_at = datetime.now(timezone.utc)

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc)


# ── Final verdict ─────────────────────────────────────────────────────────────

class MergeVerdict(BaseModel):
    """The conclusive merge decision produced by the risk aggregator."""
    verdict: str = Field(
        ...,
        description="One of: 'READY_TO_MERGE', 'CAUTION', 'BLOCKED'.",
        pattern=r"^(READY_TO_MERGE|CAUTION|BLOCKED)$",
    )
    confidence_score:    float        = Field(..., ge=0.0, le=1.0)
    overall_risk_score:  float        = Field(..., ge=0.0, le=1.0)
    primary_reasoning:   str          = Field(...)
    strengths:           list[str]    = Field(default_factory=list)
    weaknesses:          list[str]    = Field(default_factory=list)
    risks:               list[str]    = Field(default_factory=list)
    review_order:        list[str]    = Field(
        default_factory=list,
        description="Recommended file review order, most critical first.",
    )
    blocking_issues:     list[str]    = Field(
        default_factory=list,
        description="Summary of must-fix issues preventing merge.",
    )
    executive_summary:   Optional[str] = Field(default=None)


# ── Main graph state ──────────────────────────────────────────────────────────

class GraphState(BaseModel):
    """
    The single shared state object for the LangGraph pipeline.

    Fields are grouped by the node that owns them. Each node
    reads the whole state but writes only to its own section.
    """

    # ── Input (set by caller before graph.invoke) ─────────────────────────────
    pr_url:         Optional[str]  = Field(default=None)
    owner:          Optional[str]  = Field(default=None)
    repo:           Optional[str]  = Field(default=None)
    pr_number:      Optional[int]  = Field(default=None)
    analysis_id:    Optional[str]  = Field(
        default=None,
        description="UUID assigned to this analysis run.",
    )

    # ── Repository Loader node ────────────────────────────────────────────────
    repository_context: Optional[RepositoryContext] = Field(default=None)

    # ── Repository Context Builder node ──────────────────────────────────────
    pull_request_context: Optional[PullRequestContext] = Field(default=None)
    git_metadata:         Optional[GitMetadata]        = Field(default=None)

    # ── Diff Parser node ──────────────────────────────────────────────────────
    parsed_diff: Optional[ParsedDiff] = Field(default=None)

    # ── RAG node ─────────────────────────────────────────────────────────────
    rag_context: Optional[str] = Field(
        default=None,
        description="Retrieved repository context snippets for injection into agent prompts.",
    )

    # ── Agent results (written by each agent node) ────────────────────────────
    security_result:      Optional[AgentResult] = Field(default=None)
    code_quality_result:  Optional[AgentResult] = Field(default=None)
    architecture_result:  Optional[AgentResult] = Field(default=None)
    documentation_result: Optional[AgentResult] = Field(default=None)
    testing_result:       Optional[AgentResult] = Field(default=None)
    dependency_result:    Optional[AgentResult] = Field(default=None)
    performance_result:   Optional[AgentResult] = Field(default=None)

    # ── Risk Aggregator node ──────────────────────────────────────────────────
    final_verdict: Optional[MergeVerdict] = Field(default=None)

    # ── PR Summary node ───────────────────────────────────────────────────────
    final_report: Optional[str] = Field(
        default=None,
        description="Full markdown report string, ready for GitHub comment posting.",
    )

    # ── Error tracking ────────────────────────────────────────────────────────
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Non-fatal errors collected during execution.",
    )

    # ── Telemetry ─────────────────────────────────────────────────────────────
    token_usage:       TokenUsage       = Field(default_factory=TokenUsage)
    execution_metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def add_error(self, node: str, error: str) -> None:
        self.errors.append({"node": node, "error": error})

    def collect_all_agent_results(self) -> list[AgentResult]:
        """Return all non-None agent results in a flat list."""
        candidates = [
            self.security_result,
            self.code_quality_result,
            self.architecture_result,
            self.documentation_result,
            self.testing_result,
            self.dependency_result,
            self.performance_result,
        ]
        return [r for r in candidates if r is not None]

    def all_agents_complete(self) -> bool:
        """True if every expected agent result is populated."""
        return all(
            r is not None
            for r in self.collect_all_agent_results()
        )

    def diff_text(self) -> str:
        """Convenience accessor for the full diff string."""
        return self.parsed_diff.diff_text if self.parsed_diff else ""

    class Config:
        arbitrary_types_allowed = True
