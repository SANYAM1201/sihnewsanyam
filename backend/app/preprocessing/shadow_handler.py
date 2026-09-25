"""Acoustic shadow detection and inpainting for side-scan sonar images.

Acoustic shadows occur when elevated seafloor features or debris obstruct sound
waves, leaving regions of near-zero backscatter behind them. Inpainting these
regions prevents missed detections and reduces false negatives.
"""

from __future__ import annotations

import logging
from typing import Literal

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ShadowDetector:
    """Identifies acoustic shadow regions in side-scan sonar imagery."""

    def __init__(self, threshold: float = 0.15, min_shadow_size: int = 100) -> None:
        """Initialize shadow detector.

        Args:
            threshold: Intensity cutoff (0.0 to 1.0) below which pixels are
                       considered candidate acoustic shadows.
            min_shadow_size: Minimum pixel area for a shadow component to be
                             retained (filters out high-frequency acoustic speckle).
        """
        self.threshold = float(threshold)
        self.min_shadow_size = int(min_shadow_size)

    def detect(self, image: np.ndarray) -> np.ndarray:
        """Detect acoustic shadows and return a binary mask.

        Args:
            image: uint8 NumPy array of shape (H, W) or (H, W, 3).

        Returns:
            Binary uint8 mask of shape (H, W) with 255 for shadow, 0 otherwise.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("Input image must be a numpy.ndarray")
        if image.size == 0:
            raise ValueError("Input image array is empty")

        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif len(image.shape) == 2:
            gray = image
        else:
            gray = image[..., 0]

        h, w = gray.shape[:2]
        gray_norm = gray.astype(np.float32) / 255.0

        # Pixels with acoustic return below threshold indicate acoustic shadow
        thresh_val = float(np.clip(self.threshold, 0.01, 0.99))
        _, raw_mask = cv2.threshold(
            gray_norm, thresh_val, 255.0, cv2.THRESH_BINARY_INV
        )
        shadow_mask = raw_mask.astype(np.uint8)

        # Morphological opening removes salt-and-pepper speckle noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        shadow_mask = cv2.morphologyEx(
            shadow_mask, cv2.MORPH_OPEN, kernel, iterations=2
        )

        # Filter out tiny components below min_shadow_size
        if self.min_shadow_size > 0 and np.any(shadow_mask > 0):
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                shadow_mask, connectivity=8
            )
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] < self.min_shadow_size:
                    shadow_mask[labels == i] = 0

        return shadow_mask


class ShadowInpainter:
    """Inpaints acoustic shadow regions using OpenCV Navier-Stokes, Fast Marching (Telea), or PyTorch GAN."""

    def __init__(
        self,
        method: Literal["telea", "ns", "gan"] = "telea",
        inpaint_radius: int = 1,
        min_inpaint_pixels: int = 200,
        gan_model_path: str = "",
    ) -> None:
        method_lower = method.lower()
        if method_lower not in ("telea", "ns", "gan"):
            raise ValueError(f"Inpainting method must be 'telea', 'ns', or 'gan', got {method!r}")
        self.method = method_lower
        self.inpaint_radius = max(1, int(inpaint_radius))
        self.min_inpaint_pixels = max(0, int(min_inpaint_pixels))
        self.gan_model_path = gan_model_path
        self._gan_inpainter = None

        if self.method == "gan":
            try:
                from app.ml.gan_modules import GANShadowInpainter

                self._gan_inpainter = GANShadowInpainter(
                    weights_path=gan_model_path if gan_model_path else None,
                    fallback_method="telea",
                )
            except Exception as e:
                logger.warning(f"Could not initialize GAN inpainter: {e}. Falling back to OpenCV.")

    def inpaint(self, image: np.ndarray, shadow_mask: np.ndarray) -> np.ndarray:
        """Fill acoustic shadow pixels with surrounding seabed texture.

        Args:
            image: uint8 NumPy array of shape (H, W) or (H, W, 3).
            shadow_mask: uint8 NumPy array of shape (H, W) with 255 in shadow pixels.

        Returns:
            Inpainted uint8 NumPy array matching input image shape.
        """
        if not isinstance(image, np.ndarray) or not isinstance(shadow_mask, np.ndarray):
            raise TypeError("Image and shadow_mask must be numpy arrays")

        mask_2d = shadow_mask if len(shadow_mask.shape) == 2 else shadow_mask[..., 0]
        mask_2d = mask_2d.astype(np.uint8)

        nonzero_count = np.count_nonzero(mask_2d)
        if nonzero_count == 0 or nonzero_count < self.min_inpaint_pixels:
            # No significant shadows to inpaint, return original copy
            return image.copy()

        if self.method == "gan" and self._gan_inpainter is not None:
            return self._gan_inpainter.inpaint(image, mask_2d)

        flag = cv2.INPAINT_TELEA if self.method == "telea" else cv2.INPAINT_NS
        h, w = image.shape[:2]

        try:
            # Downsample large imagery (>960px) for ~5x inpainting speedup
            downsample = (h > 960 or w > 960)
            if downsample:
                target_w, target_h = max(64, w // 2), max(64, h // 2)
                small_img = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_AREA)
                small_mask = cv2.resize(mask_2d, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
                small_inpainted = cv2.inpaint(
                    small_img,
                    small_mask,
                    inpaintRadius=self.inpaint_radius,
                    flags=flag,
                )
                full_inpainted = cv2.resize(small_inpainted, (w, h), interpolation=cv2.INTER_LINEAR)
                if len(image.shape) == 3:
                    return np.where(mask_2d[..., None] > 0, full_inpainted, image)
                return np.where(mask_2d > 0, full_inpainted, image)

            inpainted = cv2.inpaint(
                image,
                mask_2d,
                inpaintRadius=self.inpaint_radius,
                flags=flag,
            )
            return inpainted
        except Exception as e:
            logger.warning(f"Shadow inpainting failed: {e}. Returning original image.")
            return image.copy()
