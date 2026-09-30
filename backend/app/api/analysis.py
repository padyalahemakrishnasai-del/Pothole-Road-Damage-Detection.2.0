"""Analysis endpoints — image and video upload, ML detection, and DB storage."""
import uuid
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.database.models import Analysis
from app.models.schemas import AnalysisResult, AnalysisSummary
from app.utils.file_handler import validate_image_file, validate_video_file, save_upload
from app.services.detector import detector_service
from app.services.video_processor import video_processor
from app.services.report_generator import report_generator

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze/image", response_model=AnalysisResult)
async def analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a road image, run YOLO damage detection, compute severity and
    maintenance priority, save results to DB, and return structured analysis.
    """
    # 1. Validate file extension and format
    validate_image_file(file)

    # 2. Save uploaded file to disk
    unique_name, file_path = await save_upload(file, subfolder="images")
    analysis_id = str(uuid.uuid4())

    try:
        # 3. Execute YOLO ML inference and annotation
        out_name = f"annotated_{unique_name}"
        prediction = detector_service.predict_image(file_path, output_filename=out_name)

        # 4. Create and persist database record
        now = datetime.datetime.now(datetime.timezone.utc)
        record = Analysis(
            analysis_id=analysis_id,
            created_at=now,
            file_name=file.filename or unique_name,
            file_type="image",
            file_path=file_path,
            damage_count=prediction["damage_count"],
            pothole_count=prediction["pothole_count"],
            crack_count=prediction["crack_count"],
            surface_damage_count=prediction["surface_damage_count"],
            avg_confidence=prediction["avg_confidence"],
            highest_severity=prediction["highest_severity"],
            priority_score=prediction["priority_score"],
            priority_label=prediction["priority_label"],
            recommendation=prediction["recommendation"],
            detections=prediction["detections"],
            output_image_path=prediction["output_image_path"],
            output_image_url=prediction["output_image_url"],
            status="completed"
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return AnalysisResult(
            analysis_id=record.analysis_id,
            file_name=record.file_name,
            file_type="image",
            created_at=record.created_at.isoformat(),
            damage_count=record.damage_count,
            pothole_count=record.pothole_count,
            crack_count=record.crack_count,
            surface_damage_count=record.surface_damage_count,
            avg_confidence=record.avg_confidence,
            highest_severity=record.highest_severity,
            priority_score=record.priority_score,
            priority_label=record.priority_label,
            recommendation=record.recommendation or "",
            detections=record.detections or [],
            output_image_url=record.output_image_url,
            output_video_url=None,
            status="completed"
        )

    except Exception as e:
        db.rollback()
        # Save failed record if possible
        failed_record = Analysis(
            analysis_id=analysis_id,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            file_name=file.filename or unique_name,
            file_type="image",
            file_path=file_path,
            status="failed",
            error_message=str(e)
        )
        db.add(failed_record)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Inference error processing road image: {str(e)}"
        )


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific analysis result by unique ID."""
    record = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Analysis with ID '{analysis_id}' not found.")

    return AnalysisResult(
        analysis_id=record.analysis_id,
        file_name=record.file_name,
        file_type=record.file_type,
        created_at=record.created_at.isoformat() if record.created_at else "",
        damage_count=record.damage_count,
        pothole_count=record.pothole_count,
        crack_count=record.crack_count,
        surface_damage_count=record.surface_damage_count,
        avg_confidence=record.avg_confidence,
        highest_severity=record.highest_severity,
        priority_score=record.priority_score,
        priority_label=record.priority_label,
        recommendation=record.recommendation or "",
        detections=record.detections or [],
        output_image_url=record.output_image_url,
        output_video_url=record.output_video_url,
        status=record.status,
        error_message=record.error_message
    )


@router.get("/history", response_model=List[AnalysisSummary])
def get_analysis_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve historical analyses ordered by newest first."""
    records = db.query(Analysis).order_by(desc(Analysis.created_at)).limit(limit).all()
    return [
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
        for r in records
    ]


@router.delete("/analysis/{analysis_id}")
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Delete an analysis record."""
    record = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    db.delete(record)
    db.commit()
    return {"status": "success", "message": f"Analysis {analysis_id} deleted."}


@router.get("/analysis/{analysis_id}/report")
def download_inspection_report(analysis_id: str, db: Session = Depends(get_db)):
    """Generate and return an engineering PDF report for a given inspection."""
    record = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    pdf_file_path = report_generator.generate_pdf(record)
    return FileResponse(
        path=pdf_file_path,
        media_type="application/pdf",
        filename=f"RoadGuard_Inspection_{analysis_id[:8]}.pdf"
    )


@router.post("/analyze/video", response_model=AnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a road inspection video, run YOLO damage detection across sampled frames,
    render annotated output video, save aggregate results to DB, and return analysis.
    """
    # 1. Validate file extension and format
    validate_video_file(file)

    # 2. Save uploaded video to disk
    unique_name, file_path = await save_upload(file, subfolder="videos")
    analysis_id = str(uuid.uuid4())

    try:
        # 3. Execute frame-by-frame inference and rendering
        out_name = f"annotated_{unique_name}"
        prediction = video_processor.process_video(file_path, output_filename=out_name)

        # 4. Create and persist database record
        now = datetime.datetime.now(datetime.timezone.utc)
        record = Analysis(
            analysis_id=analysis_id,
            created_at=now,
            file_name=file.filename or unique_name,
            file_type="video",
            file_path=file_path,
            damage_count=prediction["damage_count"],
            pothole_count=prediction["pothole_count"],
            crack_count=prediction["crack_count"],
            surface_damage_count=prediction["surface_damage_count"],
            avg_confidence=prediction["avg_confidence"],
            highest_severity=prediction["highest_severity"],
            priority_score=prediction["priority_score"],
            priority_label=prediction["priority_label"],
            recommendation=prediction["recommendation"],
            detections=prediction["detections"],
            output_image_path=None,
            output_image_url=None,
            output_video_path=prediction["output_video_path"],
            output_video_url=prediction["output_video_url"],
            status="completed"
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return AnalysisResult(
            analysis_id=record.analysis_id,
            file_name=record.file_name,
            file_type="video",
            created_at=record.created_at.isoformat(),
            damage_count=record.damage_count,
            pothole_count=record.pothole_count,
            crack_count=record.crack_count,
            surface_damage_count=record.surface_damage_count,
            avg_confidence=record.avg_confidence,
            highest_severity=record.highest_severity,
            priority_score=record.priority_score,
            priority_label=record.priority_label,
            recommendation=record.recommendation or "",
            detections=record.detections or [],
            output_image_url=None,
            output_video_url=record.output_video_url,
            status="completed"
        )

    except Exception as e:
        db.rollback()
        failed_record = Analysis(
            analysis_id=analysis_id,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            file_name=file.filename or unique_name,
            file_type="video",
            file_path=file_path,
            status="failed",
            error_message=str(e)
        )
        db.add(failed_record)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Inference error processing road video: {str(e)}"
        )
