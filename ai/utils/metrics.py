"""
PRism AI — Runtime Metrics Tracker.

Provides lightweight, in-process tracking of per-agent LLM token consumption
and wall-clock execution timing so that callers can surface cost and latency
information without depending on an external observability backend.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Metrics:
    """Aggregate runtime metrics collected during a single graph run.

    Attributes:
        token_usage: Nested dict keyed by agent name, then by token category.
            Example::

                {
                    "Security": {"prompt_tokens": 800, "completion_tokens": 200},
                    "CodeQuality": {"prompt_tokens": 600, "completion_tokens": 150},
                }

        execution_times: Dict mapping agent name → wall-clock time in milliseconds.
    """

    def __init__(self) -> None:
        self.token_usage: Dict[str, Dict[str, int]] = {}
        self.execution_times: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_agent_run(
        self,
        agent_name: str,
        exec_time_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Record a single agent's execution metrics.

        If an agent is recorded more than once (e.g., retries), both token
        counts and execution time are *accumulated*, not replaced.

        Args:
            agent_name: Unique identifier for the agent.
            exec_time_ms: Wall-clock execution time in milliseconds.
            prompt_tokens: Number of prompt (input) tokens consumed.
            completion_tokens: Number of completion (output) tokens consumed.
        """
        if agent_name not in self.token_usage:
            self.token_usage[agent_name] = {"prompt_tokens": 0, "completion_tokens": 0}

        self.token_usage[agent_name]["prompt_tokens"] += prompt_tokens
        self.token_usage[agent_name]["completion_tokens"] += completion_tokens

        # Accumulate execution time across retries.
        self.execution_times[agent_name] = (
            self.execution_times.get(agent_name, 0.0) + exec_time_ms
        )

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    @property
    def total_tokens(self) -> int:
        """Return the grand total of all prompt + completion tokens across all agents."""
        total = 0
        for usage in self.token_usage.values():
            total += usage.get("prompt_tokens", 0)
            total += usage.get("completion_tokens", 0)
        return total

    @property
    def slowest_agent(self) -> str:
        """Return the name of the agent with the highest recorded execution time.

        Returns an empty string if no agents have been recorded yet.
        """
        if not self.execution_times:
            return ""
        return max(self.execution_times, key=lambda k: self.execution_times[k])

    def agent_total_tokens(self, agent_name: str) -> int:
        """Return combined prompt + completion tokens for a specific agent.

        Args:
            agent_name: The agent whose token usage to retrieve.

        Returns:
            Total tokens consumed by the agent, or 0 if not recorded.
        """
        usage = self.token_usage.get(agent_name, {})
        return usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

    def get_execution_time(self, agent_name: str) -> Optional[float]:
        """Return the recorded execution time (ms) for a specific agent, or None."""
        return self.execution_times.get(agent_name)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialise all metrics to a plain dict suitable for JSON output.

        Returns:
            A dict with the following structure::

                {
                    "total_tokens": 2400,
                    "slowest_agent": "Security",
                    "token_usage": {
                        "Security": {
                            "prompt_tokens": 800,
                            "completion_tokens": 200,
                            "total_tokens": 1000,
                        },
                        ...
                    },
                    "execution_times_ms": {
                        "Security": 3200.5,
                        ...
                    },
                }
        """
        enriched_usage: Dict[str, Dict[str, int]] = {}
        for agent, usage in self.token_usage.items():
            enriched_usage[agent] = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": (
                    usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                ),
            }

        return {
            "total_tokens": self.total_tokens,
            "slowest_agent": self.slowest_agent,
            "token_usage": enriched_usage,
            "execution_times_ms": dict(self.execution_times),
        }

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Metrics(agents={list(self.execution_times.keys())}, "
            f"total_tokens={self.total_tokens})"
        )
