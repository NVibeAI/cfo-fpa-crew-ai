# utils/openrouter_client.py
import os
import requests
import json

OPENROUTER_URL = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

def chat_completion(messages, model="meta-llama/llama-3.1-8b-instruct", max_tokens=512, temperature=0.2):
    """
    Simple wrapper to call OpenRouter chat completion endpoint.
    `messages` should be a list of dicts: [{"role":"system","content":"..."}, ...]
    Returns the assistant's text (string).
    """
    if not OPENROUTER_KEY:
        raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY in your .env or environment.")
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        # raise useful error
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text}")
    data = resp.json()
    # safe extraction
    try:
        content = data["choices"][0]["message"]["content"]
        return content, data
    except Exception:
        # fallback to raw json if structure differs
        return json.dumps(data), data
