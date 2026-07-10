from ai.settings import settings


class AppConfig:
    @property
    def default_llm_provider(self) -> str:
        return settings.DEFAULT_LLM_PROVIDER

    @property
    def default_embedding_provider(self) -> str:
        return settings.DEFAULT_EMBEDDING_PROVIDER

    @property
    def default_vector_db(self) -> str:
        return settings.DEFAULT_VECTOR_DB


config = AppConfig()
