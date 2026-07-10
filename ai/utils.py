"""
PRism AI — shared agent infrastructure.

Exports:
  - get_logger()        structured logger via structlog
  - with_retry()        async tenacity retry decorator
  - PromptManager       loads prompts from ai/prompts/*.md
  - BaseAgent           abstract base class every agent inherits
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ai.models.agent_result import AgentResult, AgentStatus
from ai.models.graph_state import GraphState
from ai.models.issues import IssueCategory
from backend.config import get_settings


# ─────────────────────────────────────────────────────────────────────────────
# 1. Structured logger
# ─────────────────────────────────────────────────────────────────────────────

def _configure_structlog() -> None:
    """Configure structlog once at import time."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Use console renderer in dev, JSON in production
            (
                structlog.dev.ConsoleRenderer(colors=True)
                if settings.environment == "development"
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


_configure_structlog()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger."""
    return structlog.get_logger(name)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Retry decorator
# ─────────────────────────────────────────────────────────────────────────────

_TRANSIENT_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    OSError,
)


async def with_retry(
    coro_func,
    *args: Any,
    max_attempts: Optional[int] = None,
    wait_min: Optional[float] = None,
    wait_max: Optional[float] = None,
    reraise: bool = True,
    logger: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an async coroutine function with exponential back-off retry.

    Args:
        coro_func:    An async callable.
        *args:        Positional arguments forwarded to coro_func.
        max_attempts: Override settings.retry_max_attempts.
        wait_min:     Minimum back-off seconds.
        wait_max:     Maximum back-off seconds.
        reraise:      If True, re-raises the last exception after all retries fail.
        logger:       Optional structlog logger for attempt logging.
        **kwargs:     Keyword arguments forwarded to coro_func.

    Returns:
        The return value of coro_func on success.

    Raises:
        The last exception raised by coro_func if reraise=True and all retries exhausted.
    """
    settings = get_settings()
    attempts = max_attempts or settings.retry_max_attempts
    wmin     = wait_min     or settings.retry_wait_min
    wmax     = wait_max     or settings.retry_wait_max
    _log     = logger or get_logger("prism.retry")

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=wmin, max=wmax),
            retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
            reraise=reraise,
        ):
            with attempt:
                if attempt.retry_state.attempt_number > 1:
                    _log.warning(
                        "Retrying",
                        func=getattr(coro_func, "__name__", str(coro_func)),
                        attempt=attempt.retry_state.attempt_number,
                    )
                return await coro_func(*args, **kwargs)
    except RetryError as exc:
        if reraise:
            raise exc.last_attempt.exception() from exc
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. PromptManager
# ─────────────────────────────────────────────────────────────────────────────

