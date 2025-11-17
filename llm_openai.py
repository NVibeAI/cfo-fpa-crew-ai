# llm_openai.py
from dotenv import load_dotenv
import os
from openai import OpenAI

# --------------------------------------------------------------------
# Load .env safely
# --------------------------------------------------------------------
env_path = os.path.join(os.getcwd(), ".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(f"❌ .env file not found at: {env_path}")

load_dotenv(env_path, override=True)  # Added override=True

def get_openai_client():
    """
    Returns an OpenAI client configured for OpenRouter.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    
    if not api_key:
        raise EnvironmentError("❌ Missing OPENAI_API_KEY in .env file!")
    
    # Strip any whitespace from API key
    api_key = api_key.strip()
    
    print(f"✅ OpenRouter Client Configured:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:15]}...{api_key[-4:]}")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Agno FP&A Dashboard",
        }
    )
    
    return client

def get_model_name():
    """Returns the model name from environment"""
    model = os.getenv("OPENAI_MODEL_NAME", "meta-llama/llama-3.1-70b-instruct")
    return model.strip()

def get_temperature():
    """Returns the temperature from environment"""
    return float(os.getenv("OPENAI_TEMPERATURE", "0.2"))