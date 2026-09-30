"""Integration tests for FastAPI endpoints."""
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_model_info_endpoint():
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "classes" in data
    assert "confidence_threshold" in data


def test_dashboard_stats_endpoint():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_analyses" in data
    assert "severity_distribution" in data
    assert "priority_distribution" in data


def test_history_endpoint():
    response = client.get("/api/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analyze_image_invalid_extension():
    fake_txt = io.BytesIO(b"fake text content")
    response = client.post(
        "/api/analyze/image",
        files={"file": ("test.txt", fake_txt, "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported image format" in response.json()["detail"]


def test_analyze_image_and_retrieve():
    # Create synthetic test road image with OpenCV
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw gray road asphalt
    img[:] = (60, 60, 60)
    # Draw lane mark
    cv2.line(img, (320, 0), (320, 480), (255, 255, 255), 4)
    # Encode as JPEG
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = io.BytesIO(img_encoded.tobytes())

    # Send POST request
    response = client.post(
        "/api/analyze/image",
        files={"file": ("test_road.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()

    assert "analysis_id" in data
    analysis_id = data["analysis_id"]
    assert data["file_name"] == "test_road.jpg"
    assert data["file_type"] == "image"
    assert "damage_count" in data
    assert "priority_score" in data
    assert "priority_label" in data
    assert "recommendation" in data
    assert data["status"] == "completed"

    # Retrieve by ID
    get_res = client.get(f"/api/analysis/{analysis_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["analysis_id"] == analysis_id
    assert get_data["file_name"] == "test_road.jpg"
