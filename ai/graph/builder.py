"""
PRism AI — LangGraph Builder.

Assembles the full PRism review graph:

    repository_loader → context_builder → diff_parser
        ↓  (fan-out, parallel)
        security_agent, code_quality_agent, architecture_agent,
        documentation_agent, test_coverage_agent, dependency_agent,
        repo_qa_agent
        ↓  (fan-in — all converge)
    risk_aggregation → pr_summary → END

The compiled graph uses ``MemorySaver`` checkpointing so intermediate state
is preserved across LangGraph invocations (useful for debugging and resumption).

Public surface:
    ``build_prism_graph()`` — returns the compiled ``CompiledGraph``.
    ``run_graph(initial_state)`` — convenience wrapper that invokes the graph
        and returns the final ``PRismGraphState``.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ai.agents import (
    ArchitectureAgent,
    CodeQualityAgent,
    DependencyAgent,
    DocumentationAgent,
    RepositoryQAAgent,
    SecurityAgent,
    TestCoverageAgent,
)
from ai.graph.nodes import (
    context_builder_node,
    diff_parser_node,
    pr_summary_node,
    repository_loader_node,
    risk_aggregation_node,
)
from ai.models.state import PRismGraphState
from ai.utils.logger import get_logger

logger = get_logger("graph.builder")

# ---------------------------------------------------------------------------
# Agent instantiation — singletons reused across graph invocations.
# ---------------------------------------------------------------------------

_SECURITY_AGENT = SecurityAgent("Security")
_CODE_QUALITY_AGENT = CodeQualityAgent("Code Quality")
_ARCHITECTURE_AGENT = ArchitectureAgent("Architecture")
_DOCUMENTATION_AGENT = DocumentationAgent("Documentation")
_TEST_COVERAGE_AGENT = TestCoverageAgent("Test Coverage")
_DEPENDENCY_AGENT = DependencyAgent("Dependency")
_REPO_QA_AGENT = RepositoryQAAgent("Repository QA")

# Ordered list of (node_name, agent_instance) tuples used to wire the graph.
_AGENT_NODES = [
    ("security_agent", _SECURITY_AGENT),
    ("code_quality_agent", _CODE_QUALITY_AGENT),
    ("architecture_agent", _ARCHITECTURE_AGENT),
    ("documentation_agent", _DOCUMENTATION_AGENT),
    ("test_coverage_agent", _TEST_COVERAGE_AGENT),
    ("dependency_agent", _DEPENDENCY_AGENT),
    ("repo_qa_agent", _REPO_QA_AGENT),
]

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_prism_graph():
    """Build and compile the PRism LangGraph workflow.

    Returns:
        A compiled ``langgraph`` ``CompiledGraph`` with ``MemorySaver``
        checkpointing enabled.
    """
    logger.info("build_prism_graph: assembling PRism state-graph")

    workflow: StateGraph = StateGraph(PRismGraphState)

    # -----------------------------------------------------------------------
    # Pipeline nodes (sequential)
    # -----------------------------------------------------------------------
    workflow.add_node("repository_loader", repository_loader_node)
    workflow.add_node("context_builder", context_builder_node)
    workflow.add_node("diff_parser", diff_parser_node)

    # -----------------------------------------------------------------------
    # Parallel agent nodes (fan-out from diff_parser)
    # -----------------------------------------------------------------------
    agent_node_names = []
    for node_name, agent_instance in _AGENT_NODES:
        workflow.add_node(node_name, agent_instance.execute)
        agent_node_names.append(node_name)

    # -----------------------------------------------------------------------
    # Aggregation & summary nodes
    # -----------------------------------------------------------------------
    workflow.add_node("risk_aggregation", risk_aggregation_node)
    workflow.add_node("pr_summary", pr_summary_node)

    # -----------------------------------------------------------------------
    # Edges — sequential pipeline
    # -----------------------------------------------------------------------
    workflow.set_entry_point("repository_loader")
    workflow.add_edge("repository_loader", "context_builder")
    workflow.add_edge("context_builder", "diff_parser")

    # -----------------------------------------------------------------------
    # Fan-out: diff_parser → each agent (parallel execution)
    # Fan-in:  each agent → risk_aggregation
    # -----------------------------------------------------------------------
    for node_name in agent_node_names:
        workflow.add_edge("diff_parser", node_name)
        workflow.add_edge(node_name, "risk_aggregation")

    # -----------------------------------------------------------------------
    # Final pipeline
    # -----------------------------------------------------------------------
    workflow.add_edge("risk_aggregation", "pr_summary")
    workflow.add_edge("pr_summary", END)

    # -----------------------------------------------------------------------
    # Compile with MemorySaver checkpointing
    # -----------------------------------------------------------------------
    checkpointer = MemorySaver()
    compiled = workflow.compile(checkpointer=checkpointer)
    logger.info("build_prism_graph: graph compiled successfully")
    return compiled


# Module-level compiled graph singleton (lazy — avoids import-time LLM init).
_COMPILED_GRAPH = None


def _get_compiled_graph():
    """Return the module-level compiled graph, building it on first call."""
    global _COMPILED_GRAPH  # noqa: PLW0603
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_prism_graph()
    return _COMPILED_GRAPH


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------


def run_graph(initial_state: PRismGraphState) -> PRismGraphState:
    """Invoke the PRism LangGraph and return the final state.

    The graph is executed synchronously.  Each run uses a fresh
    ``thread_id`` so checkpointed state does not bleed across calls.

    Args:
        initial_state: A fully-populated ``PRismGraphState`` instance.
            At minimum ``parsed_diff`` should be set; all agent and
            aggregation fields will be populated by the graph.

    Returns:
        The final ``PRismGraphState`` after all nodes have executed,
        including ``agent_results``, ``final_risk_score``, and ``pr_summary``.

    Raises:
        Any exception propagated from a node that is not internally caught.
    """
    graph = _get_compiled_graph()

    # Each invocation uses a unique thread so MemorySaver stays clean.
    thread_id = str(uuid.uuid4())
    config: Dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    logger.info("run_graph: starting graph invocation", thread_id=thread_id)

    final_state_dict = graph.invoke(initial_state, config=config)

    # LangGraph returns a dict when the state schema is a Pydantic model;
    # coerce back to PRismGraphState.
    if isinstance(final_state_dict, dict):
        final_state = PRismGraphState(**final_state_dict)
    else:
        final_state = final_state_dict  # type: ignore[assignment]

    logger.info(
        "run_graph: graph invocation complete",
        thread_id=thread_id,
        final_risk_score=final_state.final_risk_score,
        agents_run=list(final_state.agent_results.keys()),
    )
    return final_state
