"""Road Damage Detector service using Ultralytics YOLO.

Provides inference, severity estimation, priority scoring,
and visual annotation for road imagery and video frames.
"""
import os
import cv2
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from ultralytics import YOLO

from app.core.config import settings


# Professional color palette (BGR format for OpenCV)
COLOR_PALETTE = {
    "Pothole": (50, 50, 220),            # Crimson / Red
    "Longitudinal Crack": (30, 210, 240), # Golden Yellow
    "Transverse Crack": (220, 200, 30),  # Cyan
    "Alligator Crack": (30, 140, 240),   # Deep Amber / Orange
    "Surface Damage": (180, 50, 160),    # Violet / Purple
    "Default": (200, 160, 60),           # Slate Blue
}

SEVERITY_COLORS = {
    "Minor": (70, 180, 70),       # Green
    "Moderate": (30, 180, 230),   # Amber
    "Severe": (50, 50, 220),      # Crimson Red
    "Unknown": (150, 150, 150),   # Gray
}


class RoadDamageDetector:
    """Manages YOLO model inference, damage assessment, and annotation."""

    def __init__(self, model_path: Optional[str] = None):
        self.requested_path = model_path or settings.YOLO_MODEL_PATH
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model: Optional[YOLO] = None
        self.is_custom_model: bool = False
        self.model_status: str = "uninitialized"
        self.model_name: str = "Unknown"
        self.classes: List[str] = []
        
        self._load_model()

    def _load_model(self) -> None:
        """Load custom road damage model if available, else load base YOLO for infrastructure validation."""
        # Candidate paths to look for trained weights
        candidates = [
            Path(self.requested_path),
            Path(__file__).resolve().parents[3] / "ml" / "weights" / "best.pt",
            Path(__file__).resolve().parents[2] / "ml" / "weights" / "best.pt"
        ]

        for path in candidates:
            if path.exists() and path.is_file():
                try:
                    print(f"[Detector] Loading custom road damage weights from: {path}")
                    self.model = YOLO(str(path))
                    self.model.to(self.device)
                    self.is_custom_model = True
                    self.model_status = "custom_model_loaded"
                    self.model_name = path.name
                    self.classes = list(self.model.names.values()) if hasattr(self.model, "names") else []
                    print(f"[Detector] Custom model loaded successfully with {len(self.classes)} classes.")
                    return
                except Exception as e:
                    print(f"[Detector] Failed to load custom model at {path}: {e}")

        # Fallback to base pretrained YOLO
        try:
            fallback_weights = "yolov8n.pt"
            print(f"[Detector] Custom weights not found at {path}. Loading base model '{fallback_weights}' for pipeline verification.")
            self.model = YOLO(fallback_weights)
            self.model.to(self.device)
            self.is_custom_model = False
            self.model_status = "base_model_loaded"
            self.model_name = fallback_weights
            self.classes = list(self.model.names.values()) if hasattr(self.model, "names") else []
            print(f"[Detector] Base YOLO model loaded successfully on device: {self.device} (80 COCO classes).")
        except Exception as e:
            self.model_status = f"failed_to_load: {e}"
            self.model = None
            print(f"[Detector] Critical error loading fallback model: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Return operational details and status of the detector."""
        return {
            "model_name": self.model_name,
            "model_loaded": self.model is not None,
            "is_custom_road_damage_model": self.is_custom_model,
            "device": self.device,
            "classes": self.classes,
            "class_count": len(self.classes),
            "confidence_threshold": settings.YOLO_CONFIDENCE_THRESHOLD,
            "iou_threshold": settings.YOLO_IOU_THRESHOLD,
            "image_size": settings.YOLO_IMAGE_SIZE,
            "status": self.model_status,
            "note": (
                "Running fine-tuned Road Damage Detection model."
                if self.is_custom_model
                else "Running base pretrained YOLO model. For specialized road damage (potholes/cracks), fine-tuned weights must be placed at ml/weights/best.pt."
            )
        }

    @staticmethod
    def calculate_severity(class_name: str, area_ratio: float, confidence: float) -> str:
        """
        Estimate damage severity based on defect category, bbox area ratio, and confidence.
        
        Severity Levels:
            - Severe: Large potholes, widespread alligator cracks, or major surface ruptures.
            - Moderate: Medium-sized cracks and developing potholes.
            - Minor: Surface hairline cracks or small abrasions.
        """
        lower_name = class_name.lower()

        # Potholes and alligator cracking pose higher structural & vehicular risk
        if "pothole" in lower_name or "alligator" in lower_name:
            if area_ratio >= 0.04 or (area_ratio >= 0.02 and confidence > 0.65):
                return "Severe"
            elif area_ratio >= 0.01:
                return "Moderate"
            return "Minor"

        # Linear cracks (Longitudinal / Transverse)
        elif "crack" in lower_name:
            if area_ratio >= 0.06:
                return "Severe"
            elif area_ratio >= 0.02:
                return "Moderate"
            return "Minor"

        # General surface damage / weathering
        else:
            if area_ratio >= 0.08:
                return "Moderate"
            return "Minor"

    @staticmethod
    def calculate_priority(detections: List[Dict[str, Any]]) -> Tuple[float, str, str]:
        """
        Calculate an engineering maintenance priority score (0-100) and actionable recommendation.
        
        Formula considerations:
            - Damage count & density
            - High weight for severe potholes (immediate suspension/tire hazard)
            - Moderate-high weight for severe alligator cracks (base layer failure)
            - Aggregate confidence factor
        """
        if not detections:
            return (0.0, "Low", "No surface damage detected. Road surface is in good operating condition.")

        score = 0.0
        severe_count = 0
        pothole_count = 0
        crack_count = 0

        for d in detections:
            c_name = d["class_name"].lower()
            sev = d["severity"]
            conf = d["confidence"]

            # Severity baseline points
            if sev == "Severe":
                score += 28.0 * conf
                severe_count += 1
            elif sev == "Moderate":
                score += 14.0 * conf
            else:
                score += 5.0 * conf

            # Hazard category multipliers
            if "pothole" in c_name:
                pothole_count += 1
                score += 12.0 * conf
            elif "alligator" in c_name:
                crack_count += 1
                score += 8.0 * conf
            elif "crack" in c_name:
                crack_count += 1
                score += 4.0 * conf

        # Cap score at 100
        score = min(round(score, 1), 100.0)

        # Categorize Priority & Recommendation
        if score >= 80.0 or severe_count >= 2 or pothole_count >= 3:
            label = "Critical"
            recommendation = (
                "Immediate structural intervention required. High-severity potholes/cracking "
                "pose imminent hazard to motorists. Dispatch maintenance crew for emergency patching."
            )
        elif score >= 60.0 or severe_count >= 1:
            label = "High"
            recommendation = (
                "Priority repair recommended within 14 days. Surface deterioration is actively progressing "
                "and may cause sub-base water infiltration."
            )
        elif score >= 35.0:
            label = "Medium"
            recommendation = (
                "Routine maintenance scheduling recommended within 30-60 days. "
                "Apply crack sealing to prevent propagation into structural alligator cracking."
            )
        else:
            label = "Low"
            recommendation = (
                "Minor surface wear detected. Continue standard inspection intervals; "
                "no immediate intervention required."
            )

        return score, label, recommendation

    def annotate_frame(
        self,
        image_bgr: np.ndarray,
        detections: List[Dict[str, Any]],
        draw_summary_badge: bool = True
    ) -> np.ndarray:
        """
        Draw clean, high-visibility engineering bounding boxes and labels onto an image.
        """
        annotated = image_bgr.copy()
        h, w = annotated.shape[:2]

        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
            cls_name = det["class_name"]
            conf = det["confidence"]
            sev = det["severity"]

            # Determine color
            box_color = COLOR_PALETTE.get(cls_name, COLOR_PALETTE["Default"])

            # 1. Draw outer bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2, cv2.LINE_AA)

            # 2. Draw subtle corner accents for crisp appearance
            corner_len = min(16, (x2 - x1) // 4, (y2 - y1) // 4)
            if corner_len > 4:
                # Top-left
                cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), box_color, 3, cv2.LINE_AA)
                cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), box_color, 3, cv2.LINE_AA)
                # Bottom-right
                cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), box_color, 3, cv2.LINE_AA)
                cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), box_color, 3, cv2.LINE_AA)

            # 3. Label text
            label_text = f"{cls_name} {conf:.0%} [{sev}]"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

            # Background banner for text
            label_y1 = max(0, y1 - text_h - baseline - 6)
            label_y2 = y1
            label_x2 = min(w, x1 + text_w + 10)

            # Filled banner
            cv2.rectangle(annotated, (x1, label_y1), (label_x2, label_y2), box_color, cv2.FILLED)
            # Text string
            cv2.putText(
                annotated,
                label_text,
                (x1 + 5, y1 - baseline - 2),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        # Draw summary header overlay on top-left if detections exist
        if draw_summary_badge and detections:
            header_text = f"Detections: {len(detections)}"
            cv2.rectangle(annotated, (15, 15), (200, 50), (20, 24, 33), cv2.FILLED)
            cv2.rectangle(annotated, (15, 15), (200, 50), (245, 158, 11), 1, cv2.LINE_AA)
            cv2.putText(
                annotated,
                header_text,
                (25, 38),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return annotated

    def predict_image(
        self,
        image_path: str,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run inference on an image file, generate severity and priority analysis,
        and save annotated image output.
        """
        if self.model is None:
            raise RuntimeError(f"Detector model is not available: {self.model_status}")

        # Read image to obtain dimensions
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Could not read image file at: {image_path}")

        img_h, img_w = img_bgr.shape[:2]
        total_area = float(img_h * img_w)

        # Run Ultralytics inference
        results = self.model.predict(
            source=image_path,
            conf=settings.YOLO_CONFIDENCE_THRESHOLD,
            iou=settings.YOLO_IOU_THRESHOLD,
            imgsz=settings.YOLO_IMAGE_SIZE,
            device=self.device,
            verbose=False
        )

        detections: List[Dict[str, Any]] = []
        pothole_count = 0
        crack_count = 0
        surface_damage_count = 0

        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes

            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_idx = int(box.cls[0].cpu().numpy())

                class_name = self.classes[cls_idx] if cls_idx < len(self.classes) else f"class_{cls_idx}"

                # Calculate bbox area ratio
                box_w = max(0.0, xyxy[2] - xyxy[0])
                box_h = max(0.0, xyxy[3] - xyxy[1])
                area_ratio = (box_w * box_h) / total_area if total_area > 0 else 0.0

                # Compute severity
                severity = self.calculate_severity(class_name, area_ratio, conf)

                # Class counts
                lower_name = class_name.lower()
                if "pothole" in lower_name:
                    pothole_count += 1
                elif "crack" in lower_name:
                    crack_count += 1
                elif "surface" in lower_name:
                    surface_damage_count += 1

                detections.append({
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "bbox": [round(c, 1) for c in xyxy],
                    "severity": severity,
                    "area_ratio": round(area_ratio, 6)
                })

        # Calculate Priority Score and Recommendation
        priority_score, priority_label, recommendation = self.calculate_priority(detections)

        # Calculate average confidence
        avg_conf = (
            round(sum(d["confidence"] for d in detections) / len(detections), 4)
            if detections else 0.0
        )

        # Find highest severity level
        severity_rank = {"Severe": 3, "Moderate": 2, "Minor": 1, "None": 0}
        highest_severity = "None"
        if detections:
            highest_severity = max(
                (d["severity"] for d in detections),
                key=lambda s: severity_rank.get(s, 0)
            )

        # Save annotated image
        annotated_bgr = self.annotate_frame(img_bgr, detections)
        out_name = output_filename or f"annotated_{Path(image_path).name}"
        out_path = Path(settings.OUTPUT_DIR) / out_name
        cv2.imwrite(str(out_path), annotated_bgr)

        output_image_url = f"/outputs/{out_name}"

        return {
            "damage_count": len(detections),
            "pothole_count": pothole_count,
            "crack_count": crack_count,
            "surface_damage_count": surface_damage_count,
            "avg_confidence": avg_conf,
            "highest_severity": highest_severity,
            "priority_score": priority_score,
            "priority_label": priority_label,
            "recommendation": recommendation,
            "detections": detections,
            "output_image_url": output_image_url,
            "output_image_path": str(out_path),
        }


# Global detector instance for reuse across requests
detector_service = RoadDamageDetector()
