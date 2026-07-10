"""
Testing Agent — missing tests, edge cases, coverage gaps, test quality.
"""

from __future__ import annotations

from typing import Any

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState
from ai.models.issues import Issue, IssueCategory, IssueSeverity
from ai.utils import BaseAgent


class TestingAgent(BaseAgent):
    """
    Evaluates test coverage and quality of changes in the PR.

    Checks:
      - New functions / classes missing unit tests
      - Edge cases and error paths not covered
      - Overly broad mocks hiding real integration issues
      - Deleted tests without replacement
      - Coverage metric delta (estimated from diff)
    """

    name     = "TestingAgent"
    category = IssueCategory.TESTING
    version  = "1.0.0"

    async def _analyse(self, state: GraphState) -> AgentResult:
        llm     = self._get_llm_wrapper()
        diff    = self._build_diff_summary(state)
        pr_meta = self._pr_metadata_block(state)

        # Count test files in diff to give agent useful signal
        test_file_count = 0
        prod_file_count = 0
        if state.parsed_diff:
            for f in state.parsed_diff.files:
                if f.is_test_file:
                    test_file_count += 1
                else:
                    prod_file_count += 1

        repo_ctx = f"Test files in diff: {test_file_count}\nProduction files in diff: {prod_file_count}"
        if state.repository_context:
            rc = state.repository_context
            repo_ctx += f"\nLanguage: {rc.primary_language or 'unknown'}"

        system_prompt = self._prompt_manager.render(
            "testing",
            pr_metadata=pr_meta,
            repository_context=repo_ctx,
            diff=diff,
        )
        user_prompt = (
            "Evaluate the test coverage and quality of this PR. "
            "Return a single valid JSON object. "
            "For every HIGH issue, include a skeleton test case in suggested_fix."
        )

        raw, p_tokens, c_tokens = await llm.ainvoke_json(system_prompt, user_prompt)

        issues         = self._parse_issues(raw.get("issues", []))
        score          = float(raw.get("score", 1.0))
        confidence     = float(raw.get("confidence", 0.8))
        summary        = str(raw.get("summary", "Testing analysis complete."))
        recommendations = [str(r) for r in raw.get("recommendations", [])]
        coverage_meta  = raw.get("coverage_assessment", {})

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
            metadata={
                "coverage_assessment": coverage_meta,
                "test_files_in_diff": test_file_count,
                "prod_files_in_diff": prod_file_count,
            },
        )
        if score in (0.0, 1.0) and issues:
            result.score = result.compute_score()
        return result

    def _parse_issues(self, raw_issues: list[dict[str, Any]]) -> list[Issue]:
        parsed: list[Issue] = []
        for idx, raw in enumerate(raw_issues, start=1):
            try:
                rule_id = str(raw.get("rule_id", f"TEST-{idx:03d}")).upper()
                if not rule_id.startswith("TEST"):
                    rule_id = f"TEST-{idx:03d}"
                severity_raw = str(raw.get("severity", "medium")).lower()
                try:
                    severity = IssueSeverity(severity_raw)
                except ValueError:
                    severity = IssueSeverity.MEDIUM
                parsed.append(Issue(
                    rule_id=rule_id,
                    category=self.category,
                    severity=severity,
                    title=str(raw.get("title", "Testing gap"))[:200],
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
                self._log.warning("Skipping malformed test issue %d: %s", idx, exc)
        return parsed
