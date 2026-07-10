"""
Security Agent — detects OWASP Top 10 and additional vulnerabilities in PR diffs.

Flow:
  1. Build context: PR metadata + diff + RAG snippets
  2. Render the security.md prompt with all context
  3. Invoke LLM requesting JSON response
  4. Parse and validate the response into Issue objects
  5. Compute final score and return AgentResult
"""

from __future__ import annotations

import json
from typing import Any

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState
from ai.models.issues import Issue, IssueCategory, IssueSeverity
from ai.utils import BaseAgent, parse_llm_json


class SecurityAgent(BaseAgent):
    """
    Analyses PR diffs for security vulnerabilities.

    Checks (non-exhaustive):
      - SQL / Command / LDAP injection
      - XSS, CSRF, SSRF, Open Redirect
      - Path traversal, Zip Slip
      - Hardcoded secrets and weak crypto
      - Broken auth / missing authorisation
      - Sensitive data in logs
    """

    name     = "SecurityAgent"
    category = IssueCategory.SECURITY
    version  = "1.0.0"

    async def _analyse(self, state: GraphState) -> AgentResult:
        llm     = self._get_llm_wrapper()
        diff    = self._build_diff_summary(state)
        pr_meta = self._pr_metadata_block(state)

        repo_ctx = ""
        if state.repository_context:
            rc = state.repository_context
            repo_ctx = (
                f"Repository: {rc.full_name}\n"
                f"Language: {rc.primary_language or 'unknown'}\n"
                f"Topics: {', '.join(rc.topics) or 'none'}\n"
                f"Has security policy: {rc.has_security_policy}"
            )

        rag_ctx = state.rag_context or "No RAG context available for this PR."

        system_prompt = self._prompt_manager.render(
            "security",
            pr_metadata=pr_meta,
            repository_context=repo_ctx,
            rag_context=rag_ctx,
            diff=diff,
        )
        user_prompt = (
            "Perform a complete security analysis of the above PR. "
            "Return your findings as a single JSON object matching the schema. "
            "Be precise — only flag what is evidenced in the diff."
        )

        raw, p_tokens, c_tokens = await llm.ainvoke_json(system_prompt, user_prompt)

        issues  = self._parse_issues(raw.get("issues", []))
        score   = float(raw.get("score", 1.0))
        confidence = float(raw.get("confidence", 0.85))
        summary    = str(raw.get("summary", "Security analysis complete."))
        recommendations = [str(r) for r in raw.get("recommendations", [])]

        result = AgentResult(
            agent_name=self.name,
            category=self.category,
            status=AgentStatus.SUCCESS,
            issues=issues,
            score=max(0.0, min(1.0, score)),
            confidence=max(0.0, min(1.0, confidence)),
            summary=summary,
            recommendations=recommendations,
            llm_model_used=llm.model_name,
            prompt_tokens=p_tokens,
            output_tokens=c_tokens,
        )
        # Override score with computed value if LLM produced a suspiciously round number
        if score in (0.0, 1.0) and issues:
            result.score = result.compute_score()

        return result

    def _parse_issues(self, raw_issues: list[dict[str, Any]]) -> list[Issue]:
        """Parse and validate raw LLM issue dicts into Issue objects."""
        parsed: list[Issue] = []
        for idx, raw in enumerate(raw_issues, start=1):
            try:
                # Normalise rule_id: ensure SEC-NNN format
                rule_id = str(raw.get("rule_id", f"SEC-{idx:03d}")).upper()
                if not rule_id.startswith("SEC-"):
                    rule_id = f"SEC-{idx:03d}"

                severity_raw = str(raw.get("severity", "medium")).lower()
                try:
                    severity = IssueSeverity(severity_raw)
                except ValueError:
                    severity = IssueSeverity.MEDIUM

                issue = Issue(
                    rule_id=rule_id,
                    category=IssueCategory.SECURITY,
                    severity=severity,
                    title=str(raw.get("title", "Untitled security finding"))[:200],
                    description=str(raw.get("description", "No description provided.")),
                    file_path=raw.get("file_path") or None,
                    start_line=raw.get("start_line") or None,
                    end_line=raw.get("end_line") or None,
                    code_snippet=str(raw["code_snippet"])[:2000] if raw.get("code_snippet") else None,
                    confidence=float(raw.get("confidence", 0.8)),
                    suggested_fix=raw.get("suggested_fix") or None,
                    references=[str(r) for r in raw.get("references", [])],
                    tags=[str(t) for t in raw.get("tags", [])],
                )
                parsed.append(issue)
            except Exception as exc:  # noqa: BLE001
                self._log.warning("Skipping malformed issue at index %d: %s", idx, exc)
        return parsed
