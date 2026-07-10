"""
GitHub Service — all GitHub API interaction lives here.

Responsibilities:
  - Parse GitHub PR URLs into (owner, repo, pr_number)
  - Fetch PR metadata, file diffs, CI check-runs
  - Populate PullRequestContext, RepositoryContext, GitMetadata
  - Fetch raw repository file tree for RAG indexing

Never raises on rate-limits or 404 — returns None and logs the error
so the pipeline can degrade gracefully.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

import httpx

from ai.models.pr_context import (
    CICheckRun,
    CIStatus,
    DependencyFile,
    GitMetadata,
    PullRequestContext,
    RepositoryContext,
)
from backend.config import get_settings

logger = logging.getLogger("prism.service.github")

_PR_URL_PATTERN = re.compile(
    r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
    re.IGNORECASE,
)

_DEP_FILENAMES = {
    "requirements.txt", "requirements-dev.txt", "setup.py",
    "setup.cfg", "pyproject.toml", "package.json", "package-lock.json",
    "yarn.lock", "pom.xml", "build.gradle", "Cargo.toml",
    "Cargo.lock", "go.mod", "go.sum", "Gemfile", "Gemfile.lock",
}


# ── URL parser ────────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """
    Extract (owner, repo, pr_number) from a GitHub PR URL.

    Supports:
      https://github.com/owner/repo/pull/123
      https://github.com/owner/repo/pull/123/files
      github.com/owner/repo/pull/123

    Raises:
        ValueError: If the URL does not match a GitHub PR pattern.
    """
    m = _PR_URL_PATTERN.search(url)
    if not m:
        raise ValueError(
            f"Cannot parse GitHub PR URL: {url!r}. "
            "Expected format: https://github.com/owner/repo/pull/NUMBER"
        )
    return m.group("owner"), m.group("repo"), int(m.group("number"))


# ── HTTP client factory ───────────────────────────────────────────────────────

def _build_client() -> httpx.AsyncClient:
    settings = get_settings()
    headers  = {
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = settings.github_token
    if token:
        headers["Authorization"] = f"Bearer {token.get_secret_value()}"
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers=headers,
        timeout=30.0,
        follow_redirects=True,
    )


# ── Core fetcher ──────────────────────────────────────────────────────────────

class GitHubService:
    """
    Async GitHub API client.

    All public methods return typed model objects.
    On HTTP error, they log the issue and return None / empty lists.
    """

    async def fetch_pull_request(
        self,
        owner: str,
        repo:  str,
        pr_number: int,
    ) -> Optional[PullRequestContext]:
        """Fetch PR metadata and CI checks. Returns None on failure."""
        async with _build_client() as client:
            # ── PR metadata ───────────────────────────────────────────────────
            resp = await client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
            if resp.status_code != 200:
                logger.error(
                    "GitHub PR fetch failed: %s %s — HTTP %d",
                    owner, pr_number, resp.status_code,
                )
                return None

            data = resp.json()

            # ── File diffs ────────────────────────────────────────────────────
            files_resp = await client.get(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100},
            )
            raw_files = files_resp.json() if files_resp.status_code == 200 else []

            # ── CI check-runs ─────────────────────────────────────────────────
            head_sha   = data.get("head", {}).get("sha", "")
            ci_checks  = await self._fetch_check_runs(client, owner, repo, head_sha)

            pr = PullRequestContext(
                number=data["number"],
                title=data.get("title", ""),
                body=data.get("body"),
                author=data.get("user", {}).get("login"),
                state=data.get("state", "open"),
                draft=data.get("draft", False),
                mergeable=data.get("mergeable"),
                labels=[lbl["name"] for lbl in data.get("labels", [])],
                requested_reviewers=[
                    r.get("login", "") for r in data.get("requested_reviewers", [])
                ],
                ci_checks=ci_checks,
                html_url=data.get("html_url"),
            )

            # Stash raw files for the diff_parser_node to process
            # Using object.__setattr__ to bypass Pydantic validation on extra field
            try:
                object.__setattr__(pr, "_raw_files", raw_files)
            except Exception:
                pass  # Pydantic v2 might block this — handled by analysis_service

            # Attach raw files directly as a reachable attribute
            pr.__dict__["_raw_files"] = raw_files

            return pr

    async def fetch_repository_context(
        self,
        owner: str,
        repo:  str,
    ) -> Optional[RepositoryContext]:
        """Fetch static repository metadata for context building."""
        async with _build_client() as client:
            resp = await client.get(f"/repos/{owner}/{repo}")
            if resp.status_code != 200:
                logger.error(
                    "GitHub repo fetch failed: %s/%s — HTTP %d",
                    owner, repo, resp.status_code,
                )
                return None

            data = resp.json()

            # Languages breakdown
            lang_resp  = await client.get(f"/repos/{owner}/{repo}/languages")
            languages  = lang_resp.json() if lang_resp.status_code == 200 else {}

            # Topics
            topics_resp = await client.get(
                f"/repos/{owner}/{repo}/topics",
                headers={"Accept": "application/vnd.github.mercy-preview+json"},
            )
            topics = topics_resp.json().get("names", []) if topics_resp.status_code == 200 else []

            # Top-level directory tree
            tree      = await self._fetch_tree(client, owner, repo, data.get("default_branch", "main"))
            dep_files = await self._fetch_dependency_files(client, owner, repo, tree)

            return RepositoryContext(
                owner=owner,
                name=repo,
                full_name=f"{owner}/{repo}",
                default_branch=data.get("default_branch", "main"),
                description=data.get("description"),
                primary_language=data.get("language"),
                languages=languages,
                topics=topics,
                has_readme=any(
                    e.get("path", "").upper().startswith("README") for e in tree
                ),
                has_contributing=any(
                    "CONTRIBUTING" in e.get("path", "").upper() for e in tree
                ),
                has_ci=any(
                    ".github/workflows" in e.get("path", "") for e in tree
                ),
                has_security_policy=any(
                    "SECURITY" in e.get("path", "").upper() for e in tree
                ),
                directory_tree=[e.get("path", "") for e in tree[:100]],
                dependency_files=dep_files,
                stars=data.get("stargazers_count", 0),
                forks=data.get("forks_count", 0),
                open_issues_count=data.get("open_issues_count", 0),
            )

    async def fetch_git_metadata(
        self,
        owner: str,
        repo:  str,
        pr_number: int,
    ) -> Optional[GitMetadata]:
        """Fetch git commit metadata for the PR head."""
        async with _build_client() as client:
            resp = await client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            head = data.get("head", {})
            base = data.get("base", {})

            commits_resp = await client.get(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/commits",
                params={"per_page": 10},
            )
            commits = commits_resp.json() if commits_resp.status_code == 200 else []
            messages = [
                c.get("commit", {}).get("message", "")
                for c in commits
            ]

            author_info = {}
            if commits:
                last = commits[-1]
                author_info = {
                    "author_login": last.get("author", {}).get("login"),
                    "author_email": last.get("commit", {}).get("author", {}).get("email"),
                }

            return GitMetadata(
                head_sha=head.get("sha", ""),
                base_sha=base.get("sha", ""),
                head_branch=head.get("ref", ""),
                base_branch=base.get("ref", "main"),
                commit_count=len(commits),
                commit_messages=messages,
                **author_info,
            )

    async def fetch_repo_files_for_rag(
        self,
        owner: str,
        repo:  str,
        branch: str = "main",
        max_files: int = 200,
    ) -> dict[str, str]:
        """
        Fetch a representative subset of repository files for RAG indexing.

        Returns {relative_path: file_content} for indexable source files.
        Binary, generated, and very large files are excluded.
        """
        async with _build_client() as client:
            tree = await self._fetch_tree(client, owner, repo, branch, recursive=True)

            # Filter to indexable source files
            indexable_extensions = {
                ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
                ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".md",
                ".yaml", ".yml", ".toml", ".sql",
            }
            source_files = [
                e for e in tree
                if e.get("type") == "blob"
                and any(e.get("path", "").endswith(ext) for ext in indexable_extensions)
                and int(e.get("size", 0)) < 100_000
            ][:max_files]

            files: dict[str, str] = {}
            for entry in source_files:
                path    = entry["path"]
                content = await self._fetch_file_content(client, owner, repo, path)
                if content:
                    files[path] = content

            logger.info(
                "Fetched %d files for RAG indexing from %s/%s",
                len(files), owner, repo,
            )
            return files

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _fetch_check_runs(
        self,
        client: httpx.AsyncClient,
        owner:  str,
        repo:   str,
        sha:    str,
    ) -> list[CICheckRun]:
        if not sha:
            return []
        resp = await client.get(
            f"/repos/{owner}/{repo}/commits/{sha}/check-runs",
            params={"per_page": 50},
        )
        if resp.status_code != 200:
            return []

        runs: list[CICheckRun] = []
        for item in resp.json().get("check_runs", []):
            conclusion = item.get("conclusion")
            ci_status  = self._map_conclusion(conclusion)
            runs.append(CICheckRun(
                name=item.get("name", ""),
                status=item.get("status", ""),
                conclusion=conclusion,
                ci_status=ci_status,
                url=item.get("html_url"),
            ))
        return runs

    @staticmethod
    def _map_conclusion(conclusion: Optional[str]) -> CIStatus:
        mapping = {
            "success":   CIStatus.SUCCESS,
            "failure":   CIStatus.FAILURE,
            "neutral":   CIStatus.NEUTRAL,
            "cancelled": CIStatus.FAILURE,
            "skipped":   CIStatus.SKIPPED,
            "timed_out": CIStatus.FAILURE,
        }
        return mapping.get(conclusion or "", CIStatus.UNKNOWN)

    async def _fetch_tree(
        self,
        client:    httpx.AsyncClient,
        owner:     str,
        repo:      str,
        branch:    str,
        recursive: bool = False,
    ) -> list[dict]:
        params = {"recursive": "1"} if recursive else {}
        resp   = await client.get(
            f"/repos/{owner}/{repo}/git/trees/{branch}",
            params=params,
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("tree", [])

    async def _fetch_dependency_files(
        self,
        client: httpx.AsyncClient,
        owner:  str,
        repo:   str,
        tree:   list[dict],
    ) -> list[DependencyFile]:
        dep_files: list[DependencyFile] = []
        ecosystem_map = {
            "requirements.txt": "pip", "requirements-dev.txt": "pip",
            "setup.py": "pip",         "pyproject.toml": "pip",
            "package.json": "npm",     "yarn.lock": "npm",
            "pom.xml": "maven",        "build.gradle": "maven",
            "Cargo.toml": "cargo",     "go.mod": "go",
            "Gemfile": "gem",
        }
        for entry in tree:
            path  = entry.get("path", "")
            fname = path.split("/")[-1]
            if fname in _DEP_FILENAMES and entry.get("type") == "blob":
                content = await self._fetch_file_content(client, owner, repo, path)
                if content:
                    dep_files.append(DependencyFile(
                        path=path,
                        ecosystem=ecosystem_map.get(fname, "unknown"),
                        content=content,
                    ))
        return dep_files

    async def _fetch_file_content(
        self,
        client: httpx.AsyncClient,
        owner:  str,
        repo:   str,
        path:   str,
    ) -> Optional[str]:
        import base64
        resp = await client.get(f"/repos/{owner}/{repo}/contents/{path}")
        if resp.status_code != 200:
            return None
        data     = resp.json()
        encoding = data.get("encoding", "")
        content  = data.get("content", "")
        if encoding == "base64":
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                return None
        return content or None
