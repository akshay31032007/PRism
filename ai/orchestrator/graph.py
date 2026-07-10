"""
LangGraph pipeline definition — assembles all nodes into a compiled graph.

Execution order:
  diff_parser → rag_retrieval → parallel_agents → merge_verdict → report

All nodes are async. The parallel_agents node fans out 7 agents concurrently
via asyncio.gather() inside the node itself (LangGraph doesn't yet have native
async fan-out; we implement it in the node body for full control).

Usage:
    from ai.orchestrator.graph import build_graph
    graph  = build_graph()
    result = await graph.ainvoke(initial_state)
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from ai.models.graph_state import GraphState
from ai.orchestrator.workflow import (
    diff_parser_node,
    merge_verdict_node,
    parallel_agents_node,
    rag_retrieval_node,
    report_node,
)
from ai.orchestrator.router import route_after_agents


def build_graph() -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph.

    Returns a compiled graph ready for ainvoke() / invoke().
    """
    builder = StateGraph(GraphState)

    # ── Add nodes ─────────────────────────────────────────────────────────────
    builder.add_node("diff_parser",      diff_parser_node)
    builder.add_node("rag_retrieval",    rag_retrieval_node)
    builder.add_node("parallel_agents",  parallel_agents_node)
    builder.add_node("merge_verdict",    merge_verdict_node)
    builder.add_node("report",           report_node)

    # ── Set entry point ───────────────────────────────────────────────────────
    builder.set_entry_point("diff_parser")

    # ── Linear edges ─────────────────────────────────────────────────────────
    builder.add_edge("diff_parser",     "rag_retrieval")
    builder.add_edge("rag_retrieval",   "parallel_agents")

    # ── Conditional edge: after agents, route to merge or report ─────────────
    builder.add_conditional_edges(
        "parallel_agents",
        route_after_agents,
        {
            "merge_verdict": "merge_verdict",
            "report":        "report",
        },
    )

    builder.add_edge("merge_verdict", "report")
    builder.add_edge("report",        END)

    return builder.compile()


# ── Module-level singleton ────────────────────────────────────────────────────
# Compiled once at import time; thread-safe for concurrent invocations.
_graph = None


def get_graph():
    """Return the compiled singleton graph, building it on first call."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
