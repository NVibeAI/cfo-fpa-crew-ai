# list_available_models.py
"""
Query NVIDIA NGC API to list all available models for your API key.
"""

import requests
import json
from config import LLMConfig

print("=" * 70)
print("Checking Available NVIDIA NGC Models")
print("=" * 70)

# API endpoint to list models
url = "https://integrate.api.nvidia.com/v1/models"

# Headers with your API key
headers = {
    "Authorization": f"Bearer {LLMConfig.NVIDIA_NGC_API_KEY}",
    "Content-Type": "application/json"
}

print(f"\n🔑 Using API Key: {LLMConfig.NVIDIA_NGC_API_KEY[:20]}...")
print(f"🌐 Querying: {url}\n")

try:
    # Make request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if 'data' key exists (common API response format)
        if isinstance(data, dict) and 'data' in data:
            models = data['data']
        elif isinstance(data, list):
            models = data
        else:
            models = [data]
        
        print(f"✅ Found {len(models)} available models:\n")
        print("=" * 70)
        
        # List all models
        for i, model in enumerate(models, 1):
            if isinstance(model, dict):
                model_id = model.get('id', model.get('name', 'Unknown'))
                description = model.get('description', 'No description')
                owner = model.get('owned_by', model.get('owner', 'N/A'))
                
                print(f"\n{i}. Model ID: {model_id}")
                print(f"   Owner: {owner}")
                if description and description != 'No description':
                    print(f"   Description: {description[:100]}...")
            else:
                print(f"\n{i}. {model}")
        
        print("\n" + "=" * 70)
        print("💡 To use a model, copy its ID and update your .env file:")
        print("   NVIDIA_MODEL=<model-id>")
        
    elif response.status_code == 401:
        print("❌ Error 401: Invalid API key")
        print("   Generate a new key at: https://org.ngc.nvidia.com/setup")
        
    elif response.status_code == 403:
        print("❌ Error 403: Access forbidden")
        print("   Your API key may not have permission to list models")
        
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
    print("\n💡 Check your internet connection and try again")

print("=" * 70)