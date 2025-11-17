# llm_client.py
"""
Provider-agnostic LLM client supporting:
- openai: OpenAI API or OpenAI-compatible APIs (OpenRouter, etc.)
- nim: NVIDIA NIM (OpenAI-compatible endpoint)
- local: Local model via OpenAI-compatible API
"""
import os
from openai import OpenAI
from typing import Optional, Dict, List, Any
from config import LLMConfig, get_llm_config


class LLMClient:
    """
    Provider-agnostic LLM client that supports multiple backends.
    
    Supported providers:
    - "openai": OpenAI API or OpenAI-compatible (OpenRouter, etc.)
    - "nim": NVIDIA NIM (OpenAI-compatible endpoint)
    - "local": Local model via OpenAI-compatible API
    """
    
    def __init__(self, provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client with provider configuration.
        
        Args:
            provider: Provider name ("openai", "nim", "local")
                     If None, reads from LLMConfig.LLM_PROVIDER
            config: Optional config dict to override env vars
                   Keys: api_key, base_url, model, temperature, etc.
        """
        # Get provider from parameter or config module
        self.provider = (provider or LLMConfig.LLM_PROVIDER).lower()
        
        if self.provider not in ["openai", "nim", "local"]:
            raise ValueError(f"Unsupported provider: {self.provider}. Must be 'openai', 'nim', or 'local'")
        
        # Load configuration from config module (with optional overrides)
        self.config = self._load_config(config)
        
        # Validate NIM config if needed
        if self.provider == "nim":
            LLMConfig.validate_nim_config()
        
        # Initialize client based on provider
        self.client = self._initialize_client()
        
        # Model and temperature settings
        self.model = self.config.get("model")
        self.temperature = float(self.config.get("temperature", 0.2))
        self.max_tokens = int(self.config.get("max_tokens", 2000))
        
        print(f"✅ LLM Client initialized:")
        print(f"   Provider: {self.provider}")
        print(f"   Model: {self.model}")
        print(f"   Base URL: {self.config.get('base_url', 'N/A')}")
    
    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Load configuration from config module or provided config dict."""
        # Get base config from config module
        base_config = get_llm_config(self.provider)
        
        # Override with provided config if any
        if config:
            base_config.update(config)
        
        return base_config
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client with provider-specific configuration."""
        api_key = self.config.get("api_key")
        base_url = self.config.get("base_url")
        
        if not base_url:
            if self.provider == "nim":
                raise ValueError("NIM_BASE_URL must be set for NVIDIA NIM provider")
            elif self.provider == "local":
                raise ValueError("LOCAL_BASE_URL must be set for local provider")
        
        if not api_key and self.provider != "local":
            raise ValueError(f"API key required for provider: {self.provider}")
        
        # Build headers based on provider
        headers = {}
        
        if self.provider == "openai":
            # OpenRouter/OpenAI headers
            headers = {
                "HTTP-Referer": LLMConfig.HTTP_REFERER,
                "X-Title": LLMConfig.X_TITLE,
            }
        elif self.provider == "nim":
            # NVIDIA NIM headers (if needed)
            headers = {
                "Authorization": f"Bearer {api_key}" if api_key else None,
            }
            headers = {k: v for k, v in headers.items() if v is not None}
        
        # Create OpenAI client (works with all OpenAI-compatible APIs)
        client = OpenAI(
            api_key=api_key or "not-needed",  # Some local providers don't need API key
            base_url=base_url,
            default_headers=headers if headers else None
        )
        
        return client
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat completion request and return response text.
        
        Args:
            messages: List of message dicts with "role" and "content"
                     Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
        
        Returns:
            Response text string
        """
        # Use provided params or fall back to instance defaults
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = f"Error calling {self.provider} provider: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e
    
    def get_client(self) -> OpenAI:
        """Get the underlying OpenAI client instance."""
        return self.client


# Factory function for backward compatibility
def get_llm_client(provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> LLMClient:
    """
    Factory function to create an LLMClient instance.
    
    Args:
        provider: Provider name ("openai", "nim", "local")
        config: Optional configuration dict
    
    Returns:
        LLMClient instance
    """
    return LLMClient(provider=provider, config=config)


# Backward compatibility: Create default client instance
_default_client: Optional[LLMClient] = None

def get_default_client() -> LLMClient:
    """Get or create the default LLM client instance."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client

