"""Standalone 2D Haar Wavelet Transform layer for PyTorch networks."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class HaarWavelet2D(nn.Module):
    """2D Haar Wavelet Transform layer decomposing C channels into 4*C sub-bands."""

    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels

        ll = torch.tensor([[1.0, 1.0], [1.0, 1.0]]) * 0.5
        lh = torch.tensor([[1.0, -1.0], [1.0, -1.0]]) * 0.5
        hl = torch.tensor([[1.0, 1.0], [-1.0, -1.0]]) * 0.5
        hh = torch.tensor([[1.0, -1.0], [-1.0, 1.0]]) * 0.5

        filters = torch.stack([ll, lh, hl, hh], dim=0).unsqueeze(1)  # (4, 1, 2, 2)
        self.register_buffer("filters", filters)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, C, H, W = x.shape
        pad_h = H % 2
        pad_w = W % 2
        if pad_h or pad_w:
            x = F.pad(x, (0, pad_w, 0, pad_h), mode="reflect")

        weight = self.filters.repeat(C, 1, 1, 1)
        out = F.conv2d(x, weight, stride=2, padding=0, groups=C)
        return out
