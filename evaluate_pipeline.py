"""Evaluation script comparing YOLOv8 detection results with and without SSS preprocessing."""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
from PIL import Image

from app.preprocessing.identity_preprocessor import IdentityPreprocessor
from app.preprocessing.sonar_preprocessor import SonarPreprocessor
from app.services.sonar_model_service import SonarModelService


def draw_bounding_boxes(
    image: np.ndarray, detections, box_color=(0, 255, 0), label_color=(255, 255, 255)
) -> np.ndarray:
    annotated = image.copy()
    for det in detections:
        if det.bbox is None:
            continue
        x1 = int(round(det.bbox.x))
        y1 = int(round(det.bbox.y))
        x2 = int(round(det.bbox.x + det.bbox.width))
        y2 = int(round(det.bbox.y + det.bbox.height))

        # Clamp to bounds
        h, w = annotated.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)
        caption = f"{det.class_label} {det.confidence:.2f}"

        # Draw label badge
        (tw, th), baseline = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            annotated,
            (x1, max(0, y1 - th - baseline - 4)),
            (x1 + tw + 6, max(th + baseline + 4, y1)),
            box_color,
            -1,
        )
        cv2.putText(
            annotated,
            caption,
            (x1 + 3, max(th, y1 - baseline - 2)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
    return annotated


def evaluate():
    root = Path(__file__).resolve().parent
    demo_dir = root / "demo_data"
    images = sorted(list(demo_dir.glob("*.png")))
    if not images:
        print("No demo images found!")
        return

    # Initialize model service
    model_path = root / "model" / "best.pt"
    if not model_path.exists():
        model_path = backend_dir / "best.pt"
    print(f"Loading YOLOv8 weights from: {model_path}")
    model = SonarModelService(model_path=str(model_path))
    model.load()

    identity_prep = IdentityPreprocessor()
    sonar_prep = SonarPreprocessor(
        apply_sss_processing=True,
        apply_bac=True,
        apply_stripe_filter=True,
        apply_sharpening=True,
        apply_shadow_inpainting=True,
        shadow_threshold=0.15,
        shadow_inpaint_method="telea",
    )

    print("\n" + "=" * 65)
    print("  EVALUATING MODEL PREDICTIONS ON DEMO SIDE-SCAN SONAR IMAGES")
    print("=" * 65)

    sample_count = min(6, len(images))
    total_raw_dets = 0
    total_enhanced_dets = 0
    conf_raw_sum = 0.0
    conf_enh_sum = 0.0

    eval_pairs = []

    for i, img_path in enumerate(images[:sample_count]):
        raw_bytes = img_path.read_bytes()

        # Run with Identity (Raw)
        raw_input = identity_prep.process(raw_bytes)
        res_raw = model.predict(raw_input)

        # Run with Enhanced SSS Preprocessor
        enh_input = sonar_prep.process(raw_bytes)
        res_enh = model.predict(enh_input)

        total_raw_dets += len(res_raw.detections)
        total_enhanced_dets += len(res_enh.detections)
        if res_raw.detections:
            conf_raw_sum += sum(d.confidence for d in res_raw.detections)
        if res_enh.detections:
            conf_enh_sum += sum(d.confidence for d in res_enh.detections)

        print(f"\n[{i+1}/{sample_count}] Image: {img_path.name}")
        print(f"  • RAW / Identity Pipeline  : {len(res_raw.detections)} detections -> "
              f"{[f'{d.class_label} ({d.confidence:.2f})' for d in res_raw.detections]}")
        print(f"  • ENHANCED SSS Pipeline    : {len(res_enh.detections)} detections -> "
              f"{[f'{d.class_label} ({d.confidence:.2f})' for d in res_enh.detections]}")

        eval_pairs.append((img_path, res_raw, res_enh))

    avg_conf_raw = conf_raw_sum / max(1, total_raw_dets)
    avg_conf_enh = conf_enh_sum / max(1, total_enhanced_dets)

    print("\n" + "=" * 65)
    print("  SUMMARY EVALUATION METRICS")
    print("=" * 65)
    print(f"  Total Detections (Raw)      : {total_raw_dets}")
    print(f"  Total Detections (Enhanced) : {total_enhanced_dets}")
    print(f"  Mean Confidence (Raw)       : {avg_conf_raw:.4f}")
    print(f"  Mean Confidence (Enhanced)  : {avg_conf_enh:.4f}")
    print("=" * 65)

    # Save visual comparison for the first sample image
    first_path, first_raw_res, first_enh_res = eval_pairs[0]
    orig_img = np.array(Image.open(first_path).convert("RGB"))

    vis_raw = draw_bounding_boxes(orig_img, first_raw_res.detections, box_color=(230, 50, 50))
    vis_enh = draw_bounding_boxes(orig_img, first_enh_res.detections, box_color=(40, 220, 40))

    # Resize to side-by-side for comparison visualization
    target_w = 800
    target_h = int(orig_img.shape[0] * (target_w / orig_img.shape[1]))
    vis_raw_resized = cv2.resize(vis_raw, (target_w, target_h))
    vis_enh_resized = cv2.resize(vis_enh, (target_w, target_h))

    # Add header bars
    header_raw = np.zeros((40, target_w, 3), dtype=np.uint8)
    header_enh = np.zeros((40, target_w, 3), dtype=np.uint8)
    cv2.putText(header_raw, f"WITHOUT Preprocessing ({len(first_raw_res.detections)} objects)", (15, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(header_enh, f"WITH Enhanced SSS Preprocessing ({len(first_enh_res.detections)} objects)", (15, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    col1 = np.vstack([header_raw, vis_raw_resized])
    col2 = np.vstack([header_enh, vis_enh_resized])
    comparison = np.hstack([col1, col2])

    out_path = root / "detection_comparison.png"
    Image.fromarray(comparison).save(out_path)
    print(f"\nVisual comparison saved to: {out_path.name}")


if __name__ == "__main__":
    evaluate()
