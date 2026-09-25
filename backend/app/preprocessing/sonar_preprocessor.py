"""Main Side-Scan Sonar preprocessing orchestrator.

Coordinates SSS-specific radiometric corrections (BAC, stripe removal, sharpening),
acoustic shadow detection and inpainting, and YOLOv8 letterbox tensor preparation.
Includes automatic graceful fallback to raw bytes if any stage fails.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

from app.preprocessing.base import Preprocessor
from app.preprocessing.shadow_handler import ShadowDetector, ShadowInpainter
from app.preprocessing.sidescan_processor import SidescanProcessor
from app.preprocessing.yolo_preprocessor import YOLOPreprocessingConfig, YOLOPreprocessor
from app.schemas.ml import PreprocessedInput

logger = logging.getLogger(__name__)


class SonarPreprocessor(Preprocessor):
    """End-to-end preprocessor for side-scan sonar imagery."""

    def __init__(
        self,
        apply_sss_processing: bool = True,
        apply_bac: bool = True,
        apply_stripe_filter: bool = True,
        apply_sharpening: bool = True,
        apply_shadow_inpainting: bool = True,
        shadow_threshold: float = 0.15,
        shadow_inpaint_method: str = "telea",
        yolo_config: Optional[YOLOPreprocessingConfig] = None,
    ) -> None:
        self.apply_sss_processing = apply_sss_processing
        self.apply_shadow_inpainting = apply_shadow_inpainting
        self.yolo_config = yolo_config or YOLOPreprocessingConfig()

        self.sidescan_processor = SidescanProcessor(
            apply_bac=apply_bac,
            apply_stripe_filter=apply_stripe_filter,
            apply_sharpening=apply_sharpening,
        )
        self.shadow_detector = ShadowDetector(threshold=shadow_threshold)
        self.shadow_inpainter = ShadowInpainter(method=shadow_inpaint_method)
        self.yolo_preprocessor = YOLOPreprocessor(self.yolo_config)

    def process(self, raw_image_bytes: bytes) -> PreprocessedInput:
        """Convert raw image bytes into a preprocessed YOLOv8 tensor input.

        Gracefully degrades to raw bytes if any processing error occurs.
        """
        if not isinstance(raw_image_bytes, bytes):
            raise TypeError("raw_image_bytes must be a bytes instance")
        if len(raw_image_bytes) == 0:
            raise ValueError("raw_image_bytes must not be empty")

        try:
            # Step 1: Decode raw image bytes into RGB NumPy array
            image = Image.open(io.BytesIO(raw_image_bytes)).convert("RGB")
            image_np = np.array(image)

            # Step 2: SSS-specific corrections (BAC, 2D-FFT stripe filter, homomorphic)
            if self.apply_sss_processing:
                image_np = self.sidescan_processor.process(image_np)

            # Step 3: Acoustic shadow detection & inpainting
            if self.apply_shadow_inpainting:
                shadow_mask = self.shadow_detector.detect(image_np)
                if np.any(shadow_mask > 0):
                    image_np = self.shadow_inpainter.inpaint(image_np, shadow_mask)

            # Step 4: YOLOv8 letterbox resizing, normalization & CHW tensor formatting
            processed_tensor, meta = self.yolo_preprocessor.process_with_meta(image_np)

            return PreprocessedInput(
                data=processed_tensor,
                metadata={
                    "orig_shape": meta.orig_shape,
                    "scale": meta.scale,
                    "pad_left": meta.pad_left,
                    "pad_top": meta.pad_top,
                },
            )

        except Exception as e:
            logger.warning(
                f"Sonar preprocessing encountered an error: {e}. "
                "Gracefully falling back to raw image bytes."
            )
            return PreprocessedInput(data=raw_image_bytes)

    def process_array(self, image_np: np.ndarray) -> np.ndarray:
        """Helper to run preprocessing directly on an in-memory NumPy array."""
        if self.apply_sss_processing:
            image_np = self.sidescan_processor.process(image_np)
        if self.apply_shadow_inpainting:
            shadow_mask = self.shadow_detector.detect(image_np)
            if np.any(shadow_mask > 0):
                image_np = self.shadow_inpainter.inpaint(image_np, shadow_mask)
        return self.yolo_preprocessor.process(image_np)
