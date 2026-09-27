"""GAN-based acoustic shadow inpainter service with OpenCV fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch

from app.ml.gan_modules import InpaintUNetGenerator

logger = logging.getLogger(__name__)


class InpainterService:
    """Service handling acoustic shadow inpainting using PyTorch GAN or OpenCV Telea fallback."""

    def __init__(self, weights_path: str = "models/gan_shadow_inpaint.pth") -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.weights_path = Path(weights_path)
        self.generator = InpaintUNetGenerator(in_channels=4, out_channels=3)
        self.use_gan = False
        self._load_weights()

    def _load_weights(self) -> None:
        if self.weights_path.is_file():
            try:
                state_dict = torch.load(self.weights_path, map_location=self.device)
                self.generator.load_state_dict(state_dict)
                self.generator.to(self.device)
                self.generator.eval()
                self.use_gan = True
                logger.info("GAN shadow inpainting weights loaded from %s", self.weights_path)
            except Exception as e:
                self.use_gan = False
                logger.warning("Failed to load GAN weights (%s). Falling back to OpenCV Telea.", e)
        else:
            self.use_gan = False
            logger.info("GAN weights not found at %s. Operating with OpenCV Telea inpainting.", self.weights_path)

    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Inpaint acoustic shadow regions in sonar image.

        Args:
            image: 2D uint8 grayscale or 3D uint8 BGR image.
            mask: 2D uint8 binary mask (255 for shadow regions to inpaint).

        Returns:
            Inpainted uint8 image matching input dimensions.
        """
        if not self.use_gan:
            if image.ndim == 2:
                return cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            # 3-channel Telea
            channels = [cv2.inpaint(image[:, :, c], mask, 3, cv2.INPAINT_TELEA) for c in range(3)]
            return np.stack(channels, axis=-1)

        try:
            # GAN 4-channel inference: RGB (or 3-channel grayscale) + Mask
            if image.ndim == 2:
                rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                rgb = image.copy()

            h, w = rgb.shape[:2]
            # Normalize to [-1, 1]
            img_tensor = torch.from_numpy(rgb).permute(2, 0, 1).float().unsqueeze(0) / 127.5 - 1.0
            mask_tensor = torch.from_numpy(mask).float().unsqueeze(0).unsqueeze(0) / 255.0

            # 4-channel concatenation [B, 4, H, W]
            inp = torch.cat([img_tensor, mask_tensor], dim=1).to(self.device)

            with torch.no_grad():
                out = self.generator(inp)
                # Rescale from [-1, 1] to [0, 255]
                out_np = ((out.squeeze(0).permute(1, 2, 0).cpu().numpy() + 1.0) * 127.5).clip(0, 255).astype(np.uint8)

            if image.ndim == 2:
                return cv2.cvtColor(out_np, cv2.COLOR_RGB2GRAY)
            return out_np
        except Exception as exc:
            logger.warning("GAN inpaint error (%s). Falling back to OpenCV.", exc)
            if image.ndim == 2:
                return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
            channels = [cv2.inpaint(image[:, :, c], mask, 3, cv2.INPAINT_TELEA) for c in range(3)]
            return np.stack(channels, axis=-1)
