"""AI RoadGuard — FastAPI Application Entry Point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import init_db
from app.api import health, analysis, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print(f"📁 Uploads: {settings.UPLOAD_DIR}")
    print(f"📁 Outputs: {settings.OUTPUT_DIR}")
    
    # Initialize database tables
    init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down AI RoadGuard API")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Road Damage Detection & Maintenance Prioritization API",
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories for serving annotated images/videos
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

# Register API routes
app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
