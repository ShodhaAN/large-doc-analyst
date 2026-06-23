from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router

app = FastAPI(
    title="Large Document Analyst",
    description="Upload PDFs and ask questions using RAG + Llama 3",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}