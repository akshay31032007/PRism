"""
Documentation Agent — docstrings, PR description, API docs, README freshness.
"""

from __future__ import annotations

from typing import Any

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState
from ai.models.issues import Issue, IssueCategory, IssueSeverity
from ai.utils import BaseAgent


class DocumentationAgent(BaseAgent):
    """
    Evaluates documentation quality across all surfaces touched by the PR.

    Checks:
      - Docstrings on new public functions/classes/methods
      - PR description adequacy (why, not just what)
      - API endpoint documentation (OpenAPI/Swagger)
      - README and .env.example freshness
      - Changelog updates for user-facing changes
    """

    name     = "DocumentationAgent"
    category = IssueCategory.DOCUMENTATION
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
                f"Has README: {rc.has_readme}\n"
                f"Has CONTRIBUTING: {rc.has_contributing}"
            )

        system_prompt = self._prompt_manager.render(
            "documentation",
            pr_metadata=pr_meta,
            repository_context=repo_ctx,
            diff=diff,
        )
        user_prompt = (
            "Evaluate the documentation quality of this PR. "
            "Return a single valid JSON object. "
            "Reference specific functions, classes, or files from the diff."
        )

        raw, p_tokens, c_tokens = await llm.ainvoke_json(system_prompt, user_prompt)

        issues         = self._parse_issues(raw.get("issues", []))
        score          = float(raw.get("score", 1.0))
        confidence     = float(raw.get("confidence", 0.8))
        summary        = str(raw.get("summary", "Documentation analysis complete."))
        recommendations = [str(r) for r in raw.get("recommendations", [])]
        pr_desc_quality = str(raw.get("pr_description_quality", "unknown"))

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
            metadata={"pr_description_quality": pr_desc_quality},
        )
        if score in (0.0, 1.0) and issues:
            result.score = result.compute_score()
        return result

    def _parse_issues(self, raw_issues: list[dict[str, Any]]) -> list[Issue]:
        parsed: list[Issue] = []
        for idx, raw in enumerate(raw_issues, start=1):
            try:
                rule_id = str(raw.get("rule_id", f"DOC-{idx:03d}")).upper()
                if not rule_id.startswith("DOC"):
                    rule_id = f"DOC-{idx:03d}"
                severity_raw = str(raw.get("severity", "low")).lower()
                try:
                    severity = IssueSeverity(severity_raw)
                except ValueError:
                    severity = IssueSeverity.LOW
                parsed.append(Issue(
                    rule_id=rule_id,
                    category=self.category,
                    severity=severity,
                    title=str(raw.get("title", "Documentation issue"))[:200],
                    description=str(raw.get("description", "")),
                    file_path=raw.get("file_path") or None,
                    start_line=raw.get("start_line") or None,
                    end_line=raw.get("end_line") or None,
                    code_snippet=str(raw["code_snippet"])[:2000] if raw.get("code_snippet") else None,
                    confidence=float(raw.get("confidence", 0.75)),
                    suggested_fix=raw.get("suggested_fix") or None,
                    references=[str(r) for r in raw.get("references", [])],
                    tags=[str(t) for t in raw.get("tags", [])],
                ))
            except Exception as exc:  # noqa: BLE001
                self._log.warning("Skipping malformed doc issue %d: %s", idx, exc)
        return parsed
