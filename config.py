"""
Configuration module for LLM providers.
Reads from .env file and provides unified config interface.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMConfig:
    """Central configuration for all LLM providers"""
    
    # Default provider (can be overridden in .env)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "vertex_ai").lower()
    
    # Vertex AI Configuration
    VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "")
    VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
    VERTEX_SERVICE_ACCOUNT_JSON = os.getenv("VERTEX_SERVICE_ACCOUNT_JSON", "")
    VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
    VERTEX_TEMPERATURE = float(os.getenv("VERTEX_TEMPERATURE", "0.7"))
    VERTEX_MAX_TOKENS = int(os.getenv("VERTEX_MAX_TOKENS", "1024"))
    
    # NVIDIA NGC Configuration
    NVIDIA_NGC_API_KEY = os.getenv("NVIDIA_NGC_API_KEY", "")
    NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
    NVIDIA_TEMPERATURE = float(os.getenv("NVIDIA_TEMPERATURE", "0.2"))
    NVIDIA_MAX_TOKENS = int(os.getenv("NVIDIA_MAX_TOKENS", "1024"))


def get_llm_config(provider: str = None) -> Dict[str, Any]:
    """
    Get configuration for specified LLM provider.
    
    Args:
        provider: "vertex_ai", "nvidia_ngc", or None (uses default)
    
    Returns:
        Dictionary with provider configuration
    """
    if provider is None:
        provider = LLMConfig.LLM_PROVIDER
    
    provider = provider.lower()
    
    if provider == "vertex_ai":
        return {
            "provider": "vertex_ai",
            "project_id": LLMConfig.VERTEX_PROJECT_ID,
            "location": LLMConfig.VERTEX_LOCATION,
            "service_account_json": LLMConfig.VERTEX_SERVICE_ACCOUNT_JSON,
            "model": LLMConfig.VERTEX_MODEL,
            "temperature": LLMConfig.VERTEX_TEMPERATURE,
            "max_tokens": LLMConfig.VERTEX_MAX_TOKENS,
        }
    
    elif provider in ["nvidia_ngc", "nvidia"]:
        return {
            "provider": "nvidia_ngc",
            "api_key": LLMConfig.NVIDIA_NGC_API_KEY,
            "base_url": LLMConfig.NVIDIA_BASE_URL,
            "model": LLMConfig.NVIDIA_MODEL,
            "temperature": LLMConfig.NVIDIA_TEMPERATURE,
            "max_tokens": LLMConfig.NVIDIA_MAX_TOKENS,
        }
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'vertex_ai' or 'nvidia_ngc'")


def validate_config(provider: str = None):
    """
    Validate that all required configuration is present.
    
    Args:
        provider: Provider to validate (or None for default)
    
    Raises:
        ValueError if configuration is incomplete
    """
    config = get_llm_config(provider)
    
    if config["provider"] == "vertex_ai":
        missing = []
        if not config["project_id"]:
            missing.append("VERTEX_PROJECT_ID")
        if not config["service_account_json"]:
            missing.append("VERTEX_SERVICE_ACCOUNT_JSON")
        
        if missing:
            raise ValueError(
                f"Missing Vertex AI configuration: {', '.join(missing)}\n"
                f"Please set these in your .env file."
            )
        
        # Check if JSON file exists
        import os
        if not os.path.exists(config["service_account_json"]):
            raise ValueError(
                f"Service account JSON file not found: {config['service_account_json']}\n"
                f"Please check the path in VERTEX_SERVICE_ACCOUNT_JSON"
            )
    
    elif config["provider"] == "nvidia_ngc":
        if not config["api_key"]:
            raise ValueError(
                "Missing NVIDIA NGC API key.\n"
                "Please set NVIDIA_NGC_API_KEY in your .env file."
            )
    
    return True