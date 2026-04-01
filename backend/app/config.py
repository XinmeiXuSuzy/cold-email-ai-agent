from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/cold_email"

    # LLM
    litellm_model: str = "gpt-4o-mini"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Langfuse
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Email
    email_provider: str = "mock"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@example.com"
    from_name: str = "Cold Email Agent"

    # App
    api_secret_key: str = "dev-secret-key"
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
