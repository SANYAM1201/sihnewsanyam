"""SADH (Shadow-derived Acoustic Dimension Height) Physics Module.

Implements hydrographic acoustic shadow geometry:
In side-scan sonar, elevated objects project an acoustic shadow on the seabed
whose length L relates to target height h_est, towfish altitude H_s, and
slant range R_s via:
    h_est = (L * H_s) / R_s
"""

from __future__ import annotations

import math
import numpy as np


def estimate_target_height(
    shadow_length_m: float,
    altitude_m: float,
    slant_range_m: float,
) -> float:
    """Calculate object height above seafloor from acoustic shadow length.

    Formula:
        h_est = (L * H_s) / R_s

    Args:
        shadow_length_m: Length of acoustic shadow along acoustic range axis (meters).
        altitude_m: Altitude of towfish / transducer above seabed (H_s, meters).
        slant_range_m: Slant range from transducer to target (R_s, meters).

    Returns:
        Estimated target physical height in meters (clamped >= 0).
    """
    if slant_range_m <= 1e-3 or altitude_m <= 1e-3 or shadow_length_m <= 0:
        return 0.0
    # Standard acoustic shadow height formula
    h_est = (shadow_length_m * altitude_m) / slant_range_m
    return round(float(max(0.0, h_est)), 3)


def compute_physics_confidence(
    class_label: str,
    detection_conf: float,
    estimated_height_m: float,
    has_shadow: bool,
) -> float:
    """Compute acoustic physics consistency score.

    Elevated structures (shipwrecks, cylinders, pipes) MUST cast an acoustic
    shadow behind them. Detections with zero shadow are penalized as potential
    seafloor sediment artifacts or false alarms.

    Args:
        class_label: Target classification label.
        detection_conf: Neural network raw confidence score [0.0, 1.0].
        estimated_height_m: Calculated target height in meters.
        has_shadow: True if an acoustic shadow region was confirmed.

    Returns:
        physics_confidence score [0.0, 1.0].
    """
    label_lower = class_label.lower()
    elevated_classes = {"shipwreck", "cylinder", "pipe", "container", "drum"}

    if any(c in label_lower for c in elevated_classes):
        if has_shadow and estimated_height_m >= 0.2:
            # Consistent 3D target relief
            score = 0.50 + 0.45 * detection_conf + min(0.04, estimated_height_m * 0.01)
        else:
            # Missing or near-zero shadow for an elevated class -> penalize
            score = max(0.20, detection_conf * 0.55)
    else:
        # Flexible or low-profile debris (e.g. ghost net flat on seabed)
        if has_shadow:
            score = 0.60 + 0.35 * detection_conf
        else:
            score = 0.40 + 0.45 * detection_conf

    return round(float(np.clip(score, 0.05, 0.99)), 3)


def extract_sadh_from_bbox(
    bbox_x: float,
    bbox_y: float,
    bbox_w: float,
    bbox_h: float,
    img_w: int,
    img_h: int,
    altitude_m: float = 15.0,
    range_res_m: float = 0.05,
    shadow_mask: np.ndarray | None = None,
) -> tuple[float, bool]:
    """Extract shadow length and presence from image coordinates and optional shadow mask.

    Args:
        bbox_x, bbox_y, bbox_w, bbox_h: Normalized bounding box coordinates [0, 1].
        img_w, img_h: Pixel dimensions of original sonogram.
        altitude_m: Transducer altitude in meters.
        range_res_m: Across-range pixel resolution in meters per pixel.
        shadow_mask: Optional binary uint8 mask of detected acoustic shadows.

    Returns:
        tuple (shadow_length_m, has_shadow).
    """
    px_x = int(bbox_x * img_w)
    px_y = int(bbox_y * img_h)
    px_w = max(2, int(bbox_w * img_w))
    px_h = max(2, int(bbox_h * img_h))

    is_starboard = (px_x + px_w // 2) >= (img_w // 2)

    shadow_px_len = 0.0
    has_shadow = False

    if shadow_mask is not None and shadow_mask.size > 0:
        h_mask, w_mask = shadow_mask.shape[:2]
        sx = int(px_x * w_mask / img_w)
        sy = int(px_y * h_mask / img_h)
        sw = max(2, int(px_w * w_mask / img_w))
        sh = max(2, int(px_h * h_mask / img_h))

        search_dist = int(sw * 3)
        if is_starboard:
            x_start = min(w_mask - 1, sx + sw)
            x_end = min(w_mask, x_start + search_dist)
            sub_mask = shadow_mask[sy : sy + sh, x_start:x_end]
        else:
            x_end = max(0, sx)
            x_start = max(0, x_end - search_dist)
            sub_mask = shadow_mask[sy : sy + sh, x_start:x_end]

        if sub_mask.size > 0:
            shadow_cols = np.any(sub_mask > 0, axis=0)
            shadow_count = int(np.sum(shadow_cols))
            if shadow_count >= 2:
                has_shadow = True
                shadow_px_len = float(shadow_count * (img_w / w_mask))

    if not has_shadow:
        aspect_ratio = px_w / max(1.0, px_h)
        if aspect_ratio > 1.2:
            has_shadow = True
            shadow_px_len = float(px_w * 0.8)

    shadow_length_m = shadow_px_len * range_res_m
    return shadow_length_m, has_shadow
