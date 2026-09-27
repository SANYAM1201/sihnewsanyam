"""Digital Signal Processing (DSP) Module for Hydrographic Sonar Data."""

from __future__ import annotations

import cv2
import numpy as np

from app.preprocessing.adaptive_bac import adaptive_beam_angle_correction, dynamic_bac
from app.preprocessing.slant_range import slant_range_correct, slant_range_to_ground_range, ground_range_to_slant_range, SlantRangeCorrector

slant_range_correction = slant_range_correct


def tvg_correction(
    signal: np.ndarray,
    alpha_db_per_m: float = 0.1,
    sound_speed: float = 1500.0,
    sample_rate_hz: float = 100000.0,
) -> np.ndarray:
    """Time-Variable Gain (TVG) correction for acoustic attenuation loss (20 log R + 2 alpha R)."""
    if signal.size == 0:
        return signal

    num_samples = signal.shape[-1]
    time_vec = np.arange(1, num_samples + 1, dtype=np.float32) / sample_rate_hz
    range_m = 0.5 * sound_speed * time_vec

    # TVG gain curve in dB: 20 * log10(R) + 2 * alpha * R
    r_safe = np.maximum(range_m, 0.1)
    gain_db = 20.0 * np.log10(r_safe) + 2.0 * alpha_db_per_m * r_safe
    gain_linear = np.power(10.0, gain_db / 20.0)

    # Normalize gain curve to prevent saturation
    gain_linear = gain_linear / np.max(gain_linear)

    corrected = signal.astype(np.float32) * gain_linear
    return np.clip(corrected, 0.0, 255.0).astype(np.uint8)


def bilateral_filter(
    image: np.ndarray,
    d: int = 9,
    sigma_color: float = 75.0,
    sigma_space: float = 75.0,
) -> np.ndarray:
    """Edge-preserving bilateral filtering to reduce speckle noise while maintaining boundary gradients."""
    return cv2.bilateralFilter(image, d, sigma_color, sigma_space)


__all__ = [
    "adaptive_beam_angle_correction",
    "dynamic_bac",
    "slant_range_correct",
    "slant_range_correction",
    "slant_range_to_ground_range",
    "ground_range_to_slant_range",
    "SlantRangeCorrector",
    "tvg_correction",
    "bilateral_filter",
]
