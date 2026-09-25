"""Memory leak and resource cleanup tests for SSS preprocessing pipeline."""

from __future__ import annotations

import gc
import os
import numpy as np
import psutil
import pytest

from app.preprocessing.sonar_preprocessor import SonarPreprocessor


def run_memory_check() -> float:
    process = psutil.Process(os.getpid())
    preprocessor = SonarPreprocessor(
        apply_sss_processing=True,
        apply_bac=True,
        apply_stripe_filter=True,
        apply_sharpening=True,
        apply_shadow_inpainting=True,
    )

    # Warmup
    dummy = np.random.randint(40, 220, (640, 640, 3), dtype=np.uint8)
    for _ in range(5):
        _ = preprocessor.process_array(dummy)

    gc.collect()
    rss_before = process.memory_info().rss

    # Process 100 unique frames
    for i in range(100):
        frame = np.random.randint(30, 230, (512, 512, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 5
        _ = preprocessor.process_array(frame)

    gc.collect()
    rss_after = process.memory_info().rss
    growth_mb = (rss_after - rss_before) / (1024 * 1024)
    assert growth_mb < 50.0, f"Memory growth of {growth_mb:.2f} MB exceeds 50 MB threshold"
    return growth_mb


def test_preprocessing_no_memory_leak():
    """Verify that processing 100 consecutive images does not exhibit memory leakage."""
    run_memory_check()


if __name__ == "__main__":
    growth = run_memory_check()
    print(f"✅ No memory leak detected: {growth:.1f}MB growth (under 50MB threshold)")
