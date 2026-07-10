"""
LangGraph conditional edge router.

After the parallel agent fan-out completes, the router inspects
GraphState and decides whether to proceed to the merge verdict node
or to short-circuit directly to the report node.
"""

from __future__ import annotations

from ai.models.graph_state import GraphState


def route_after_agents(state: GraphState) -> str:
    """
    Called after all parallel agent nodes complete.

    Returns the name of the next node to execute.

    Logic:
    - If any critical error caused all agents to fail → go straight to report
      with a degraded verdict (the merge node will handle partial results).
    - Otherwise → proceed to merge_verdict node normally.
    """
    completed = state.collect_all_agent_results()
    if not completed:
        # Nothing ran — likely an upstream failure in the diff parser
        return "report"
    return "merge_verdict"


def route_after_loader(state: GraphState) -> str:
    """
    Called after the repository loader node.

    If the loader failed to populate repository_context, skip straight
    to the diff parser (it can still work without repo context).
    """
    if state.repository_context is None:
        return "diff_parser"
    return "rag_retrieval"
