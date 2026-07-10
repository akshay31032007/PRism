"""
AgentResult — the complete output contract for every agent.
Agents return one AgentResult each; the graph aggregates them.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field, computed_field

from .issues import Issue, IssueSeverity, IssueCategory


class AgentStatus(str, Enum):
    """Execution status of an individual agent run."""
    SUCCESS  = "success"   # Completed normally
    PARTIAL  = "partial"   # Completed with degraded quality (e.g. truncation)
    SKIPPED  = "skipped"   # Not applicable to this PR (e.g. no deps file)
    FAILED   = "failed"    # Runtime error — result should not be trusted


class AgentResult(BaseModel):
    """
    The complete, structured output from a single agent.

    This is the only type that agents are allowed to return to the graph.
    All downstream consumers (risk aggregator, summary agent) read from
    this model — never from raw LLM text.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    agent_name: str = Field(
        ...,
        description="Human-readable agent identifier. E.g. 'SecurityAgent'.",
    )

    agent_version: str = Field(
        default="1.0.0",
        description="Semantic version of the agent. Bumped on prompt/logic changes.",
        pattern=r"^\d+\.\d+\.\d+$",
    )

    category: IssueCategory = Field(
        ...,
        description="The domain this agent is responsible for.",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: AgentStatus = Field(
        default=AgentStatus.SUCCESS,
        description="Whether the agent ran to completion.",
    )

    error_message: Optional[str] = Field(
        default=None,
        description="If status is FAILED or PARTIAL, the reason.",
    )

    # ── Findings ──────────────────────────────────────────────────────────────
    issues: list[Issue] = Field(
        default_factory=list,
        description="All issues found. Empty list means the agent found nothing to flag.",
    )

    # ── Scores ────────────────────────────────────────────────────────────────
    score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description=(
            "Domain health score for this PR: 1.0 = perfect, 0.0 = critical failure. "
            "Computed by the agent from severity/count of issues."
        ),
    )

    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Agent's overall confidence in its own analysis.",
    )

    # ── Narrative ─────────────────────────────────────────────────────────────
    summary: str = Field(
        ...,
        min_length=10,
        description=(
            "Two-to-four sentence narrative summary of the agent's findings. "
            "Written for engineers, not managers."
        ),
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of concrete action items. "
            "Each item should be independently actionable."
        ),
        max_length=15,
    )

    # ── Execution telemetry ───────────────────────────────────────────────────
    llm_model_used: Optional[str] = Field(
        default=None,
        description="The LLM model identifier that produced this result.",
    )

    prompt_tokens: int  = Field(default=0, ge=0)
    output_tokens: int  = Field(default=0, ge=0)
    latency_ms:    int  = Field(default=0, ge=0, description="Wall-clock ms for this agent.")

    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the agent completed.",
    )

    # ── Extra structured data ─────────────────────────────────────────────────
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific structured extras (e.g. CVSS vectors, complexity metrics).",
    )

    # ── Computed helpers ──────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def blocking_issue_count(self) -> int:
        """Number of CRITICAL or HIGH severity issues."""
        return sum(1 for i in self.issues if i.is_blocking())

    @computed_field  # type: ignore[misc]
    @property
    def total_issue_count(self) -> int:
        return len(self.issues)

    @computed_field  # type: ignore[misc]
    @property
    def has_blocking_issues(self) -> bool:
        return self.blocking_issue_count > 0

    def issues_by_severity(self, severity: IssueSeverity) -> list[Issue]:
        return [i for i in self.issues if i.severity == severity]

    def compute_score(self) -> float:
        """
        Derive a [0, 1] health score from the issue list.

        Weight scheme:
          CRITICAL → −0.40 per issue (floor at 0.0 after 2)
          HIGH     → −0.20 per issue
          MEDIUM   → −0.08 per issue
          LOW      → −0.02 per issue
          INFO     → no deduction
        """
        weights = {
            IssueSeverity.CRITICAL: 0.40,
            IssueSeverity.HIGH:     0.20,
            IssueSeverity.MEDIUM:   0.08,
            IssueSeverity.LOW:      0.02,
            IssueSeverity.INFO:     0.00,
        }
        deduction = sum(weights.get(i.severity, 0.0) for i in self.issues)
        return max(0.0, round(1.0 - deduction, 4))
