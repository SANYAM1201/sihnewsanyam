"""Unit tests for PyTorch GAN shadow inpainting module."""

from __future__ import annotations

import tempfile
from pathlib import Path
import numpy as np
import pytest
import torch

from app.ml.gan_modules import GANShadowInpainter, InpaintUNetGenerator


class TestGANShadowInpainter:
    def test_generator_architecture(self):
        generator = InpaintUNetGenerator(in_channels=4, out_channels=3)
        dummy_input = torch.randn(1, 4, 128, 128)
        output = generator(dummy_input)
        assert output.shape == (1, 3, 128, 128)
        assert output.min() >= 0.0
        assert output.max() <= 1.0

    def test_fallback_when_no_weights(self):
        inpainter = GANShadowInpainter(weights_path=None)
        assert not inpainter.is_model_loaded

        # Should use OpenCV fallback seamlessly
        img = np.ones((100, 100, 3), dtype=np.uint8) * 150
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[30:70, 30:70] = 255
        result = inpainter.inpaint(img, mask)
        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_inpaint_with_weights(self):
        generator = InpaintUNetGenerator(in_channels=4, out_channels=3)
        with tempfile.NamedTemporaryFile(suffix=".pt") as tmp:
            torch.save(generator.state_dict(), tmp.name)

            inpainter = GANShadowInpainter(weights_path=tmp.name)
            assert inpainter.is_model_loaded

            img = np.ones((64, 64, 3), dtype=np.uint8) * 128
            mask = np.zeros((64, 64), dtype=np.uint8)
            mask[20:40, 20:40] = 255
            result = inpainter.inpaint(img, mask)
            assert result.shape == img.shape
            assert result.dtype == np.uint8
