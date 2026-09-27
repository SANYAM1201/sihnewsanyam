"""Unit tests for safe_image_loader service."""

import cv2
import numpy as np
import pytest

from app.services.safe_image_loader import safe_load_image


def test_safe_load_image_valid_png() -> None:
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    loaded = safe_load_image(buf.tobytes())
    assert loaded.shape == (100, 100, 3)


def test_safe_load_image_valid_jpg() -> None:
    img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    loaded = safe_load_image(buf.tobytes())
    assert loaded.shape == (64, 64, 3)


def test_safe_load_image_empty_bytes() -> None:
    with pytest.raises(ValueError, match="Empty image data"):
        safe_load_image(b"")

    # With fallback_to_blank=True
    blank = safe_load_image(b"", target_size=(200, 200), fallback_to_blank=True)
    assert blank.shape == (200, 200, 3)
    assert blank.dtype == np.uint8


def test_safe_load_image_corrupt_bytes() -> None:
    with pytest.raises(ValueError, match="Could not load image"):
        safe_load_image(b"\x00\x01\x02\x03\x04\x05")

    # With fallback_to_blank=True
    blank = safe_load_image(b"\x00\x01\x02\x03\x04\x05", fallback_to_blank=True)
    assert blank.shape == (512, 512, 3)
    assert blank.dtype == np.uint8


def test_safe_load_image_target_size() -> None:
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    loaded = safe_load_image(buf.tobytes(), target_size=(64, 64))
    assert loaded.shape == (64, 64, 3)


def test_safe_load_image_rgba() -> None:
    img_rgba = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img_rgba)
    assert ok
    loaded = safe_load_image(buf.tobytes())
    assert loaded.ndim in (2, 3)

