import json
from utils.openrouter_client import OpenRouterClient

# Load the system prompt
with open("prompts/finance_prompt.json", "r") as f:
    prompt_data = json.load(f)

system_prompt = prompt_data["system"]

# Initialize the client
client = OpenRouterClient("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")

# Example FP&A task
user_prompt = """
Q3 revenue grew by 8.4%, cost of goods sold rose by 6%, and marketing expenses increased by 10%.
Please summarize key insights and suggest 2 cost optimization strategies.
"""

try:
    result = client.chat(system_prompt, user_prompt)
    print("\n✅ CFO Crew AI Response:\n")
    print(result)
except Exception as e:
    print("❌ Error:", e)
