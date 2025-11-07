import os
from dotenv import load_dotenv

# Absolute path to .env
env_path = r"C:\Users\Lenovo\Documents\fpna_cfo_crew_ai\.env"

# Debug info
print("🔍 Checking .env path:", env_path)
print("🧭 File exists:", os.path.exists(env_path))

# Force load .env from this absolute path
load_dotenv(dotenv_path=env_path, override=True)

# Try to read the key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("✅ OPENAI_API_KEY loaded successfully!")
    print("🔑 First 10 chars:", api_key[:10], "...")
else:
    print("❌ Still not loaded. Let's debug deeper:")
    print("📂 Current working directory:", os.getcwd())

    # Read the file raw to check its content
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            print("\n📝 .env contents:\n" + f.read())
    else:
        print("🚫 .env file not found at expected path.")

