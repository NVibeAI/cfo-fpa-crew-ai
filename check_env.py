from dotenv import load_dotenv, find_dotenv
import os

env_path = find_dotenv()
print("🧭 Found .env at:", env_path if env_path else "❌ Not found")

load_dotenv(env_path)
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("✅ OPENAI_API_KEY loaded successfully!")
    print("🔑 First 10 chars:", api_key[:10], "...")
else:
    print("❌ OPENAI_API_KEY not loaded. Please check .env format or encoding.")
