# LLM API Flow Analysis - FP&A CFO Crew AI

## 1. All LLM API Call Locations

### Primary LLM Call Points:

#### **A. Main Application Flow (Streamlit Dashboard)**
- **File**: `app.py`
- **Entry Point**: Line 114 - `run_agent_task(agent_choice, user_query, context=None)`
- **Flow**: User input → Streamlit chat → Agent orchestrator → LLM API

#### **B. Agent Runner (Core LLM Call)**
- **File**: `agno_runner.py`
- **Function**: `run_agent_task()` (Lines 7-60)
- **LLM Call**: Line 46 - `client.chat.completions.create()`
- **This is the PRIMARY LLM API call location**

#### **C. LLM Client Configuration**
- **File**: `llm_openai.py`
- **Function**: `get_openai_client()` (Lines 15-41)
- **Returns**: OpenAI client configured for OpenRouter
- **Base URL**: `https://openrouter.ai/api/v1` (default)

#### **D. Alternative LLM Wrapper**
- **File**: `utils/openrouter_client.py`
- **Function**: `chat_completion()` (Lines 9-38)
- **Method**: Direct HTTP POST to OpenRouter API
- **Status**: Alternative implementation (not currently used in main flow)

#### **E. Test Files (Not in Production Flow)**
- `test_api.py` - Line 24: `client.chat.completions.create()`
- `test_llm.py` - Line 12: `client.chat.completions.create()`
- `test_openrouter.py` - Line 37: `client.chat.completions.create()`
- `test_openrouter_direct.py` - Direct HTTP requests
- `quick_test.py` - Line 9: `client.chat.completions.create()`

#### **F. Legacy CrewAI Integration (Potentially Unused)**
- **Files**: `tasks/data_integration.py`, `tasks/fpna_forecast.py`, etc.
- **Status**: References `crew.llm` but `crew_config.py` was deleted
- **Note**: These may not be active in current implementation

---

## 2. Main Functions/Classes for LLM Requests

### **Primary Function: `run_agent_task()`**
**Location**: `agno_runner.py:7-60`

```python
def run_agent_task(agent_key, task_description, context=None):
    """
    Main function that orchestrates LLM API calls.
    
    Steps:
    1. Gets agent configuration from agno_config
    2. Builds message array with system prompt + user task
    3. Calls client.chat.completions.create()
    4. Extracts response.choices[0].message.content
    5. Returns text response
    """
```

**Key Code**:
```python
response = client.chat.completions.create(
    model=model,              # From agno_config (default: "meta-llama/llama-3.1-70b-instruct")
    messages=messages,        # [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]
    temperature=temperature,  # From agno_config (default: 0.2)
    max_tokens=2000
)
output = response.choices[0].message.content
```

### **Client Initialization: `get_openai_client()`**
**Location**: `llm_openai.py:15-41`

```python
def get_openai_client():
    """
    Creates and returns OpenAI client configured for OpenRouter.
    
    Configuration:
    - API Key: From OPENAI_API_KEY env var
    - Base URL: https://openrouter.ai/api/v1 (default)
    - Headers: HTTP-Referer, X-Title for OpenRouter tracking
    """
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Agno FP&A Dashboard",
        }
    )
    return client
```

### **Agent Configuration: `get_agent_config()`**
**Location**: `agno_config.py:124-126`

```python
def get_agent_config(agent_key):
    """
    Returns agent configuration dictionary with:
    - name: Agent display name
    - role: Agent role description
    - system_prompt: System prompt for LLM
    - backstory: Agent background
    """
```

### **Alternative Wrapper: `chat_completion()`**
**Location**: `utils/openrouter_client.py:9-38`

```python
def chat_completion(messages, model, max_tokens, temperature):
    """
    Direct HTTP POST wrapper for OpenRouter API.
    Uses requests library instead of OpenAI SDK.
    Currently not used in main flow.
    """
```

---

## 3. Complete Request Flow: HTTP → Orchestrator → LLM → Response

