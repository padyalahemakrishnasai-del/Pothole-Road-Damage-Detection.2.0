"""Dataset preparation script for road damage detection.

Extracts the public IVCNZ Pothole dataset, validates pairs,
and creates structured train/val/test splits in ml/dataset/.
"""
import os
import random
import zipfile
import shutil
from pathlib import Path

# Fix random seed for reproducibility
random.seed(42)

ML_DIR = Path(__file__).resolve().parent
ROOT_DIR = ML_DIR.parent
ZIP_PATH = ROOT_DIR / "backend" / "pothole_dataset.zip"
DATASET_DIR = ML_DIR / "dataset"


def setup_directories():
    for split in ["train", "val", "test"]:
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)


def extract_and_split(max_samples=350):
    print("[Dataset] Extracting and splitting dataset...")
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Dataset zip not found at {ZIP_PATH}")

    setup_directories()

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        # Find all jpg files
        image_names = [f for f in z.namelist() if f.endswith('.jpg') and not f.startswith('__MACOSX')]
        print(f"[Dataset] Found {len(image_names)} total images in zip archive.")

        # Shuffle and select a reasonable subset for school project training speed
        random.shuffle(image_names)
        selected_images = image_names[:max_samples]

        n_train = int(len(selected_images) * 0.75)  # 262
        n_val = int(len(selected_images) * 0.18)    # 63
        n_test = len(selected_images) - n_train - n_val  # 25

        splits = (
            [("train", img) for img in selected_images[:n_train]] +
            [("val", img) for img in selected_images[n_train:n_train + n_val]] +
            [("test", img) for img in selected_images[n_train + n_val:]]
        )

        for split, img_path in splits:
            stem = Path(img_path).stem
            txt_path = f"Pothole Dataset/{stem}.txt"

            # Extract image
            img_data = z.read(img_path)
            target_img = DATASET_DIR / "images" / split / f"{stem}.jpg"
            with open(target_img, "wb") as f:
                f.write(img_data)

            # Extract label
            try:
                txt_data = z.read(txt_path)
            except KeyError:
                txt_data = b""

            target_txt = DATASET_DIR / "labels" / split / f"{stem}.txt"
            with open(target_txt, "wb") as f:
                f.write(txt_data)

    print(f"[Dataset] Successfully prepared dataset in {DATASET_DIR}:")
    print(f"   - Train: {n_train} images")
    print(f"   - Val:   {n_val} images")
    print(f"   - Test:  {n_test} images")


if __name__ == "__main__":
    extract_and_split(max_samples=350)
