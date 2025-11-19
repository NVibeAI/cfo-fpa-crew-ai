# api_server.py
"""
FastAPI backend server for LLM testing and API endpoints.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from llm_client import get_default_client
from config import LLMConfig
import uvicorn

app = FastAPI(
    title="FP&A CFO Crew AI API",
    description="Backend API for LLM provider testing and operations",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FP&A CFO Crew AI API",
        "version": "1.0.0",
        "endpoints": {
            "/llm/nim-test": "Test LLM provider (uses LLM_PROVIDER from config)"
        }
    }


@app.get("/llm/nim-test", response_class=PlainTextResponse)
async def nim_test():
    """
    Test endpoint for LLM provider.
    
    Instantiates LLMClient with current config and sends a test request.
    Returns the raw text response from the LLM.
    
    Uses LLM_PROVIDER from config (can be "openai", "nim", or "local").
    """
    try:
        # Get current provider from config
        provider = LLMConfig.LLM_PROVIDER
        
        # Instantiate LLMClient with current config
        client = get_default_client()
        
        # Send test request
        messages = [{"role": "user", "content": "Say hello from NIM integration test"}]
        
        # Get response
        response_text = client.chat_completion(messages)
        
        # Return raw text response
        return response_text
    
    except ValueError as e:
        # Configuration errors
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    
    except Exception as e:
        # LLM API errors
        raise HTTPException(
            status_code=500,
            detail=f"LLM request failed: {str(e)}"
        )


@app.get("/llm/config")
async def get_config():
    """Get current LLM configuration (without sensitive data)."""
    return {
        "provider": LLMConfig.LLM_PROVIDER,
        "config": {
            "base_url": getattr(LLMConfig, f"{LLMConfig.LLM_PROVIDER.upper()}_BASE_URL", None) or 
                       getattr(LLMConfig, "OPENAI_API_BASE", None),
            "model": getattr(LLMConfig, f"{LLMConfig.LLM_PROVIDER.upper()}_MODEL", None) or 
                    getattr(LLMConfig, "OPENAI_MODEL_NAME", None),
            "api_key_set": bool(
                getattr(LLMConfig, f"{LLMConfig.LLM_PROVIDER.upper()}_API_KEY", None) or
                getattr(LLMConfig, "OPENAI_API_KEY", None)
            )
        }
    }


if __name__ == "__main__":
    # Run the server
    print("🚀 Starting FP&A CFO Crew AI API Server...")
    print(f"📋 Current LLM Provider: {LLMConfig.LLM_PROVIDER}")
    print("📍 API available at: http://localhost:8000")
    print("🧪 Test endpoint: http://localhost:8000/llm/nim-test")
    print("📖 API docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)

