
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)

class LLMConfig:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia_ngc")
    
    # NVIDIA NGC
    NVIDIA_NGC_API_KEY: str = os.getenv("NVIDIA_NGC_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
    NVIDIA_TEMPERATURE: float = float(os.getenv("NVIDIA_TEMPERATURE", "0.7"))
    NVIDIA_MAX_TOKENS: int = int(os.getenv("NVIDIA_MAX_TOKENS", "1024"))
    
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
        
        raise ValueError(f"Unsupported provider: {provider}")

def get_llm_config(provider: Optional[str] = None) -> dict:
    return LLMConfig.get_provider_config(provider)
