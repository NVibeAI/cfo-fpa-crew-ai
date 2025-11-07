import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Custom OpenRouter headers
custom_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://openrouter.ai",  # your app or site
    "X-Title": "FP&A CrewAI"
}

# Monkey patch to inject headers correctly
old_request = client.request

def patched_request(self, cast_to, options=None, **kwargs):
    if options and hasattr(options, "headers"):
        # merge existing headers
        all_headers = {**custom_headers, **(options.headers or {})}
        options.headers = all_headers
    else:
        # if options is None or missing headers field
        kwargs["options"] = type("obj", (), {"headers": custom_headers})()
    return old_request(cast_to, options=options, **kwargs)

client.request = patched_request.__get__(client, OpenAI)

# Test
response = client.chat.completions.create(
    model="meta-llama/llama-3.1-70b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hi from OpenRouter connection test!"}
    ]
)

print(response.choices[0].message.content)
