"""File handling utilities — validation, sanitization, saving."""
import os
import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    # Keep only alphanumeric, dots, hyphens, underscores
    name = re.sub(r'[^\w\-.]', '_', filename)
    # Prevent directory traversal
    name = name.replace('..', '_')
    return name


def validate_image_file(file: UploadFile) -> None:
    """Validate that an uploaded file is an allowed image type."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{ext}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )


def validate_video_file(file: UploadFile) -> None:
    """Validate that an uploaded file is an allowed video type."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )


async def save_upload(file: UploadFile, subfolder: str = "") -> tuple[str, str]:
    """
    Save an uploaded file to the uploads directory.
    
    Returns:
        tuple of (unique_filename, full_save_path)
    """
    ext = Path(file.filename).suffix.lower()
    safe_name = sanitize_filename(Path(file.filename).stem)
    unique_name = f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"
    
    save_dir = Path(settings.UPLOAD_DIR)
    if subfolder:
        save_dir = save_dir / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    
    save_path = save_dir / unique_name
    
    # Read and check size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Maximum allowed: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    with open(save_path, "wb") as f:
        f.write(contents)
    
    return unique_name, str(save_path)
