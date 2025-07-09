from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    """
    # Azure OpenAI Configuration
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    openai_api_version: str = Field("2023-05-15", env="OPENAI_API_VERSION")
    openai_model_name: str = Field("gpt-4", env="OPENAI_MODEL_NAME")

    # Database URLs
    postgres_url: str = Field(..., env="POSTGRES_URL")
    mongo_url: str = Field(..., env="MONGO_URL")

    # Redis Configuration
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")

    # Webhook Verification Tokens
    facebook_verify_token: str = Field(..., env="FACEBOOK_VERIFY_TOKEN")
    instagram_verify_token: str = Field(..., env="INSTAGRAM_VERIFY_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Instantiate the settings
settings = Settings()
