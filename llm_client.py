from openai import OpenAI
from typing import Optional, Dict, List, Any
from config import LLMConfig, get_llm_config

class LLMClient:
    def __init__(self, provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.provider = (provider or LLMConfig.LLM_PROVIDER).lower()
        self.config = get_llm_config(self.provider)
        if config:
            self.config.update(config)
        
        # SET MODEL ATTRIBUTES FIRST (before calling init methods)
        self.model = self.config["model"]
        self.temperature = self.config["temperature"]
        self.max_tokens = self.config["max_tokens"]
        
        # Initialize based on provider
        if self.provider == "vertex_ai":
            self._init_vertex_ai()
        else:
            self._init_openai_compatible()
        
        print(f"✅ LLM Client: {self.provider}")
        print(f"   Model: {self.model}")

    def _init_openai_compatible(self):
        """Initialize OpenAI-compatible clients (NVIDIA NGC, OpenRouter, etc.)"""
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
        print(f"   API Key: {self.config['api_key'][:15]}...")

    def _init_vertex_ai(self):
        """Initialize Vertex AI client with proper authentication"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            from google.oauth2 import service_account  # ← ADDED THIS
            
            self.project_id = self.config["project_id"]
            self.location = self.config["location"]
            
            # ===== AUTHENTICATION FIX - THIS IS THE ONLY NEW PART =====
            service_account_json = self.config.get("service_account_json")
            
            if service_account_json:
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
                
                print(f"   Project: {self.project_id}")
                print(f"   Location: {self.location}")
                print(f"   Auth: Service Account JSON")
            else:
                # Fall back to default credentials (gcloud CLI)
                vertexai.init(project=self.project_id, location=self.location)
                print(f"   Project: {self.project_id}")
                print(f"   Location: {self.location}")
                print(f"   Auth: Default Credentials (gcloud)")
            # ===== END OF AUTHENTICATION FIX =====
            
            # Create the generative model
            self.vertex_model = GenerativeModel(self.model)
            
        except ImportError:
            raise ImportError(
                "Vertex AI dependencies not installed. "
                "Install with: pip install google-cloud-aiplatform"
            )
        except FileNotFoundError:
            raise ValueError(
                f"Service account JSON file not found. "
                f"Please check the path in VERTEX_SERVICE_ACCOUNT_JSON"
            )

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Unified chat completion method that works with all providers.
        """
        try:
            if self.provider == "vertex_ai":
                return self._vertex_ai_completion(messages, **kwargs)
            else:
                return self._openai_compatible_completion(messages, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error calling {self.provider}: {str(e)}")

    def _openai_compatible_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """OpenAI-compatible completion (NVIDIA NGC, OpenRouter, etc.)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    def _vertex_ai_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Vertex AI completion using Generative AI API"""
        try:
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
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
            
            # If there's a system instruction, create model with it
            if system_instruction:
                from vertexai.generative_models import GenerativeModel
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
            raise RuntimeError(f"Vertex AI API error: {str(e)}")

    def get_client(self):
        """Return the underlying client (for backward compatibility)"""
        if self.provider == "vertex_ai":
            return self.vertex_model
        return self.client


_default_client = None
def get_default_client():
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client