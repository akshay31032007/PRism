"""
Merge Recommendation Agent — risk aggregation and final verdict synthesis.

This is the final node in the parallel agent pipeline. It receives all
agent results from GraphState, invokes the merge.md prompt to synthesise
a final verdict, and writes a fully-populated MergeVerdict back to state.
"""

from __future__ import annotations

import json
from typing import Any

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState, MergeVerdict
from ai.models.issues import IssueCategory, IssueSeverity
from ai.utils import BaseAgent, get_logger

logger = get_logger("prism.agent.merge")


class MergeRecommendationAgent(BaseAgent):
    """
    Synthesises all agent findings into a final BLOCKED / CAUTION / READY_TO_MERGE verdict.

    Hard rules (applied before calling the LLM):
      - Any CRITICAL issue from any agent → BLOCKED
      - CI checks failing → BLOCKED
      - Two or more HIGH security issues → BLOCKED
      - These overrides prevent the LLM from hallucinating a passing verdict

    The LLM is then called to produce the full reasoning, strengths,
    weaknesses, risks, and review order.
    """

    name     = "MergeRecommendationAgent"
    category = IssueCategory.MERGE_READINESS
    version  = "1.0.0"

    async def _analyse(self, state: GraphState) -> AgentResult:
        llm = self._get_llm_wrapper()

        all_results = state.collect_all_agent_results()

        # ── Hard pre-flight checks (deterministic overrides) ──────────────────
        hard_block_reason = self._check_hard_blocks(state, all_results)

        # ── Build the agent results summary JSON for the prompt ───────────────
        results_summary = self._build_results_summary(all_results)
        pr_meta         = self._pr_metadata_block(state)

        agent_results_json = json.dumps(
            {
                "pr_metadata_text": pr_meta,
                "hard_block_reason": hard_block_reason,
                "agent_summaries": results_summary,
            },
            indent=2,
        )

        system_prompt = self._prompt_manager.render(
            "merge",
            agent_results_json=agent_results_json,
        )
        user_prompt = (
            "Based on all agent findings above, produce the final merge verdict JSON. "
            "If hard_block_reason is non-null, the verdict MUST be BLOCKED and that "
            "reason must appear in primary_reasoning."
        )

        raw, p_tokens, c_tokens = await llm.ainvoke_json(system_prompt, user_prompt)

        verdict_str = str(raw.get("verdict", "CAUTION")).upper()
        if verdict_str not in ("READY_TO_MERGE", "CAUTION", "BLOCKED"):
            verdict_str = "CAUTION"

        # Enforce hard blocks — never allow LLM to override deterministic rules
        if hard_block_reason and verdict_str == "READY_TO_MERGE":
            verdict_str = "BLOCKED"

        confidence_score   = float(raw.get("confidence_score",   0.7))
        overall_risk_score = float(raw.get("overall_risk_score", 0.5))
        primary_reasoning  = str(raw.get("primary_reasoning", "Analysis complete."))
        executive_summary  = raw.get("executive_summary")
        strengths          = [str(s) for s in raw.get("strengths",       [])]
        weaknesses         = [str(w) for w in raw.get("weaknesses",      [])]
        risks              = [str(r) for r in raw.get("risks",           [])]
        blocking_issues    = [str(b) for b in raw.get("blocking_issues", [])]
        review_order       = [str(f) for f in raw.get("review_order",    [])]

        verdict = MergeVerdict(
            verdict=verdict_str,
            confidence_score=max(0.0, min(1.0, confidence_score)),
            overall_risk_score=max(0.0, min(1.0, overall_risk_score)),
            primary_reasoning=primary_reasoning,
            executive_summary=executive_summary,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks,
            blocking_issues=blocking_issues,
            review_order=review_order,
        )

        # Write verdict to graph state
        state.final_verdict = verdict

        # Return an AgentResult for telemetry tracking
        return AgentResult(
            agent_name=self.name,
            category=self.category,
            status=AgentStatus.SUCCESS,
            issues=[],
            score=1.0 - overall_risk_score,
            confidence=confidence_score,
            summary=f"Final verdict: {verdict_str}. {primary_reasoning}",
            recommendations=[],
            llm_model_used=llm.model_name,
            prompt_tokens=p_tokens,
            output_tokens=c_tokens,
            metadata={
                "verdict": verdict_str,
                "overall_risk_score": overall_risk_score,
                "hard_block_reason": hard_block_reason,
            },
        )

    def _check_hard_blocks(
        self,
        state: GraphState,
        all_results: list[AgentResult],
    ) -> str | None:
        """
        Apply deterministic blocking rules that the LLM cannot override.

        Returns a reason string if blocked, None if no hard block.
        """
        # Rule 1: Failing CI checks
        pr = state.pull_request_context
        if pr and pr.ci_failure_count > 0:
            return (
                f"CI checks are failing ({pr.ci_failure_count} failure(s)). "
                "The PR cannot be merged until all checks pass."
            )

        # Rule 2: Any CRITICAL issue from any agent
        for result in all_results:
            for issue in result.issues:
                if issue.severity == IssueSeverity.CRITICAL:
                    return (
                        f"CRITICAL issue detected: [{issue.rule_id}] {issue.title} "
                        f"in {issue.file_path or 'unknown file'}."
                    )

        # Rule 3: Two or more HIGH security issues
        high_sec_count = sum(
            1 for r in all_results
            if r.category == IssueCategory.SECURITY
            for i in r.issues
            if i.severity == IssueSeverity.HIGH
        )
        if high_sec_count >= 2:
            return (
                f"{high_sec_count} HIGH-severity security issues detected. "
                "PR requires security remediation before merge."
            )

        return None

    def _build_results_summary(
        self, results: list[AgentResult]
    ) -> list[dict[str, Any]]:
        """Convert AgentResults to a compact summary dict for the LLM prompt."""
        summaries = []
        for r in results:
            summaries.append({
                "agent":            r.agent_name,
                "status":           r.status.value,
                "score":            round(r.score, 3),
                "confidence":       round(r.confidence, 3),
                "summary":          r.summary,
                "blocking_issues":  r.blocking_issue_count,
                "total_issues":     r.total_issue_count,
                "top_issues": [
                    {
                        "rule_id":   i.rule_id,
                        "severity":  i.severity.value,
                        "title":     i.title,
                        "file_path": i.file_path,
                    }
                    for i in sorted(
                        r.issues,
                        key=lambda x: ["critical","high","medium","low","info"].index(x.severity.value),
                    )[:5]
                ],
                "recommendations": r.recommendations[:3],
            })
        return summaries
