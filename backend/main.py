"""
ClipGenius - Main FastAPI Application
Gerador automático de cortes virais com IA
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import CLIPS_DIR, VIDEOS_DIR
from models import init_db
from api.routes import router
from api.auth_routes import router as auth_router
from api.editor_routes import router as editor_router
from logging_config import configure_logging, get_logger

# Configure structured logging on startup
configure_logging()
logger = get_logger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)


# CORS configuration from environment
# Default: localhost for development
# Production: set CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else DEFAULT_CORS_ORIGINS
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("Initializing ClipGenius")
    print("Initializing ClipGenius...")
    init_db()
    logger.info("Database initialized successfully")
    print("Database initialized")
    logger.info("CORS origins configured", cors_origins=CORS_ORIGINS)
    print(f"CORS origins: {CORS_ORIGINS}")
    yield
    logger.info("Shutting down ClipGenius")
    print("Shutting down ClipGenius")


app = FastAPI(
    title="ClipGenius API",
    description="API para geração automática de cortes virais com IA",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for serving videos
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
app.mount("/clips", StaticFiles(directory=str(CLIPS_DIR)), name="clips")

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(editor_router, prefix="/api")


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
