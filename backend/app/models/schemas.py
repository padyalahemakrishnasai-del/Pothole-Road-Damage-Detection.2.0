"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    message: str
    model_loaded: bool = False
    device: str = "unknown"


class Detection(BaseModel):
    """A single detected damage instance."""
    class_name: str = Field(..., description="Damage category name")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence 0-1")
    bbox: list[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    severity: str = Field(default="Unknown", description="Estimated severity level")
    area_ratio: float = Field(default=0.0, description="Ratio of bbox area to image area")


class AnalysisResult(BaseModel):
    """Full analysis result for an image or video."""
    analysis_id: str
    file_name: str
    file_type: str  # "image" or "video"
    created_at: str
    
    # Counts
    damage_count: int = 0
    pothole_count: int = 0
    crack_count: int = 0
    surface_damage_count: int = 0
    
    # Scores
    avg_confidence: float = 0.0
    highest_severity: str = "None"
    priority_score: float = 0.0
    priority_label: str = "Low"
    recommendation: str = ""
    
    # Detailed detections
    detections: list[Detection] = []
    
    # Output URLs
    output_image_url: Optional[str] = None
    output_video_url: Optional[str] = None
    
    status: str = "completed"
    error_message: Optional[str] = None


class AnalysisSummary(BaseModel):
    """Summary item for history listing."""
    analysis_id: str
    created_at: str
    file_name: str
    file_type: str
    damage_count: int
    highest_severity: str
    priority_score: float
    priority_label: str
    status: str


class DashboardStats(BaseModel):
    """Dashboard aggregate statistics."""
    total_analyses: int = 0
    images_analyzed: int = 0
    videos_analyzed: int = 0
    total_damages: int = 0
    total_potholes: int = 0
    total_cracks: int = 0
    total_surface_damage: int = 0
    avg_confidence: float = 0.0
    severity_distribution: dict = {}
    priority_distribution: dict = {}
    damage_type_distribution: dict = {}
    recent_analyses: list[AnalysisSummary] = []


class ModelInfo(BaseModel):
    """Model information response."""
    model_name: str = "YOLO"
    model_version: str = "unknown"
    model_loaded: bool = False
    device: str = "cpu"
    classes: list[str] = []
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.45
    image_size: int = 640
    status: str = "not_loaded"
