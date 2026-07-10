"""
Pull Request and Repository context models.
These are populated by the GitHub scraper and loader nodes before
any agent sees the data.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ── Low-level diff primitives ─────────────────────────────────────────────────

class HunkLine(BaseModel):
    """A single line within a diff hunk."""
    line_number_old: Optional[int] = Field(default=None)
    line_number_new: Optional[int] = Field(default=None)
    content:   str  = Field(..., description="Raw line content including +/- prefix.")
    line_type: str  = Field(
        ...,
        description="'added', 'removed', or 'context'.",
        pattern=r"^(added|removed|context)$",
    )

    @property
    def is_added(self)   -> bool: return self.line_type == "added"
    @property
    def is_removed(self) -> bool: return self.line_type == "removed"


class FileDiff(BaseModel):
    """The complete diff for a single changed file."""
    filename:      str             = Field(..., description="Relative path in the repo.")
    status:        str             = Field(
        ...,
        description="'added', 'modified', 'removed', 'renamed', 'copied'.",
    )
    additions:     int             = Field(default=0, ge=0)
    deletions:     int             = Field(default=0, ge=0)
    patch:         Optional[str]   = Field(
        default=None,
        description="Raw unified diff patch string as returned by GitHub API.",
    )
    lines:         list[HunkLine]  = Field(
        default_factory=list,
        description="Parsed hunk lines (populated by diff parser node).",
    )
    previous_filename: Optional[str] = Field(
        default=None,
        description="Original filename for renamed/copied files.",
    )
    language:      Optional[str]   = Field(
        default=None,
        description="Detected programming language (populated by context builder).",
    )

    @property
    def changed_line_count(self) -> int:
        return self.additions + self.deletions

    @property
    def is_test_file(self) -> bool:
        """Heuristic: is this likely a test file?"""
        lower = self.filename.lower()
        return any(
            marker in lower
            for marker in ("test_", "_test", "/tests/", "/test/", "spec.", ".spec.")
        )


class ParsedDiff(BaseModel):
    """The aggregate parsed diff for the entire pull request."""
    files:          list[FileDiff] = Field(default_factory=list)
    total_additions: int           = Field(default=0, ge=0)
    total_deletions: int           = Field(default=0, ge=0)
    truncated:       bool          = Field(
        default=False,
        description="True if the diff was cut short due to size limits.",
    )
    truncated_at_chars: Optional[int] = Field(default=None)

    @property
    def changed_files_count(self) -> int:
        return len(self.files)

    @property
    def diff_text(self) -> str:
        """Reconstruct a single text blob for LLM consumption."""
        parts: list[str] = []
        for f in self.files:
            parts.append(f"=== {f.status.upper()}: {f.filename} ===")
            if f.patch:
                parts.append(f.patch)
        return "\n".join(parts)

    def get_file(self, path: str) -> Optional[FileDiff]:
        return next((f for f in self.files if f.filename == path), None)


# ── CI/CD status ──────────────────────────────────────────────────────────────

class CIStatus(str, Enum):
    SUCCESS  = "success"
    FAILURE  = "failure"
    PENDING  = "pending"
    SKIPPED  = "skipped"
    NEUTRAL  = "neutral"
    UNKNOWN  = "unknown"


class CICheckRun(BaseModel):
    """A single CI check-run result from GitHub."""
    name:        str            = Field(..., description="Check run name.")
    status:      str            = Field(..., description="queued|in_progress|completed.")
    conclusion:  Optional[str]  = Field(default=None)
    ci_status:   CIStatus       = Field(default=CIStatus.UNKNOWN)
    url:         Optional[str]  = Field(default=None)
    started_at:  Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


# ── Dependency file ───────────────────────────────────────────────────────────

class DependencyFile(BaseModel):
    """A dependency manifest found in the repository."""
    path:      str       = Field(..., description="Relative path, e.g. 'requirements.txt'.")
    ecosystem: str       = Field(..., description="'pip', 'npm', 'cargo', 'maven', 'go'.")
    content:   str       = Field(..., description="Raw file content.")
    changed:   bool      = Field(
        default=False,
        description="True if this file is part of the PR diff.",
    )


# ── Repository context ────────────────────────────────────────────────────────

class RepositoryContext(BaseModel):
    """Static facts about the repository — collected once per analysis."""
    owner:             str             = Field(...)
    name:              str             = Field(...)
    full_name:         str             = Field(...)
    default_branch:    str             = Field(default="main")
    description:       Optional[str]  = Field(default=None)
    primary_language:  Optional[str]  = Field(default=None)
    languages:         dict[str, int] = Field(
        default_factory=dict,
        description="GitHub language breakdown: {language: bytes}.",
    )
    topics:            list[str]       = Field(default_factory=list)
    has_readme:        bool            = Field(default=False)
    has_contributing:  bool            = Field(default=False)
    has_ci:            bool            = Field(default=False)
    has_security_policy: bool         = Field(default=False)
    directory_tree:    list[str]       = Field(
        default_factory=list,
        description="Top-level directory listing (depth 2 max).",
    )
    dependency_files:  list[DependencyFile] = Field(default_factory=list)
    stars:             int             = Field(default=0, ge=0)
    forks:             int             = Field(default=0, ge=0)
    open_issues_count: int             = Field(default=0, ge=0)

    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.full_name}"


# ── Git metadata ──────────────────────────────────────────────────────────────

class GitMetadata(BaseModel):
    """Commit-level metadata for the PR's head."""
    head_sha:          str             = Field(...)
    base_sha:          str             = Field(...)
    head_branch:       str             = Field(...)
    base_branch:       str             = Field(...)
    commit_count:      int             = Field(default=1, ge=1)
    commit_messages:   list[str]       = Field(default_factory=list)
    author_login:      Optional[str]  = Field(default=None)
    author_email:      Optional[str]  = Field(default=None)
    committed_at:      Optional[datetime] = Field(default=None)


# ── Pull Request context ──────────────────────────────────────────────────────

class PullRequestContext(BaseModel):
    """Everything known about the pull request itself."""
    number:      int            = Field(..., ge=1)
    title:       str            = Field(...)
    body:        Optional[str]  = Field(default=None, description="PR description.")
    author:      Optional[str]  = Field(default=None)
    state:       str            = Field(default="open")
    draft:       bool           = Field(default=False)
    mergeable:   Optional[bool] = Field(default=None)
    labels:      list[str]      = Field(default_factory=list)
    requested_reviewers: list[str] = Field(default_factory=list)
    ci_checks:   list[CICheckRun]  = Field(default_factory=list)
    created_at:  Optional[datetime] = Field(default=None)
    updated_at:  Optional[datetime] = Field(default=None)
    html_url:    Optional[str]      = Field(default=None)

    @property
    def all_ci_passing(self) -> bool:
        """True only when every completed check concluded with success."""
        completed = [c for c in self.ci_checks if c.status == "completed"]
        if not completed:
            return True  # No checks = not failing
        return all(c.ci_status == CIStatus.SUCCESS for c in completed)

    @property
    def ci_failure_count(self) -> int:
        return sum(
            1 for c in self.ci_checks
            if c.ci_status == CIStatus.FAILURE
        )

    @property
    def description_quality(self) -> str:
        """Rough quality bucket for the PR description."""
        if not self.body or len(self.body.strip()) < 20:
            return "missing"
        if len(self.body.strip()) < 100:
            return "minimal"
        return "adequate"
