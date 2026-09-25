"""YOLOv8-specific preprocessing and tensor preparation.

Handles letterbox resizing with aspect-ratio preservation, symmetric padding,
dynamic channel conversion, float32 normalization [0.0, 1.0], and transposition
to (Channels, Height, Width) tensor format.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class YOLOPreprocessingConfig:
    """Configuration options for YOLOv8 preprocessing."""

    target_size: Tuple[int, int] = (640, 640)
    normalize: bool = True
    mean: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    std: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    swap_rgb: bool = False


@dataclass(frozen=True)
class LetterboxMeta:
    """Geometric transformation metadata for inverse bounding box remapping."""

    scale: float
    pad_left: int
    pad_top: int
    orig_shape: Tuple[int, int]  # (height, width)


class YOLOPreprocessor:
    """Preprocesses sonar image arrays into YOLOv8 model-ready tensors."""

    def __init__(self, config: YOLOPreprocessingConfig | None = None) -> None:
        self.config = config or YOLOPreprocessingConfig()

    def process(self, image: np.ndarray) -> np.ndarray:
        """Process a single image array into CHW float32 format.

        Args:
            image: uint8 NumPy array of shape (H, W) or (H, W, 3).

        Returns:
            float32 NumPy array of shape (3, target_h, target_w) in range [0, 1].
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("Input must be a numpy.ndarray")
        if image.size == 0:
            raise ValueError("Input image array is empty")

        chw, _ = self.process_with_meta(image)
        return chw

    def process_with_meta(self, image: np.ndarray) -> Tuple[np.ndarray, LetterboxMeta]:
        """Process image and return CHW array along with letterbox transformation metadata."""
        if not isinstance(image, np.ndarray):
            raise TypeError("Input must be a numpy.ndarray")
        if image.size == 0:
            raise ValueError("Input image array is empty")

        # Ensure 3-channel RGB image
        img_rgb = self._ensure_3channel(image)

        if self.config.swap_rgb:
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # Letterbox resize with padding to maintain aspect ratio
        padded, meta = self.letterbox_resize(img_rgb, self.config.target_size)

        # Convert to float32 and normalize to [0, 1]
        if self.config.normalize:
            padded = padded.astype(np.float32) / 255.0
            if self.config.mean != (0.0, 0.0, 0.0) or self.config.std != (1.0, 1.0, 1.0):
                mean = np.array(self.config.mean, dtype=np.float32)
                std = np.array(self.config.std, dtype=np.float32)
                padded = (padded - mean) / std
        else:
            padded = padded.astype(np.float32)

        # Transpose HWC to CHW
        chw = np.transpose(padded, (2, 0, 1))
        return np.ascontiguousarray(chw), meta

    def letterbox_resize(
        self, image: np.ndarray, target_size: Tuple[int, int]
    ) -> Tuple[np.ndarray, LetterboxMeta]:
        """Resize image while maintaining aspect ratio and symmetrically padding borders."""
        h, w = image.shape[:2]
        target_h, target_w = target_size

        scale = min(target_h / max(1, h), target_w / max(1, w))
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))

        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Symmetrical padding
        pad_w = target_w - new_w
        pad_h = target_h - new_h

        pad_left = pad_w // 2
        pad_right = pad_w - pad_left
        pad_top = pad_h // 2
        pad_bottom = pad_h - pad_top

        padded = cv2.copyMakeBorder(
            resized,
            pad_top,
            pad_bottom,
            pad_left,
            pad_right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )

        meta = LetterboxMeta(
            scale=scale,
            pad_left=pad_left,
            pad_top=pad_top,
            orig_shape=(h, w),
        )
        return padded, meta

    def _ensure_3channel(self, image: np.ndarray) -> np.ndarray:
        """Convert grayscale / 2D arrays to 3-channel RGB."""
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if len(image.shape) == 3:
            if image.shape[2] == 1:
                return cv2.cvtColor(image[..., 0], cv2.COLOR_GRAY2RGB)
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            if image.shape[2] == 3:
                return image
        raise ValueError(f"Unsupported image shape for preprocessing: {image.shape}")

    def batch_process(self, images: list[np.ndarray]) -> np.ndarray:
        """Process a list of images into a batched array (B, C, H, W)."""
        if not images:
            raise ValueError("images list cannot be empty")
        processed = [self.process(img) for img in images]
        return np.stack(processed, axis=0)
