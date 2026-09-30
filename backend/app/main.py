"""AI RoadGuard — FastAPI Application Entry Point."""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.database.session import init_db
from app.api import health, analysis, dashboard

# Path to the React frontend build output
FRONTEND_BUILD_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


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

# --- Serve React Frontend in Production ---
if FRONTEND_BUILD_DIR.exists() and (FRONTEND_BUILD_DIR / "index.html").exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "assets")), name="frontend-assets")

    # Catch-all: serve index.html for any non-API route (client-side routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If a static file exists at the path, serve it
        file_path = FRONTEND_BUILD_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for React Router
        return FileResponse(str(FRONTEND_BUILD_DIR / "index.html"))
