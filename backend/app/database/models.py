"""SQLAlchemy ORM models for analysis records."""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from app.database.session import Base


class Analysis(Base):
    """Stores metadata and results for each road damage analysis."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(String(36), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    
    # Source info
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # "image" or "video"
    file_path = Column(String(500), nullable=True)
    
    # Results
    damage_count = Column(Integer, default=0)
    pothole_count = Column(Integer, default=0)
    crack_count = Column(Integer, default=0)
    surface_damage_count = Column(Integer, default=0)
    
    avg_confidence = Column(Float, default=0.0)
    highest_severity = Column(String(20), default="None")
    priority_score = Column(Float, default=0.0)
    priority_label = Column(String(20), default="Low")
    recommendation = Column(Text, nullable=True)
    
    # Detailed results stored as JSON
    detections = Column(JSON, nullable=True)
    
    # Output paths & URLs
    output_image_path = Column(String(500), nullable=True)
    output_image_url = Column(String(500), nullable=True)
    output_video_path = Column(String(500), nullable=True)
    output_video_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="completed")  # processing, completed, failed
    error_message = Column(Text, nullable=True)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "damage_count": self.damage_count,
            "pothole_count": self.pothole_count,
            "crack_count": self.crack_count,
            "surface_damage_count": self.surface_damage_count,
            "avg_confidence": round(self.avg_confidence, 4) if self.avg_confidence else 0,
            "highest_severity": self.highest_severity,
            "priority_score": round(self.priority_score, 1) if self.priority_score else 0,
            "priority_label": self.priority_label,
            "recommendation": self.recommendation or "",
            "detections": self.detections or [],
            "output_image_url": self.output_image_url,
            "output_video_url": self.output_video_url,
            "status": self.status,
            "error_message": self.error_message,
        }
