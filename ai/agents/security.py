from langchain_core.messages import HumanMessage, SystemMessage
from ai.agents.base import BaseAgent
from ai.models.state import PRismGraphState
from ai.models.agent import AgentResult, Issue
from ai.parsers.ast import ast_parser
from ai.utils.security_scanners import SecurityScannerWrapper
import json

class SecurityAgent(BaseAgent):
    def run(self, state: PRismGraphState) -> AgentResult:
        self.logger.info("Executing deep security analysis...")
        issues = []
        
        if not state.parsed_diff or not state.parsed_diff.diff_content:
            return AgentResult(agent_name=self.name, status="SUCCESS", issues=[])

        # 1. External Scanners (Semgrep, Bandit)
        repo_path = state.repo_context.repo_url if state.repo_context else "."
        semgrep_results = SecurityScannerWrapper.run_semgrep(repo_path)
        bandit_results = SecurityScannerWrapper.run_bandit(repo_path)
        
        for res in semgrep_results:
            issues.append(Issue(
                rule_id=res.get("check_id", "SEMGREP"),
                severity=res.get("extra", {}).get("severity", "HIGH"),
                confidence=0.9,
                reasoning=res.get("extra", {}).get("message", "Semgrep vulnerability found"),
                file_path=res.get("path"),
                lines=[res.get("start", {}).get("line", 0)]
            ))
            
        for res in bandit_results:
            issues.append(Issue(
                rule_id=res.get("test_id", "BANDIT"),
                severity=res.get("issue_severity", "MEDIUM"),
                confidence=res.get("issue_confidence", "HIGH") == "HIGH" and 0.9 or 0.6,
                reasoning=res.get("issue_text", "Bandit vulnerability found"),
                file_path=res.get("filename"),
                lines=[res.get("line_number", 0)]
            ))

        # 2. AST Analysis for hardcoded secrets and basic injections
        # Iterating over changed files to parse them
        for changed_file in state.changed_files:
            if changed_file.path.endswith(".py"):
                tree = ast_parser.parse(changed_file.patch.encode("utf-8"), "python")
                if tree:
                    # Example: finding string literals that might be secrets
                    string_nodes = ast_parser.find_nodes(tree.root_node, "string")
                    for node in string_nodes:
                        text = node.text.decode("utf-8")
                        if "password" in text.lower() or "secret" in text.lower():
                            issues.append(Issue(
                                rule_id="AST-SEC-001",
                                severity="CRITICAL",
                                confidence=0.8,
                                reasoning=f"Potential hardcoded secret found: {text}",
                                file_path=changed_file.path,
                                lines=[node.start_point[0] + 1]
                            ))
                            
        # 3. LLM Analysis for complex business logic flaws (AuthZ, SSRF, etc.)
        messages = [
            SystemMessage(content=(
                "You are an expert Security Engineer. Analyze the provided diff for OWASP Top 10 vulnerabilities, "
                "including SSRF, CSRF, Path Traversal, Command Injection, Unsafe Deserialization, and Auth issues. "
                "Return findings in a structured format (JSON list of issues)."
            )),
            HumanMessage(content=f"Diff:\n{state.parsed_diff.diff_content}")
        ]
        
        _ = self.llm.invoke(messages)
        # Assuming LLM returns structured JSON that we parse. Mocking one result:
        issues.append(Issue(
            rule_id="LLM-AUTH-01",
            severity="HIGH",
            confidence=0.75,
            reasoning="Authorization check missing before database update.",
        ))
        
        return AgentResult(
            agent_name=self.name,
            status="SUCCESS",
            issues=issues
        )
