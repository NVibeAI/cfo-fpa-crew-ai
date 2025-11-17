# LLM Provider Configuration Guide

The project now uses a provider-agnostic `LLMClient` that supports multiple LLM backends.

## Supported Providers

1. **openai** - OpenAI API or OpenAI-compatible APIs (OpenRouter, etc.) - **Default**
2. **nim** - NVIDIA NIM (OpenAI-compatible endpoint)
3. **local** - Local model via OpenAI-compatible API (Ollama, etc.)

## Configuration via Environment Variables

### Provider Selection

Set `LLM_PROVIDER` in your `.env` file:
```bash
LLM_PROVIDER=openai    # or "nim" or "local"
```

---

## Provider-Specific Configuration

### 1. OpenAI/OpenRouter (Default)

```bash
LLM_PROVIDER=openai

# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL_NAME=meta-llama/llama-3.1-70b-instruct
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=2000

# Optional headers
HTTP_REFERER=http://localhost:8501
X_TITLE=Agno FP&A Dashboard
```

### 2. NVIDIA NIM

```bash
LLM_PROVIDER=nim

# Required
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=your-nim-api-key
NIM_MODEL=meta/llama-3.1-70b-instruct

# Optional (defaults shown)
NIM_TEMPERATURE=0.2
NIM_MAX_TOKENS=2000
```

**NVIDIA NIM Setup:**
1. Get your NIM API key from NVIDIA
2. Set `NIM_BASE_URL` to your NIM endpoint (usually `https://integrate.api.nvidia.com/v1`)
3. Set `NIM_MODEL` to the model you want to use
4. Set `NIM_API_KEY` to your API key

**Example NIM Configuration:**
```bash
LLM_PROVIDER=nim
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=nvapi-xxxxx
NIM_MODEL=meta/llama-3.1-70b-instruct
```

### 3. Local Model (Ollama, etc.)

```bash
LLM_PROVIDER=local

# Required
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=llama3

# Optional (defaults shown)
LOCAL_API_KEY=not-needed
LOCAL_TEMPERATURE=0.2
LOCAL_MAX_TOKENS=2000
```

**Local Setup (Ollama Example):**
1. Install and run Ollama: `ollama serve`
2. Pull a model: `ollama pull llama3`
3. Set `LOCAL_BASE_URL=http://localhost:11434/v1`
4. Set `LOCAL_MODEL=llama3` (or your model name)

**Example Local Configuration:**
```bash
LLM_PROVIDER=local
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=llama3
```

---

## Usage Examples

### Using the LLMClient Class Directly

```python
from llm_client import LLMClient

# Initialize with provider from env vars
client = LLMClient()

# Or specify provider explicitly
client = LLMClient(provider="nim")

# Or with custom config
client = LLMClient(
    provider="nim",
    config={
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "your-key",
        "model": "meta/llama-3.1-70b-instruct"
    }
)

# Make a chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

response = client.chat_completion(messages)
print(response)
```

### Using the Factory Function

```python
from llm_client import get_llm_client

# Get default client (reads from env vars)
client = get_llm_client()

# Or with custom provider
client = get_llm_client(provider="nim")
```

### Using the Default Client (Current Implementation)

The current codebase uses `get_default_client()` which is automatically initialized:

```python
from llm_client import get_default_client

llm_client = get_default_client()
response = llm_client.chat_completion(messages)
```

---

## Migration from Old Code

The new `LLMClient` is backward compatible. The old code:

```python
from llm_openai import get_openai_client
client = get_openai_client()
response = client.chat.completions.create(...)
```

Now works as:

```python
from llm_client import get_default_client
llm_client = get_default_client()
response = llm_client.chat_completion(messages)
```

The `agno_config.py` and `agno_runner.py` have been updated to use the new client automatically.

---

## Testing Different Providers

### Test OpenAI/OpenRouter
```bash
LLM_PROVIDER=openai
python -c "from llm_client import get_default_client; c = get_default_client(); print(c.chat_completion([{'role': 'user', 'content': 'Hello'}]))"
```

### Test NVIDIA NIM
```bash
LLM_PROVIDER=nim
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=your-key
NIM_MODEL=meta/llama-3.1-70b-instruct
python -c "from llm_client import get_default_client; c = get_default_client(); print(c.chat_completion([{'role': 'user', 'content': 'Hello'}]))"
```

### Test Local (Ollama)
```bash
LLM_PROVIDER=local
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=llama3
python -c "from llm_client import get_default_client; c = get_default_client(); print(c.chat_completion([{'role': 'user', 'content': 'Hello'}]))"
```

---

## Troubleshooting

### Error: "Unsupported provider"
- Make sure `LLM_PROVIDER` is set to one of: `openai`, `nim`, `local`

### Error: "NIM_BASE_URL must be set"
- For NIM provider, you must set `NIM_BASE_URL` in your `.env` file

### Error: "API key required"
- Make sure you've set the appropriate API key:
  - `OPENAI_API_KEY` for openai provider
  - `NIM_API_KEY` for nim provider
  - `LOCAL_API_KEY` is optional for local provider

### Error: "Connection refused" (Local)
- Make sure your local LLM server is running
- Check that `LOCAL_BASE_URL` points to the correct address

---

## Notes

- All providers use the OpenAI-compatible API format
- The `LLMClient` automatically handles provider-specific headers and configuration
- You can switch providers by just changing the `LLM_PROVIDER` env var
- The client is initialized once and reused across the application

