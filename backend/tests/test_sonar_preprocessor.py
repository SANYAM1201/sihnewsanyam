"""Unit tests for Side-Scan Sonar preprocessing modules."""

from __future__ import annotations

import io
import numpy as np
import pytest
from PIL import Image

from app.config import Settings
from app.preprocessing.identity_preprocessor import IdentityPreprocessor
from app.preprocessing.shadow_handler import ShadowDetector, ShadowInpainter
from app.preprocessing.sidescan_processor import SidescanProcessor
from app.preprocessing.sonar_preprocessor import SonarPreprocessor
from app.preprocessing.yolo_preprocessor import YOLOPreprocessingConfig, YOLOPreprocessor
from app.schemas.ml import PreprocessedInput
from app.services.factory import create_inference_service


class TestSidescanProcessor:
    @pytest.fixture
    def stripe_image(self) -> np.ndarray:
        # Create 120x120 image with artificial horizontal scanlines
        img = np.ones((120, 120, 3), dtype=np.uint8) * 120
        for row in range(0, 120, 10):
            img[row : row + 3, :] = 250
        return img

    @pytest.fixture
    def gradient_image(self) -> np.ndarray:
        # Create image with column intensity ramp (simulating grazing angle falloff)
        cols = np.linspace(30, 220, 120, dtype=np.float32)
        grid = np.tile(cols, (120, 1))
        return np.stack([grid] * 3, axis=-1).astype(np.uint8)

    def test_bac_normalization(self, gradient_image: np.ndarray):
        processor = SidescanProcessor(apply_bac=True, apply_stripe_filter=False, apply_sharpening=False)
        result = processor.process(gradient_image)
        assert result.shape == gradient_image.shape
        assert result.dtype == np.uint8
        # Column variance across the swath should decrease after BAC normalization
        raw_col_means = np.mean(gradient_image, axis=0)
        proc_col_means = np.mean(result, axis=0)
        assert np.std(proc_col_means) < np.std(raw_col_means)

    def test_stripe_filter(self, stripe_image: np.ndarray):
        processor = SidescanProcessor(apply_bac=False, apply_stripe_filter=True, apply_sharpening=False)
        result = processor.process(stripe_image)
        assert result.shape == stripe_image.shape
        assert result.dtype == np.uint8

    def test_homomorphic_sharpening(self, gradient_image: np.ndarray):
        processor = SidescanProcessor(apply_bac=False, apply_stripe_filter=False, apply_sharpening=True)
        result = processor.process(gradient_image)
        assert result.shape == gradient_image.shape
        assert result.dtype == np.uint8

    def test_bottom_line_detection(self):
        processor = SidescanProcessor()
        # Create an image: top 25 rows is water column (near zero), rows 25-100 is seabed (intensity 140)
        img = np.ones((100, 80), dtype=np.uint8) * 140
        img[:25, :] = 5
        bld = processor.detect_bottom_line(img, threshold_factor=2.0)
        assert len(bld) == 80
        # Bottom line should be detected around row 25
        assert np.all(np.abs(bld - 25) <= 2)

    def test_rejects_invalid_inputs(self):
        processor = SidescanProcessor()
        with pytest.raises(TypeError):
            processor.process("not an array")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            processor.process(np.array([]))


