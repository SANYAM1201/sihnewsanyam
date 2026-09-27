"""Sonar Sentry SIH-26057 Dataset Preparation and Augmentation Engine.

Standardizes heterogeneous marine sonar datasets (SCTD, Seabed, Marine Debris)
into standardized YOLOv8 format with acoustic metadata for SADH multi-task training.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sonar_dataset_prep")

CLASSES = [
    "ghost_net",
    "sunken_debris",
    "shipwreck",
    "pipeline",
    "seafloor_rock",
    "metal_drum",
]
CLASS_MAP = {name: idx for idx, name in enumerate(CLASSES)}


def apply_rayleigh_speckle(img: np.ndarray, sigma: float = 0.3) -> np.ndarray:
    """Apply multiplicative Rayleigh distributed speckle noise characteristic of side-scan sonar."""
    h, w = img.shape[:2]
    # Rayleigh noise: sqrt(x^2 + y^2) where x, y ~ N(0, sigma)
    n1 = np.random.normal(0, sigma, (h, w))
    n2 = np.random.normal(0, sigma, (h, w))
    noise = np.sqrt(n1**2 + n2**2)
    # Normalize to mean 1
    noise = noise / (np.mean(noise) + 1e-6)

    if len(img.shape) == 3:
        noise = np.expand_dims(noise, axis=-1)

    noisy = img.astype(np.float32) * noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def apply_towfish_heave_stripes(
    img: np.ndarray, amplitude: float = 35.0, period: int = 16
) -> np.ndarray:
    """Simulate towfish heave motion causing cross-track periodic intensity banding."""
    h, w = img.shape[:2]
    y = np.arange(h)
    stripe_pattern = amplitude * np.sin(2.0 * np.pi * y / period)

    if len(img.shape) == 3:
        stripe_pattern = stripe_pattern[:, np.newaxis, np.newaxis]
    else:
        stripe_pattern = stripe_pattern[:, np.newaxis]

    striped = img.astype(np.float32) + stripe_pattern
    return np.clip(striped, 0, 255).astype(np.uint8)


def apply_acoustic_shadow_jitter(
    img: np.ndarray, bbox: List[float], jitter_factor: float = 1.15
) -> np.ndarray:
    """Simulate variations in acoustic shadow length by modulating dark pixels downstream of target."""
    cx, cy, bw, bh = bbox
    h, w = img.shape[:2]
    # Estimate shadow region extending away from nadir (towards outer swath)
    x1 = int((cx - bw / 2.0) * w)
    x2 = int((cx + bw / 2.0 + bw * jitter_factor) * w)
    y1 = int((cy - bh / 2.0) * h)
    y2 = int((cy + bh / 2.0) * h)

    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)

    modified = img.copy()
    if x2 > x1 and y2 > y1:
        # Darken shadow region
        modified[y1:y2, x1:x2] = (modified[y1:y2, x1:x2].astype(np.float32) * 0.4).astype(np.uint8)
    return modified


def synthesize_sonar_sample(
    idx: int,
    output_img_dir: Path,
    output_lbl_dir: Path,
    output_meta_dir: Path,
    width: int = 640,
    height: int = 640,
) -> Dict[str, Any]:
    """Generate a high-fidelity synthetic side-scan sonar image with targets and metadata."""
    # 1. Seafloor reverberation background
    bg = np.random.normal(120, 25, (height, width)).astype(np.float32)
    bg = cv2.GaussianBlur(bg, (5, 5), 1.5)

    # 2. Add nadir blind zone (water column) in center
    nadir_half_w = int(width * 0.08)
    center_x = width // 2
    bg[:, center_x - nadir_half_w : center_x + nadir_half_w] *= 0.15

    # 3. Add targets
    num_targets = random.randint(1, 4)
    annotations = []
    meta_targets = []

    altitude_m = round(random.uniform(8.0, 18.0), 2)
    slant_range_max_m = 50.0

    for _ in range(num_targets):
        cls_idx = random.randint(0, len(CLASSES) - 1)
        cls_name = CLASSES[cls_idx]

        # Target bounding box (avoid nadir)
        on_port = random.choice([True, False])
        if on_port:
            tx = random.randint(20, center_x - nadir_half_w - 60)
        else:
            tx = random.randint(center_x + nadir_half_w + 20, width - 60)

        ty = random.randint(30, height - 60)
        tw = random.randint(25, 60)
        th = random.randint(20, 50)

        # Highlight highlight (acoustic reflection)
        bg[ty : ty + th, tx : tx + tw] += random.uniform(80, 130)

        # Acoustic shadow length by physics: L_s = (h * R) / H
        slant_range_m = (abs(tx - center_x) / (width / 2.0)) * slant_range_max_m
        sim_target_height_m = round(random.uniform(0.4, 2.5), 2)
        shadow_len_m = (sim_target_height_m * slant_range_m) / max(altitude_m, 1.0)
        shadow_len_px = int((shadow_len_m / slant_range_max_m) * (width / 2.0))
        shadow_len_px = max(10, min(shadow_len_px, 120))

        # Shadow direction (away from center nadir)
        if on_port:
            sx1 = max(0, tx - shadow_len_px)
            sx2 = tx
        else:
            sx1 = tx + tw
            sx2 = min(width, tx + tw + shadow_len_px)

        bg[ty : ty + th, sx1:sx2] *= 0.12

        # YOLO format: cls cx cy w h (normalized)
        cx = (tx + tw / 2.0) / width
        cy = (ty + th / 2.0) / height
        norm_w = tw / width
        norm_h = th / height
        annotations.append(f"{cls_idx} {cx:.6f} {cy:.6f} {norm_w:.6f} {norm_h:.6f}")

        meta_targets.append(
            {
                "class_id": cls_idx,
                "class_name": cls_name,
                "bbox_xywh": [round(cx, 4), round(cy, 4), round(norm_w, 4), round(norm_h, 4)],
                "height_m": sim_target_height_m,
                "shadow_len_px": shadow_len_px,
                "slant_range_m": round(slant_range_m, 2),
                "altitude_m": altitude_m,
                "is_geology": cls_name == "seafloor_rock",
            }
        )

    # 4. Apply sonar speckle noise
    sonar_img = np.clip(bg, 0, 255).astype(np.uint8)
    sonar_img = apply_rayleigh_speckle(sonar_img, sigma=0.25)

    # Convert to 3-channel (standard input for YOLOv8)
    sonar_bgr = cv2.cvtColor(sonar_img, cv2.COLOR_GRAY2BGR)

    # Save image
    img_name = f"sonar_sample_{idx:05d}.jpg"
    lbl_name = f"sonar_sample_{idx:05d}.txt"
    meta_name = f"sonar_sample_{idx:05d}.meta.json"

    cv2.imwrite(str(output_img_dir / img_name), sonar_bgr)

    # Save YOLO label
    with open(output_lbl_dir / lbl_name, "w", encoding="utf-8") as f:
        f.write("\n".join(annotations))

    # Save acoustic metadata
    sample_meta = {
        "image_file": img_name,
        "width": width,
        "height": height,
        "altitude_m": altitude_m,
        "targets": meta_targets,
    }
    with open(output_meta_dir / meta_name, "w", encoding="utf-8") as f:
        json.dump(sample_meta, f, indent=2)

    return sample_meta


def prepare_sih_dataset(
    output_root: Path,
    total_samples: int = 120,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
) -> Dict[str, int]:
    """Generate or prepare dataset partitions with full acoustic metadata."""
    logger.info("Initializing Sonar Sentry dataset preparation into: %s", output_root)

    splits = {
        "train": int(total_samples * train_ratio),
        "val": int(total_samples * val_ratio),
        "test": total_samples - int(total_samples * train_ratio) - int(total_samples * val_ratio),
    }

    counts = {}
    current_idx = 0

    for split_name, count in splits.items():
        img_dir = output_root / split_name / "images"
        lbl_dir = output_root / split_name / "labels"
        meta_dir = output_root / split_name / "metadata"

        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Generating %d samples for %s split...", count, split_name)
        for _ in range(count):
            synthesize_sonar_sample(
                idx=current_idx,
                output_img_dir=img_dir,
                output_lbl_dir=lbl_dir,
                output_meta_dir=meta_dir,
            )
            current_idx += 1
        counts[split_name] = count

    logger.info("Dataset preparation complete! Split summary: %s", counts)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Sonar Sentry Dataset")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--samples", type=int, default=100, help="Total sample count to synthesize")
    args = parser.parse_args()

    prepare_sih_dataset(output_root=Path(args.output), total_samples=args.samples)
