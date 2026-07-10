from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None

    # Embeddings Providers
    VOYAGE_API_KEY: Optional[str] = None
    JINA_API_KEY: Optional[str] = None

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # Infrastructure
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    POSTGRES_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # Observability
    LANGSMITH_API_KEY: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    # Defaults
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_EMBEDDING_PROVIDER: str = "openai"
    DEFAULT_VECTOR_DB: str = "qdrant"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
