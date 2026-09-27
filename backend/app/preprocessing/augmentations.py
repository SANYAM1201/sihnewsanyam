"""Multi-Frequency Acoustic Sonar Augmentations.

Simulates acoustic physics variation across frequency bands (e.g. 100 kHz low-freq wide beam
vs 900 kHz high-resolution side-scan) for robust deep learning model training.
"""

from __future__ import annotations

import cv2
import numpy as np


class MultiFrequencySonarAugmentor:
    """Applies acoustic frequency domain transformations to sonar sonograms."""

    def __init__(
        self,
        target_frequency_khz: float = 455.0,
        speckle_intensity: float = 0.15,
        absorption_factor: float = 0.05,
    ) -> None:
        self.target_frequency_khz = target_frequency_khz
        self.speckle_intensity = speckle_intensity
        self.absorption_factor = absorption_factor

    def apply_speckle_noise(self, image: np.ndarray) -> np.ndarray:
        """Simulate frequency-dependent Rayleigh/Gamma multiplicative speckle noise."""
        h, w = image.shape[:2]
        # High frequency -> finer speckle; Low frequency -> coarse speckle
        grain_scale = max(1, int(900.0 / max(100.0, self.target_frequency_khz)))
        noise_raw = np.random.gamma(
            shape=1.0 / (self.speckle_intensity + 1e-6),
            scale=self.speckle_intensity,
            size=(max(1, h // grain_scale), max(1, w // grain_scale)),
        ).astype(np.float32)

        noise_resized = cv2.resize(noise_raw, (w, h), interpolation=cv2.INTER_LINEAR)
        if image.ndim == 3:
            noise_resized = noise_resized[..., np.newaxis]

        noisy = image.astype(np.float32) * noise_resized
        return np.clip(noisy, 0, 255).astype(np.uint8)

    def apply_frequency_absorption(self, image: np.ndarray) -> np.ndarray:
        """Simulate high-frequency acoustic attenuation falloff with slant range distance."""
        h, w = image.shape[:2]
        # Range decay curve across horizontal width (range axis)
        range_coords = np.linspace(0.0, 1.0, w, dtype=np.float32)
        freq_decay = np.exp(-self.absorption_factor * (self.target_frequency_khz / 100.0) * range_coords)

        if image.ndim == 3:
            decay_mask = freq_decay[np.newaxis, :, np.newaxis]
        else:
            decay_mask = freq_decay[np.newaxis, :]

        decayed = image.astype(np.float32) * decay_mask
        return np.clip(decayed, 0, 255).astype(np.uint8)

    def augment(self, image: np.ndarray) -> np.ndarray:
        """Applies complete multi-frequency sonar augmentation pipeline."""
        img_noisy = self.apply_speckle_noise(image)
        return self.apply_frequency_absorption(img_noisy)
