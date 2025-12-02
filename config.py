import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)

class LLMConfig:
    # Provider selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia_ngc")
    
    # NVIDIA NGC Configuration
    NVIDIA_NGC_API_KEY: str = os.getenv("NVIDIA_NGC_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
    NVIDIA_TEMPERATURE: float = float(os.getenv("NVIDIA_TEMPERATURE", "0.7"))
    NVIDIA_MAX_TOKENS: int = int(os.getenv("NVIDIA_MAX_TOKENS", "1024"))
    
    # Vertex AI Configuration
    VERTEX_PROJECT_ID: str = os.getenv("VERTEX_PROJECT_ID", "")
    VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "us-central1")
    VERTEX_SERVICE_ACCOUNT_JSON: str = os.getenv("VERTEX_SERVICE_ACCOUNT_JSON", "")
    VERTEX_MODEL: str = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
    VERTEX_TEMPERATURE: float = float(os.getenv("VERTEX_TEMPERATURE", "0.7"))
    VERTEX_MAX_TOKENS: int = int(os.getenv("VERTEX_MAX_TOKENS", "1024"))
    
    @classmethod
    def get_provider_config(cls, provider: Optional[str] = None) -> dict:
        """
        Get configuration for the specified provider.
        
        Args:
            provider: Provider name (vertex_ai, nvidia_ngc, etc.)
            
        Returns:
            Dictionary with provider configuration
        """
        provider = (provider or cls.LLM_PROVIDER).lower()
        
        # NVIDIA NGC Provider
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
        
        # Vertex AI Provider
        elif provider == "vertex_ai":
            if not cls.VERTEX_PROJECT_ID:
                raise ValueError("VERTEX_PROJECT_ID must be set in .env")
            
            # Service account JSON is optional - will use gcloud if not provided
            if not cls.VERTEX_SERVICE_ACCOUNT_JSON:
                print("\n⚠️  Warning: VERTEX_SERVICE_ACCOUNT_JSON not set in .env")
                print("    Will attempt to use Application Default Credentials.")
                print("    Options:")
                print("    1. Run: gcloud auth application-default login")
                print("    2. Download service account JSON from Google Cloud Console")
                print("       and set VERTEX_SERVICE_ACCOUNT_JSON=/path/to/file.json\n")
            
            return {
                "project_id": cls.VERTEX_PROJECT_ID,
                "location": cls.VERTEX_LOCATION,
                "service_account_json": cls.VERTEX_SERVICE_ACCOUNT_JSON,
                "model": cls.VERTEX_MODEL,
                "temperature": cls.VERTEX_TEMPERATURE,
                "max_tokens": cls.VERTEX_MAX_TOKENS,
            }
        
        raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print(f"LLM Provider: {cls.LLM_PROVIDER}")
        
        if cls.LLM_PROVIDER == "vertex_ai":
            print(f"Vertex AI Project: {cls.VERTEX_PROJECT_ID}")
            print(f"Vertex AI Location: {cls.VERTEX_LOCATION}")
            print(f"Vertex AI Model: {cls.VERTEX_MODEL}")
            print(f"Service Account: {'✅ Set' if cls.VERTEX_SERVICE_ACCOUNT_JSON else '❌ Not Set (will use gcloud)'}")
        
        elif cls.LLM_PROVIDER == "nvidia_ngc":
            print(f"NVIDIA NGC Model: {cls.NVIDIA_MODEL}")
            print(f"NVIDIA NGC Base URL: {cls.NVIDIA_BASE_URL}")
            print(f"NVIDIA NGC API Key: {'✅ Set' if cls.NVIDIA_NGC_API_KEY else '❌ Not Set'}")


def get_llm_config(provider: Optional[str] = None) -> dict:
    """
    Convenience function to get provider configuration.
    
    Args:
        provider: Provider name (optional, defaults to LLM_PROVIDER env var)
        
    Returns:
        Dictionary with provider configuration
    """
    return LLMConfig.get_provider_config(provider)