from ai.agents.security import SecurityAgent
from ai.models.state import PRismGraphState


def test_security_agent_initialization():
    agent = SecurityAgent("Security")
    assert agent.name == "Security"
    assert agent.llm is not None


def test_security_agent_empty_state():
    agent = SecurityAgent("Security")
    state = PRismGraphState()
    result = agent.run(state)
    assert result.status == "SUCCESS"
    assert len(result.issues) == 0
