"""
Production-grade configuration management for ManipulatorAI.

This module provides a comprehensive configuration system using Pydantic
BaseSettings for type-safe environment variable management with validation,
computed properties, and environment-specific defaults.
"""

import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, validator, root_validator
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
    app_name: str = Field("ManipulatorAI", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(1, env="WORKERS")
    
    # =============================================================================
    # AZURE OPENAI CONFIGURATION
    # =============================================================================
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    openai_api_version: str = Field("2023-12-01-preview", env="OPENAI_API_VERSION")
    openai_model_name: str = Field("gpt-4", env="OPENAI_MODEL_NAME")
    openai_max_tokens: int = Field(2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    openai_timeout: int = Field(30, env="OPENAI_TIMEOUT")
    openai_max_retries: int = Field(3, env="OPENAI_MAX_RETRIES")
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    # PostgreSQL (Product Knowledge Base)
    postgres_url: str = Field(..., env="POSTGRES_URL")
    postgres_pool_size: int = Field(10, env="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(20, env="POSTGRES_MAX_OVERFLOW")
    postgres_pool_timeout: int = Field(30, env="POSTGRES_POOL_TIMEOUT")
    postgres_pool_recycle: int = Field(3600, env="POSTGRES_POOL_RECYCLE")
    
    # MongoDB (Conversation Storage)
    mongo_url: str = Field(..., env="MONGO_URL")
    mongo_db_name: str = Field("manipulator_conversations", env="MONGO_DB_NAME")
    mongo_max_pool_size: int = Field(100, env="MONGO_MAX_POOL_SIZE")
    mongo_min_pool_size: int = Field(10, env="MONGO_MIN_POOL_SIZE")
    mongo_max_idle_time: int = Field(45000, env="MONGO_MAX_IDLE_TIME")  # milliseconds
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(5, env="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    
    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    celery_broker_url: Optional[str] = Field(None, env="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(None, env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field("json", env="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field("json", env="CELERY_RESULT_SERIALIZER")
    celery_accept_content: List[str] = Field(["json"], env="CELERY_ACCEPT_CONTENT")
    celery_task_time_limit: int = Field(300, env="CELERY_TASK_TIME_LIMIT")  # 5 minutes
    celery_task_soft_time_limit: int = Field(240, env="CELERY_TASK_SOFT_TIME_LIMIT")  # 4 minutes
    
    # =============================================================================
    # WEBHOOK CONFIGURATION
    # =============================================================================
    facebook_verify_token: str = Field(..., env="FACEBOOK_VERIFY_TOKEN")
    instagram_verify_token: str = Field(..., env="INSTAGRAM_VERIFY_TOKEN")
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    webhook_timeout: int = Field(10, env="WEBHOOK_TIMEOUT")
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    allowed_hosts: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")  # json or text
    log_file_path: str = Field("logs/manipulator_ai.log", env="LOG_FILE_PATH")
    log_max_size: int = Field(10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # =============================================================================
    # BUSINESS LOGIC CONFIGURATION
    # =============================================================================
    correlation_threshold: float = Field(0.8, env="CORRELATION_THRESHOLD")
    max_cross_product_suggestions: int = Field(5, env="MAX_CROSS_PRODUCT_SUGGESTIONS")
    conversation_timeout_minutes: int = Field(30, env="CONVERSATION_TIMEOUT_MINUTES")
    max_persistence_attempts: int = Field(3, env="MAX_PERSISTENCE_ATTEMPTS")
    welcome_message_cache_ttl: int = Field(3600, env="WELCOME_MESSAGE_CACHE_TTL")  # 1 hour
    
    # =============================================================================
    # RATE LIMITING CONFIGURATION
    # =============================================================================
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")  # seconds
    webhook_rate_limit: int = Field(1000, env="WEBHOOK_RATE_LIMIT")  # per minute
    
    # =============================================================================
    # MONITORING & PERFORMANCE
    # =============================================================================
    health_check_timeout: int = Field(5, env="HEALTH_CHECK_TIMEOUT")
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    
    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment is one of accepted values."""
        allowed_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v.lower()
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is acceptable."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("correlation_threshold")
    def validate_correlation_threshold(cls, v):
        """Ensure correlation threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Correlation threshold must be between 0 and 1")
        return v
    
    @validator("openai_temperature")
    def validate_openai_temperature(cls, v):
        """Ensure OpenAI temperature is within valid range."""
        if not 0 <= v <= 2:
            raise ValueError("OpenAI temperature must be between 0 and 2")
        return v
    
    @validator("port")
    def validate_port(cls, v):
        """Ensure port is within valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("azure_openai_endpoint")
    def validate_azure_endpoint(cls, v):
        """Ensure Azure OpenAI endpoint is properly formatted."""
        if not v.startswith("https://"):
            raise ValueError("Azure OpenAI endpoint must start with https://")
        if not v.endswith(".openai.azure.com"):
            raise ValueError("Azure OpenAI endpoint must end with .openai.azure.com")
        return v
    
    @root_validator
    def validate_secret_key_length(cls, values):
        """Ensure secret key is sufficiently long for security."""
        secret_key = values.get("secret_key")
        if secret_key and len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return values
    
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
    def database_urls(self) -> dict:
        """Get all database URLs in a convenient dictionary."""
        return {
            "postgres": self.postgres_url,
            "mongo": self.mongo_url,
            "redis": self.redis_url
        }

    class Config:
        """Pydantic configuration for Settings class."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
        # Allow environment variables to override .env file values
        env_file_override = True


@lru_cache()
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
