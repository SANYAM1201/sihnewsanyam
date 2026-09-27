"""Unit tests for Multi-Frequency Sonar Augmentations."""

import numpy as np

from app.preprocessing.augmentations import MultiFrequencySonarAugmentor


def test_speckle_noise() -> None:
    img = np.ones((100, 100), dtype=np.uint8) * 128
    augmentor = MultiFrequencySonarAugmentor(target_frequency_khz=455.0)
    noisy = augmentor.apply_speckle_noise(img)
    assert noisy.shape == img.shape
    assert noisy.dtype == np.uint8


def test_frequency_absorption() -> None:
    img = np.ones((100, 100), dtype=np.uint8) * 200
    augmentor = MultiFrequencySonarAugmentor(target_frequency_khz=900.0)
    decayed = augmentor.apply_frequency_absorption(img)
    assert decayed.shape == img.shape
    assert decayed.dtype == np.uint8
    # Absorption decay means right side (higher range index) is darker than left side
    assert float(np.mean(decayed[:, :10])) > float(np.mean(decayed[:, -10:]))


def test_full_augment() -> None:
    img = np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)
    augmentor = MultiFrequencySonarAugmentor(target_frequency_khz=100.0)
    aug = augmentor.augment(img)
    assert aug.shape == img.shape
    assert aug.dtype == np.uint8
