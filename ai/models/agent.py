from typing import List, Optional

from pydantic import BaseModel, Field


class Issue(BaseModel):
    rule_id: str
    severity: str = Field(..., description="Severity level: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    suggested_fix: Optional[str] = None
    file_path: Optional[str] = None
    lines: Optional[List[int]] = None


class AgentResult(BaseModel):
    agent_name: str
    status: str = Field(..., description="Status: SUCCESS, FAILED, ERROR")
    issues: List[Issue] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
