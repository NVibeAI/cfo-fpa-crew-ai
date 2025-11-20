# find_working_model.py
"""
Test commonly accessible models to find one that works.
"""

from llm_client import LLMClient
from config import LLMConfig
import time

# Models most likely to be publicly accessible for inference
PRIORITY_MODELS = [
    # Tier 1: Usually public and free
    "microsoft/phi-3-mini-128k-instruct",
    "microsoft/phi-3-small-128k-instruct",
    "google/gemma-2-9b-it",
    "google/gemma-2-2b-it",
    "mistralai/mistral-7b-instruct-v0.3",
    
    # Tier 2: Often accessible
    "meta/llama-3.2-3b-instruct",
    "meta/llama-3.2-1b-instruct",
    "mistralai/mistral-7b-instruct-v0.2",
    "qwen/qwen2-7b-instruct",
    
    # Tier 3: May require approval
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
]

print("=" * 70)
print("Finding Working Model for Your API Key")
print("=" * 70)
print(f"Testing {len(PRIORITY_MODELS)} commonly accessible models...\n")

working_model = None

for i, model in enumerate(PRIORITY_MODELS, 1):
    print(f"[{i}/{len(PRIORITY_MODELS)}] Testing: {model}")
    
    try:
        # Create client with specific model
        config = {
            "api_key": LLMConfig.NVIDIA_NGC_API_KEY,
            "base_url": LLMConfig.NVIDIA_BASE_URL,
            "model": model,
            "temperature": 0.7,
            "max_tokens": 20
        }
        
        client = LLMClient(provider="nvidia_ngc", config=config)
        
        # Try a simple completion
        messages = [{"role": "user", "content": "Say hello"}]
        response = client.chat_completion(messages)
        
        print(f"   ✅ SUCCESS! This model works!")
        print(f"   Response: {response[:50]}...")
        
        working_model = model
        break  # Found a working model, stop testing
        
    except Exception as e:
        error_str = str(e)
        
        if "403" in error_str or "Forbidden" in error_str:
            print(f"   ❌ Forbidden (no access)")
        elif "404" in error_str:
            print(f"   ❌ Not found")
        elif "429" in error_str:
            print(f"   ⏳ Rate limited (has access, wait and retry)")
            working_model = model
            break
        else:
            print(f"   ❌ Error: {error_str[:40]}...")
        
        time.sleep(0.5)

print("\n" + "=" * 70)

if working_model:
    print("✅ FOUND WORKING MODEL!")
    print("=" * 70)
    print(f"\nModel: {working_model}")
    print(f"\nUpdate your .env file with:")
    print(f"NVIDIA_MODEL={working_model}")
    
    # Auto-update .env
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
        
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("NVIDIA_MODEL="):
                    f.write(f"NVIDIA_MODEL={working_model}\n")
                else:
                    f.write(line)
        
        print(f"\n✅ Automatically updated .env file!")
        print(f"\nNow run:")
        print(f"  python test_nvidia_config.py")
        print(f"  streamlit run app.py")
        
    except Exception as e:
        print(f"\n⚠️  Could not auto-update .env: {e}")
        print(f"Please update manually.")
else:
    print("❌ NO WORKING MODELS FOUND")
    print("=" * 70)
    print("\nPossible issues:")
    print("1. Your API key may not have inference access")
    print("2. You may need to accept terms of service for models")
    print("3. Your account may need verification")
    print("\nNext steps:")
    print("1. Visit: https://build.nvidia.com")
    print("2. Sign in and browse models")
    print("3. Click on each model and accept any terms")
    print("4. Generate a new API key at: https://org.ngc.nvidia.com/setup")

print("=" * 70)