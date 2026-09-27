import os
import sys
import numpy as np
import pytest

from app.services.altitude_estimation import estimate_altitude_from_image


@pytest.fixture
def blank_image():
    return np.zeros((256, 512), dtype=np.uint8)


@pytest.fixture
def textured_image():
    rng = np.random.default_rng(42)
    return (rng.random((256, 512)) * 255).astype(np.uint8)


def test_returns_float(blank_image):
    result = estimate_altitude_from_image(blank_image, frequency_khz=400)
    assert isinstance(result, float)


def test_frequency_fallback_100(blank_image):
    result = estimate_altitude_from_image(blank_image, frequency_khz=100)
    assert result > 0


def test_frequency_fallback_900(blank_image):
    result = estimate_altitude_from_image(blank_image, frequency_khz=900)
    assert result > 0


def test_no_frequency_returns_value(blank_image):
    result = estimate_altitude_from_image(blank_image)
    assert result is not None and result > 0


def test_textured_image(textured_image):
    result = estimate_altitude_from_image(textured_image, frequency_khz=400)
    assert result > 0


def test_empty_and_none_image():
    assert estimate_altitude_from_image(None) == 15.0
    assert estimate_altitude_from_image(np.array([])) == 15.0
    assert estimate_altitude_from_image(np.zeros((0, 0), dtype=np.uint8)) == 15.0


def test_color_image_and_dark_nadir():
    # 3D color image with a prominent dark nadir band in center
    img = np.ones((100, 200, 3), dtype=np.uint8) * 200
    # Central 40 columns dark (< 50)
    img[:, 80:120, :] = 20

    alt = estimate_altitude_from_image(img, frequency_khz=400)
    assert isinstance(alt, float)
    assert alt > 0

