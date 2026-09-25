"""PyTorch GAN-based acoustic shadow inpainter for side-scan sonar.

Inspired by PyTorch-GAN inpainting architectures (U-Net Generator).
Takes 4-channel input (RGB + Shadow Mask) and synthesizes realistic seabed texture.
Gracefully falls back to OpenCV Telea/Navier-Stokes when weights are absent or on error.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn

from app.preprocessing.shadow_handler import ShadowInpainter

logger = logging.getLogger(__name__)


class UNetDown(nn.Module):
    def __init__(self, in_size: int, out_size: int, normalize: bool = True):
        super().__init__()
        layers = [nn.Conv2d(in_size, out_size, 4, stride=2, padding=1, bias=False)]
        if normalize:
            layers.append(nn.BatchNorm2d(out_size, 0.8))
        layers.append(nn.LeakyReLU(0.2))
        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class UNetUp(nn.Module):
    def __init__(self, in_size: int, out_size: int):
        super().__init__()
        self.model = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True),
            nn.Conv2d(in_size, out_size, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_size, 0.8),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip_input: torch.Tensor) -> torch.Tensor:
        x = self.model(x)
        diff_y = skip_input.size()[2] - x.size()[2]
        diff_x = skip_input.size()[3] - x.size()[3]
        if diff_y != 0 or diff_x != 0:
            x = nn.functional.pad(
                x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2]
            )
        return torch.cat((x, skip_input), 1)


class InpaintUNetGenerator(nn.Module):
    """Compact 4-level U-Net Generator for fast shadow texture synthesis."""

    def __init__(self, in_channels: int = 4, out_channels: int = 3):
        super().__init__()
        self.down1 = UNetDown(in_channels, 64, normalize=False)
        self.down2 = UNetDown(64, 128)
        self.down3 = UNetDown(128, 256)
        self.down4 = UNetDown(256, 512)

        self.up1 = UNetUp(512, 256)
        self.up2 = UNetUp(512, 128)
        self.up3 = UNetUp(256, 64)

        self.final = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True),
            nn.Conv2d(128, out_channels, 3, stride=1, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        d1 = self.down1(x)
        d2 = self.down2(d1)
        d3 = self.down3(d2)
        d4 = self.down4(d3)

        u1 = self.up1(d4, d3)
        u2 = self.up2(u1, d2)
        u3 = self.up3(u2, d1)
        return self.final(u3)


class GANShadowInpainter:
    """Wraps deep learning GAN inpainting with fallback to OpenCV."""

    def __init__(
        self,
        weights_path: Optional[str | Path] = None,
        device: Optional[str] = None,
        fallback_method: str = "telea",
    ) -> None:
        self.fallback_inpainter = ShadowInpainter(method=fallback_method)
        self.model: Optional[InpaintUNetGenerator] = None
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        if weights_path is not None and Path(weights_path).exists():
            try:
                self._load_model(weights_path)
            except Exception as e:
                logger.warning(f"Failed to load GAN weights from {weights_path}: {e}. Using OpenCV fallback.")
        else:
            logger.info("No GAN weights specified or file missing. Initialized with OpenCV fallback.")

    def _load_model(self, path: str | Path) -> None:
        model = InpaintUNetGenerator(in_channels=4, out_channels=3)
        checkpoint = torch.load(path, map_location=self.device)
        state_dict = checkpoint["state_dict"] if "state_dict" in checkpoint else checkpoint
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model
        logger.info(f"Loaded GAN shadow inpainting weights from {path}")

    @property
    def is_model_loaded(self) -> bool:
        return self.model is not None

    def inpaint(self, image: np.ndarray, shadow_mask: np.ndarray) -> np.ndarray:
        """Inpaint shadow pixels using GAN if available, else OpenCV fallback."""
        if not np.any(shadow_mask > 0):
            return image.copy()

        if self.model is None:
            return self.fallback_inpainter.inpaint(image, shadow_mask)

        try:
            return self._gan_inpaint(image, shadow_mask)
        except Exception as e:
            logger.warning(f"GAN inpainting inference failed: {e}. Falling back to OpenCV.")
            return self.fallback_inpainter.inpaint(image, shadow_mask)

    def _gan_inpaint(self, image: np.ndarray, shadow_mask: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        img_norm = image.astype(np.float32) / 255.0
        mask_2d = (shadow_mask > 0).astype(np.float32)[..., np.newaxis]

        # Combine RGB + binary mask into 4-channel tensor
        combined = np.concatenate([img_norm, mask_2d], axis=-1)
        tensor_in = torch.from_numpy(combined).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output_tensor = self.model(tensor_in)

        out_np = output_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        out_uint8 = np.clip(out_np * 255.0, 0, 255).astype(np.uint8)

        # Blend only inside the shadow mask
        result = np.where(shadow_mask[..., np.newaxis] > 0, out_uint8, image)
        return result
