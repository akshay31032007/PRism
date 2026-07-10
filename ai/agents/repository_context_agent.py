"""
Repository Context Agent — Dependency security, licensing, supply chain risk.

Note: Despite the filename (repository_context_agent.py in the spec folder),
this implements the Dependency Agent role from the engineering spec §7.6.
The repository_context_agent name is preserved for folder compatibility.
"""

from __future__ import annotations

from typing import Any

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState
from ai.models.issues import Issue, IssueCategory, IssueSeverity
from ai.utils import BaseAgent


class DependencyAgent(BaseAgent):
    """
    Audits dependency changes in PR for security and supply chain risks.

    Checks:
      - Known CVEs in newly added / updated packages
      - Typosquatting risk (suspicious package names)
      - Floating (unpinned) version specifiers
      - License compatibility (GPL/AGPL in commercial projects)
      - Abandoned or unmaintained packages
      - Dev dependencies promoted to production sections
    """

    name     = "DependencyAgent"
    category = IssueCategory.DEPENDENCY
    version  = "1.0.0"

    async def _analyse(self, state: GraphState) -> AgentResult:
        llm     = self._get_llm_wrapper()
        diff    = self._build_diff_summary(state)
        pr_meta = self._pr_metadata_block(state)

        # Build a summary of known dependency files in the repo
        dep_files_text = "No dependency files found."
        if state.repository_context and state.repository_context.dependency_files:
            lines = []
            for df in state.repository_context.dependency_files[:5]:
                # Send file content but cap it to avoid blowing the context window
                content_preview = df.content[:3000] + "..." if len(df.content) > 3000 else df.content
                lines.append(f"### {df.path} (ecosystem: {df.ecosystem})\n{content_preview}")
            dep_files_text = "\n\n".join(lines)

        # Check whether this PR actually touches any dependency files
        has_dep_changes = False
        if state.parsed_diff:
            dep_filenames = {
                "requirements.txt", "requirements-dev.txt", "setup.py",
                "setup.cfg", "pyproject.toml", "package.json", "package-lock.json",
                "yarn.lock", "pom.xml", "build.gradle", "Cargo.toml",
                "Cargo.lock", "go.mod", "go.sum", "Gemfile", "Gemfile.lock",
            }
            for f in state.parsed_diff.files:
                fname = f.filename.split("/")[-1].lower()
                if fname in dep_filenames:
                    has_dep_changes = True
                    break

        if not has_dep_changes:
            return AgentResult(
                agent_name=self.name,
                category=self.category,
                status=AgentStatus.SKIPPED,
                issues=[],
                score=1.0,
                confidence=1.0,
                summary=(
                    "No dependency manifest files were modified in this PR. "
                    "Dependency analysis was skipped."
                ),
                recommendations=[],
            )

        system_prompt = self._prompt_manager.render(
            "dependency",
            pr_metadata=pr_meta,
            dependency_files=dep_files_text,
            diff=diff,
        )
        user_prompt = (
            "Audit the dependency changes in this PR. "
            "Return a single valid JSON object. "
            "Do NOT fabricate CVE IDs — only report CVEs you are confident are real."
        )

        raw, p_tokens, c_tokens = await llm.ainvoke_json(system_prompt, user_prompt)

        issues          = self._parse_issues(raw.get("issues", []))
        score           = float(raw.get("score", 1.0))
        confidence      = float(raw.get("confidence", 0.8))
        summary         = str(raw.get("summary", "Dependency analysis complete."))
        recommendations = [str(r) for r in raw.get("recommendations", [])]
        dep_changes     = raw.get("dependency_changes", {})

        result = AgentResult(
            agent_name=self.name,
            category=self.category,
            status=AgentStatus.SUCCESS,
            issues=issues,
            score=max(0.0, min(1.0, score)),
            confidence=max(0.0, min(1.0, confidence)),
            summary=summary,
            recommendations=recommendations,
            llm_model_used=llm.model_name,
            prompt_tokens=p_tokens,
            output_tokens=c_tokens,
            metadata={"dependency_changes": dep_changes},
        )
        if score in (0.0, 1.0) and issues:
            result.score = result.compute_score()
        return result

    def _parse_issues(self, raw_issues: list[dict[str, Any]]) -> list[Issue]:
        parsed: list[Issue] = []
        for idx, raw in enumerate(raw_issues, start=1):
            try:
                rule_id = str(raw.get("rule_id", f"DEP-{idx:03d}")).upper()
                if not rule_id.startswith("DEP"):
                    rule_id = f"DEP-{idx:03d}"
                severity_raw = str(raw.get("severity", "medium")).lower()
                try:
                    severity = IssueSeverity(severity_raw)
                except ValueError:
                    severity = IssueSeverity.MEDIUM
                parsed.append(Issue(
                    rule_id=rule_id,
                    category=self.category,
                    severity=severity,
                    title=str(raw.get("title", "Dependency issue"))[:200],
                    description=str(raw.get("description", "")),
                    file_path=raw.get("file_path") or None,
                    start_line=raw.get("start_line") or None,
                    end_line=raw.get("end_line") or None,
                    code_snippet=str(raw["code_snippet"])[:2000] if raw.get("code_snippet") else None,
                    confidence=float(raw.get("confidence", 0.8)),
                    suggested_fix=raw.get("suggested_fix") or None,
                    references=[str(r) for r in raw.get("references", [])],
                    tags=[str(t) for t in raw.get("tags", [])],
                ))
            except Exception as exc:  # noqa: BLE001
                self._log.warning("Skipping malformed dep issue %d: %s", idx, exc)
        return parsed