class PromptManager:
    """
    Loads agent system prompts from ai/prompts/*.md.

    Prompts support simple {{variable}} template substitution.
    Templates are loaded once and cached in memory.
    """

    _PROMPTS_DIR = Path(__file__).parent / "prompts"
    _cache: dict[str, str] = {}

    @classmethod
    def load(cls, name: str) -> str:
        """
        Load a prompt by filename stem (without .md extension).

        Example:
            PromptManager.load("security")  → content of ai/prompts/security.md

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        if name not in cls._cache:
            path = cls._PROMPTS_DIR / f"{name}.md"
            if not path.exists():
                raise FileNotFoundError(
                    f"Prompt file not found: {path}. "
                    f"Available: {[p.stem for p in cls._PROMPTS_DIR.glob('*.md')]}"
                )
            cls._cache[name] = path.read_text(encoding="utf-8")
        return cls._cache[name]

    @classmethod
    def render(cls, name: str, **variables: Any) -> str:
        """
        Load a prompt and substitute {{variable}} placeholders.

        Example:
            PromptManager.render("security", language="Python", diff="...")
        """
        template = cls.load(name)
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    @classmethod
    def clear_cache(cls) -> None:
        """Clear in-memory cache — useful in tests."""
        cls._cache.clear()


# ─────────────────────────────────────────────────────────────────────────────
# 4. JSON validation helper
# ─────────────────────────────────────────────────────────────────────────────

def parse_llm_json(raw: str) -> dict[str, Any]:
    """
    Robustly parse a JSON dict from an LLM response string.

    Handles:
      - Clean JSON strings
      - JSON wrapped in markdown fences (```json ... ```)
      - Leading/trailing whitespace

    Raises:
        json.JSONDecodeError: If the content cannot be parsed as JSON.
    """
    text = raw.strip()
    # Strip markdown fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    # Find the first { ... } block if there's surrounding prose
    if not text.startswith("{"):
        brace_match = re.search(r"(\{[\s\S]*\})", text)
        if brace_match:
            text = brace_match.group(1)
    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
# 5. BaseAgent
# ─────────────────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Abstract base class for all PRism analysis agents.

    Contract:
      - Subclasses implement _analyse(state) and return an AgentResult.
      - run(state) wraps _analyse with timing, error handling, and retry.
      - Each agent declares its name, category, and version as class attributes.

    Example subclass:
        class SecurityAgent(BaseAgent):
            name     = "SecurityAgent"
            category = IssueCategory.SECURITY
            version  = "1.0.0"

            async def _analyse(self, state: GraphState) -> AgentResult:
                ...
    """

    # Subclasses MUST override these
    name:     str           = "BaseAgent"
    category: IssueCategory = IssueCategory.SECURITY
    version:  str           = "1.0.0"

    def __init__(self) -> None:
        self._log    = get_logger(f"prism.agent.{self.name.lower()}")
        self._settings = get_settings()
        self._prompt_manager = PromptManager

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def _analyse(self, state: GraphState) -> AgentResult:
        """
        Core analysis logic.  Must return a fully-populated AgentResult.
        Agents should not catch exceptions here — BaseAgent.run() handles that.
        """
        ...

    # ── Public runner ─────────────────────────────────────────────────────────

    async def run(self, state: GraphState) -> AgentResult:
        """
        Execute the agent with timing, structured logging, and safe error capture.

        On any unhandled exception:
          - Logs the error with full traceback context
          - Returns a FAILED AgentResult so the graph can continue
          - Does NOT re-raise — the pipeline continues with degraded results
        """
        self._log.info("Agent starting", agent=self.name, pr=state.pr_number)
        start_ms = time.perf_counter()

        try:
            result = await self._run_with_retry(state)
            elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
            result.latency_ms = elapsed_ms
            result.agent_version = self.version

            self._log.info(
                "Agent finished",
                agent=self.name,
                status=result.status.value,
                issues=result.total_issue_count,
                score=result.score,
                latency_ms=elapsed_ms,
            )
            return result

        except Exception as exc:  # noqa: BLE001
            elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
            self._log.error(
                "Agent failed",
                agent=self.name,
                error=str(exc),
                exc_info=True,
            )
            return AgentResult(
                agent_name=self.name,
                agent_version=self.version,
                category=self.category,
                status=AgentStatus.FAILED,
                error_message=str(exc),
                summary=f"{self.name} failed to complete analysis: {exc}",
                score=0.5,  # Conservative — neither perfect nor catastrophic
                confidence=0.0,
                latency_ms=elapsed_ms,
            )

    async def _run_with_retry(self, state: GraphState) -> AgentResult:
        """
        Run _analyse() with tenacity retries.
        Handles both transient network errors and Groq/OpenAI rate limits (429).
        """
        import httpx as _httpx

        settings = get_settings()

        def _is_retryable(exc: BaseException) -> bool:
            # Network errors
            if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
                return True
            # Rate limit — any provider
            name = type(exc).__name__
            msg  = str(exc).lower()
            if "ratelimit" in name.lower() or "rate_limit" in name.lower():
                return True
            if "429" in msg or "rate limit" in msg or "too many" in msg:
                return True
            return False

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.retry_max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=settings.retry_wait_min,
                max=settings.retry_wait_max,
            ),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                try:
                    return await self._analyse(state)
                except Exception as exc:
                    if _is_retryable(exc):
                        if attempt.retry_state.attempt_number > 1:
                            self._log.warning(
                                "Agent retrying due to: %s",
                                type(exc).__name__,
                                agent=self.name,
                                attempt=attempt.retry_state.attempt_number,
                            )
                        raise  # let tenacity handle the wait+retry
                    raise  # non-retryable — bubble up immediately

        raise RuntimeError(f"{self.name} exceeded retry budget")

    # ── Shared helpers available to all subclasses ────────────────────────────

    def _get_llm_wrapper(self):
        """Return the appropriate LLM wrapper for the configured provider."""
        from ai.llm import GeminiWrapper, OpenAIWrapper
        from backend.config import LLMProvider

        provider = self._settings.default_llm_provider
        if provider == LLMProvider.GEMINI:
            return GeminiWrapper()
        if provider == LLMProvider.OPENAI:
            return OpenAIWrapper()
        # For Groq, Anthropic, OpenRouter, Azure, Ollama — use a universal wrapper
        return _UniversalLLMWrapper(provider)

    def _truncate_diff(self, diff_text: str) -> tuple[str, bool]:
        """
        Truncate the diff to the configured max_diff_chars limit.

        Returns:
            (truncated_text, was_truncated)
        """
        limit = self._settings.max_diff_chars
        if len(diff_text) <= limit:
            return diff_text, False
        truncated = diff_text[:limit]
        # Don't cut in the middle of a line
        last_newline = truncated.rfind("\n")
        if last_newline > limit * 0.8:
            truncated = truncated[:last_newline]
        return (
            truncated
            + f"\n\n[... DIFF TRUNCATED AT {limit} CHARS — "
            f"{len(diff_text) - limit} chars omitted ...]",
            True,
        )

    def _build_diff_summary(self, state: GraphState) -> str:
        """Build a compact diff summary string safe to inject into prompts."""
        if not state.parsed_diff:
            return "No diff available."
        diff_text, _ = self._truncate_diff(state.parsed_diff.diff_text)
        return diff_text

    def _pr_metadata_block(self, state: GraphState) -> str:
        """Format PR metadata as a structured text block for prompts."""
        pr  = state.pull_request_context
        repo = state.repository_context
        if not pr:
            return "PR metadata unavailable."
        lines = [
            f"PR #{pr.number}: {pr.title}",
            f"Author: {pr.author or 'unknown'}",
            f"State: {pr.state}  Draft: {pr.draft}",
            f"Labels: {', '.join(pr.labels) or 'none'}",
            f"CI checks passing: {pr.all_ci_passing}  "
            f"  Failures: {pr.ci_failure_count}",
            f"Description quality: {pr.description_quality}",
        ]
        if pr.body:
            lines.append(f"Description:\n{pr.body[:1000]}")
        if repo:
            lines.append(
                f"Repository: {repo.full_name}  "
                f"Language: {repo.primary_language or 'unknown'}"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Universal LLM wrapper — works for any provider via LLMFactory
# ─────────────────────────────────────────────────────────────────────────────

class _UniversalLLMWrapper:
    """
    Thin wrapper that works for any LLM provider (Groq, Anthropic, OpenRouter, etc.)
    by delegating to LLMFactory.  Exposes the same interface as GeminiWrapper /
    OpenAIWrapper so agents don't need to know which provider is active.
    """

    def __init__(self, provider=None) -> None:
        from ai.llm.llm_factory import LLMFactory
        self._llm   = LLMFactory.create(provider=provider)
        self._name  = LLMFactory.get_model_name(provider)

    async def ainvoke_json(self, system_prompt: str, user_prompt: str):
        """Invoke and parse JSON — mirrors GeminiWrapper.ainvoke_json()."""
        import json, re
        from langchain_core.messages import SystemMessage, HumanMessage

        json_system = (
            system_prompt
            + "\n\nIMPORTANT: Your response MUST be a single valid JSON object. "
            "Do not wrap it in markdown fences. Start with '{' and end with '}'."
        )
        messages = [SystemMessage(content=json_system), HumanMessage(content=user_prompt)]
        response = await self._llm.ainvoke(messages)

        content = str(response.content).strip()
        # Strip markdown fences if present
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if fence:
            content = fence.group(1).strip()
        # Find first {...} block
        if not content.startswith("{"):
            m = re.search(r"(\{[\s\S]*\})", content)
            if m:
                content = m.group(1)

        parsed = json.loads(content)
        usage  = getattr(response, "usage_metadata", {}) or {}
        return parsed, usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    async def ainvoke_text(self, system_prompt: str, user_prompt: str):
        """Plain text invocation — mirrors GeminiWrapper.ainvoke_text()."""
        from langchain_core.messages import SystemMessage, HumanMessage
        messages  = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response  = await self._llm.ainvoke(messages)
        usage     = getattr(response, "usage_metadata", {}) or {}
        return str(response.content), usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    @property
    def model_name(self) -> str:
        return self._name
