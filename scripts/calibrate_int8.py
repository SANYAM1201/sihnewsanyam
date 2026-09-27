"""INT8 Calibration provider for TensorRT quantization on sonar imagery."""

import os
from glob import glob
from pathlib import Path

import cv2
import numpy as np


class SonarInt8Calibrator:
    """IInt8Calibrator implementation for INT8 PTQ (Post-Training Quantization)."""

    def __init__(self, calibration_dir: str = "datasets/screenshots_dev", cache_file: str = "models/calibration.cache", batch_size: int = 1):
        self.images = glob(f"{calibration_dir}/**/*.png", recursive=True) + glob(f"{calibration_dir}/**/*.jpg", recursive=True)
        self.batch_size = batch_size
        self.cache_file = cache_file
        self.current_idx = 0
        print(f"Loaded {len(self.images)} images for INT8 calibration.")

    def get_batch(self, names=None):
        if self.current_idx + self.batch_size > len(self.images):
            return None

        batch = []
        for i in range(self.batch_size):
            img_path = self.images[self.current_idx + i]
            img = cv2.imread(img_path)
            if img is None:
                continue
            img = cv2.resize(img, (640, 640))
            img = img.astype(np.float32) / 255.0
            # [H, W, C] -> [C, H, W]
            img = np.transpose(img, (2, 0, 1))
            batch.append(img)

        self.current_idx += self.batch_size
        return [np.ascontiguousarray(np.stack(batch))]

    def read_calibration_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                return f.read()
        return None

    def write_calibration_cache(self, cache):
        Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "wb") as f:
            f.write(cache)


if __name__ == "__main__":
    calibrator = SonarInt8Calibrator()
    print("SonarInt8Calibrator initialized. Ready for TensorRT INT8 quantization workflow.")