### **Flow Diagram:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. HTTP REQUEST (Streamlit Web Interface)                      │
│    File: app.py                                                 │
│    Entry: User types in chat input (Line 93)                    │
│    Handler: st.chat_input() → user_query variable              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. STREAMLIT ORCHESTRATOR                                       │
│    File: app.py:114                                             │
│    Action: response = run_agent_task(agent_choice, user_query) │
│    - Gets agent config from session state                      │
│    - Calls agent runner function                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. AGENT ORCHESTRATOR                                           │
│    File: agno_runner.py:7-60                                    │
│    Function: run_agent_task(agent_key, task_description)        │
│                                                                 │
│    Steps:                                                       │
│    a) Get agent config (agno_config.get_agent_config())        │
│    b) Build messages array:                                     │
│       - System message: agent["system_prompt"]                 │
│       - User message: task_description                          │
│    c) Prepare LLM call                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LLM CLIENT PREPARATION                                       │
│    File: agno_config.py:9                                       │
│    Variables: client, model, temperature                        │
│                                                                 │
│    Client Source: llm_openai.get_openai_client()               │
│    - Loads OPENAI_API_KEY from .env                            │
│    - Sets base_url to OpenRouter                               │
│    - Configures headers                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. LLM API CALL (OpenRouter/OpenAI Compatible)                 │
│    File: agno_runner.py:46                                     │
│    Method: client.chat.completions.create()                     │
│                                                                 │
│    Request Details:                                             │
│    - Endpoint: https://openrouter.ai/api/v1/chat/completions   │
│    - Model: meta-llama/llama-3.1-70b-instruct (default)        │
│    - Messages: [system_prompt, user_task]                      │
│    - Temperature: 0.2                                          │
│    - Max Tokens: 2000                                          │
│                                                                 │
│    HTTP Request:                                                │
│    POST https://openrouter.ai/api/v1/chat/completions          │
│    Headers:                                                     │
│      Authorization: Bearer <OPENAI_API_KEY>                    │
│      HTTP-Referer: http://localhost:8501                       │
│      X-Title: Agno FP&A Dashboard                              │
│    Body:                                                        │
│      {                                                          │
│        "model": "meta-llama/llama-3.1-70b-instruct",          │
│        "messages": [...],                                       │
│        "temperature": 0.2,                                      │
│        "max_tokens": 2000                                       │
│      }                                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM RESPONSE PROCESSING                                     │
│    File: agno_runner.py:53                                     │
│    Extraction: response.choices[0].message.content             │
│                                                                 │
│    Response Structure:                                          │
│    {                                                            │
│      "choices": [{                                              │
│        "message": {                                             │
│          "content": "<LLM generated text>"                     │
│        }                                                        │
│      }]                                                         │
│    }                                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. RESPONSE RETURN                                             │
│    File: agno_runner.py:56                                     │
│    Return: output (string)                                     │
│    → Returns to app.py:114                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. HTTP RESPONSE (Streamlit UI Update)                         │
│    File: app.py:117                                            │
│    Action: st.markdown(response)                                │
│    - Displays response in chat interface                        │
│    - Saves to outputs/ folder                                  │
│    - Updates session state                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary of Current Architecture

### **Active LLM Integration:**
- **Provider**: OpenRouter (OpenAI-compatible API)
- **Model**: `meta-llama/llama-3.1-70b-instruct` (default, configurable via env)
- **SDK**: OpenAI Python SDK (configured with custom base_url)
- **Primary Call Location**: `agno_runner.py:46`

### **Key Files:**
1. **`app.py`** - Streamlit UI, receives user input
2. **`agno_runner.py`** - Core orchestrator, makes LLM calls
3. **`agno_config.py`** - Agent definitions, client initialization
4. **`llm_openai.py`** - Client factory, environment loading

### **Environment Variables:**
- `OPENAI_API_KEY` - API key (works with OpenRouter)
- `OPENAI_API_BASE` - Base URL (default: `https://openrouter.ai/api/v1`)
- `OPENAI_MODEL_NAME` - Model identifier (default: `meta-llama/llama-3.1-70b-instruct`)
- `OPENAI_TEMPERATURE` - Temperature setting (default: `0.2`)

### **Message Format:**
```python
messages = [
    {"role": "system", "content": "<agent system prompt>"},
    {"role": "user", "content": "<user task/query>"}
]
```

### **Response Format:**
```python
response.choices[0].message.content  # String containing LLM response
```

---

## Notes:
- The codebase uses **OpenRouter** as the LLM provider (not direct OpenAI)
- All LLM calls go through the **OpenAI SDK** with a custom `base_url`
- The main entry point is the **Streamlit dashboard** (`app.py`)
- Agent configurations are stored in **`agno_config.py`**
- Legacy CrewAI code exists but may not be active (crew_config.py was deleted)

