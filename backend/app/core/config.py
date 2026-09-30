from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Project
    PROJECT_NAME: str = "AI RoadGuard API"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./road_damage.db"
    
    # YOLO Model
    YOLO_MODEL_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "weights" / "best.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    YOLO_IOU_THRESHOLD: float = 0.45
    YOLO_IMAGE_SIZE: int = 640
    
    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png"]
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".mov", ".avi"]
    
    # Paths
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    OUTPUT_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "outputs")
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
