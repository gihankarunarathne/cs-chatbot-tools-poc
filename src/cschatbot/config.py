from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str
    intent_model: str = "gpt-4o-mini"
    response_model: str = "gpt-4o"
    log_level: str = "INFO"
    llm_max_retries: int = 3
    llm_timeout_secs: float = 30.0

    @field_validator("openai_api_key")
    @classmethod
    def _require_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in .env or the environment "
                "(see .env.example)."
            )
        return v


settings = Settings()
