from openai import OpenAI
from typing import Optional, Dict, List, Any
from config import LLMConfig, get_llm_config

class LLMClient:
    def __init__(self, provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.provider = (provider or LLMConfig.LLM_PROVIDER).lower()
        self.config = get_llm_config(self.provider)
        if config:
            self.config.update(config)
        
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
        
        self.model = self.config["model"]
        self.temperature = self.config["temperature"]
        self.max_tokens = self.config["max_tokens"]
        
        print(f"✅ LLM Client: {self.provider}")
        print(f"   Model: {self.model}")
        print(f"   API Key: {self.config['api_key'][:15]}...")

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Error calling {self.provider}: {str(e)}")

_default_client = None
def get_default_client():
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
