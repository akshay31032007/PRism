"""
PRism AI — centralised configuration.
All settings are loaded from environment variables (via .env).
Never access os.environ directly elsewhere in the codebase — import from here.
"""

from __future__ import annotations

import sys
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve .env relative to this file (backend/config.py), not cwd
_ENV_FILE = Path(__file__).parent / ".env"


# ── Provider enums ─────────────────────────────────────────────────────────────

class LLMProvider(str, Enum):
    OPENAI      = "openai"
    ANTHROPIC   = "anthropic"
    GEMINI      = "gemini"
    GROQ        = "groq"
    OPENROUTER  = "openrouter"
    AZURE       = "azure"
    OLLAMA      = "ollama"


class EmbeddingProvider(str, Enum):
    OPENAI               = "openai"
    VOYAGE               = "voyage"
    JINA                 = "jina"
    SENTENCE_TRANSFORMERS = "sentence_transformers"


class VectorDBProvider(str, Enum):
    QDRANT  = "qdrant"
    CHROMA  = "chroma"
    FAISS   = "faiss"


# ── Main settings ──────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """All application settings. Loaded once at startup via get_settings()."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM API Keys ──────────────────────────────────────────────────────────
    openai_api_key:       Optional[SecretStr] = Field(default=None)
    anthropic_api_key:    Optional[SecretStr] = Field(default=None)
    google_api_key:       Optional[SecretStr] = Field(default=None)
    openrouter_api_key:   Optional[SecretStr] = Field(default=None)
    groq_api_key:         Optional[SecretStr] = Field(default=None)
    azure_openai_api_key: Optional[SecretStr] = Field(default=None)
    azure_openai_endpoint: Optional[str]      = Field(default=None)

    # ── Embedding API Keys ────────────────────────────────────────────────────
    voyage_api_key: Optional[SecretStr] = Field(default=None)
    jina_api_key:   Optional[SecretStr] = Field(default=None)

    # ── GitHub ────────────────────────────────────────────────────────────────
    github_token:          Optional[SecretStr] = Field(default=None)
    github_app_id:         Optional[str]       = Field(default=None)
    github_private_key:    Optional[SecretStr] = Field(default=None)
    github_webhook_secret: Optional[SecretStr] = Field(default=None)

    # ── Vector DB ─────────────────────────────────────────────────────────────
    qdrant_url:     str                    = Field(default="http://localhost:6333")
    qdrant_api_key: Optional[SecretStr]    = Field(default=None)

    # ── Databases ─────────────────────────────────────────────────────────────
    postgres_url: Optional[str] = Field(default=None)
    redis_url:    str           = Field(default="redis://localhost:6379")

    # ── Observability ─────────────────────────────────────────────────────────
    langsmith_api_key: Optional[SecretStr] = Field(default=None)
    sentry_dsn:        Optional[str]       = Field(default=None)

    # ── Provider Selection ────────────────────────────────────────────────────
    default_llm_provider:       LLMProvider       = Field(default=LLMProvider.GEMINI)
    default_embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.SENTENCE_TRANSFORMERS
    )
    default_vector_db: VectorDBProvider = Field(default=VectorDBProvider.QDRANT)

    # ── LLM Behaviour ─────────────────────────────────────────────────────────
    llm_temperature:  float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens:   int   = Field(default=4096, ge=256, le=32768)
    llm_timeout_secs: int   = Field(default=120, ge=10, le=600)

    # ── Model names ───────────────────────────────────────────────────────────
    openai_model:    str = Field(default="gpt-4o")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    gemini_model:    str = Field(default="gemini-1.5-pro")
    groq_model:      str = Field(default="llama3-8b-8192")

    # ── Embedding Model names ─────────────────────────────────────────────────
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    st_embedding_model:     str = Field(default="all-MiniLM-L6-v2")

    # ── App Behaviour ─────────────────────────────────────────────────────────
    app_name:    str  = Field(default="PRism AI")
    debug:       bool = Field(default=False)
    environment: str  = Field(default="development")
    log_level:   str  = Field(default="INFO")

    # ── Analysis limits ───────────────────────────────────────────────────────
    max_diff_chars:         int = Field(default=60_000)
    max_files_per_analysis: int = Field(default=50)
    max_chunk_size:         int = Field(default=1_500)
    chunk_overlap:          int = Field(default=200)
    retriever_top_k:        int = Field(default=8)

    # ── Retry policy ──────────────────────────────────────────────────────────
    retry_max_attempts: int   = Field(default=3)
    retry_wait_min:     float = Field(default=1.0)
    retry_wait_max:     float = Field(default=30.0)

    @field_validator("default_llm_provider", mode="before")
    @classmethod
    def normalise_llm_provider(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v

    def get_active_llm_key(self) -> Optional[str]:
        """Return the plaintext API key for the active LLM provider."""
        mapping = {
            LLMProvider.OPENAI:     self.openai_api_key,
            LLMProvider.ANTHROPIC:  self.anthropic_api_key,
            LLMProvider.GEMINI:     self.google_api_key,
            LLMProvider.GROQ:       self.groq_api_key,
            LLMProvider.OPENROUTER: self.openrouter_api_key,
            LLMProvider.AZURE:      self.azure_openai_api_key,
        }
        secret = mapping.get(self.default_llm_provider)
        return secret.get_secret_value() if secret else None

    def validate_provider_key(self) -> None:
        """Raise at startup if the configured provider has no key."""
        if self.default_llm_provider == LLMProvider.OLLAMA:
            return  # Ollama is local — no key needed
        if not self.get_active_llm_key():
            print(
                f"[PRism] WARNING: No API key set for provider "
                f"'{self.default_llm_provider.value}'. "
                f"Set the corresponding key in your .env file.",
                file=sys.stderr,
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    settings = Settings()
    settings.validate_provider_key()
    return settings
