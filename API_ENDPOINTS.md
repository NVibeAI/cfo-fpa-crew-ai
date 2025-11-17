# API Endpoints Guide

## Quick Start

### Start the API Server

```powershell
python api_server.py
```

The server will start on `http://localhost:8000`

---

## Endpoints

### 1. `/llm/nim-test` - Test LLM Provider

**Description**: Tests the current LLM provider (configured via `LLM_PROVIDER` env var)

**Method**: `GET`

**Response**: Plain text response from the LLM

**Example Request**:
```bash
curl http://localhost:8000/llm/nim-test
```

**Example Response**:
```
Hello! This is a test response from the NIM integration.
```

**How it works**:
1. Reads `LLM_PROVIDER` from config (can be "openai", "nim", or "local")
2. Instantiates `LLMClient` with current configuration
3. Sends test message: `"Say hello from NIM integration test"`
4. Returns the raw text response

---

### 2. `/llm/config` - Get Current Configuration

**Description**: Returns current LLM configuration (without sensitive API keys)

**Method**: `GET`

**Response**: JSON object with provider and config details

**Example Request**:
```bash
curl http://localhost:8000/llm/config
```

**Example Response**:
```json
{
  "provider": "nim",
  "config": {
    "base_url": "https://integrate.api.nvidia.com/v1",
    "model": "meta/llama-3.1-70b-instruct",
    "api_key_set": true
  }
}
```

---

### 3. `/` - Root Endpoint

**Description**: API information and available endpoints

**Method**: `GET`

**Response**: JSON object with API info

---

## Testing with Different Providers

### Test with NIM

```powershell
# Set NIM environment variables
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="your-nim-key"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"

# Start server
python api_server.py

# In another terminal, test the endpoint
curl http://localhost:8000/llm/nim-test
```

### Test with OpenAI/OpenRouter

```powershell
# Set OpenAI environment variables
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_API_BASE="https://openrouter.ai/api/v1"

# Start server
python api_server.py

# Test
curl http://localhost:8000/llm/nim-test
```

### Test with Local Model

```powershell
# Set local environment variables
$env:LLM_PROVIDER="local"
$env:LOCAL_BASE_URL="http://localhost:11434/v1"
$env:LOCAL_MODEL="llama3"

# Start server
python api_server.py

# Test
curl http://localhost:8000/llm/nim-test
```

---

## Using in Browser

1. Start the server: `python api_server.py`
2. Open browser: `http://localhost:8000/llm/nim-test`
3. You'll see the raw text response

---

## API Documentation

FastAPI automatically generates interactive API docs:

1. Start the server: `python api_server.py`
2. Open browser: `http://localhost:8000/docs`
3. Test endpoints directly from the browser!

---

## Error Handling

The endpoint returns appropriate HTTP status codes:

- **200**: Success - LLM response returned
- **400**: Configuration error (missing required env vars)
- **500**: LLM API error (connection failed, invalid API key, etc.)

---

## Example: Complete Test Flow

```powershell
# 1. Set NIM configuration
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"

# 2. Start the API server
python api_server.py

# 3. In another terminal, test the endpoint
curl http://localhost:8000/llm/nim-test

# Expected output:
# Hello! This is a test response from the NIM integration.
```

---

## Integration with Other Services

You can call this endpoint from:
- Frontend applications
- Other microservices
- CI/CD pipelines
- Monitoring tools
- Load testing tools

Example from Python:
```python
import requests

response = requests.get("http://localhost:8000/llm/nim-test")
print(response.text)
```

