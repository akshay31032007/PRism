from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ai.models.agent import AgentResult


class RepositoryContext(BaseModel):
    repo_url: str
    base_branch: str
    head_branch: str
    repo_description: Optional[str] = None


class PullRequestContext(BaseModel):
    pr_number: int
    title: str
    description: Optional[str] = None
    author: str


class ParsedDiff(BaseModel):
    files_changed: int
    insertions: int
    deletions: int
    diff_content: str


class RepositoryTree(BaseModel):
    structure: Dict[str, Any]


class ChangedFile(BaseModel):
    path: str
    status: str  # added, modified, removed
    patch: str


class GitMetadata(BaseModel):
    commit_sha: str
    author_email: str


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class PRismGraphState(BaseModel):
    repo_context: Optional[RepositoryContext] = None
    pr_context: Optional[PullRequestContext] = None
    parsed_diff: Optional[ParsedDiff] = None
    repo_tree: Optional[RepositoryTree] = None
    changed_files: List[ChangedFile] = Field(default_factory=list)
    git_metadata: Optional[GitMetadata] = None
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    execution_time_ms: float = 0.0
    final_risk_score: Optional[float] = None
    pr_summary: Optional[str] = None
