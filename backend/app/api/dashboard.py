"""Dashboard statistics and analytics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.database.models import Analysis
from app.models.schemas import DashboardStats, AnalysisSummary

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Compute aggregate analytics across all recorded damage analyses."""
    analyses = db.query(Analysis).all()
    
    total_analyses = len(analyses)
    images_analyzed = sum(1 for a in analyses if a.file_type == "image")
    videos_analyzed = sum(1 for a in analyses if a.file_type == "video")
    
    total_damages = sum(a.damage_count for a in analyses)
    total_potholes = sum(a.pothole_count for a in analyses)
    total_cracks = sum(a.crack_count for a in analyses)
    total_surface_damage = sum(a.surface_damage_count for a in analyses)
    
    # Calculate global average confidence
    valid_confs = [a.avg_confidence for a in analyses if a.avg_confidence and a.avg_confidence > 0]
    avg_confidence = round(sum(valid_confs) / len(valid_confs), 4) if valid_confs else 0.0

    # Severity distribution
    severity_distribution = {"Severe": 0, "Moderate": 0, "Minor": 0, "None": 0}
    for a in analyses:
        sev = a.highest_severity or "None"
        severity_distribution[sev] = severity_distribution.get(sev, 0) + 1

    # Priority distribution
    priority_distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for a in analyses:
        prio = a.priority_label or "Low"
        priority_distribution[prio] = priority_distribution.get(prio, 0) + 1

    # Damage type distribution
    damage_type_distribution = {
        "Pothole": total_potholes,
        "Cracks": total_cracks,
        "Surface Damage": total_surface_damage
    }

    # Fetch 10 most recent analyses
    recent_records = (
        db.query(Analysis)
        .order_by(desc(Analysis.created_at))
        .limit(10)
        .all()
    )

    recent_analyses = [
        AnalysisSummary(
            analysis_id=r.analysis_id,
            created_at=r.created_at.isoformat() if r.created_at else "",
            file_name=r.file_name,
            file_type=r.file_type,
            damage_count=r.damage_count,
            highest_severity=r.highest_severity,
            priority_score=r.priority_score,
            priority_label=r.priority_label,
            status=r.status
        )
        for r in recent_records
    ]

    return DashboardStats(
        total_analyses=total_analyses,
        images_analyzed=images_analyzed,
        videos_analyzed=videos_analyzed,
        total_damages=total_damages,
        total_potholes=total_potholes,
        total_cracks=total_cracks,
        total_surface_damage=total_surface_damage,
        avg_confidence=avg_confidence,
        severity_distribution=severity_distribution,
        priority_distribution=priority_distribution,
        damage_type_distribution=damage_type_distribution,
        recent_analyses=recent_analyses
    )
