"""Unit tests for Digital Signal Processing (DSP) routines."""

import numpy as np

from app.services.dsp import (
    adaptive_beam_angle_correction,
    bilateral_filter,
    dynamic_bac,
    slant_range_correction,
    tvg_correction,
)


def test_tvg_correction() -> None:
    signal = np.ones((10, 100), dtype=np.uint8) * 100
    corrected = tvg_correction(signal)
    assert corrected.shape == signal.shape
    assert corrected.dtype == np.uint8


def test_bilateral_filter() -> None:
    img = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
    filtered = bilateral_filter(img)
    assert filtered.shape == img.shape
    assert filtered.dtype == np.uint8


def test_adaptive_bac() -> None:
    img = np.random.randint(50, 200, (64, 64), dtype=np.uint8)
    bac_out = adaptive_beam_angle_correction(img)
    assert bac_out.shape == img.shape
    assert bac_out.dtype == np.uint8


def test_dynamic_bac() -> None:
    img = np.random.randint(50, 200, (64, 64), dtype=np.uint8)
    dyn_out = dynamic_bac(img)
    assert dyn_out.shape == img.shape
    assert dyn_out.dtype == np.uint8
