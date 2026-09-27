"""Slant-Range Correction (SRC) Service with PNG Fallback Estimation."""

from __future__ import annotations

import numpy as np

from app.preprocessing.slant_range import slant_range_correct


def apply_src(
    image: np.ndarray,
    altitude: float | None = None,
    frequency_khz: float | None = None,
    max_range: float = 50.0,
    bilateral: bool = False,
) -> np.ndarray:
    """Apply Slant-Range Correction to a sonar image.

    If altitude is not explicitly provided (e.g. standard PNG without metadata),
    estimates towfish altitude based on bottom-line arrival or acoustic frequency heuristics.
    """
    if image is None or image.size == 0:
        return image

    if altitude is None or altitude <= 0:
        # Fallback estimation for plain PNG images with no embedded metadata
        if frequency_khz and frequency_khz > 500:
            estimated_alt = 15.0
        else:
            estimated_alt = 10.0
    else:
        estimated_alt = altitude

    return slant_range_correct(
        ping=image,
        altitude=estimated_alt,
        max_range=max_range,
        bilateral=bilateral,
    )
