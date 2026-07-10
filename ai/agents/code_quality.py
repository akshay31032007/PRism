from langchain_core.messages import HumanMessage, SystemMessage

from ai.agents.base import BaseAgent
from ai.models.state import PRismGraphState
from ai.models.agent import AgentResult, Issue
from ai.parsers.ast import ast_parser

class CodeQualityAgent(BaseAgent):
    def _calculate_complexity(self, node) -> int:
        """Naive calculation of cyclomatic complexity from AST node."""
        complexity = 1
        # Simple keywords that increase complexity in python
        decision_types = ["if_statement", "for_statement", "while_statement", "except_clause", "with_item"]
        results = []
        for t in decision_types:
            results.extend(ast_parser.find_nodes(node, t))
        return complexity + len(results)

    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Executing deep code quality analysis...")
        issues = []
        
        if not state.parsed_diff or not state.parsed_diff.diff_content:
            return AgentResult(agent_name=self.name, status="SUCCESS", issues=[])

        # 1. AST Analysis for Cyclomatic Complexity & Long Methods
        for changed_file in state.changed_files:
            if changed_file.path.endswith(".py"):
                tree = ast_parser.parse(changed_file.patch.encode("utf-8"), "python")
                if tree:
                    functions = ast_parser.extract_function_definitions(tree.root_node, "python")
                    for func in functions:
                        # Long method check
                        line_count = func.end_point[0] - func.start_point[0]
                        if line_count > 50:
                            issues.append(Issue(
                                rule_id="CQ-LONG-METHOD",
                                severity="MEDIUM",
                                confidence=0.9,
                                reasoning=f"Method exceeds 50 lines ({line_count} lines). Consider refactoring.",
                                file_path=changed_file.path,
                                lines=[func.start_point[0] + 1]
                            ))
                            
                        # Cyclomatic complexity check
                        complexity = self._calculate_complexity(func)
                        if complexity > 10:
                            issues.append(Issue(
                                rule_id="CQ-COMPLEXITY",
                                severity="HIGH",
                                confidence=0.9,
                                reasoning=f"High cyclomatic complexity detected (Score: {complexity}).",
                                file_path=changed_file.path,
                                lines=[func.start_point[0] + 1]
                            ))

        # 2. LLM Analysis for SOLID, Clean Architecture, Naming, Refactoring
        messages = [
            SystemMessage(content=(
                "You are an expert Code Quality Agent. Review the diff for violations of SOLID principles, "
                "Clean Architecture, poor naming conventions, dead code, and duplicate code. "
                "Provide actionable refactoring suggestions and a maintainability score. "
                "Return findings in a structured format (JSON list of issues)."
            )),
            HumanMessage(content=f"Diff:\n{state.parsed_diff.diff_content}")
        ]
        
        _ = self.llm.invoke(messages)
        
        # Mocking LLM structured result
        issues.append(Issue(
            rule_id="CQ-SOLID-SRP",
            severity="MEDIUM",
            confidence=0.8,
            reasoning="Function handles both data fetching and formatting (violates Single Responsibility Principle).",
        ))
        
        return AgentResult(
            agent_name=self.name,
            status="SUCCESS",
            issues=issues
        )
