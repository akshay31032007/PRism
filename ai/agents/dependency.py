from langchain_core.messages import HumanMessage, SystemMessage

from ai.agents.base import BaseAgent
from ai.models.agent import AgentResult, Issue
from ai.models.state import PRismGraphState


class DependencyAgent(BaseAgent):
    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Analyzing dependencies...")

        # Check if dependency files are in the diff
        has_deps = any(
            f.path
            in [
                "requirements.txt",
                "package.json",
                "pom.xml",
                "Cargo.toml",
                "go.mod",
                "pyproject.toml",
            ]
            for f in state.changed_files
        )

        if not has_deps and (not state.parsed_diff or not state.parsed_diff.diff_content):
            return AgentResult(
                agent_name=self.name,
                status="SUCCESS",
                issues=[],
            )

        messages = [
            SystemMessage(
                content="You are a Dependency Agent. Review the diff for CVEs, license issues, outdated packages, and version conflicts in dependency files."
            ),
            HumanMessage(
                content=f"Diff:\n{state.parsed_diff.diff_content if state.parsed_diff else ''}"
            ),
        ]

        # Call LLM
        _ = self.llm.invoke(messages)

        mock_issue = Issue(
            rule_id="DEP-001",
            severity="HIGH",
            confidence=0.7,
            reasoning="Outdated package with known vulnerabilities identified.",
        )

        return AgentResult(
            agent_name=self.name, status="SUCCESS", issues=[mock_issue] if has_deps else []
        )
