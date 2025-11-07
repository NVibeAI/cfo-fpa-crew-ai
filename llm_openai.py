# llm_openai.py
from dotenv import load_dotenv
import os
from crewai import LLM

# --------------------------------------------------------------------
# Load .env safely
# --------------------------------------------------------------------
env_path = os.path.join(os.getcwd(), ".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(f"❌ .env file not found at: {env_path}")
load_dotenv(env_path)

# --------------------------------------------------------------------
# Get LLM configuration for CrewAI v1.3.0
# --------------------------------------------------------------------
def get_llm():
    """
    Returns a CrewAI LLM object configured for OpenRouter.
    CrewAI 1.3.0 uses the new LLM class that handles OpenAI-compatible APIs.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENAI_MODEL_NAME", "meta-llama/llama-3.1-70b-instruct")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

    if not api_key:
        raise EnvironmentError("❌ Missing OPENAI_API_KEY in .env file!")

    print(f"✅ LLM Configuration Loaded:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature}")

    # Use CrewAI's LLM class with OpenAI-compatible configuration
    llm = LLM(
        model=f"openai/{model}",  # Prefix with 'openai/' for OpenAI-compatible APIs
        api_key=api_key,
        base_url=base_url,
        temperature=temperature
    )
    
    return llm