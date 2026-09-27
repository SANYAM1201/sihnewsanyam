"""Adaptive Beam Angle Correction (BAC) with Edge Preservation.

Maintains boundary gradient sharpness at high IoU thresholds (mAP@0.50:0.95)
by fusing column-wise gain normalization with an edge-preserving bilaterally weighted map.
"""

from __future__ import annotations

import cv2
import numpy as np


def adaptive_beam_angle_correction(
    image: np.ndarray,
    sigma: float = 6.0,
    edge_preservation: float = 0.8,
) -> np.ndarray:
    """Enhanced BAC with edge-aware smoothing.

    Args:
        image: 2D uint8 grayscale or 3D BGR sonar sonogram.
        sigma: Column-wise smoothing factor across range.
        edge_preservation: Weight for edge preservation (0.0 = full smooth, 1.0 = full edge keep).

    Returns:
        Gain-corrected uint8 image with sharp object boundaries.
    """
    is_3ch = image.ndim == 3
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if is_3ch else image.copy()

    # Detect high-frequency boundary gradients
    edges = cv2.Canny(gray, 40, 120)
    edge_mask = (cv2.GaussianBlur(edges.astype(np.float32), (5, 5), 0) / 255.0).clip(0.0, 1.0)

    # Column-wise gain profile
    mean_profile = np.mean(gray.astype(np.float32), axis=0, keepdims=True)
    # 1D Gaussian smoothing of across-range illumination falloff
    ksize = int(sigma * 4) | 1
    smooth_profile = cv2.GaussianBlur(mean_profile, (ksize, 1), sigma)
    smooth_profile = np.maximum(smooth_profile, 1.0)

    target_level = np.mean(smooth_profile)
    gain_curve = target_level / smooth_profile

    # Standard BAC application
    bac_applied = (gray.astype(np.float32) * gain_curve).clip(0, 255)

    # Edge-aware blending: keep high gradients crisp and unblurred
    blended = (1.0 - edge_preservation * edge_mask) * bac_applied + (edge_preservation * edge_mask) * gray.astype(np.float32)
    result = np.clip(blended, 0, 255).astype(np.uint8)

    if is_3ch:
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    return result


def dynamic_bac(image: np.ndarray, min_sigma: float = 2.0, max_sigma: float = 10.0) -> np.ndarray:
    """Automatically adjusts BAC smoothing sigma based on image gradient entropy."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    complexity = float(np.std(mag))

    norm_complexity = np.clip(complexity / 50.0, 0.0, 1.0)
    sigma = max_sigma - (max_sigma - min_sigma) * norm_complexity
    return adaptive_beam_angle_correction(image, sigma=sigma, edge_preservation=0.75)
