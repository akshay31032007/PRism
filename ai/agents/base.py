import time
from abc import ABC, abstractmethod

from ai.llm.wrapper import LLMWrapper
from ai.models.agent import AgentResult
from ai.models.state import PRismGraphState
from ai.utils.logger import get_logger


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")
        self.llm = LLMWrapper.get_llm()

    @abstractmethod
    def run(self, state: PRismGraphState) -> AgentResult:
        """Execute the agent logic and return the result."""
        pass

    def execute(self, state: PRismGraphState) -> PRismGraphState:
        """Wrapper method called by LangGraph node."""
        start_time = time.time()
        self.logger.info("Starting agent execution", agent=self.name)

        try:
            result = self.run(state)
            result.execution_time_ms = (time.time() - start_time) * 1000

            # Update state with agent result
            state.agent_results[self.name] = result
            self.logger.info("Agent execution completed", agent=self.name, status=result.status)
        except Exception as e:
            self.logger.error("Agent execution failed", agent=self.name, error=str(e))
            error_result = AgentResult(
                agent_name=self.name,
                status="ERROR",
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            state.agent_results[self.name] = error_result

        return state
