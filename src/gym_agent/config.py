"""
Configuration settings for GymAI Agent.

Supports multiple environments: dev, preprod, prod
"""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environments."""
    DEV = "dev"
    PREPROD = "preprod"
    PROD = "prod"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    environment: Environment = Environment.DEV
    debug: bool = True
    
    # Application
    app_name: str = "GymAI Agent"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # LLM Providers
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    default_llm_provider: LLMProvider = LLMProvider.OPENAI
    default_model: str = "gpt-4o"
    
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    database_url: str = ""
    
    # Telegram
    telegram_bot_token: str = ""
    
    # WhatsApp (Phase 2)
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    
    # Security
    jwt_secret_key: str = "change-me-in-production"
    webhook_secret: str = "change-me-in-production"
    
    # Monitoring
    logfire_token: str = ""
    
    # Rate Limiting
    max_messages_per_hour: int = 10
    max_unanswered_messages: int = 2
    followup_wait_hours: int = 48
    
    @property
    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEV
    
    @property
    def is_prod(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PROD
    
    def get_llm_api_key(self, provider: LLMProvider | None = None) -> str:
        """Get API key for the specified LLM provider."""
        provider = provider or self.default_llm_provider
        
        match provider:
            case LLMProvider.OPENAI:
                return self.openai_api_key
            case LLMProvider.GEMINI:
                return self.google_api_key
            case LLMProvider.OPENROUTER:
                return self.openrouter_api_key
            case _:
                raise ValueError(f"Unknown provider: {provider}")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
