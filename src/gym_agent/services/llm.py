"""
Multi-LLM Provider Service for GymAI Agent.

Supports: OpenAI, Google Gemini, OpenRouter
"""

from functools import lru_cache
from typing import Any

from pydantic_ai import Agent

from gym_agent.config import LLMProvider, settings


class LLMService:
    """
    Multi-LLM provider service.
    
    Provides a unified interface for switching between LLM providers.
    """
    
    # Model mappings per provider
    MODELS = {
        LLMProvider.OPENAI: {
            "default": "gpt-4o",
            "fast": "gpt-4o-mini",
            "embedding": "text-embedding-3-small",
        },
        LLMProvider.GEMINI: {
            "default": "gemini-1.5-pro",
            "fast": "gemini-1.5-flash",
            "embedding": "text-embedding-004",
        },
        LLMProvider.OPENROUTER: {
            "default": "google/gemini-2.0-flash-exp:free",
            "fast": "google/gemini-2.0-flash-exp:free",
            "anthropic": "anthropic/claude-3-5-sonnet",
        },
    }
    
    def __init__(
        self,
        provider: LLMProvider | None = None,
        model: str | None = None,
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider to use. Defaults to settings.
            model: Specific model to use. Defaults to provider's default.
        """
        self.provider = provider or settings.default_llm_provider
        self.model_name = model or settings.default_model or self.MODELS[self.provider]["default"]
        self._validate_api_key()
    
    def _validate_api_key(self) -> None:
        """Validate that API key is configured for the provider."""
        api_key = settings.get_llm_api_key(self.provider)
        if not api_key:
            raise ValueError(
                f"API key not configured for provider: {self.provider.value}. "
                f"Set the appropriate environment variable."
            )
    
    def get_model_string(self) -> str:
        """
        Get the Pydantic AI model string for current provider.
        
        Returns:
            Model string in format 'provider:model'
        """
        match self.provider:
            case LLMProvider.OPENAI:
                return f"openai:{self.model_name}"
            
            case LLMProvider.GEMINI:
                return f"gemini-1.5-pro"
            
            case LLMProvider.OPENROUTER:
                return f"openai:{self.model_name}"
            
            case _:
                raise ValueError(f"Unknown provider: {self.provider}")
    
    def get_openrouter_base_url(self) -> str | None:
        """Get base URL for OpenRouter if using that provider."""
        if self.provider == LLMProvider.OPENROUTER:
            return "https://openrouter.ai/api/v1"
        return None
    
    def create_agent(
        self,
        output_type: type,
        system_prompt: str,
        **agent_kwargs: Any,
    ) -> Agent:
        """
        Create a Pydantic AI agent with the configured LLM.
        
        Args:
            output_type: Pydantic model for structured output
            system_prompt: System prompt for the agent
            **agent_kwargs: Additional arguments for Agent
            
        Returns:
            Configured Pydantic AI Agent
        """
        import os
        
        model_string = self.get_model_string()
        
        # Handle OpenRouter's custom base URL
        if self.provider == LLMProvider.OPENROUTER:
            os.environ["OPENAI_BASE_URL"] = self.get_openrouter_base_url() or ""
            os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        
        return Agent(
            model_string,
            output_type=output_type,
            system_prompt=system_prompt,
            **agent_kwargs,
        )
    
    @classmethod
    def available_providers(cls) -> list[str]:
        """List available LLM providers with configured API keys."""
        available = []
        for provider in LLMProvider:
            try:
                api_key = settings.get_llm_api_key(provider)
                if api_key:
                    available.append(provider.value)
            except Exception:
                pass
        return available
    
    def switch_provider(self, provider: LLMProvider, model: str | None = None) -> "LLMService":
        """
        Create a new LLM service instance with a different provider.
        
        Args:
            provider: New provider to use
            model: Optional model override
            
        Returns:
            New LLMService instance
        """
        return LLMService(provider=provider, model=model)


@lru_cache
def get_llm_service() -> LLMService:
    """Get cached default LLM service instance."""
    return LLMService()
