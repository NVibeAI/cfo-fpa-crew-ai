from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="FP&A CFO Crew AI API",
    description="Backend API for Financial Planning & Analysis",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
origins = [
    "http://localhost:8501",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "FP&A CFO Crew AI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting server...")
    print("📍 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    
    # Pass app object directly (NOT string) to avoid module import issues
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
