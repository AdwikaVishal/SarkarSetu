"""Application configuration using Pydantic Settings."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="SarkarSetu AI", validation_alias="APP_NAME")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")

    # Database
    database_url: str = Field(validation_alias="DATABASE_URL")
    database_pool_size: int = Field(default=5, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, validation_alias="DATABASE_POOL_TIMEOUT")

    # External APIs
    gemini_api_key: str = Field(validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-flash", validation_alias="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.7, validation_alias="GEMINI_TEMPERATURE")
    gemini_max_output_tokens: int = Field(default=8192, validation_alias="GEMINI_MAX_OUTPUT_TOKENS")
    gemini_timeout_seconds: int = Field(default=30, validation_alias="GEMINI_TIMEOUT_SECONDS")
    gemini_max_retries: int = Field(default=3, validation_alias="GEMINI_MAX_RETRIES")
    gemini_enabled: bool = Field(default=False, validation_alias="GEMINI_ENABLED")

    # Security
    jwt_secret: str = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Password hashing (Argon2id)
    argon2_time_cost: int = Field(default=3, validation_alias="ARGON2_TIME_COST")
    argon2_memory_cost: int = Field(default=65536, validation_alias="ARGON2_MEMORY_COST")  # 64 MB
    argon2_parallelism: int = Field(default=4, validation_alias="ARGON2_PARALLELISM")
    argon2_hash_length: int = Field(default=32, validation_alias="ARGON2_HASH_LENGTH")
    argon2_salt_length: int = Field(default=16, validation_alias="ARGON2_SALT_LENGTH")

    # Password policy
    min_password_length: int = Field(default=12, validation_alias="MIN_PASSWORD_LENGTH")
    require_uppercase: bool = Field(default=True, validation_alias="REQUIRE_UPPERCASE")
    require_lowercase: bool = Field(default=True, validation_alias="REQUIRE_LOWERCASE")
    require_digits: bool = Field(default=True, validation_alias="REQUIRE_DIGITS")
    require_special_chars: bool = Field(default=True, validation_alias="REQUIRE_SPECIAL_CHARS")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"], validation_alias="CORS_ORIGINS")

    # Knowledge Retrieval
    knowledge_retrieval_enabled: bool = Field(
        default=True, validation_alias="KNOWLEDGE_RETRIEVAL_ENABLED"
    )
    knowledge_retrieval_top_k: int = Field(
        default=5, validation_alias="KNOWLEDGE_RETRIEVAL_TOP_K"
    )
    knowledge_retrieval_min_score: float = Field(
        default=0.3, validation_alias="KNOWLEDGE_RETRIEVAL_MIN_SCORE"
    )
    knowledge_retrieval_rerank: bool = Field(
        default=True, validation_alias="KNOWLEDGE_RETRIEVAL_RERANK"
    )
    knowledge_retrieval_timeout_seconds: int = Field(
        default=10, validation_alias="KNOWLEDGE_RETRIEVAL_TIMEOUT_SECONDS"
    )
    knowledge_retrieval_dev_fixture: bool = Field(
        default=True, validation_alias="KNOWLEDGE_RETRIEVAL_DEV_FIXTURE"
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
