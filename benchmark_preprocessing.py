"""Benchmark script to measure latency and throughput of the SSS preprocessing pipeline."""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

# Add backend directory to sys.path so app imports work
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import numpy as np
from PIL import Image

from app.preprocessing.identity_preprocessor import IdentityPreprocessor
from app.preprocessing.shadow_handler import ShadowDetector, ShadowInpainter
from app.preprocessing.sidescan_processor import SidescanProcessor
from app.preprocessing.sonar_preprocessor import SonarPreprocessor
from app.preprocessing.yolo_preprocessor import YOLOPreprocessingConfig, YOLOPreprocessor


def run_benchmark():
    root = Path(__file__).resolve().parent
    demo_dir = root / "demo_data"
    images = sorted(list(demo_dir.glob("*.png")))
    if not images:
        print("No demo images found in demo_data/")
        return

    test_images = images[:10]  # Benchmark first 10 images
    print(f"===========================================================")
    print(f"  SONAR SENTRY PREPROCESSING BENCHMARK (N={len(test_images)} images)")
    print(f"===========================================================")

    raw_bytes_list = [p.read_bytes() for p in test_images]

    # Preprocessors
    identity = IdentityPreprocessor()
    enhanced = SonarPreprocessor(
        apply_sss_processing=True,
        apply_bac=True,
        apply_stripe_filter=True,
        apply_sharpening=True,
        apply_shadow_inpainting=True,
        shadow_threshold=0.15,
        shadow_inpaint_method="telea",
        yolo_config=YOLOPreprocessingConfig(target_size=(640, 640)),
    )

    # Measure Identity
    t0 = time.perf_counter()
    for b in raw_bytes_list:
        identity.process(b)
    t_identity = (time.perf_counter() - t0) / len(test_images)

    # Measure Enhanced End-to-End
    t0 = time.perf_counter()
    for b in raw_bytes_list:
        enhanced.process(b)
    t_enhanced = (time.perf_counter() - t0) / len(test_images)

    # Breakdown of individual stages on first image
    first_bytes = raw_bytes_list[0]
    img = Image.open(io.BytesIO(first_bytes)).convert("RGB")
    arr = np.array(img)

    bac_proc = SidescanProcessor(apply_bac=True, apply_stripe_filter=False, apply_sharpening=False)
    stripe_proc = SidescanProcessor(apply_bac=False, apply_stripe_filter=True, apply_sharpening=False)
    sharp_proc = SidescanProcessor(apply_bac=False, apply_stripe_filter=False, apply_sharpening=True)
    detector = ShadowDetector(threshold=0.15)
    inpainter = ShadowInpainter(method="telea")
    yolo_prep = YOLOPreprocessor(YOLOPreprocessingConfig(target_size=(640, 640)))

    # Warmup
    _ = bac_proc.process(arr)

    # Timings
    iters = 10
    t0 = time.perf_counter()
    for _ in range(iters):
        _ = bac_proc.process(arr)
    t_bac = (time.perf_counter() - t0) / iters

    t0 = time.perf_counter()
    for _ in range(iters):
        _ = stripe_proc.process(arr)
    t_stripe = (time.perf_counter() - t0) / iters

    t0 = time.perf_counter()
    for _ in range(iters):
        _ = sharp_proc.process(arr)
    t_sharp = (time.perf_counter() - t0) / iters

    mask = detector.detect(arr)
    t0 = time.perf_counter()
    for _ in range(iters):
        _ = detector.detect(arr)
    t_detect = (time.perf_counter() - t0) / iters

    t0 = time.perf_counter()
    for _ in range(iters):
        _ = inpainter.inpaint(arr, mask)
    t_inpaint = (time.perf_counter() - t0) / iters

    t0 = time.perf_counter()
    for _ in range(iters):
        _ = yolo_prep.process(arr)
    t_yolo = (time.perf_counter() - t0) / iters

    print(f"\n1. Overall Pipeline Latency Comparison:")
    print(f"   - Identity Preprocessor (no-op) : {t_identity*1000:7.2f} ms / image (FPS: {1.0/t_identity:6.1f})")
    print(f"   - SonarPreprocessor (Full SSS)  : {t_enhanced*1000:7.2f} ms / image (FPS: {1.0/t_enhanced:6.1f})")

    print(f"\n2. Detailed Stage Breakdown (Image dimensions: {arr.shape[1]}x{arr.shape[0]}):")
    print(f"   - Beam Angle Correction (BAC)   : {t_bac*1000:7.2f} ms")
    print(f"   - 2D-FFT Stripe Noise Filter    : {t_stripe*1000:7.2f} ms")
    print(f"   - Homomorphic Edge Sharpening   : {t_sharp*1000:7.2f} ms")
    print(f"   - Acoustic Shadow Detection     : {t_detect*1000:7.2f} ms")
    print(f"   - Shadow Inpainting (Telea)     : {t_inpaint*1000:7.2f} ms")
    print(f"   - YOLOv8 Letterbox + Normalize  : {t_yolo*1000:7.2f} ms")
    print(f"===========================================================\n")


if __name__ == "__main__":
    run_benchmark()
