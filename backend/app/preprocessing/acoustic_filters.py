"""Hydro-Acoustic Radiometric & Speckle Filters.

Implements Enhanced Lee speckle filter and adaptive CLAHE contrast equalization
for Side-Scan Sonar (SSS) acoustic returns.
"""

from __future__ import annotations

import cv2
import numpy as np


class AcousticFilters:
    """Hydro-acoustic filtering pipeline for raw acoustic backscatter."""

    @staticmethod
    def enhanced_lee_filter(
        img: np.ndarray,
        win_size: int = 7,
        cu: float = 0.523,
        cmax: float = 1.73,
    ) -> np.ndarray:
        """Enhanced Lee filter for speckle reduction in synthetic aperture & sidescan sonar.

        Separates image into homogeneous, heterogeneous, and point-target regions.
        """
        if img.ndim == 3:
            channels = [AcousticFilters.enhanced_lee_filter(img[:, :, c], win_size, cu, cmax) for c in range(img.shape[2])]
            return np.stack(channels, axis=-1)

        src = img.astype(np.float32)
        k = win_size

        # Local mean and local variance
        mean = cv2.blur(src, (k, k))
        sq_mean = cv2.blur(src**2, (k, k))
        var = np.maximum(sq_mean - mean**2, 0.0)

        # Coefficient of variation
        ci = np.sqrt(var) / (mean + 1e-6)

        # Weighting function
        w = np.zeros_like(src)
        # Heterogeneous area
        mask_mid = (ci >= cu) & (ci <= cmax)
        b = np.exp(-2.0 * (ci[mask_mid] - cu) / (cmax - cu + 1e-6))
        w[mask_mid] = b

        # Homogeneous area
        mask_low = ci < cu
        w[mask_low] = 1.0

        # Point targets
        mask_high = ci > cmax
        w[mask_high] = 0.0

        filtered = mean * w + src * (1.0 - w)
        return np.clip(filtered, 0, 255).astype(np.uint8)

    @staticmethod
    def apply_clahe(img: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
        """Contrast Limited Adaptive Histogram Equalization across outer swath."""
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        if img.ndim == 2:
            return clahe.apply(img)
        elif img.ndim == 3:
            # Convert to LAB and equalize L channel
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return img


def apply_acoustic_filters(img: np.ndarray) -> np.ndarray:
    """Chains Enhanced Lee speckle attenuation and CLAHE contrast balance."""
    denoised = AcousticFilters.enhanced_lee_filter(img, win_size=5)
    enhanced = AcousticFilters.apply_clahe(denoised, clip_limit=2.0)
    return enhanced
