from llm_client import LLMClient

# Test Vertex AI
print("Testing Vertex AI...")
vertex_client = LLMClient(provider="vertex_ai")
response = vertex_client.chat_completion([
    {"role": "user", "content": "Say 'Vertex AI is working!' in exactly 5 words."}
])
print(f"Vertex AI Response: {response}")

# Test NVIDIA NGC
print("\nTesting NVIDIA NGC...")
nvidia_client = LLMClient(provider="nvidia_ngc")
response = nvidia_client.chat_completion([
    {"role": "user", "content": "Say 'NVIDIA is working!' in exactly 4 words."}
])
print(f"NVIDIA Response: {response}")

print("\n✅ Both providers working!")