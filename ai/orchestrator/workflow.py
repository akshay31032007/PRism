"""
LangGraph node implementations — each function is one node in the graph.

Node contract:  async def node_name(state: GraphState) -> GraphState
Every node reads from state, does its work, and returns the mutated state.
Nodes NEVER raise — they log errors and write to state.errors.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from ai.agents.architecture_agent    import ArchitectureAgent
from ai.agents.code_quality_agent    import CodeQualityAgent
from ai.agents.documentation_agent   import DocumentationAgent
from ai.agents.merge_recommendation_agent import MergeRecommendationAgent
from ai.agents.performance_agent     import PerformanceAgent
from ai.agents.repository_context_agent  import DependencyAgent
from ai.agents.security_agent        import SecurityAgent
from ai.agents.testing_agent         import TestingAgent
from ai.models.graph_state           import GraphState
from ai.utils                        import get_logger

logger = get_logger("prism.orchestrator.workflow")


# ── Node: diff_parser ─────────────────────────────────────────────────────────

async def diff_parser_node(state: GraphState) -> GraphState:
    """
    Parses the raw file patches from PullRequestContext into a structured
    ParsedDiff with per-line HunkLine objects.

    Depends on: state.pull_request_context (set by context builder)
    Writes:     state.parsed_diff
    """
    t0 = time.perf_counter()
    try:
        from ai.models.pr_context import FileDiff, HunkLine, ParsedDiff
        from backend.config import get_settings
        settings = get_settings()

        if not state.pull_request_context:
            state.add_error("diff_parser", "No pull_request_context available.")
            state.parsed_diff = ParsedDiff()
            return state

        # Pull raw file diffs — stored via __dict__ by github_service
        raw_files: list[Any] = state.pull_request_context.__dict__.get("_raw_files", [])

        file_diffs: list[FileDiff] = []
        total_add = 0
        total_del = 0
        truncated = False
        char_budget = settings.max_diff_chars
        chars_used  = 0

        for rf in raw_files:
            if chars_used >= char_budget:
                truncated = True
                break

            patch = rf.get("patch", "") or ""
            chars_used += len(patch)
            if chars_used > char_budget:
                patch = patch[: char_budget - (chars_used - len(patch))]
                truncated = True

            additions = rf.get("additions", 0)
            deletions = rf.get("deletions", 0)
            total_add += additions
            total_del += deletions

            # Parse patch lines
            lines: list[HunkLine] = []
            new_lineno = 1
            old_lineno = 1
            for raw_line in patch.splitlines():
                if raw_line.startswith("@@"):
                    # Parse hunk header: @@ -old_start,count +new_start,count @@
                    import re
                    m = re.search(r"-(\d+)(?:,\d+)? \+(\d+)", raw_line)
                    if m:
                        old_lineno = int(m.group(1))
                        new_lineno = int(m.group(2))
                    continue
                if raw_line.startswith("+") and not raw_line.startswith("+++"):
                    lines.append(HunkLine(
                        line_number_new=new_lineno,
                        content=raw_line,
                        line_type="added",
                    ))
                    new_lineno += 1
                elif raw_line.startswith("-") and not raw_line.startswith("---"):
                    lines.append(HunkLine(
                        line_number_old=old_lineno,
                        content=raw_line,
                        line_type="removed",
                    ))
                    old_lineno += 1
                else:
                    lines.append(HunkLine(
                        line_number_old=old_lineno,
                        line_number_new=new_lineno,
                        content=raw_line,
                        line_type="context",
                    ))
                    old_lineno += 1
                    new_lineno += 1

            file_diffs.append(FileDiff(
                filename=rf.get("filename", "unknown"),
                status=rf.get("status", "modified"),
                additions=additions,
                deletions=deletions,
                patch=patch,
                lines=lines,
            ))

        state.parsed_diff = ParsedDiff(
            files=file_diffs,
            total_additions=total_add,
            total_deletions=total_del,
            truncated=truncated,
            truncated_at_chars=char_budget if truncated else None,
        )
        logger.info(
            "diff_parser: parsed %d files, +%d/-%d lines, truncated=%s",
            len(file_diffs), total_add, total_del, truncated,
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("diff_parser_node failed: %s", exc, exc_info=True)
        state.add_error("diff_parser", str(exc))

    state.execution_metrics.record("diff_parser", time.perf_counter() - t0)
    return state


# ── Node: rag_retrieval ───────────────────────────────────────────────────────

async def rag_retrieval_node(state: GraphState) -> GraphState:
    """
    Retrieves relevant codebase context snippets from the vector store.

    Depends on: state.repository_context, state.pull_request_context
    Writes:     state.rag_context
    """
    t0 = time.perf_counter()
    try:
        if not state.owner or not state.repo:
            state.rag_context = ""
            return state

        from rag.retriever import PRismRetriever

        retriever = PRismRetriever(owner=state.owner, repo=state.repo)
        pr = state.pull_request_context

        changed_files: list[str] = []
        if state.parsed_diff:
            changed_files = [f.filename for f in state.parsed_diff.files]

        pr_title = pr.title if pr else (state.analysis_id or "")
        pr_body  = pr.body  if pr else None

        state.rag_context = await retriever.retrieve_for_diff(
            changed_files=changed_files,
            pr_title=pr_title,
            pr_description=pr_body,
        )
        logger.debug("rag_retrieval: retrieved %d chars", len(state.rag_context or ""))

    except Exception as exc:  # noqa: BLE001
        logger.warning("rag_retrieval_node failed (non-fatal): %s", exc)
        state.rag_context = ""

    state.execution_metrics.record("rag_retrieval", time.perf_counter() - t0)
    return state


# ── Node: parallel_agents ────────────────────────────────────────────────────

async def parallel_agents_node(state: GraphState) -> GraphState:
    """
    Runs all 7 specialist agents sequentially in two batches with a short
    delay between batches to stay within Groq's free-tier TPM limit (12k/min).
    """
    t0 = time.perf_counter()

    batch1 = [SecurityAgent(), CodeQualityAgent(), TestingAgent()]
    batch2 = [ArchitectureAgent(), DocumentationAgent(), PerformanceAgent(), DependencyAgent()]

    logger.info("parallel_agents: launching batch 1 (%d agents)", len(batch1))
    results1 = await asyncio.gather(*[a.run(state) for a in batch1])

    # Brief pause between batches to respect TPM limits on free-tier Groq
    await asyncio.sleep(4)

    logger.info("parallel_agents: launching batch 2 (%d agents)", len(batch2))
    results2 = await asyncio.gather(*[a.run(state) for a in batch2])

    all_results = list(results1) + list(results2)
    (
        state.security_result,
        state.code_quality_result,
        state.testing_result,
        state.architecture_result,
        state.documentation_result,
        state.performance_result,
        state.dependency_result,
    ) = all_results

    for r in all_results:
        state.token_usage.add(r.prompt_tokens, r.output_tokens)

    total_issues = sum(r.total_issue_count for r in all_results)
    blocking     = sum(r.blocking_issue_count for r in all_results)
    logger.info("parallel_agents: complete. total_issues=%d blocking=%d", total_issues, blocking)

    state.execution_metrics.record("parallel_agents", time.perf_counter() - t0)
    return state


# ── Node: merge_verdict ───────────────────────────────────────────────────────

async def merge_verdict_node(state: GraphState) -> GraphState:
    """
    Runs the MergeRecommendationAgent to synthesise the final verdict.

    Writes: state.final_verdict (via agent), plus agent result telemetry.
    """
    t0 = time.perf_counter()
    try:
        agent  = MergeRecommendationAgent()
        result = await agent.run(state)
        state.token_usage.add(result.prompt_tokens, result.output_tokens)
        logger.info(
            "merge_verdict: verdict=%s confidence=%.2f",
            state.final_verdict.verdict if state.final_verdict else "UNKNOWN",
            state.final_verdict.confidence_score if state.final_verdict else 0.0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("merge_verdict_node failed: %s", exc, exc_info=True)
        state.add_error("merge_verdict", str(exc))
        # Fallback verdict
        from ai.models.graph_state import MergeVerdict
        state.final_verdict = MergeVerdict(
            verdict="CAUTION",
            confidence_score=0.3,
            overall_risk_score=0.7,
            primary_reasoning=f"Verdict synthesis failed due to an internal error: {exc}",
        )

    state.execution_metrics.record("merge_verdict", time.perf_counter() - t0)
    return state


# ── Node: report ─────────────────────────────────────────────────────────────

async def report_node(state: GraphState) -> GraphState:
    """
    Generates the final markdown GitHub comment report.
    Builds the report directly from structured agent data without an extra
    LLM call — this avoids a second TPM hit on Groq's free tier and makes
    the report deterministic and fast.
    """
    t0 = time.perf_counter()
    try:
        verdict  = state.final_verdict
        results  = state.collect_all_agent_results()
        pr       = state.pull_request_context
        repo     = state.repository_context

        verdict_emoji = {
            "READY_TO_MERGE": "🟢", "CAUTION": "🟡", "BLOCKED": "🔴"
        }.get(verdict.verdict if verdict else "", "⚪")

        sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}

        lines: list[str] = []

        # ── Header ──────────────────────────────────────────────────────────
        pr_title = pr.title if pr else f"PR #{state.pr_number}"
        lines.append(f"# PRism AI Analysis Report")
        lines.append(f"## PR #{state.pr_number}: {pr_title}")
        lines.append("")

        # ── Verdict banner ───────────────────────────────────────────────────
        if verdict:
            v_label  = verdict.verdict.replace("_", " ")
            conf_pct = round(verdict.confidence_score * 100)
            callout  = {"READY_TO_MERGE": "[!NOTE]", "CAUTION": "[!WARNING]", "BLOCKED": "[!CAUTION]"}.get(verdict.verdict, "[!NOTE]")
            lines.append(f"### Verdict: {verdict_emoji} {v_label}  (Confidence: {conf_pct}%)")
            lines.append("")
            lines.append(f"> {callout}")
            lines.append(f"> {verdict.primary_reasoning}")
            lines.append("")

            if verdict.executive_summary:
                lines.append("### Executive Summary")
                lines.append(verdict.executive_summary)
                lines.append("")

        # ── Agent scorecard ──────────────────────────────────────────────────
        lines.append("### Agent Scorecard")
        lines.append("")
        lines.append("| Agent | Score | Issues | Blocking | Status |")
        lines.append("|-------|-------|--------|----------|--------|")
        for r in results:
            pct   = round(r.score * 100)
            bar   = "🟢" if pct >= 80 else ("🟡" if pct >= 50 else "🔴")
            lines.append(
                f"| {r.agent_name.replace('Agent','')} | {bar} {pct}% "
                f"| {r.total_issue_count} | {r.blocking_issue_count} | {r.status.value} |"
            )
        lines.append("")

        # ── Blocking issues ──────────────────────────────────────────────────
        if verdict and verdict.blocking_issues:
            lines.append("### 🔴 Blocking Issues")
            for issue in verdict.blocking_issues:
                lines.append(f"- {issue}")
            lines.append("")

        # ── Findings by domain ───────────────────────────────────────────────
        lines.append("### Findings by Domain")
        lines.append("")
        for r in results:
            if not r.issues:
                continue
            lines.append(f"<details>")
            lines.append(f"<summary><strong>{r.agent_name}</strong> — {r.total_issue_count} issue(s)</summary>")
            lines.append("")
            for issue in r.issues:
                emoji = sev_emoji.get(issue.severity.value, "⚪")
                loc   = f" `{issue.file_path}:{issue.start_line}`" if issue.file_path else ""
                lines.append(f"**{emoji} [{issue.rule_id}] {issue.title}**{loc}")
                lines.append(f"> {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"")
                    lines.append(f"*Fix:* {issue.suggested_fix}")
                lines.append("")
            lines.append("</details>")
            lines.append("")

        # ── Strengths ────────────────────────────────────────────────────────
        if verdict and verdict.strengths:
            lines.append("### ✅ Strengths")
            for s in verdict.strengths:
                lines.append(f"- {s}")
            lines.append("")

        # ── Recommendations ──────────────────────────────────────────────────
        all_recs: list[str] = []
        for r in results:
            all_recs.extend(r.recommendations[:2])
        if all_recs:
            lines.append("### Recommendations")
            for rec in all_recs[:10]:
                lines.append(f"- {rec}")
            lines.append("")

        # ── Review order ─────────────────────────────────────────────────────
        if verdict and verdict.review_order:
            lines.append("### Recommended Review Order")
            for i, f in enumerate(verdict.review_order[:8], 1):
                lines.append(f"{i}. `{f}`")
            lines.append("")

        # ── Footer ────────────────────────────────────────────────────────────
        repo_name = repo.full_name if repo else f"{state.owner}/{state.repo}"
        lines.append("---")
        lines.append(
            f"*Generated by PRism AI · {repo_name} · "
            f"Tokens: {state.token_usage.total_tokens:,} · "
            f"Latency: {round(state.execution_metrics.total_latency_s, 1)}s*"
        )

        state.final_report = "\n".join(lines)

    except Exception as exc:
        logger.error("report_node failed: %s", exc, exc_info=True)
        state.add_error("report", str(exc))
        verdict = state.final_verdict
        state.final_report = (
            f"# PRism AI Analysis\n\n"
            f"**Verdict**: {verdict.verdict if verdict else 'UNKNOWN'}\n\n"
            f"{verdict.primary_reasoning if verdict else ''}"
        )

    state.execution_metrics.record("report", time.perf_counter() - t0)
    state.execution_metrics.finish()
    return state


def _build_pr_meta_text(state: GraphState) -> str:
    pr   = state.pull_request_context
    repo = state.repository_context
    if not pr:
        return f"PR #{state.pr_number} — metadata unavailable"
    lines = [
        f"PR #{pr.number}: {pr.title}",
        f"Repository: {repo.full_name if repo else state.repo}",
        f"Author: {pr.author or 'unknown'}  |  Branch: "
        f"{state.git_metadata.head_branch if state.git_metadata else 'unknown'}",
        f"CI: {'PASSING' if pr.all_ci_passing else f'FAILING ({pr.ci_failure_count} failures)'}",
    ]
    return "\n".join(lines)
