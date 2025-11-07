from llm_openai import get_llm

# Get the configuration dictionary
llm_config = get_llm()
client = llm_config["client"]
model = llm_config["model"]

print(f"✅ Using OpenRouter base: {client.base_url}")
print(f"✅ Model: {model}")

# Send a test message
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Hello from CrewAI via OpenRouter!"}
    ],
    max_tokens=50,
)

# Print model’s reply
print("\n✅ Model reply:\n", response.choices[0].message.content)
