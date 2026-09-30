"""Unit and integration tests for PDF report generation."""
import os
import io
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_pdf_report_generation():
    # 1. First upload a synthetic image to create an analysis record
    img = np.full((300, 300, 3), 70, dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    
    upload_res = client.post(
        "/api/analyze/image",
        files={"file": ("report_test.jpg", io.BytesIO(encoded.tobytes()), "image/jpeg")}
    )
    assert upload_res.status_code == 200
    analysis_id = upload_res.json()["analysis_id"]

    # 2. Request PDF report
    report_res = client.get(f"/api/analysis/{analysis_id}/report")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert len(report_res.content) > 1000  # Non-trivial PDF content
    assert report_res.content.startswith(b"%PDF")
