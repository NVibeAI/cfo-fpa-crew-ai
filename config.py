# config.py
"""
Centralized configuration module for LLM provider settings.
Reads configuration from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load .env file if it exists
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)


class LLMConfig:
    """
    Configuration class for LLM provider settings.
    Reads from environment variables with defaults.
    """
    
    # Provider selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # OpenAI/OpenRouter settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "meta-llama/llama-3.1-70b-instruct")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    # NVIDIA NIM settings
    NIM_BASE_URL: Optional[str] = os.getenv("NIM_BASE_URL")
    NIM_API_KEY: Optional[str] = os.getenv("NIM_API_KEY")
    NIM_MODEL: Optional[str] = os.getenv("NIM_MODEL")
    NIM_TEMPERATURE: float = float(os.getenv("NIM_TEMPERATURE", "0.2"))
    NIM_MAX_TOKENS: int = int(os.getenv("NIM_MAX_TOKENS", "2000"))
    
    # Local model settings
    LOCAL_BASE_URL: str = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    LOCAL_API_KEY: str = os.getenv("LOCAL_API_KEY", "not-needed")
    LOCAL_MODEL: str = os.getenv("LOCAL_MODEL", "llama3")
    LOCAL_TEMPERATURE: float = float(os.getenv("LOCAL_TEMPERATURE", "0.2"))
    LOCAL_MAX_TOKENS: int = int(os.getenv("LOCAL_MAX_TOKENS", "2000"))
    
    # Optional headers
    HTTP_REFERER: str = os.getenv("HTTP_REFERER", "http://localhost:8501")
    X_TITLE: str = os.getenv("X_TITLE", "Agno FP&A Dashboard")
    
    @classmethod
    def get_provider_config(cls, provider: Optional[str] = None) -> dict:
        """
        Get configuration dictionary for a specific provider.
        
        Args:
            provider: Provider name ("openai", "nim", "local")
                     If None, uses LLM_PROVIDER
        
        Returns:
            Dictionary with provider-specific configuration
        """
        provider = (provider or cls.LLM_PROVIDER).lower()
        
        if provider == "openai":
            return {
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_API_BASE,
                "model": cls.OPENAI_MODEL_NAME,
                "temperature": cls.OPENAI_TEMPERATURE,
                "max_tokens": cls.OPENAI_MAX_TOKENS,
            }
        
        elif provider == "nim":
            return {
                "api_key": cls.NIM_API_KEY or cls.OPENAI_API_KEY,  # Fallback to OpenAI key
                "base_url": cls.NIM_BASE_URL,
                "model": cls.NIM_MODEL,
                "temperature": cls.NIM_TEMPERATURE,
                "max_tokens": cls.NIM_MAX_TOKENS,
            }
        
        elif provider == "local":
            return {
                "api_key": cls.LOCAL_API_KEY,
                "base_url": cls.LOCAL_BASE_URL,
                "model": cls.LOCAL_MODEL,
                "temperature": cls.LOCAL_TEMPERATURE,
                "max_tokens": cls.LOCAL_MAX_TOKENS,
            }
        
        else:
            raise ValueError(f"Unsupported provider: {provider}. Must be 'openai', 'nim', or 'local'")
    
    @classmethod
    def validate_nim_config(cls) -> bool:
        """Validate that NIM configuration is complete."""
        if not cls.NIM_BASE_URL:
            raise ValueError("NIM_BASE_URL must be set for NVIDIA NIM provider")
        if not cls.NIM_API_KEY and not cls.OPENAI_API_KEY:
            raise ValueError("NIM_API_KEY or OPENAI_API_KEY must be set for NVIDIA NIM provider")
        if not cls.NIM_MODEL:
            raise ValueError("NIM_MODEL must be set for NVIDIA NIM provider")
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)."""
        print("📋 LLM Configuration:")
        print(f"   Provider: {cls.LLM_PROVIDER}")
        
        if cls.LLM_PROVIDER == "openai":
            print(f"   Base URL: {cls.OPENAI_API_BASE}")
            print(f"   Model: {cls.OPENAI_MODEL_NAME}")
            print(f"   API Key: {'✅ Set' if cls.OPENAI_API_KEY else '❌ Not set'}")
        
        elif cls.LLM_PROVIDER == "nim":
            print(f"   Base URL: {cls.NIM_BASE_URL or '❌ Not set'}")
            print(f"   Model: {cls.NIM_MODEL or '❌ Not set'}")
            print(f"   API Key: {'✅ Set' if (cls.NIM_API_KEY or cls.OPENAI_API_KEY) else '❌ Not set'}")
        
        elif cls.LLM_PROVIDER == "local":
            print(f"   Base URL: {cls.LOCAL_BASE_URL}")
            print(f"   Model: {cls.LOCAL_MODEL}")


# Convenience function to get current provider config
def get_llm_config(provider: Optional[str] = None) -> dict:
    """Get configuration for the specified provider."""
    return LLMConfig.get_provider_config(provider)

