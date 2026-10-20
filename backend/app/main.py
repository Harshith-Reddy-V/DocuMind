"""
DocuMind FastAPI Application Entrypoint.
"""
import os
import sys

# Ensure backend directory is in sys.path so 'app' modules resolve regardless of working directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.routes import documents, workspace, patent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and storage directories on startup
    settings.ensure_directories()
    init_db()
    yield


app = FastAPI(
    title="DocuMind API",
    description="Gemini-powered grounded Q&A and summarization over academic documents.",
    version="1.0.0",
    lifespan=lifespan,
)

is_wildcard = "*" in settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(workspace.router)
app.include_router(patent.router)


@app.get("/")
async def root():
    """Root landing endpoint for deployment verification."""
    return {
        "name": "DocuMind API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }


@app.get("/api/health")
async def health_check():
    """Service health check and configuration status."""
    return {
        "status": "ok",
        "gemini_key_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
        "generation_model": settings.GEMINI_GENERATION_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
    }


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Sanitize unexpected exceptions so internal paths, keys, or stack traces
    are never leaked to clients.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "code": "INTERNAL_SERVER_ERROR"}
    )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
