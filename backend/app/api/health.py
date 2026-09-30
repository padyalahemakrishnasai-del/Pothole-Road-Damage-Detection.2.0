"""Health and model info endpoints."""
from fastapi import APIRouter
from app.models.schemas import HealthResponse, ModelInfo
from app.services.detector import detector_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check API and model health status."""
    info = detector_service.get_info()
    return HealthResponse(
        status="ok",
        message="AI RoadGuard API is running",
        model_loaded=info["model_loaded"],
        device=info["device"]
    )


@router.get("/api/model/info", response_model=ModelInfo)
def model_info():
    """Get information about the loaded ML model."""
    info = detector_service.get_info()
    return ModelInfo(
        model_name=info["model_name"],
        model_version="8.4.170",
        model_loaded=info["model_loaded"],
        device=info["device"],
        classes=info["classes"],
        confidence_threshold=info["confidence_threshold"],
        iou_threshold=info["iou_threshold"],
        image_size=info["image_size"],
        status=info["status"]
    )

