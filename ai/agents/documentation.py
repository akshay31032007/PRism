from langchain_core.messages import HumanMessage, SystemMessage

from ai.agents.base import BaseAgent
from ai.models.agent import AgentResult, Issue
from ai.models.state import PRismGraphState


class DocumentationAgent(BaseAgent):
    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Analyzing documentation...")

        if not state.parsed_diff or not state.parsed_diff.diff_content:
            return AgentResult(
                agent_name=self.name,
                status="SUCCESS",
                issues=[],
            )

        messages = [
            SystemMessage(
                content="You are a Documentation Agent. Review the diff for missing or outdated comments, docstrings, and README updates."
            ),
            HumanMessage(content=f"Diff:\n{state.parsed_diff.diff_content}"),
        ]

        # Call LLM
        _ = self.llm.invoke(messages)

        mock_issue = Issue(
            rule_id="DOC-001",
            severity="LOW",
            confidence=0.9,
            reasoning="Missing docstring for new public method.",
        )

        return AgentResult(agent_name=self.name, status="SUCCESS", issues=[mock_issue])