class TestShadowHandler:
    @pytest.fixture
    def shadow_image(self) -> np.ndarray:
        # 100x100 image with bright seafloor (180) and a dark acoustic shadow (10)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 180
        img[30:70, 30:70] = 10  # Deep shadow region
        # Also add a tiny 2x2 speckle
        img[5:7, 5:7] = 5
        return img

    def test_shadow_detection(self, shadow_image: np.ndarray):
        detector = ShadowDetector(threshold=0.15, min_shadow_size=100)
        mask = detector.detect(shadow_image)
        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8
        # Shadow region (30:70, 30:70) should be detected as 255
        assert np.all(mask[35:65, 35:65] == 255)
        # Tiny 2x2 speckle should be filtered out by min_shadow_size
        assert np.all(mask[5:7, 5:7] == 0)

    def test_shadow_inpainting_telea(self, shadow_image: np.ndarray):
        detector = ShadowDetector(threshold=0.15, min_shadow_size=50)
        inpainter = ShadowInpainter(method="telea", inpaint_radius=3)
        mask = detector.detect(shadow_image)
        inpainted = inpainter.inpaint(shadow_image, mask)
        assert inpainted.shape == shadow_image.shape
        # Inpainted shadow pixels should have increased intensity closer to the background
        assert float(np.mean(inpainted[35:65, 35:65])) > 50.0

    def test_shadow_inpainting_ns(self, shadow_image: np.ndarray):
        detector = ShadowDetector(threshold=0.15, min_shadow_size=50)
        inpainter = ShadowInpainter(method="ns", inpaint_radius=3)
        mask = detector.detect(shadow_image)
        inpainted = inpainter.inpaint(shadow_image, mask)
        assert inpainted.shape == shadow_image.shape
        assert float(np.mean(inpainted[35:65, 35:65])) > 50.0

    def test_empty_shadow_mask(self, shadow_image: np.ndarray):
        inpainter = ShadowInpainter()
        empty_mask = np.zeros((100, 100), dtype=np.uint8)
        result = inpainter.inpaint(shadow_image, empty_mask)
        assert np.array_equal(result, shadow_image)


class TestYOLOPreprocessor:
    @pytest.fixture
    def nonsquare_image(self) -> np.ndarray:
        return np.ones((100, 200, 3), dtype=np.uint8) * 128

    def test_letterbox_resize_and_chw_tensor(self, nonsquare_image: np.ndarray):
        config = YOLOPreprocessingConfig(target_size=(640, 640), normalize=True)
        preprocessor = YOLOPreprocessor(config)
        chw = preprocessor.process(nonsquare_image)
        assert chw.shape == (3, 640, 640)
        assert chw.dtype == np.float32
        assert 0.0 <= chw.min() <= chw.max() <= 1.0

    def test_grayscale_conversion(self):
        gray = np.ones((80, 80), dtype=np.uint8) * 100
        preprocessor = YOLOPreprocessor()
        chw = preprocessor.process(gray)
        assert chw.shape == (3, 640, 640)
        assert chw.dtype == np.float32

    def test_batch_process(self, nonsquare_image: np.ndarray):
        preprocessor = YOLOPreprocessor()
        batch = preprocessor.batch_process([nonsquare_image, nonsquare_image])
        assert batch.shape == (2, 3, 640, 640)


class TestSonarPreprocessor:
    @pytest.fixture
    def sample_png_bytes(self) -> bytes:
        img = Image.new("RGB", (150, 100), color=(140, 140, 140))
        # Draw a dark acoustic shadow stripe
        arr = np.array(img)
        arr[40:70, 40:80] = 10
        img = Image.fromarray(arr)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        return bio.getvalue()

    def test_full_pipeline_process(self, sample_png_bytes: bytes):
        preprocessor = SonarPreprocessor(
            apply_sss_processing=True,
            apply_bac=True,
            apply_stripe_filter=True,
            apply_sharpening=True,
            apply_shadow_inpainting=True,
            shadow_threshold=0.15,
            shadow_inpaint_method="telea",
            yolo_config=YOLOPreprocessingConfig(target_size=(640, 640)),
        )
        output = preprocessor.process(sample_png_bytes)
        assert isinstance(output, PreprocessedInput)
        tensor = output.data
        assert isinstance(tensor, np.ndarray)
        assert tensor.shape == (3, 640, 640)
        assert tensor.dtype == np.float32
        assert 0.0 <= tensor.min() <= tensor.max() <= 1.0

    def test_rejects_non_bytes(self):
        preprocessor = SonarPreprocessor()
        with pytest.raises(TypeError):
            preprocessor.process("not bytes")  # type: ignore[arg-type]

    def test_rejects_empty_bytes(self):
        preprocessor = SonarPreprocessor()
        with pytest.raises(ValueError):
            preprocessor.process(b"")

    def test_graceful_fallback_on_corrupt_data(self):
        preprocessor = SonarPreprocessor()
        # Invalid image bytes that PIL cannot decode
        corrupt = b"not an image file content"
        output = preprocessor.process(corrupt)
        assert isinstance(output, PreprocessedInput)
        # Should gracefully return raw bytes without raising
        assert output.data == corrupt


