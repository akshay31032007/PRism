"""
PRism AI — Custom Exception Hierarchy.

All exceptions inherit from PRismException so callers can catch the entire
family with a single ``except PRismException`` clause while still being able
to distinguish between them when needed.
"""


class PRismException(Exception):
    """Base exception for all PRism AI errors."""

    def __init__(self, message: str = "", *args) -> None:
        super().__init__(message, *args)
        self.message = message

    def __str__(self) -> str:
        return self.message or super().__str__()


class AgentExecutionError(PRismException):
    """Raised when an agent fails fatally during execution.

    Args:
        agent_name: The name of the agent that failed.
        message: Human-readable description of the failure.
    """

    def __init__(self, agent_name: str, message: str = "") -> None:
        full_message = f"Agent '{agent_name}' failed: {message}" if message else f"Agent '{agent_name}' failed."
        super().__init__(full_message)
        self.agent_name = agent_name


class LLMProviderError(PRismException):
    """Raised when an LLM provider call fails (network error, quota, auth, etc.).

    Args:
        provider: The LLM provider identifier (e.g. ``'openai'``).
        message: Human-readable description of the failure.
    """

    def __init__(self, provider: str, message: str = "") -> None:
        full_message = (
            f"LLM provider '{provider}' call failed: {message}"
            if message
            else f"LLM provider '{provider}' call failed."
        )
        super().__init__(full_message)
        self.provider = provider


class RAGIndexError(PRismException):
    """Raised when indexing documents into the vector store fails.

    Args:
        collection: The name of the vector-store collection being indexed.
        message: Human-readable description of the failure.
    """

    def __init__(self, collection: str = "", message: str = "") -> None:
        full_message = (
            f"RAG indexing failed for collection '{collection}': {message}"
            if collection
            else f"RAG indexing failed: {message}"
        )
        super().__init__(full_message)
        self.collection = collection


class RAGRetrievalError(PRismException):
    """Raised when querying / retrieving documents from the vector store fails.

    Args:
        collection: The name of the vector-store collection being queried.
        message: Human-readable description of the failure.
    """

    def __init__(self, collection: str = "", message: str = "") -> None:
        full_message = (
            f"RAG retrieval failed for collection '{collection}': {message}"
            if collection
            else f"RAG retrieval failed: {message}"
        )
        super().__init__(full_message)
        self.collection = collection


class ConfigurationError(PRismException):
    """Raised when a required configuration value is missing or invalid.

    Args:
        config_key: The configuration key that is missing or invalid.
        message: Human-readable description of the issue.
    """

    def __init__(self, config_key: str = "", message: str = "") -> None:
        full_message = (
            f"Configuration error for key '{config_key}': {message}"
            if config_key
            else f"Configuration error: {message}"
        )
        super().__init__(full_message)
        self.config_key = config_key


class ASTParseError(PRismException):
    """Raised when the AST parser fails to parse source code.

    Args:
        file_path: Path to the file that could not be parsed.
        language: The target programming language (e.g. ``'python'``).
        message: Human-readable description of the parse failure.
    """

    def __init__(self, file_path: str = "", language: str = "", message: str = "") -> None:
        parts = []
        if file_path:
            parts.append(f"file='{file_path}'")
        if language:
            parts.append(f"language='{language}'")
        detail = ", ".join(parts)
        full_message = (
            f"AST parse error ({detail}): {message}"
            if detail
            else f"AST parse error: {message}"
        )
        super().__init__(full_message)
        self.file_path = file_path
        self.language = language
