"""Unit tests for RoadDamageDetector service."""
import pytest
import numpy as np
import cv2
from app.services.detector import RoadDamageDetector


@pytest.fixture
def detector():
    return RoadDamageDetector()


def test_detector_initialization(detector):
    assert detector.model is not None
    info = detector.get_info()
    assert info["model_loaded"] is True
    assert info["device"] in ["cpu", "cuda"]
    assert len(info["classes"]) > 0


def test_severity_calculation(detector):
    # Pothole severity
    assert detector.calculate_severity("Pothole", 0.05, 0.8) == "Severe"
    assert detector.calculate_severity("Pothole", 0.02, 0.7) == "Severe"
    assert detector.calculate_severity("Pothole", 0.012, 0.5) == "Moderate"
    assert detector.calculate_severity("Pothole", 0.005, 0.5) == "Minor"

    # Alligator Crack severity
    assert detector.calculate_severity("Alligator Crack", 0.045, 0.9) == "Severe"
    assert detector.calculate_severity("Alligator Crack", 0.015, 0.5) == "Moderate"

    # Linear Cracks
    assert detector.calculate_severity("Longitudinal Crack", 0.07, 0.8) == "Severe"
    assert detector.calculate_severity("Transverse Crack", 0.03, 0.6) == "Moderate"
    assert detector.calculate_severity("Longitudinal Crack", 0.01, 0.6) == "Minor"


def test_priority_calculation_empty(detector):
    score, label, rec = detector.calculate_priority([])
    assert score == 0.0
    assert label == "Low"
    assert "No surface damage" in rec


def test_priority_calculation_critical(detector):
    detections = [
        {"class_name": "Pothole", "confidence": 0.9, "severity": "Severe"},
        {"class_name": "Pothole", "confidence": 0.85, "severity": "Severe"},
        {"class_name": "Alligator Crack", "confidence": 0.8, "severity": "Severe"},
    ]
    score, label, rec = detector.calculate_priority(detections)
    assert score >= 80.0
    assert label == "Critical"
    assert "Immediate structural intervention" in rec


def test_annotation_frame(detector):
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    detections = [
        {
            "class_name": "Pothole",
            "confidence": 0.95,
            "bbox": [50.0, 50.0, 150.0, 150.0],
            "severity": "Severe",
            "area_ratio": 0.11
        }
    ]
    annotated = detector.annotate_frame(img, detections)
    assert annotated.shape == img.shape
    # Check that pixels were drawn on
    assert np.any(annotated != 0)
