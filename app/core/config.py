"""
Application configuration.

Every value that could plausibly change per-environment (which models are
being used, which Hugging Face credentials are active, database/redis
locations, rate limits...) lives here and comes from the environment.
Nothing in this file, and nothing downstream of it, hard-codes a model
name, a Hugging Face repo id, or a secret.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# The pgvector column dimension is fixed at migration time, so it lives
# here as a plain constant rather than something that can silently drift
# from the schema via an environment variable.
EMBEDDING_DIMENSIONS = 384


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "development"
    APP_NAME: str = "MyAI Backend"
    DEBUG: bool = False

    # --- Datastores ---
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True

    # --- Auth ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # --- Hugging Face ---
    # A single token is normally enough to access the configured models.
    HF_API_TOKEN: str

    # Optional provider-specific tokens.
    HF_GLM_TOKEN: str | None = None
    HF_KIMI_TOKEN: str | None = None

    # --- Models ---
    # Model identifiers come entirely from environment variables.
    GLM_MODEL_ID: str
    KIMI_MODEL_ID: str
    EMBEDDING_MODEL_ID: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # --- Observability ---
    SENTRY_DSN: str | None = None

    # --- HTTP / Security ---
    #
    # Keep this as a STRING because pydantic-settings automatically tries
    # to JSON-decode list[str] environment variables before validators run.
    #
    # Example:
    # CORS_ORIGINS=http://localhost:3000
    #
    # Multiple origins:
    # CORS_ORIGINS=http://localhost:3000,https://example.com
    #
    CORS_ORIGINS: str = "http://localhost:3000"

    MAX_UPLOAD_SIZE_MB: int = 20
    REQUEST_TIMEOUT_SECONDS: int = 60
    PROVIDER_TIMEOUT_SECONDS: int = 120

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a clean list."""
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()