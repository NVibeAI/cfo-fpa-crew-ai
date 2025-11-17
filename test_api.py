# test_api.py
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Test",
    }
)

try:
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": "Say 'API works!'"}],
        max_tokens=10
    )
    print(f"✅ Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")