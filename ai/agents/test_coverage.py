from langchain_core.messages import HumanMessage, SystemMessage

from ai.agents.base import BaseAgent
from ai.models.agent import AgentResult, Issue
from ai.models.state import PRismGraphState


class TestCoverageAgent(BaseAgent):
    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Analyzing test coverage...")

        if not state.parsed_diff or not state.parsed_diff.diff_content:
            return AgentResult(
                agent_name=self.name,
                status="SUCCESS",
                issues=[],
            )

        messages = [
            SystemMessage(
                content="You are a Test Coverage Agent. Review the diff for missing tests and edge cases."
            ),
            HumanMessage(content=f"Diff:\n{state.parsed_diff.diff_content}"),
        ]

        # Call LLM
        _ = self.llm.invoke(messages)

        mock_issue = Issue(
            rule_id="TEST-001",
            severity="MEDIUM",
            confidence=0.8,
            reasoning="New business logic added without corresponding unit tests.",
        )

        return AgentResult(agent_name=self.name, status="SUCCESS", issues=[mock_issue])
