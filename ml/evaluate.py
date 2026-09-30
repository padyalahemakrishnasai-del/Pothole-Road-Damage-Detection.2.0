"""Evaluation script for Road Damage Detection models.

Calculates validation mAP50, mAP50-95, precision, and recall metrics.
"""
import os
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate YOLO Road Damage Model")
    parser.add_argument(
        "--weights",
        type=str,
        default=str(Path(__file__).parent / "weights" / "best.pt"),
        help="Path to trained model weights"
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(Path(__file__).parent / "configs" / "road_damage.yaml"),
        help="Path to dataset yaml"
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 60)
    print("📈 Road Damage Detection — Model Evaluation")
    print("=" * 60)

    if not os.path.exists(args.weights):
        print(f"⚠️  Weights file '{args.weights}' not found.")
        print("Note: To evaluate, train the model first or place weights at ml/weights/best.pt.")
        sys.exit(1)

    if not os.path.exists(args.data):
        print(f"❌ Error: Dataset config not found at '{args.data}'")
        sys.exit(1)

    print(f"📦 Loading weights: {args.weights}")
    model = YOLO(args.weights)

    print("⏳ Running validation...")
    metrics = model.val(
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(Path(__file__).parent / "runs" / "val"),
        name="road_damage_eval"
    )

    print("-" * 60)
    print("🏆 Overall Metrics:")
    print(f"   mAP50:     {metrics.box.map50:.4f}")
    print(f"   mAP50-95:  {metrics.box.map:.4f}")
    print(f"   Precision: {metrics.box.mp:.4f}")
    print(f"   Recall:    {metrics.box.mr:.4f}")
    print("-" * 60)


if __name__ == "__main__":
    main()
