"""Shadow-Aided Decoupling Head (SADH) - Multitask Height & Shadow Prediction."""

from __future__ import annotations

import torch
import torch.nn as nn
from backend.app.services.physics.sadh_loss import SADHHead

__all__ = ["SADHHead"]
