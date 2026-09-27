"""Wavelet-Embedded Residual Backbone (WERB).

2D Haar DWT layers to separate structural topologies (X_LL) from high-frequency speckle
(X_LH, X_HL, X_HH). Routes noise through suppression blocks while preserving structural features.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class HaarDWT2D(nn.Module):
    """2D Haar Discrete Wavelet Transform Layer.

    Decomposes input into 4 orthogonal sub-bands:
    - LL (low-low): Structural topology and continuous echo
    - LH (low-high): Horizontal high-frequency edges & speckle
    - HL (high-low): Vertical high-frequency edges & heave lines
    - HH (high-high): Diagonal high-frequency scatter
    """

    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels

        # 2D Haar 2x2 filter kernels (scale factor 0.5 for energy conservation)
        ll = torch.tensor([[1.0, 1.0], [1.0, 1.0]]) * 0.5
        lh = torch.tensor([[1.0, -1.0], [1.0, -1.0]]) * 0.5
        hl = torch.tensor([[1.0, 1.0], [-1.0, -1.0]]) * 0.5
        hh = torch.tensor([[1.0, -1.0], [-1.0, 1.0]]) * 0.5

        # Shape: (4, 1, 2, 2) -> repeated for grouped convolution
        filters = torch.stack([ll, lh, hl, hh], dim=0).unsqueeze(1)
        self.register_buffer("filters", filters)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        B, C, H, W = x.shape
        # Pad if odd dimensions
        pad_h = H % 2
        pad_w = W % 2
        if pad_h or pad_w:
            x = F.pad(x, (0, pad_w, 0, pad_h), mode="reflect")

        # Expand filters across all channels with groups=C
        weight = self.filters.repeat(C, 1, 1, 1)  # (4*C, 1, 2, 2)
        out = F.conv2d(x, weight, stride=2, padding=0, groups=C)  # (B, 4*C, H/2, W/2)

        # Reshape to (B, C, 4, H/2, W/2)
        out = out.view(B, C, 4, out.shape[-2], out.shape[-1])
        ll = out[:, :, 0]
        lh = out[:, :, 1]
        hl = out[:, :, 2]
        hh = out[:, :, 3]
        return ll, lh, hl, hh


class InverseHaarDWT2D(nn.Module):
    """Inverse 2D Haar Discrete Wavelet Transform.

    Reconstructs spatial signal from LL, LH, HL, HH sub-bands.
    """

    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels

        ll = torch.tensor([[1.0, 1.0], [1.0, 1.0]]) * 0.5
        lh = torch.tensor([[1.0, -1.0], [1.0, -1.0]]) * 0.5
        hl = torch.tensor([[1.0, 1.0], [-1.0, -1.0]]) * 0.5
        hh = torch.tensor([[1.0, -1.0], [-1.0, 1.0]]) * 0.5

        filters = torch.stack([ll, lh, hl, hh], dim=0).unsqueeze(1)
        self.register_buffer("filters", filters)

    def forward(self, ll: torch.Tensor, lh: torch.Tensor, hl: torch.Tensor, hh: torch.Tensor) -> torch.Tensor:
        B, C, H, W = ll.shape
        stacked = torch.stack([ll, lh, hl, hh], dim=2).view(B, 4 * C, H, W)
        weight = self.filters.repeat(C, 1, 1, 1)
        recon = F.conv_transpose2d(stacked, weight, stride=2, padding=0, groups=C)
        return recon


class NoiseSuppressionBlock(nn.Module):
    """Adaptive soft-thresholding block for high-frequency sub-bands (LH, HL, HH)."""

    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels
        self.threshold = nn.Parameter(torch.ones(1, channels * 3, 1, 1) * 0.05)
        self.scale = nn.Parameter(torch.ones(1, channels * 3, 1, 1) * 2.0)

    def forward(self, lh: torch.Tensor, hl: torch.Tensor, hh: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        cat_noise = torch.cat([lh, hl, hh], dim=1)
        # Soft-thresholding gate
        gate = torch.sigmoid(self.scale * (torch.abs(cat_noise) - self.threshold))
        suppressed = cat_noise * gate
        c = lh.shape[1]
        return suppressed[:, :c], suppressed[:, c : 2 * c], suppressed[:, 2 * c :]


class WERBBlock(nn.Module):
    """Wavelet-Embedded Residual Block.

    Separates input into structural (LL) and high-frequency noise components.
    Structural stream uses deep residual convolutions; noise stream is gated
    via adaptive soft-thresholding.
    """

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.stride = stride

        self.dwt = HaarDWT2D(in_channels)
        self.noise_suppression = NoiseSuppressionBlock(in_channels)

        # Structural path
        self.structural_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels // 2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels // 2, out_channels // 2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels // 2),
        )

        # Noise path
        self.noise_conv = nn.Sequential(
            nn.Conv2d(in_channels * 3, out_channels // 2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels // 2, out_channels // 2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels // 2),
        )

        # Upsample/interpolate to match output spatial resolution if needed
        self.shortcut = nn.Sequential()
        if in_channels != out_channels or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        ll, lh, hl, hh = self.dwt(x)

        # Process structural stream (LL)
        struct_feat = self.structural_conv(ll)

        # Process suppressed noise stream
        lh_s, hl_s, hh_s = self.noise_suppression(lh, hl, hh)
        noise_feat = self.noise_conv(torch.cat([lh_s, hl_s, hh_s], dim=1))

        # Combine streams
        combined = torch.cat([struct_feat, noise_feat], dim=1)

        # Match spatial dimension to target
        if self.stride == 1:
            combined = F.interpolate(combined, size=(x.shape[2], x.shape[3]), mode="bilinear", align_corners=False)
        else:
            target_h = math.ceil(x.shape[2] / self.stride)
            target_w = math.ceil(x.shape[3] / self.stride)
            combined = F.interpolate(combined, size=(target_h, target_w), mode="bilinear", align_corners=False)

        res = self.shortcut(identity)
        if res.shape[-2:] != combined.shape[-2:]:
            res = F.interpolate(res, size=combined.shape[-2:], mode="bilinear", align_corners=False)

        out = self.relu(combined + res)
        return out


class WERBBackbone(nn.Module):
    """Complete Multi-Scale WERB Backbone for Marine Sonar Detection."""

    def __init__(self, in_channels: int = 3, num_classes: int = 8):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
        )
        self.block1 = WERBBlock(32, 64, stride=1)
        self.block2 = WERBBlock(64, 128, stride=2)
        self.block3 = WERBBlock(128, 256, stride=2)
        self.block4 = WERBBlock(256, 512, stride=2)

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        x0 = self.stem(x)
        c1 = self.block1(x0)
        c2 = self.block2(c1)
        c3 = self.block3(c2)
        c4 = self.block4(c3)
        return [c2, c3, c4]


class WERBYOLOv8s(nn.Module):
    """YOLOv8s model wrapper incorporating the WERB backbone."""

    def __init__(self, num_classes: int = 8):
        super().__init__()
        self.num_classes = num_classes
        self.backbone = WERBBackbone(in_channels=3, num_classes=num_classes)
        # 1x1 projection head for multi-scale features
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(1),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        logits = self.head(features[-1])
        return logits
