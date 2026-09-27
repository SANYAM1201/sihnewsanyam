"""SADH Physics Loss & Multi-Task Decoupling Head.

Embeds acoustic shadow geometry into PyTorch backpropagation:
    L_theo = (h_hat * R_s) / H_s
    L_phys = |L_pred - L_theo|
Penalizes confidence on physical violations and suppresses geological false alarms.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class SADHPhysicsLoss(nn.Module):
    """Shadow-Aided Decoupling Head (SADH) differentiable physics loss."""

    def __init__(self, lambda_phys: float = 2.0, lambda_height: float = 1.0, lambda_shadow: float = 1.0):
        super().__init__()
        self.lambda_phys = lambda_phys
        self.lambda_height = lambda_height
        self.lambda_shadow = lambda_shadow
        self.mse = nn.MSELoss(reduction="mean")

    def forward(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        metadata: Dict[str, torch.Tensor],
    ) -> Dict[str, torch.Tensor]:
        """Compute SADH multi-task loss.

        predictions: 'h_pred', 'L_pred', 'conf', 'class_logits'
        targets: 'h_true', 'L_true', 'is_geology', 'class_labels'
        metadata: 'R_s' (slant range), 'H_s' (towfish altitude)
        """
        h_pred = predictions["h_pred"].view(-1)
        L_pred = predictions["L_pred"].view(-1)
        conf = predictions.get("conf", torch.ones_like(h_pred)).view(-1)

        h_true = targets["h_true"].view(-1)
        L_true = targets["L_true"].view(-1)
        is_geology = targets.get("is_geology", torch.zeros_like(h_pred, dtype=torch.bool)).view(-1)

        R_s = metadata.get("R_s", torch.tensor(100.0, device=h_pred.device))
        H_s = metadata.get("H_s", torch.tensor(10.0, device=h_pred.device))

        # Theoretical acoustic shadow length: L_theo = (h_hat * R_s) / H_s
        L_theo = (h_pred * R_s) / (H_s + 1e-6)

        # Physics geometric violation
        phys_violation = torch.abs(L_pred - L_theo)

        # Height and shadow regression losses
        loss_h = self.mse(h_pred, h_true)
        loss_L = self.mse(L_pred, L_true)

        # Physics loss weighted by detection confidence
        loss_phys = torch.mean(phys_violation * conf)

        # False-alarm penalty for geology exhibiting high confidence with missing shadow
        geo_penalty = torch.mean(is_geology.float() * conf * self.lambda_phys)

        total_loss = (
            self.lambda_height * loss_h
            + self.lambda_shadow * loss_L
            + self.lambda_phys * loss_phys
            + geo_penalty
        )

        return {
            "total_physics_loss": total_loss,
            "loss_h": loss_h,
            "loss_L": loss_L,
            "loss_phys": loss_phys,
            "geo_penalty": geo_penalty,
        }


class SADHHead(nn.Module):
    """Multi-task prediction head predicting class logits, height, and shadow."""

    def __init__(self, in_channels: int = 256, num_classes: int = 8, pool: bool = True):
        super().__init__()
        self.num_classes = num_classes
        self.pool = pool

        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        if pool:
            self.pool_layer = nn.AdaptiveAvgPool2d((1, 1))

        # Multi-task output projections
        self.class_head = nn.Linear(256, num_classes) if pool else nn.Conv2d(256, num_classes, kernel_size=1)
        self.height_head = nn.Sequential(
            nn.Linear(256, 1) if pool else nn.Conv2d(256, 1, kernel_size=1),
            nn.ReLU(),  # Physical target height must be >= 0
        )
        self.shadow_head = nn.Sequential(
            nn.Linear(256, 1) if pool else nn.Conv2d(256, 1, kernel_size=1),
            nn.ReLU(),  # Shadow length must be >= 0
        )
        self.conf_head = nn.Sequential(
            nn.Linear(256, 1) if pool else nn.Conv2d(256, 1, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.shared(x)
        if self.pool:
            feat = self.pool_layer(feat).flatten(1)
        class_logits = self.class_head(feat)
        h_pred = self.height_head(feat)
        L_pred = self.shadow_head(feat)
        conf = self.conf_head(feat)

        return {
            "class_logits": class_logits,
            "h_pred": h_pred,
            "L_pred": L_pred,
            "conf": conf,
        }


class SADHYOLOv8s(nn.Module):
    """Full Sonar Sentry SADH Multi-Task Neural Network."""

    def __init__(self, num_classes: int = 8):
        super().__init__()
        self.num_classes = num_classes

        # ResNet/ConvNet feature backbone
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        self.sadh_head = SADHHead(in_channels=256, num_classes=num_classes)
        self.physics_loss = SADHPhysicsLoss()

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.backbone(x)
        pred = self.sadh_head(feat)
        return pred

    def compute_loss(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        metadata: Dict[str, torch.Tensor],
    ) -> Dict[str, torch.Tensor]:
        phys_losses = self.physics_loss(predictions, targets, metadata)
        cls_loss = F.cross_entropy(predictions["class_logits"], targets["class_labels"])
        total = cls_loss + phys_losses["total_physics_loss"]
        return {"total": total, "class_loss": cls_loss, **phys_losses}
