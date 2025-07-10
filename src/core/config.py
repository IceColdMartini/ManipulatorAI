"""
Production-grade configuration management for ManipulatorAI.

This module provides a comprehensive configuration system using Pydantic
BaseSettings for type-safe environment variable management with validation,
computed properties, and environment-specific defaults.
"""

import os
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Enterprise-grade application settings with comprehensive validation.

    All settings are type-validated and provide sensible defaults where appropriate.
    Critical settings (API keys, database URLs) are required and will raise
    validation errors if not provided.

    Features:
    - Type-safe environment variable loading
    - Custom validation for critical settings
    - Computed properties for derived values
    - Environment-specific configuration
    - Security-first defaults
    """

    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    app_name: str = Field(default="ManipulatorAI", description="Application name", alias="APP_NAME")
    app_version: str = Field(
        default="1.0.0", description="Application version", alias="APP_VERSION"
    )
    environment: str = Field(
        default="development", description="Deployment environment", alias="ENVIRONMENT"
    )
    debug: bool = Field(default=False, description="Enable debug mode", alias="DEBUG")

    # Server Configuration
    host: str = Field(
        default="127.0.0.1", description="Server host", alias="HOST"
    )  # Localhost only by default for security
    port: int = Field(default=8000, description="Server port", alias="PORT")
    workers: int = Field(default=1, description="Number of worker processes", alias="WORKERS")

    # =============================================================================
    # AZURE OPENAI CONFIGURATION
    # =============================================================================
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    openai_api_version: str = Field(default="2023-12-01-preview", alias="OPENAI_API_VERSION")
    openai_model_name: str = Field(default="gpt-4", alias="OPENAI_MODEL_NAME")
    openai_max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    openai_timeout: int = Field(default=30, alias="OPENAI_TIMEOUT")
    openai_max_retries: int = Field(default=3, alias="OPENAI_MAX_RETRIES")

    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    # PostgreSQL (Product Knowledge Base)
    postgres_url: str | None = Field(default=None, alias="POSTGRES_URL")
    postgres_pool_size: int = Field(default=10, alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, alias="POSTGRES_MAX_OVERFLOW")
    postgres_pool_timeout: int = Field(default=30, alias="POSTGRES_POOL_TIMEOUT")
    postgres_pool_recycle: int = Field(default=3600, alias="POSTGRES_POOL_RECYCLE")

    # MongoDB (Conversation Storage)
    mongo_url: str | None = Field(
        default=None, description="MongoDB connection URL", alias="MONGO_URL"
    )
    mongo_db_name: str = Field(
        default="manipulator_conversations",
        description="MongoDB database name",
        alias="MONGO_DB_NAME",
    )
    mongo_max_pool_size: int = Field(
        default=100, description="Maximum MongoDB connection pool size", alias="MONGO_MAX_POOL_SIZE"
    )
    mongo_min_pool_size: int = Field(
        default=10, description="Minimum MongoDB connection pool size", alias="MONGO_MIN_POOL_SIZE"
    )
    mongo_max_idle_time: int = Field(
        default=45000,
        description="MongoDB max connection idle time in ms",
        alias="MONGO_MAX_IDLE_TIME",
    )  # milliseconds

    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    redis_host: str = Field(default="localhost", description="Redis host", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, description="Redis port", alias="REDIS_PORT")
    redis_password: str | None = Field(
        default=None, description="Redis password", alias="REDIS_PASSWORD"
    )
    redis_db: int = Field(default=0, description="Redis database index", alias="REDIS_DB")
    redis_max_connections: int = Field(
        default=20, description="Max Redis connections", alias="REDIS_MAX_CONNECTIONS"
    )
    redis_socket_timeout: int = Field(
        default=5, description="Redis socket timeout in seconds", alias="REDIS_SOCKET_TIMEOUT"
    )
    redis_socket_connect_timeout: int = Field(
        default=5,
        description="Redis connection timeout in seconds",
        alias="REDIS_SOCKET_CONNECT_TIMEOUT",
    )

    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", alias="CELERY_RESULT_SERIALIZER")
    celery_accept_content: list[str] = Field(
        default_factory=lambda: ["json"], alias="CELERY_ACCEPT_CONTENT"
    )
    celery_task_time_limit: int = Field(default=300, alias="CELERY_TASK_TIME_LIMIT")  # 5 minutes
    celery_task_soft_time_limit: int = Field(
        default=240, alias="CELERY_TASK_SOFT_TIME_LIMIT"
    )  # 4 minutes

    # =============================================================================
    # WEBHOOK CONFIGURATION
    # =============================================================================
    facebook_verify_token: str | None = Field(default=None, alias="FACEBOOK_VERIFY_TOKEN")
    instagram_verify_token: str | None = Field(default=None, alias="INSTAGRAM_VERIFY_TOKEN")
    webhook_secret: str | None = Field(default=None, alias="WEBHOOK_SECRET")
    webhook_timeout: int = Field(default=10, alias="WEBHOOK_TIMEOUT")

    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"], alias="ALLOWED_HOSTS")
    cors_origins: list[str] = Field(default_factory=lambda: ["*"], alias="CORS_ORIGINS")

    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # json or text
    log_file_path: str = Field(default="logs/manipulator_ai.log", alias="LOG_FILE_PATH")
    log_max_size: int = Field(default=10485760, alias="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, alias="LOG_BACKUP_COUNT")

    # =============================================================================
    # BUSINESS LOGIC CONFIGURATION
    # =============================================================================
    correlation_threshold: float = Field(default=0.8, alias="CORRELATION_THRESHOLD")
    max_cross_product_suggestions: int = Field(default=5, alias="MAX_CROSS_PRODUCT_SUGGESTIONS")
    conversation_timeout_minutes: int = Field(default=30, alias="CONVERSATION_TIMEOUT_MINUTES")
    max_persistence_attempts: int = Field(default=3, alias="MAX_PERSISTENCE_ATTEMPTS")
    welcome_message_cache_ttl: int = Field(
        default=3600, alias="WELCOME_MESSAGE_CACHE_TTL"
    )  # 1 hour

    # =============================================================================
    # RATE LIMITING CONFIGURATION
    # =============================================================================
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")  # seconds
    webhook_rate_limit: int = Field(default=1000, alias="WEBHOOK_RATE_LIMIT")  # per minute

    # =============================================================================
    # MONITORING & PERFORMANCE
    # =============================================================================
    health_check_timeout: int = Field(default=5, alias="HEALTH_CHECK_TIMEOUT")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of accepted values."""
        allowed_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is acceptable."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("correlation_threshold")
    @classmethod
    def validate_correlation_threshold(cls, v: float) -> float:
        """Ensure correlation threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Correlation threshold must be between 0 and 1")
        return v

    @field_validator("openai_temperature")
    @classmethod
    def validate_openai_temperature(cls, v: float) -> float:
        """Ensure OpenAI temperature is within valid range."""
        if not 0 <= v <= 2:
            raise ValueError("OpenAI temperature must be between 0 and 2")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is within valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_azure_endpoint(cls, v: str | None) -> str | None:
        """Ensure Azure OpenAI endpoint is properly formatted."""
        if v is None:
            return v
        if not v.startswith("https://"):
            raise ValueError("Azure OpenAI endpoint must start with https://")
        if not v.endswith(".openai.azure.com"):
            raise ValueError("Azure OpenAI endpoint must end with .openai.azure.com")
        return v

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Settings":
        """Ensure all required fields are present."""
        required_fields = {
            "azure_openai_api_key": "AZURE_OPENAI_API_KEY",
            "azure_openai_endpoint": "AZURE_OPENAI_ENDPOINT",
            "postgres_url": "POSTGRES_URL",
            "mongo_url": "MONGO_URL",
            "facebook_verify_token": "FACEBOOK_VERIFY_TOKEN",
            "instagram_verify_token": "INSTAGRAM_VERIFY_TOKEN",
            "secret_key": "SECRET_KEY",
        }

        missing_fields = []
        for field_name, env_var in required_fields.items():
            field_value = getattr(self, field_name, None)
            if field_value is None:
                missing_fields.append(f"{field_name} (set {env_var} environment variable)")

        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")

        # Validate secret key length
        if self.secret_key and len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")

        return self

    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker_url_computed(self) -> str:
        """Get Celery broker URL, defaulting to Redis URL if not specified."""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_result_backend_computed(self) -> str:
        """Get Celery result backend, defaulting to Redis URL if not specified."""
        return self.celery_result_backend or self.redis_url

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    @property
    def log_file_directory(self) -> str:
        """Get the directory path for log files."""
        return os.path.dirname(self.log_file_path)

    @property
    def database_urls(self) -> dict[str, str | None]:
        """Get all database URLs in a convenient dictionary."""
        return {"postgres": self.postgres_url, "mongo": self.mongo_url, "redis": self.redis_url}

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance for dependency injection.

    Using lru_cache ensures settings are loaded only once per application
    lifecycle, improving performance and ensuring consistency.

    Returns:
        Cached Settings instance
    """
    return Settings()


# Create a global settings instance for convenient access
# This will be imported throughout the application
settings = get_settings()
