"""
PRism AI — LangGraph Node Implementations.

Each function in this module is wired as a node inside the PRism state-graph.
Nodes receive a ``PRismGraphState`` instance, perform their work, mutate the
relevant fields, and return the (updated) state.

Node execution order:
    repository_loader → context_builder → diff_parser
        → [7 parallel agent nodes]
            → risk_aggregation → pr_summary → END
"""

from __future__ import annotations

from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage

from ai.llm.wrapper import LLMWrapper
from ai.models.state import PRismGraphState
from ai.utils.logger import get_logger

logger = get_logger("graph.nodes")

# ---------------------------------------------------------------------------
# Weight map: agent-result key → contribution weight (must sum ≤ 1.0).
# Keys must match the agent names used when calling agent.execute().
# ---------------------------------------------------------------------------
_RISK_WEIGHTS: Dict[str, float] = {
    "Security": 0.35,
    "Code Quality": 0.20,
    "Architecture": 0.15,
    "Test Coverage": 0.15,
    "Dependency": 0.10,
    "Documentation": 0.05,
    "Repository QA": 0.00,  # Included for completeness; contributes via default path
}

# Severity → raw score multiplier.
_SEVERITY_SCORES: Dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.7,
    "MEDIUM": 0.4,
    "LOW": 0.1,
}

# Default weight for agents not explicitly listed in _RISK_WEIGHTS (e.g. Repository QA).
_DEFAULT_AGENT_WEIGHT: float = 0.05


# ---------------------------------------------------------------------------
# Passthrough nodes — loading/parsing is handled externally before graph run.
# ---------------------------------------------------------------------------


def repository_loader_node(state: PRismGraphState) -> PRismGraphState:
    """Passthrough: repository cloning/loading is handled prior to graph invocation."""
    logger.info("repository_loader_node: passthrough", node="repository_loader")
    return state


def context_builder_node(state: PRismGraphState) -> PRismGraphState:
    """Passthrough: context is pre-populated in the initial state."""
    logger.info("context_builder_node: passthrough", node="context_builder")
    return state


def diff_parser_node(state: PRismGraphState) -> PRismGraphState:
    """Passthrough: diff parsing is pre-populated in the initial state."""
    logger.info("diff_parser_node: passthrough", node="diff_parser")
    return state


# ---------------------------------------------------------------------------
# Risk Aggregation — weighted scoring across all agent results.
# ---------------------------------------------------------------------------


def _compute_agent_sub_score(issues) -> float:
    """Compute a normalised sub-score for a single agent's issue list.

    The sub-score is the *average weighted severity* across all issues,
    clamped to [0.0, 1.0].  An empty issues list yields 0.0.

    Args:
        issues: List of ``Issue`` objects from the agent result.

    Returns:
        Float in [0.0, 1.0].
    """
    if not issues:
        return 0.0

    raw_total = sum(
        _SEVERITY_SCORES.get(issue.severity.upper(), 0.1) for issue in issues
    )
    # Normalise by issue count so a single CRITICAL doesn't dominate forever.
    sub_score = raw_total / max(len(issues), 1)
    return min(sub_score, 1.0)


def risk_aggregation_node(state: PRismGraphState) -> PRismGraphState:
    """Compute the final weighted risk score from all agent results.

    Algorithm
    ---------
    For each agent result:
      1. Compute a ``sub_score`` = sum(severity_weight per issue) / max(len(issues), 1)
      2. Look up the agent's contribution weight from ``_RISK_WEIGHTS``
         (fall back to ``_DEFAULT_AGENT_WEIGHT`` for unknown agents).
      3. Accumulate ``weight * sub_score`` into ``final_risk_score``.

    The result is clamped to [0.0, 1.0] and stored in ``state.final_risk_score``.
    """
    logger.info("risk_aggregation_node: computing weighted risk score", node="risk_aggregation")

    weighted_sum: float = 0.0
    weight_total: float = 0.0

    for agent_name, agent_result in state.agent_results.items():
        weight = _RISK_WEIGHTS.get(agent_name, _DEFAULT_AGENT_WEIGHT)
        sub_score = _compute_agent_sub_score(agent_result.issues)

        logger.info(
            "risk_aggregation_node: agent scored",
            agent=agent_name,
            weight=weight,
            sub_score=sub_score,
            issue_count=len(agent_result.issues),
        )

        weighted_sum += weight * sub_score
        weight_total += weight

    # Protect against divide-by-zero when no agents ran.
    if weight_total > 0:
        normalised = weighted_sum / weight_total
    else:
        normalised = 0.0

    state.final_risk_score = max(0.0, min(1.0, normalised))
    logger.info(
        "risk_aggregation_node: final risk score computed",
        final_risk_score=state.final_risk_score,
    )
    return state


# ---------------------------------------------------------------------------
# PR Summary — rich LLM-generated executive summary.
# ---------------------------------------------------------------------------

