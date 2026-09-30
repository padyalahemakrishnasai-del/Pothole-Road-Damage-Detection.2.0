"""Integration tests for video processing and video analysis endpoint."""
import io
import cv2
import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.video_processor import VideoProcessor

client = TestClient(app)


@pytest.fixture
def sample_video_path(tmp_path):
    """Generate a small synthetic 10-frame road inspection video."""
    video_file = tmp_path / "synthetic_road.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_file), fourcc, 10.0, (320, 240))

    for i in range(10):
        frame = np.full((240, 320, 3), 60, dtype=np.uint8)
        # Draw road line
        cv2.line(frame, (160, 0), (160, 240), (255, 255, 255), 2)
        writer.write(frame)

    writer.release()
    return str(video_file)


def test_video_processor_synthetic(sample_video_path):
    processor = VideoProcessor(frame_step=2)
    res = processor.process_video(sample_video_path, output_filename="test_proc.mp4")

    assert "damage_count" in res
    assert "priority_score" in res
    assert "priority_label" in res
    assert "output_video_url" in res
    assert res["processed_frames"] > 0


def test_analyze_video_endpoint(sample_video_path):
    with open(sample_video_path, "rb") as f:
        video_bytes = f.read()

    response = client.post(
        "/api/analyze/video",
        files={"file": ("test_road.mp4", io.BytesIO(video_bytes), "video/mp4")}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["file_type"] == "video"
    assert "analysis_id" in data
    assert data["status"] == "completed"
    assert data["output_video_url"] is not None
