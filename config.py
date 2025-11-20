import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)

class LLMConfig:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia_ngc")
    
    # NVIDIA NGC Configuration
    NVIDIA_NGC_API_KEY: str = os.getenv("NVIDIA_NGC_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
    NVIDIA_TEMPERATURE: float = float(os.getenv("NVIDIA_TEMPERATURE", "0.7"))
    NVIDIA_MAX_TOKENS: int = int(os.getenv("NVIDIA_MAX_TOKENS", "1024"))
    
    # OpenAI / OpenRouter Configuration (Optional - for fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    @classmethod
    def get_provider_config(cls, provider: Optional[str] = None) -> dict:
        provider = (provider or cls.LLM_PROVIDER).lower()
        
        if provider == "nvidia_ngc":
            if not cls.NVIDIA_NGC_API_KEY:
                raise ValueError("NVIDIA_NGC_API_KEY must be set in .env")
            return {
                "api_key": cls.NVIDIA_NGC_API_KEY,
                "base_url": cls.NVIDIA_BASE_URL,
                "model": cls.NVIDIA_MODEL,
                "temperature": cls.NVIDIA_TEMPERATURE,
                "max_tokens": cls.NVIDIA_MAX_TOKENS,
            }
        
        elif provider == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY must be set in .env")
            return {
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_API_BASE,
                "model": cls.OPENAI_MODEL_NAME,
                "temperature": cls.OPENAI_TEMPERATURE,
                "max_tokens": cls.OPENAI_MAX_TOKENS,
            }
        
        raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    def print_config(cls):
        """Debug helper to print current configuration"""
        print(f"Provider: {cls.LLM_PROVIDER}")
        
        if cls.LLM_PROVIDER.lower() == "nvidia_ngc":
            print(f"API Key: {'✅ Set' if cls.NVIDIA_NGC_API_KEY else '❌ Not set'}")
            print(f"Base URL: {cls.NVIDIA_BASE_URL}")
            print(f"Model: {cls.NVIDIA_MODEL}")
            print(f"Temperature: {cls.NVIDIA_TEMPERATURE}")
            print(f"Max Tokens: {cls.NVIDIA_MAX_TOKENS}")
        
        elif cls.LLM_PROVIDER.lower() == "openai":
            print(f"API Key: {'✅ Set' if cls.OPENAI_API_KEY else '❌ Not set'}")
            print(f"Base URL: {cls.OPENAI_API_BASE}")
            print(f"Model: {cls.OPENAI_MODEL_NAME}")
            print(f"Temperature: {cls.OPENAI_TEMPERATURE}")
            print(f"Max Tokens: {cls.OPENAI_MAX_TOKENS}")

def get_llm_config(provider: Optional[str] = None) -> dict:
    return LLMConfig.get_provider_config(provider)