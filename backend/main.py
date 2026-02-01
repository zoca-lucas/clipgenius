"""
ClipGenius - Main FastAPI Application
Gerador automático de cortes virais com IA
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from config import CLIPS_DIR, VIDEOS_DIR
from models import init_db
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    print("🚀 Initializing ClipGenius...")
    init_db()
    print("✅ Database initialized")
    yield
    print("👋 Shutting down ClipGenius")


app = FastAPI(
    title="ClipGenius API",
    description="API para geração automática de cortes virais com IA",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for serving videos
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
app.mount("/clips", StaticFiles(directory=str(CLIPS_DIR)), name="clips")

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ClipGenius API",
        "version": "1.0.0",
        "description": "Gerador automático de cortes virais com IA",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
