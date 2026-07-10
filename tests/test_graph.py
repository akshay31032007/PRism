import pytest

from ai.graph.builder import build_prism_graph
from ai.models.state import PRismGraphState


def test_graph_compilation():
    workflow = build_prism_graph()
    assert workflow is not None


@pytest.mark.asyncio
async def test_graph_execution():
    workflow = build_prism_graph()

    initial_state = PRismGraphState()

    # Normally we would use a mock LLM here for tests to avoid hitting the actual API
    # Since our agents are just using the LLM directly, we'd mock LLMWrapper.
    # For now, we will just ensure the structure executes without raising unexpected errors.
    # This is a placeholder for a complete execution test.
    pass
