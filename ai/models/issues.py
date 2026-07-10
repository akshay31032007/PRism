"""
Issue model — the atomic unit of agent output.
Every finding raised by any agent is expressed as an Issue.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class IssueSeverity(str, Enum):
    """CVSS-inspired severity ladder used across all agents."""
    CRITICAL = "critical"   # Must fix before merge; blocks the PR
    HIGH     = "high"       # Strong recommendation to fix; flags PR
    MEDIUM   = "medium"     # Should fix; advisory
    LOW      = "low"        # Nice-to-have improvement
    INFO     = "info"       # Informational only, no action required


class IssueCategory(str, Enum):
    """Domain category — determines which agent surfaces the issue."""
    SECURITY         = "security"
    CODE_QUALITY     = "code_quality"
    ARCHITECTURE     = "architecture"
    DOCUMENTATION    = "documentation"
    TESTING          = "testing"
    DEPENDENCY       = "dependency"
    PERFORMANCE      = "performance"
    MERGE_READINESS  = "merge_readiness"


class Issue(BaseModel):
    """
    A single finding raised by an agent.

    Every field is required unless explicitly marked Optional.
    The combination of (file_path, start_line, rule_id) should be unique
    within one analysis run.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    rule_id: str = Field(
        ...,
        description=(
            "Short, stable identifier for this class of issue. "
            "E.g. 'SEC-001', 'QUAL-003'. Used for deduplication and tracking."
        ),
        pattern=r"^[A-Z]{2,8}-\d{3}$",
        examples=["SEC-001", "ARCH-004"],
    )

    category: IssueCategory = Field(
        ...,
        description="Domain this issue belongs to.",
    )

    severity: IssueSeverity = Field(
        ...,
        description="How critical this finding is.",
    )

    # ── What was found ────────────────────────────────────────────────────────
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="One-line human-readable summary of the issue.",
    )

    description: str = Field(
        ...,
        min_length=10,
        description=(
            "Detailed explanation of the problem: what it is, "
            "why it matters, and concrete evidence from the diff."
        ),
    )

    # ── Where it was found ────────────────────────────────────────────────────
    file_path: Optional[str] = Field(
        default=None,
        description="Relative path of the affected file within the repository.",
    )

    start_line: Optional[int] = Field(
        default=None,
        ge=1,
        description="1-indexed line number where the issue begins.",
    )

    end_line: Optional[int] = Field(
        default=None,
        ge=1,
        description="1-indexed line number where the issue ends (inclusive).",
    )

    code_snippet: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="The exact code fragment that triggers this issue.",
    )

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description=(
            "Agent's confidence that this is a genuine issue, not a false positive. "
            "0.0 = pure speculation, 1.0 = certainty."
        ),
    )

    # ── Remediation ───────────────────────────────────────────────────────────
    suggested_fix: Optional[str] = Field(
        default=None,
        description=(
            "Concrete, actionable fix. Should be code or specific steps, "
            "not vague advice like 'improve this'."
        ),
    )

    references: list[str] = Field(
        default_factory=list,
        description=(
            "URLs or identifiers for supporting documentation. "
            "E.g. OWASP links, CVE IDs, PEP references."
        ),
        max_length=10,
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    tags: list[str] = Field(
        default_factory=list,
        description="Free-form tags for grouping and filtering. E.g. ['owasp-a03', 'injection'].",
        max_length=20,
    )

    @field_validator("end_line", mode="after")
    @classmethod
    def end_line_gte_start(cls, v: Optional[int], info) -> Optional[int]:
        start = info.data.get("start_line")
        if v is not None and start is not None and v < start:
            raise ValueError(f"end_line ({v}) must be >= start_line ({start})")
        return v

    def is_blocking(self) -> bool:
        """True if this issue must be resolved before the PR can merge."""
        return self.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)

    def to_summary(self) -> str:
        """One-line console-friendly summary."""
        loc = f" [{self.file_path}:{self.start_line}]" if self.file_path else ""
        return (
            f"[{self.severity.value.upper()}] {self.rule_id} — "
            f"{self.title}{loc} (confidence={self.confidence:.0%})"
        )