class TestFactoryAndServiceIntegration:
    def test_factory_creates_sonar_preprocessor(self):
        settings = Settings(
            model_provider="mock",
            sss_enable_processing=True,
        )
        service = create_inference_service(settings)
        assert isinstance(service._preprocessor, SonarPreprocessor)

    def test_factory_creates_identity_preprocessor_when_disabled(self):
        settings = Settings(
            model_provider="mock",
            sss_enable_processing=False,
        )
        service = create_inference_service(settings)
        assert isinstance(service._preprocessor, IdentityPreprocessor)


class TestEdgeCases:
    """Test resilience against edge cases: extreme aspect ratios, noise, sizes, channels."""

    def test_tiny_image(self):
        preprocessor = SonarPreprocessor()
        tiny = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        result = preprocessor.process_array(tiny)
        assert result.shape == (3, 640, 640)
        assert result.dtype == np.float32

    def test_large_image(self):
        preprocessor = SonarPreprocessor()
        large = np.random.randint(50, 200, (2000, 2000, 3), dtype=np.uint8)
        result = preprocessor.process_array(large)
        assert result.shape == (3, 640, 640)
        assert result.dtype == np.float32

    def test_extreme_aspect_ratio_tall(self):
        preprocessor = SonarPreprocessor()
        tall = np.random.randint(50, 200, (1500, 50, 3), dtype=np.uint8)
        result = preprocessor.process_array(tall)
        assert result.shape == (3, 640, 640)
        assert result.dtype == np.float32

    def test_extreme_aspect_ratio_wide(self):
        preprocessor = SonarPreprocessor()
        wide = np.random.randint(50, 200, (50, 1500, 3), dtype=np.uint8)
        result = preprocessor.process_array(wide)
        assert result.shape == (3, 640, 640)
        assert result.dtype == np.float32

    def test_grayscale_2d_array(self):
        preprocessor = SonarPreprocessor()
        gray = np.random.randint(50, 200, (200, 200), dtype=np.uint8)
        result = preprocessor.process_array(gray)
        assert result.shape == (3, 640, 640)

    def test_rgba_4channel_array(self):
        preprocessor = SonarPreprocessor()
        rgba = np.random.randint(50, 200, (150, 150, 4), dtype=np.uint8)
        result = preprocessor.process_array(rgba)
        assert result.shape == (3, 640, 640)

    def test_all_black_image(self):
        preprocessor = SonarPreprocessor()
        black = np.zeros((100, 100, 3), dtype=np.uint8)
        result = preprocessor.process_array(black)
        assert result.shape == (3, 640, 640)
        assert not np.isnan(result).any()

    def test_all_white_image(self):
        preprocessor = SonarPreprocessor()
        white = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = preprocessor.process_array(white)
        assert result.shape == (3, 640, 640)
        assert not np.isnan(result).any()

    def test_speckle_noise_resilience(self):
        preprocessor = SonarPreprocessor()
        base = np.ones((150, 150, 3), dtype=np.uint8) * 128
        # Add high-frequency speckle noise
        noise = np.random.randint(-50, 50, (150, 150, 3))
        noisy = np.clip(base.astype(np.int32) + noise, 0, 255).astype(np.uint8)
        result = preprocessor.process_array(noisy)
        assert result.shape == (3, 640, 640)
        assert not np.isnan(result).any()

