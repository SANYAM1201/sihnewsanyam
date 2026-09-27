"""Differentiable Acoustic Physics Loss for Shadow-Aided Decoupling Head."""

from __future__ import annotations

import torch
import torch.nn as nn
from backend.app.services.physics.sadh_loss import SADHPhysicsLoss

__all__ = ["SADHPhysicsLoss"]
