"""PRism AI — shared Pydantic models package."""

from .issues import Issue, IssueSeverity, IssueCategory
from .agent_result import AgentResult, AgentStatus
from .pr_context import (
    PullRequestContext,
    RepositoryContext,
    ParsedDiff,
    FileDiff,
    HunkLine,
    GitMetadata,
    CICheckRun,
    DependencyFile,
)
from .graph_state import GraphState, TokenUsage, ExecutionMetrics

__all__ = [
    # Issues
    "Issue",
    "IssueSeverity",
    "IssueCategory",
    # Agent results
    "AgentResult",
    "AgentStatus",
    # PR / Repo context
    "PullRequestContext",
    "RepositoryContext",
    "ParsedDiff",
    "FileDiff",
    "HunkLine",
    "GitMetadata",
    "CICheckRun",
    "DependencyFile",
    # Graph
    "GraphState",
    "TokenUsage",
    "ExecutionMetrics",
]
