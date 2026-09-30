"""Video processing service for road damage detection.

Extracts frames, performs YOLO inference, computes aggregate defect
severity and priority across the video, and renders an annotated video.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.services.detector import detector_service


class VideoProcessor:
    """Processes video files frame-by-frame with road damage detection."""

    def __init__(self, frame_step: int = 3):
        """
        Args:
            frame_step: Process 1 frame every `frame_step` frames for speed,
                        interpolating annotations across intermediate frames.
        """
        self.frame_step = frame_step

    def process_video(
        self,
        video_path: str,
        output_filename: Optional[str] = None,
        max_duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Process an uploaded video file, annotate frames, and compute aggregate metrics.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file at: {video_path}")

        # Video properties
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        fps = min(max(float(orig_fps), 10.0), 30.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Safeguard max frames (e.g. 60 seconds)
        max_frames = int(fps * max_duration_seconds)
        if total_frames > max_frames:
            total_frames = max_frames

        # Output video file setup
        out_name = output_filename or f"annotated_{Path(video_path).stem}.mp4"
        out_path = Path(settings.OUTPUT_DIR) / out_name

        # Try web-compatible codecs: avc1 (H.264) first, then mp4v
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
        if not writer.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

        all_detections: List[Dict[str, Any]] = []
        frame_idx = 0
        last_detections: List[Dict[str, Any]] = []
        total_area = float(width * height)

        pothole_instances = 0
        crack_instances = 0
        surface_instances = 0

        try:
            while cap.isOpened() and frame_idx < total_frames:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # Run inference every `frame_step` frames
                if frame_idx % self.frame_step == 0:
                    current_detections: List[Dict[str, Any]] = []

                    if detector_service.model is not None:
                        results = detector_service.model.predict(
                            source=frame,
                            conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                            iou=settings.YOLO_IOU_THRESHOLD,
                            imgsz=settings.YOLO_IMAGE_SIZE,
                            device=detector_service.device,
                            verbose=False
                        )

                        if results and len(results) > 0:
                            boxes = results[0].boxes
                            for box in boxes:
                                xyxy = box.xyxy[0].cpu().numpy().tolist()
                                conf = float(box.conf[0].cpu().numpy())
                                cls_idx = int(box.cls[0].cpu().numpy())
                                class_name = (
                                    detector_service.classes[cls_idx]
                                    if cls_idx < len(detector_service.classes)
                                    else f"class_{cls_idx}"
                                )

                                box_w = max(0.0, xyxy[2] - xyxy[0])
                                box_h = max(0.0, xyxy[3] - xyxy[1])
                                area_ratio = (box_w * box_h) / total_area if total_area > 0 else 0.0

                                sev = detector_service.calculate_severity(class_name, area_ratio, conf)

                                lower_name = class_name.lower()
                                if "pothole" in lower_name:
                                    pothole_instances += 1
                                elif "crack" in lower_name:
                                    crack_instances += 1
                                elif "surface" in lower_name:
                                    surface_instances += 1

                                det_info = {
                                    "class_name": class_name,
                                    "confidence": round(conf, 4),
                                    "bbox": [round(c, 1) for c in xyxy],
                                    "severity": sev,
                                    "area_ratio": round(area_ratio, 6),
                                    "frame": frame_idx
                                }
                                current_detections.append(det_info)
                                all_detections.append(det_info)

                    last_detections = current_detections

                # Annotate current frame with bounding boxes
                annotated_frame = detector_service.annotate_frame(frame, last_detections)
                writer.write(annotated_frame)
                frame_idx += 1

        finally:
            cap.release()
            writer.release()

        # Deduplicate / aggregate defect counts across sampled frames
        # Approximate unique defects by sampling density
        sample_factor = max(1, self.frame_step)
        est_potholes = max(1, pothole_instances // sample_factor) if pothole_instances > 0 else 0
        est_cracks = max(1, crack_instances // sample_factor) if crack_instances > 0 else 0
        est_surface = max(1, surface_instances // sample_factor) if surface_instances > 0 else 0
        total_unique_damages = est_potholes + est_cracks + est_surface

        # Overall priority score & recommendation
        priority_score, priority_label, recommendation = detector_service.calculate_priority(all_detections)

        # Average confidence across all frames
        valid_confs = [d["confidence"] for d in all_detections]
        avg_conf = round(sum(valid_confs) / len(valid_confs), 4) if valid_confs else 0.0

        # Highest severity detected
        severity_rank = {"Severe": 3, "Moderate": 2, "Minor": 1, "None": 0}
        highest_severity = "None"
        if all_detections:
            highest_severity = max(
                (d["severity"] for d in all_detections),
                key=lambda s: severity_rank.get(s, 0)
            )

        # Representative detections (top 20 by confidence)
        sorted_detections = sorted(all_detections, key=lambda d: d["confidence"], reverse=True)[:20]

        return {
            "damage_count": total_unique_damages,
            "pothole_count": est_potholes,
            "crack_count": est_cracks,
            "surface_damage_count": est_surface,
            "avg_confidence": avg_conf,
            "highest_severity": highest_severity,
            "priority_score": priority_score,
            "priority_label": priority_label,
            "recommendation": recommendation,
            "detections": sorted_detections,
            "output_video_url": f"/outputs/{out_name}",
            "output_video_path": str(out_path),
            "processed_frames": frame_idx
        }


# Global video processor instance
video_processor = VideoProcessor(frame_step=3)
