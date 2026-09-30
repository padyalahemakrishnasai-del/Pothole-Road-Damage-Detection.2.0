"""Training script for Road Damage Detection using Ultralytics YOLO.

Usage:
    python train.py [--config configs/training_config.yaml] [--data configs/road_damage.yaml]
"""
import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLO on Road Damage Dataset")
    parser.add_argument(
        "--data",
        type=str,
        default=str(Path(__file__).parent / "configs" / "road_damage.yaml"),
        help="Path to dataset yaml"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
        help="Path to training config yaml"
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs")
    parser.add_argument("--batch", type=int, default=None, help="Override batch size")
    parser.add_argument("--imgsz", type=int, default=None, help="Override image size")
    parser.add_argument("--device", type=str, default=None, help="Device to use ('0', 'cpu')")
    return parser.parse_args()


def load_yaml(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def main():
    args = parse_args()
    print("=" * 60)
    print("🚀 Road Damage Detection — YOLO Training Pipeline")
    print("=" * 60)

    cfg = load_yaml(args.config) if os.path.exists(args.config) else {}

    model_name = cfg.get("model", "yolov8n.pt")
    epochs = args.epochs or cfg.get("epochs", 50)
    batch = args.batch or cfg.get("batch_size", 16)
    imgsz = args.imgsz or cfg.get("image_size", 640)
    device = args.device or cfg.get("device", "")

    print(f"📦 Base Model: {model_name}")
    print(f"📊 Dataset Config: {args.data}")
    print(f"⚙️  Epochs: {epochs} | Batch: {batch} | ImgSz: {imgsz}")
    print(f"💻 Device: {device or 'auto'}")
    print("-" * 60)

    if not os.path.exists(args.data):
        print(f"❌ Error: Dataset config not found at '{args.data}'")
        sys.exit(1)

    # Initialize YOLO model
    model = YOLO(model_name)

    # Train
    print("⏳ Starting model training...")
    results = model.train(
        data=args.data,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        patience=cfg.get("patience", 10),
        lr0=cfg.get("lr0", 0.01),
        lrf=cfg.get("lrf", 0.01),
        augment=cfg.get("augment", True),
        project=str(Path(__file__).parent / "runs" / "train"),
        name="road_damage",
        device=device if device else None,
        save=True,
    )

    # Copy best weights to ml/weights/best.pt
    save_dir = Path(results.save_dir) if hasattr(results, "save_dir") else None
    if save_dir:
        best_pt = save_dir / "weights" / "best.pt"
        if best_pt.exists():
            target_dir = Path(__file__).parent / "weights"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / "best.pt"
            shutil.copy(best_pt, target_path)
            print(f"✅ Successfully exported best model weights to: {target_path}")

    print("🎉 Training finished.")


if __name__ == "__main__":
    main()
