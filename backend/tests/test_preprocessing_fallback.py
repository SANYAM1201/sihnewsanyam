"""Tests for error handling and graceful degradation in SSS preprocessing."""

from __future__ import annotations

import io
from unittest.mock import patch
import numpy as np
from PIL import Image
import pytest

from app.preprocessing.sonar_preprocessor import SonarPreprocessor
from app.preprocessing.sidescan_processor import SidescanProcessor
from app.schemas.ml import PreprocessedInput


@pytest.fixture
def sample_image_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


class TestStageFallbacks:
    def test_bac_failure_does_not_abort_pipeline(self):
        processor = SidescanProcessor(apply_bac=True, apply_stripe_filter=True, apply_sharpening=True)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        with patch.object(processor, "_apply_bac", side_effect=RuntimeError("Simulated BAC error")):
            result = processor.process(img)
            # Should not raise exception; returns valid processed array
            assert isinstance(result, np.ndarray)
            assert result.shape == img.shape

    def test_stripe_filter_failure_does_not_abort_pipeline(self):
        processor = SidescanProcessor(apply_bac=True, apply_stripe_filter=True, apply_sharpening=True)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        with patch.object(processor, "_apply_stripe_filter", side_effect=RuntimeError("Simulated FFT error")):
            result = processor.process(img)
            assert isinstance(result, np.ndarray)
            assert result.shape == img.shape

    def test_homomorphic_failure_does_not_abort_pipeline(self):
        processor = SidescanProcessor(apply_bac=True, apply_stripe_filter=True, apply_sharpening=True)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        with patch.object(processor, "_apply_homomorphic", side_effect=RuntimeError("Simulated sharpening error")):
            result = processor.process(img)
            assert isinstance(result, np.ndarray)
            assert result.shape == img.shape

    def test_shadow_detection_failure_in_pipeline(self, sample_image_bytes: bytes):
        preprocessor = SonarPreprocessor()

        with patch.object(preprocessor.shadow_detector, "detect", side_effect=RuntimeError("Shadow detector crash")):
            # Top-level catch triggers graceful fallback to raw bytes
            output = preprocessor.process(sample_image_bytes)
            assert isinstance(output, PreprocessedInput)
            assert output.data == sample_image_bytes

    def test_shadow_inpainter_internal_failure(self):
        from app.preprocessing.shadow_handler import ShadowInpainter
        inpainter = ShadowInpainter()
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        mask = np.ones((100, 100), dtype=np.uint8) * 255

        with patch("cv2.inpaint", side_effect=RuntimeError("OpenCV inpaint crash")):
            result = inpainter.inpaint(img, mask)
            # Inpainter catches exception internally and returns image copy
            assert isinstance(result, np.ndarray)
            assert np.array_equal(result, img)

    def test_yolo_preprocessor_failure_triggers_raw_fallback(self, sample_image_bytes: bytes):
        preprocessor = SonarPreprocessor()

        with patch.object(preprocessor.yolo_preprocessor, "process_with_meta", side_effect=RuntimeError("YOLO resize fail")):
            output = preprocessor.process(sample_image_bytes)
            assert isinstance(output, PreprocessedInput)
            assert output.data == sample_image_bytes
