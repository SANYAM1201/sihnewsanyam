"""Unit tests for Slant Range Correction PNG fallback service."""

import numpy as np

from app.services.slant_range_correction import apply_src


def test_apply_src_explicit_altitude() -> None:
    img = (np.random.rand(256, 512) * 255).astype(np.uint8)
    out = apply_src(img, altitude=20.0)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


def test_apply_src_frequency_fallback() -> None:
    img = (np.random.rand(256, 512) * 255).astype(np.uint8)
    out = apply_src(img, frequency_khz=600.0)
    assert out.shape == img.shape


def test_apply_src_unknown_metadata() -> None:
    img = (np.random.rand(256, 512) * 255).astype(np.uint8)
    out = apply_src(img)
    assert out.shape == img.shape
