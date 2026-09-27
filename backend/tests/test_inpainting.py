import numpy as np
import pytest

from app.services.inpainting import InpainterService


@pytest.fixture
def inpainter():
    return InpainterService()


@pytest.fixture
def sonar_image():
    rng = np.random.default_rng(7)
    return (rng.random((256, 256)) * 255).astype(np.uint8)


@pytest.fixture
def shadow_mask():
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[60:100, 60:100] = 255
    return mask


def test_inpaint_returns_same_shape(inpainter, sonar_image, shadow_mask):
    result = inpainter.inpaint(sonar_image, shadow_mask)
    assert result.shape == sonar_image.shape


def test_inpaint_returns_uint8(inpainter, sonar_image, shadow_mask):
    result = inpainter.inpaint(sonar_image, shadow_mask)
    assert result.dtype == np.uint8


def test_inpaint_no_crash_empty_mask(inpainter, sonar_image):
    empty_mask = np.zeros_like(sonar_image)
    result = inpainter.inpaint(sonar_image, empty_mask)
    assert result.shape == sonar_image.shape


def test_inpaint_no_crash_full_mask(inpainter, sonar_image):
    full_mask = np.ones_like(sonar_image) * 255
    result = inpainter.inpaint(sonar_image, full_mask)
    assert result.shape == sonar_image.shape


def test_inpaint_values_in_range(inpainter, sonar_image, shadow_mask):
    result = inpainter.inpaint(sonar_image, shadow_mask)
    assert result.min() >= 0 and result.max() <= 255


def test_inpaint_3_channel(inpainter, shadow_mask):
    img3 = np.zeros((256, 256, 3), dtype=np.uint8)
    result = inpainter.inpaint(img3, shadow_mask)
    assert result.shape == (256, 256, 3)


def test_inpaint_gan_mode(shadow_mask):
    inpainter = InpainterService()
    inpainter.use_gan = True
    img2 = np.zeros((64, 64), dtype=np.uint8)
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20:40, 20:40] = 255
    res2 = inpainter.inpaint(img2, mask)
    assert res2.shape == (64, 64)

    img3 = np.zeros((64, 64, 3), dtype=np.uint8)
    res3 = inpainter.inpaint(img3, mask)
    assert res3.shape == (64, 64, 3)

