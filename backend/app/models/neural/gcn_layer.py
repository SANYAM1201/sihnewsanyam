"""Graph Convolutional Network (GCN) layer for Debris Graph Reasoning."""

from __future__ import annotations

import torch
import torch.nn as nn
from backend.app.models.neural.debris_graph import GraphConvolution

__all__ = ["GraphConvolution", "GCNBlock"]


class GCNBlock(nn.Module):
    """Two-layer GCN block with residual connection and ReLU activation."""

    def __init__(self, in_features: int, hidden_features: int, out_features: int, dropout: float = 0.1):
        super().__init__()
        self.gcn1 = GraphConvolution(in_features, hidden_features)
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout)
        self.gcn2 = GraphConvolution(hidden_features, out_features)
        self.res_proj = (
            nn.Linear(in_features, out_features)
            if in_features != out_features
            else nn.Identity()
        )

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        res = self.res_proj(x)
        out = self.gcn1(x, adj)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.gcn2(out, adj)
        return out + res
