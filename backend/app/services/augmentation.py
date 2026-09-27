"""Sonar-specific data augmentation pipeline for training robust multi-frequency detectors."""

from __future__ import annotations

import cv2
import numpy as np


class SonarAugmentor:
    """Acoustic image augmentation simulating variable sea-state, grazing angles, and gain."""

    @staticmethod
    def add_speckle_noise(image: np.ndarray, strength: float = 0.15) -> np.ndarray:
        """Simulates Rayleigh-distributed acoustic reverberation speckle noise."""
        noise = np.random.rayleigh(scale=strength, size=image.shape)
        noisy = image.astype(np.float32) * (1.0 + noise)
        return np.clip(noisy, 0, 255).astype(np.uint8)

    @staticmethod
    def simulate_gain_falloff(image: np.ndarray, factor: float = 0.4) -> np.ndarray:
        """Simulates uneven time-varied gain (TVG) across acoustic sweep."""
        h, w = image.shape[:2]
        ramp = np.linspace(1.0 - factor, 1.0 + factor, w, dtype=np.float32)
        if image.ndim == 3:
            ramp = ramp[np.newaxis, :, np.newaxis]
        else:
            ramp = ramp[np.newaxis, :]
        return np.clip(image.astype(np.float32) * ramp, 0, 255).astype(np.uint8)

    @staticmethod
    def random_shadow_attenuation(image: np.ndarray) -> np.ndarray:
        """Simulates acoustic grazing shadow dark patch."""
        h, w = image.shape[:2]
        x1 = np.random.randint(0, w // 2)
        y1 = np.random.randint(0, h // 2)
        w_box = np.random.randint(20, w // 3)
        h_box = np.random.randint(10, h // 3)

        out = image.copy()
        out[y1 : y1 + h_box, x1 : x1 + w_box] = (out[y1 : y1 + h_box, x1 : x1 + w_box] * 0.2).astype(np.uint8)
        return out


def augment_sonar_image(image: np.ndarray) -> np.ndarray:
    """Applies a random suite of sonar acoustic transformations."""
    aug = SonarAugmentor()
    res = image.copy()
    if np.random.rand() > 0.5:
        res = cv2.flip(res, 1)  # Port <-> Starboard flip
    if np.random.rand() > 0.4:
        res = aug.add_speckle_noise(res, strength=0.1)
    if np.random.rand() > 0.5:
        res = aug.simulate_gain_falloff(res, factor=0.25)
    return res
