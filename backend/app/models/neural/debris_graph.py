"""Debris Graph Reasoning Module (D-GRM).

Graph Convolutional Network (GCN) that links scattered, torn ghost net fragments
and debris clusters into unified hazard zones.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class GraphConvolution(nn.Module):
    """Spectral Graph Convolutional Layer (Kipf & Welling)."""

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """Graph convolution: H^(l+1) = sigma(A_norm * H^(l) * W)."""
        N = x.size(0)
        # Add self-loops
        adj_tilde = adj + torch.eye(N, device=x.device, dtype=adj.dtype)
        # Symmetrically normalize adjacency
        deg = torch.sum(adj_tilde, dim=1)
        deg_inv_sqrt = torch.pow(torch.clamp(deg, min=1e-6), -0.5)
        d_mat = torch.diag(deg_inv_sqrt)
        norm_adj = torch.mm(torch.mm(d_mat, adj_tilde), d_mat)

        out = torch.mm(norm_adj, x)
        return self.linear(out)


class SpatialProximityAdjacency(nn.Module):
    """Constructs adjacency matrix based on spatial Euclidean proximity of candidate detections."""

    def __init__(self, max_distance: float = 0.4, sigma: float = 0.15):
        super().__init__()
        self.max_distance = max_distance
        self.sigma = sigma

    def forward(self, boxes: torch.Tensor) -> torch.Tensor:
        """Compute spatial adjacency from bounding box centers (x1, y1, x2, y2)."""
        N = boxes.size(0)
        if N <= 1:
            return torch.zeros((N, N), device=boxes.device)

        centers_x = (boxes[:, 0] + boxes[:, 2]) * 0.5
        centers_y = (boxes[:, 1] + boxes[:, 3]) * 0.5
        centers = torch.stack([centers_x, centers_y], dim=1)  # (N, 2)

        diff = centers.unsqueeze(1) - centers.unsqueeze(0)  # (N, N, 2)
        dist = torch.norm(diff, dim=2)  # (N, N)

        adj = torch.exp(-(dist**2) / (2 * (self.sigma**2)))
        adj = (dist <= self.max_distance).float() * adj
        # Zero out diagonal
        adj = adj * (1.0 - torch.eye(N, device=boxes.device))
        return adj


class FeatureSimilarityAdjacency(nn.Module):
    """Constructs adjacency matrix based on acoustic feature cosine similarity."""

    def __init__(self, threshold: float = 0.65):
        super().__init__()
        self.threshold = threshold

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        N = features.size(0)
        if N <= 1:
            return torch.zeros((N, N), device=features.device)

        norm_feat = F.normalize(features, p=2, dim=1)
        sim = torch.mm(norm_feat, norm_feat.t())
        adj = (sim >= self.threshold).float() * sim
        adj = adj * (1.0 - torch.eye(N, device=features.device))
        return adj


class DebrisGraphReasoningModule(nn.Module):
    """Complete D-GRM: Dual-graph reasoning module combining spatial proximity & acoustic semantics."""

    def __init__(self, input_dim: int = 256, hidden_dim: int = 128, output_dim: int = 64):
        super().__init__()
        self.spatial_adj = SpatialProximityAdjacency()
        self.feature_adj = FeatureSimilarityAdjacency()

        self.gc1 = GraphConvolution(input_dim, hidden_dim)
        self.gc2 = GraphConvolution(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)
        self.fusion = nn.Linear(input_dim + output_dim, input_dim)

    def forward(self, features: torch.Tensor, boxes: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        N = features.size(0)
        if N == 0:
            return features, torch.zeros((0, 0), device=features.device)
        if N == 1:
            return features, torch.zeros((1, 1), device=features.device)

        s_adj = self.spatial_adj(boxes)
        f_adj = self.feature_adj(features)
        adj = 0.5 * (s_adj + f_adj)

        h1 = F.relu(self.gc1(features, adj))
        h1 = self.dropout(h1)
        h2 = F.relu(self.gc2(h1, adj))

        # Residual feature fusion
        combined = torch.cat([features, h2], dim=1)
        refined = self.fusion(combined)
        return refined, adj


class DGRMYOLOv8s(nn.Module):
    """YOLOv8s model enhanced with D-GRM post-processing."""

    def __init__(self, num_classes: int = 8):
        super().__init__()
        self.num_classes = num_classes
        self.feature_encoder = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(1),
        )
        self.dgrm = DebrisGraphReasoningModule(input_dim=256)
        self.classifier = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor, boxes: torch.Tensor | None = None) -> torch.Tensor:
        feat = self.feature_encoder(x)
        if boxes is not None and boxes.size(0) > 1:
            refined, _ = self.dgrm(feat, boxes)
            logits = self.classifier(refined)
        else:
            logits = self.classifier(feat)
        return logits
