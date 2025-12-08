"""
Provider-agnostic LLM client supporting Vertex AI and NVIDIA NGC.
"""
from openai import OpenAI
from typing import Optional, Dict, List, Any
from config import LLMConfig, get_llm_config, validate_config

class LLMClient:
    def __init__(self, provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client for specified provider.
        
        Args:
            provider: "vertex_ai", "nvidia_ngc", or None (uses default from .env)
            config: Optional config overrides
        """
        self.provider = (provider or LLMConfig.LLM_PROVIDER).lower()
        self.config = get_llm_config(self.provider)
        
        if config:
            self.config.update(config)
        
        # Validate configuration
        validate_config(self.provider)
        
        # Set model attributes FIRST (before calling init methods)
        self.model = self.config["model"]
        self.temperature = self.config["temperature"]
        self.max_tokens = self.config["max_tokens"]
        
        # Initialize client and vertex_model attributes to None
        self.client = None
        self.vertex_model = None
        
        # Initialize based on provider
        if self.provider == "vertex_ai":
            self._init_vertex_ai()
        elif self.provider in ["nvidia_ngc", "nvidia"]:
            self._init_openai_compatible()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        print(f"✅ LLM Client initialized: {self.provider}")
        print(f"   Model: {self.model}")

    def _init_openai_compatible(self):
        """Initialize OpenAI-compatible clients (NVIDIA NGC, OpenRouter, etc.)"""
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
        print(f"   API Key: {self.config['api_key'][:15]}...")
        print(f"   Base URL: {self.config['base_url']}")

    def _init_vertex_ai(self):
        """Initialize Vertex AI client with service account authentication"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            from google.oauth2 import service_account
            
            self.project_id = self.config["project_id"]
            self.location = self.config["location"]
            service_account_json = self.config.get("service_account_json")
            
            if not service_account_json:
                raise ValueError(
                    "VERTEX_SERVICE_ACCOUNT_JSON not configured in .env file"
                )
            
            # Authenticate using service account JSON file
            credentials = service_account.Credentials.from_service_account_file(
                service_account_json,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Initialize Vertex AI with credentials
            vertexai.init(
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
            
            # Create the generative model
            self.vertex_model = GenerativeModel(self.model)
            
            print(f"   Project: {self.project_id}")
            print(f"   Location: {self.location}")
            print(f"   Auth: Service Account JSON")
            print(f"   ✅ Vertex AI initialized successfully")
            
        except ImportError as e:
            raise ImportError(
                "Vertex AI dependencies not installed. "
                "Install with: pip install google-cloud-aiplatform"
            ) from e
        except FileNotFoundError as e:
            raise ValueError(
                f"Service account JSON file not found: {service_account_json}\n"
                f"Please check the path in VERTEX_SERVICE_ACCOUNT_JSON"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vertex AI: {str(e)}") from e

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Unified chat completion method that works with all providers.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API
        
        Returns:
            The completion text
        """
        try:
            if self.provider == "vertex_ai":
                return self._vertex_ai_completion(messages, **kwargs)
            else:
                return self._openai_compatible_completion(messages, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error calling {self.provider}: {str(e)}") from e

    def _openai_compatible_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """OpenAI-compatible completion (NVIDIA NGC, OpenRouter, etc.)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens),
            **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
        )
        return response.choices[0].message.content

    def _vertex_ai_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Vertex AI completion using Generative AI API"""
        try:
            from vertexai.generative_models import GenerativeModel
            
            # Convert OpenAI message format to Vertex AI format
            vertex_messages = []
            system_instruction = None
            
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    vertex_messages.append({
                        "role": "user",
                        "parts": [{"text": content}]
                    })
                elif role == "assistant":
                    vertex_messages.append({
                        "role": "model",
                        "parts": [{"text": content}]
                    })
            
            # Create generation config
            generation_config = {
                "temperature": kwargs.get('temperature', self.temperature),
                "max_output_tokens": kwargs.get('max_tokens', self.max_tokens),
            }
            
            # If there's a system instruction, create model with it
            if system_instruction:
                model = GenerativeModel(
                    self.model,
                    system_instruction=system_instruction
                )
            else:
                model = self.vertex_model
            
            # Generate content
            chat = model.start_chat()
            
            # Send all messages except the last user message
            for msg in vertex_messages[:-1]:
                if msg["role"] == "user":
                    chat.send_message(msg["parts"][0]["text"])
            
            # Send final message and get response
            response = chat.send_message(
                vertex_messages[-1]["parts"][0]["text"],
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Vertex AI API error: {str(e)}") from e

    def get_client(self):
        """
        Return the underlying client (for backward compatibility).
        
        Returns:
            vertex_model for Vertex AI, OpenAI client for others
        """
        if self.provider == "vertex_ai":
            if self.vertex_model is None:
                raise RuntimeError("Vertex AI model not initialized")
            return self.vertex_model
        
        if self.client is None:
            raise RuntimeError("OpenAI-compatible client not initialized")
        return self.client

    def switch_provider(self, new_provider: str):
        """
        Switch to a different LLM provider.
        
        Args:
            new_provider: "vertex_ai" or "nvidia_ngc"
        """
        print(f"\n🔄 Switching from {self.provider} to {new_provider}...")
        self.__init__(provider=new_provider)


# Global default client
_default_client = None

def get_default_client() -> LLMClient:
    """
    Get or create the default LLM client.
    
    Returns:
        Global LLMClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client

def switch_default_provider(new_provider: str):
    """
    Switch the default client to a different provider.
    
    Args:
        new_provider: "vertex_ai" or "nvidia_ngc"
    """
    global _default_client
    _default_client = LLMClient(provider=new_provider)