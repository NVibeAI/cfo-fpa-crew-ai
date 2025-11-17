# Running with NVIDIA NIM Provider

## Quick Start

### 1. Set Environment Variables

**Option A: In `.env` file**
```bash
LLM_PROVIDER=nim
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=your-nim-api-key-here
NIM_MODEL=meta/llama-3.1-70b-instruct
```

**Option B: In PowerShell (temporary)**
```powershell
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="your-nim-api-key-here"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"
```

**Option C: In Command Prompt (temporary)**
```cmd
set LLM_PROVIDER=nim
set NIM_BASE_URL=https://integrate.api.nvidia.com/v1
set NIM_API_KEY=your-nim-api-key-here
set NIM_MODEL=meta/llama-3.1-70b-instruct
```

### 2. Run the Application

```powershell
# Run Streamlit dashboard
streamlit run app.py

# Or run a specific task
python -m agno_runner
```

---

## Example .env File for NIM

```bash
# LLM Provider Configuration
LLM_PROVIDER=nim

# NVIDIA NIM Settings
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NIM_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NIM_MODEL=meta/llama-3.1-70b-instruct

# Optional NIM Settings
NIM_TEMPERATURE=0.2
NIM_MAX_TOKENS=2000
```

---

## Example NIM Configuration Values

### Common NIM Base URLs:
- **Production**: `https://integrate.api.nvidia.com/v1`
- **Staging**: `https://staging.integrate.api.nvidia.com/v1` (if available)
- **Custom**: Your organization's custom NIM endpoint

### Common NIM Models:
- `meta/llama-3.1-70b-instruct`
- `meta/llama-3.1-8b-instruct`
- `mistralai/mistral-7b-instruct`
- `google/gemma-7b-it`
- Check NVIDIA NIM documentation for available models

### NIM API Key Format:
- Usually starts with `nvapi-` or similar
- Get from NVIDIA NIM dashboard/console

---

## Testing NIM Configuration

### Quick Test Script

Create `test_nim.py`:
```python
from config import LLMConfig
from llm_client import get_default_client

# Print current config
LLMConfig.print_config()

# Test the client
client = get_default_client()
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Say 'NIM is working!'"}
]

try:
    response = client.chat_completion(messages)
    print(f"\n✅ Response: {response}")
except Exception as e:
    print(f"\n❌ Error: {e}")
```

Run:
```powershell
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="your-key"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"
python test_nim.py
```

---

## Switching Between Providers

### Switch to NIM:
```powershell
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="your-key"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"
```

### Switch back to OpenAI/OpenRouter:
```powershell
$env:LLM_PROVIDER="openai"
# Uses existing OPENAI_API_KEY, OPENAI_API_BASE, etc.
```

### Switch to Local:
```powershell
$env:LLM_PROVIDER="local"
$env:LOCAL_BASE_URL="http://localhost:11434/v1"
$env:LOCAL_MODEL="llama3"
```

---

## Verification

After setting environment variables, verify the configuration:

```python
from config import LLMConfig

# Print current configuration
LLMConfig.print_config()

# Check specific values
print(f"Provider: {LLMConfig.LLM_PROVIDER}")
print(f"NIM Base URL: {LLMConfig.NIM_BASE_URL}")
print(f"NIM Model: {LLMConfig.NIM_MODEL}")
print(f"NIM API Key: {'✅ Set' if LLMConfig.NIM_API_KEY else '❌ Not set'}")
```

---

## Troubleshooting

### Error: "NIM_BASE_URL must be set"
- Make sure `NIM_BASE_URL` is set in your environment or `.env` file
- Check for typos in the variable name

### Error: "NIM_API_KEY or OPENAI_API_KEY must be set"
- Set `NIM_API_KEY` in your environment
- Or set `OPENAI_API_KEY` as a fallback

### Error: "NIM_MODEL must be set"
- Set `NIM_MODEL` to a valid NVIDIA NIM model name
- Check NVIDIA documentation for available models

### Error: Connection refused / Timeout
- Verify `NIM_BASE_URL` is correct
- Check your network connection
- Verify your NIM API key is valid
- Check if your organization's NIM endpoint requires VPN

---

## Complete Example: Running Streamlit with NIM

```powershell
# Set all NIM environment variables
$env:LLM_PROVIDER="nim"
$env:NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
$env:NIM_API_KEY="nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:NIM_MODEL="meta/llama-3.1-70b-instruct"
$env:NIM_TEMPERATURE="0.2"

# Run the Streamlit app
streamlit run app.py
```

The app will automatically use NVIDIA NIM for all LLM calls!

