from langchain_core.messages import HumanMessage, SystemMessage

from ai.agents.base import BaseAgent
from ai.models.agent import AgentResult, Issue
from ai.models.state import PRismGraphState


class ArchitectureAgent(BaseAgent):
    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Analyzing architecture...")

        if not state.parsed_diff or not state.parsed_diff.diff_content:
            return AgentResult(
                agent_name=self.name,
                status="SUCCESS",
                issues=[],
            )

        messages = [
            SystemMessage(
                content="You are an Architecture Agent. Review the diff for layer violations, circular dependencies, coupling, and design patterns."
            ),
            HumanMessage(content=f"Diff:\n{state.parsed_diff.diff_content}"),
        ]

        # Call LLM
        _ = self.llm.invoke(messages)

        mock_issue = Issue(
            rule_id="ARCH-001",
            severity="MEDIUM",
            confidence=0.6,
            reasoning="Potential circular dependency introduced between components.",
        )

        return AgentResult(agent_name=self.name, status="SUCCESS", issues=[mock_issue])
