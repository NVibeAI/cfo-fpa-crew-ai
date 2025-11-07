import requests
import json

api_key = "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"

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "meta-llama/llama-3.1-8b-instruct",  # reliable open model
    "messages": [
        {"role": "system", "content": "You are a test assistant. Only reply with the exact sentence requested, no extra text."},
        {"role": "user", "content": "Reply exactly with this text: Hi from openrouter connection test"}
    ],
    "max_tokens": 50
}

response = requests.post(url, headers=headers, data=json.dumps(data))

if response.status_code == 200:
    try:
        result = response.json()
        print("✅ Full response JSON:\n", json.dumps(result, indent=2))  # debug print

        # Safely extract model reply
        message = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        print("\n✅ Model reply:\n", message or "[empty text]")
    except Exception as e:
        print("⚠️ Error parsing JSON:", e)
else:
    print(f"❌ Error {response.status_code}: {response.text}")
