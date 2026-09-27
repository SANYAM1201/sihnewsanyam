import numpy as np
import pytest

from app.services.augmentation import SonarAugmentor, augment_sonar_image


@pytest.fixture
def sample_sonar_image():
    return (np.random.rand(100, 100, 3) * 255).astype(np.uint8)


def test_add_speckle_noise(sample_sonar_image):
    noisy = SonarAugmentor.add_speckle_noise(sample_sonar_image, strength=0.1)
    assert noisy.shape == sample_sonar_image.shape
    assert noisy.dtype == np.uint8


def test_simulate_gain_falloff(sample_sonar_image):
    falloff_3ch = SonarAugmentor.simulate_gain_falloff(sample_sonar_image, factor=0.3)
    assert falloff_3ch.shape == sample_sonar_image.shape
    assert falloff_3ch.dtype == np.uint8

    gray = sample_sonar_image[:, :, 0]
    falloff_1ch = SonarAugmentor.simulate_gain_falloff(gray, factor=0.3)
    assert falloff_1ch.shape == gray.shape
    assert falloff_1ch.dtype == np.uint8


def test_random_shadow_attenuation(sample_sonar_image):
    attenuated = SonarAugmentor.random_shadow_attenuation(sample_sonar_image)
    assert attenuated.shape == sample_sonar_image.shape
    assert attenuated.dtype == np.uint8


def test_augment_sonar_image(sample_sonar_image):
    augmented = augment_sonar_image(sample_sonar_image)
    assert augmented.shape == sample_sonar_image.shape
    assert augmented.dtype == np.uint8