_PR_SUMMARY_SYSTEM_PROMPT = """You are PRism AI's Senior Engineering Review Synthesiser.

Your task is to produce a comprehensive, actionable Pull Request review summary
for an engineering team, based on findings from multiple specialised AI agents.

Your output MUST follow EXACTLY this structure (use Markdown headings):

## Executive Summary
One paragraph (3-5 sentences) giving a high-level assessment of the PR.

## Strengths
Bullet-point list of what the PR does well.

## Weaknesses
Bullet-point list of concrete problems found by the agents.

## Major Risks
Bullet-point list of the top 3-5 issues that could cause production incidents,
security breaches, or significant technical debt if left unaddressed.

## Business Impact
Short paragraph: what happens if this PR is merged as-is? What is the blast radius?

## Estimated Review Time
A realistic estimate of how long a thorough human review will take (e.g. "30 minutes",
"2 hours"), given the scope of changes.

## Suggested Review Order
Ordered list of files/areas the reviewer should examine first, based on risk.

## Merge Recommendation
Exactly ONE of the following tokens on its own line, followed by a brief justification:

- **APPROVE** — the PR is safe to merge with minor follow-ups.
- **REQUEST_CHANGES** — the PR needs fixes before merging; block until resolved.
- **BLOCK** — the PR must NOT be merged; critical issues detected.
"""

_PR_SUMMARY_HUMAN_TEMPLATE = """
## Pull Request Details
- **PR Title:** {pr_title}
- **Author:** {pr_author}
- **Changed Files ({files_changed}):** {changed_files_list}
- **Insertions:** {insertions} | **Deletions:** {deletions}
- **Final Risk Score:** {risk_score:.2f} / 1.00  ({risk_label})

## Agent Findings Summary
{agent_findings}

## Detailed Issue Breakdown
{detailed_issues}

Please produce the structured PR review summary as instructed.
"""


def _risk_label(score: float) -> str:
    """Map a numeric risk score to a human-readable label."""
    if score >= 0.80:
        return "🔴 CRITICAL"
    elif score >= 0.60:
        return "🟠 HIGH"
    elif score >= 0.40:
        return "🟡 MEDIUM"
    elif score >= 0.20:
        return "🟢 LOW"
    return "✅ MINIMAL"


def _build_agent_findings_text(state: PRismGraphState) -> str:
    """Summarise each agent's output as a compact markdown table row."""
    lines = ["| Agent | Status | Issues | Top Severity |", "| ----- | ------ | ------ | ------------ |"]
    for agent_name, result in state.agent_results.items():
        severities = [i.severity.upper() for i in result.issues]
        top_sev = "—"
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if sev in severities:
                top_sev = sev
                break
        lines.append(
            f"| {agent_name} | {result.status} | {len(result.issues)} | {top_sev} |"
        )
    return "\n".join(lines)


def _build_detailed_issues_text(state: PRismGraphState) -> str:
    """Format up to 20 issues across all agents for the LLM prompt."""
    parts: list[str] = []
    count = 0
    for agent_name, result in state.agent_results.items():
        for issue in result.issues:
            if count >= 20:
                parts.append("*(… additional issues truncated for brevity)*")
                break
            file_ref = f" [{issue.file_path}]" if issue.file_path else ""
            parts.append(
                f"- **[{issue.severity}]** `{issue.rule_id}`{file_ref}: {issue.reasoning}"
            )
            count += 1
    return "\n".join(parts) if parts else "No issues detected."


def pr_summary_node(state: PRismGraphState) -> PRismGraphState:
    """Generate an executive PR summary using the LLM.

    Builds a rich prompt that includes:
    - Issue counts and top severities per agent
    - Final risk score with label
    - Changed files list
    - Detailed breakdown of the top 20 issues

    The LLM response is stored verbatim in ``state.pr_summary``.
    """
    logger.info("pr_summary_node: generating PR summary", node="pr_summary")

    llm = LLMWrapper.get_llm()

    # Build context fragments.
    pr_title = state.pr_context.title if state.pr_context else "Unknown PR"
    pr_author = state.pr_context.author if state.pr_context else "Unknown"

    files_changed = state.parsed_diff.files_changed if state.parsed_diff else len(state.changed_files)
    insertions = state.parsed_diff.insertions if state.parsed_diff else 0
    deletions = state.parsed_diff.deletions if state.parsed_diff else 0

    changed_files_list = (
        ", ".join(f.path for f in state.changed_files[:10])
        + (" …" if len(state.changed_files) > 10 else "")
        if state.changed_files
        else "N/A"
    )

    risk_score = state.final_risk_score if state.final_risk_score is not None else 0.0
    agent_findings = _build_agent_findings_text(state)
    detailed_issues = _build_detailed_issues_text(state)

    human_content = _PR_SUMMARY_HUMAN_TEMPLATE.format(
        pr_title=pr_title,
        pr_author=pr_author,
        files_changed=files_changed,
        changed_files_list=changed_files_list,
        insertions=insertions,
        deletions=deletions,
        risk_score=risk_score,
        risk_label=_risk_label(risk_score),
        agent_findings=agent_findings,
        detailed_issues=detailed_issues,
    )

    messages = [
        SystemMessage(content=_PR_SUMMARY_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    logger.info("pr_summary_node: invoking LLM", node="pr_summary")
    response = llm.invoke(messages)
    state.pr_summary = response.content if hasattr(response, "content") else str(response)

    logger.info(
        "pr_summary_node: summary generated",
        node="pr_summary",
        summary_length=len(state.pr_summary),
    )
    return state
