"""Generate synthetic acoustic shadow dataset for GAN training from clean sonar images."""

import os
from glob import glob
from pathlib import Path

import cv2
import numpy as np


def generate_synthetic_shadows(input_dir: str = "datasets/screenshots_dev", output_dir: str = "datasets/shadow_gan"):
    """Create synthetic shadow datasets by projecting geometric shadows onto clean sonograms."""
    train_in = Path(output_dir) / "train" / "input"
    train_target = Path(output_dir) / "train" / "target"
    train_in.mkdir(parents=True, exist_ok=True)
    train_target.mkdir(parents=True, exist_ok=True)

    images = glob(f"{input_dir}/**/*.png", recursive=True) + glob(f"{input_dir}/**/*.jpg", recursive=True)
    if not images:
        print(f"No source images found in {input_dir}, creating synthetic sonar texture base...")
        # Create baseline synthetic seafloor textures
        os.makedirs(input_dir, exist_ok=True)
        for i in range(10):
            texture = np.random.normal(120, 30, (512, 512)).clip(0, 255).astype(np.uint8)
            cv2.imwrite(f"{input_dir}/synth_sonar_{i:02d}.png", texture)
        images = glob(f"{input_dir}/**/*.png", recursive=True)

    print(f"Generating synthetic shadow pairs from {len(images)} images...")
    count = 0
    for img_path in images:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        h, w = img.shape[:2]

        # Generate realistic acoustic shadow: dark polygon expanding away from sonar track
        mask = np.zeros_like(img)
        # Random origin point
        ox = np.random.randint(w // 4, 3 * w // 4)
        oy = np.random.randint(h // 4, 3 * h // 4)
        # Shadow cone extending horizontally
        sw_len = np.random.randint(30, 120)
        sw_h = np.random.randint(15, 60)
        direction = 1 if ox > w // 2 else -1
        pts = np.array(
            [
                [ox, oy],
                [ox + direction * sw_len, max(0, oy - sw_h // 2)],
                [ox + direction * (sw_len + 20), oy + sw_h],
                [ox, oy + sw_h // 2],
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [pts], 255)

        # Apply acoustic shadow attenuation
        shadowed = img.copy()
        shadowed[mask == 255] = (shadowed[mask == 255] * 0.15).astype(np.uint8)

        base_name = f"shadow_{count:04d}_{Path(img_path).stem}.png"
        cv2.imwrite(str(train_in / base_name), shadowed)
        cv2.imwrite(str(train_target / base_name), img)
        count += 1

    print(f"Created {count} paired train sonograms in {output_dir}/train")


if __name__ == "__main__":
    generate_synthetic_shadows()
