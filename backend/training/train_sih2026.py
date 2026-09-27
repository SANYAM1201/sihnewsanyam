"""Sonar Sentry SIH-26057 Multi-Task Training Pipeline.

Integrates:
- Wavelet-Embedded Residual Backbone (WERB)
- Debris Graph Reasoning Module (D-GRM)
- Shadow-Acoustic Dispersion Height (SADH) Multi-Task Physics Loss
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import yaml

from backend.app.models.neural.debris_graph import DebrisGraphReasoningModule
from backend.app.models.neural.werb_backbone import WERBBackbone
from backend.app.services.physics.sadh_loss import SADHHead, SADHPhysicsLoss
from backend.training.prepare_dataset import apply_rayleigh_speckle, apply_towfish_heave_stripes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sonar_trainer")


class SonarDataset(Dataset):
    """PyTorch Dataset for Sonar Images with Acoustic Physics Annotations."""

    def __init__(self, img_dir: Path, lbl_dir: Path, meta_dir: Path, augment: bool = True):
        self.img_paths = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        self.lbl_dir = lbl_dir
        self.meta_dir = meta_dir
        self.augment = augment

    def __len__(self) -> int:
        return len(self.img_paths)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        img_path = self.img_paths[idx]
        stem = img_path.stem
        lbl_path = self.lbl_dir / f"{stem}.txt"
        meta_path = self.meta_dir / f"{stem}.meta.json"

        # Read image
        img = cv2.imread(str(img_path))
        if img is None:
            img = np.zeros((640, 640, 3), dtype=np.uint8)

        # Apply sonar augmentations
        if self.augment:
            if np.random.rand() > 0.5:
                img = apply_rayleigh_speckle(img, sigma=0.3)
            if np.random.rand() > 0.6:
                img = apply_towfish_heave_stripes(img, amplitude=25.0)

        # Resize to 640x640 if needed
        if img.shape[:2] != (640, 640):
            img = cv2.resize(img, (640, 640))

        # Convert to float tensor (C, H, W) normalized [0, 1]
        img_tensor = torch.from_numpy(img.transpose(2, 0, 1)).float() / 255.0

        # Read annotations
        boxes, classes = [], []
        if lbl_path.exists():
            with open(lbl_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        classes.append(int(parts[0]))
                        boxes.append([float(p) for p in parts[1:5]])

        # Read acoustic metadata
        alt_m = 10.0
        h_true, L_true, is_geology = 1.0, 5.0, False
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    alt_m = meta.get("altitude_m", 10.0)
                    targets = meta.get("targets", [])
                    if targets:
                        first = targets[0]
                        h_true = first.get("height_m", 1.0)
                        L_true = first.get("shadow_len_px", 50.0) / 10.0
                        is_geology = first.get("is_geology", False)
            except Exception:
                pass

        primary_class = classes[0] if classes else 0
        return {
            "image": img_tensor,
            "class_label": torch.tensor(primary_class, dtype=torch.long),
            "h_true": torch.tensor(h_true, dtype=torch.float32),
            "L_true": torch.tensor(L_true, dtype=torch.float32),
            "is_geology": torch.tensor(is_geology, dtype=torch.bool),
            "altitude_m": torch.tensor(alt_m, dtype=torch.float32),
            "slant_range_m": torch.tensor(35.0, dtype=torch.float32),
        }


class SonarSentryFullModel(nn.Module):
    """End-to-End Neural Architecture combining WERB + D-GRM + SADH."""

    def __init__(self, num_classes: int = 6):
        super().__init__()
        self.backbone = WERBBackbone(in_channels=3, num_classes=num_classes)
        # Backbone outputs: c2 (128ch), c3 (256ch), c4 (512ch)
        self.dgrm = DebrisGraphReasoningModule(input_dim=512)
        self.sadh_head = SADHHead(in_channels=512, num_classes=num_classes, pool=True)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        features = self.backbone(x)
        c4 = features[-1]  # (B, 512, H/16, W/16)
        pred = self.sadh_head(c4)
        return pred


def train_model(config_path: str, epochs: int = 1, dry_run: bool = False) -> Dict[str, Any]:
    """Execute model training loop."""
    logger.info("Loading configuration from: %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    device = torch.device(
        "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    )
    logger.info("Using device: %s", device)

    # Initialize datasets
    data_root = Path(cfg["dataset"]["train"]).parents[1]
    train_dataset = SonarDataset(
        data_root / "train" / "images",
        data_root / "train" / "labels",
        data_root / "train" / "metadata",
        augment=True,
    )
    val_dataset = SonarDataset(
        data_root / "val" / "images",
        data_root / "val" / "labels",
        data_root / "val" / "metadata",
        augment=False,
    )

    batch_size = 2 if dry_run else cfg["hyperparameters"].get("batch_size", 8)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    num_classes = cfg["dataset"].get("num_classes", 6)
    model = SonarSentryFullModel(num_classes=num_classes).to(device)

    # Physics loss & optimizer
    phys_cfg = cfg.get("physics_loss", {})
    loss_fn = SADHPhysicsLoss(
        lambda_height=phys_cfg.get("lambda_height", 1.0),
        lambda_shadow=phys_cfg.get("lambda_shadow", 1.0),
        lambda_phys=phys_cfg.get("lambda_phys", 0.5),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["hyperparameters"]["lr0"]))
    ce_loss_fn = nn.CrossEntropyLoss()

    best_val_loss = float("inf")
    metrics_history = []

    logger.info("Starting training for %d epochs...", epochs)
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_accum = 0.0

        for batch in train_loader:
            imgs = batch["image"].to(device)
            labels = batch["class_label"].to(device)
            h_true = batch["h_true"].to(device)
            L_true = batch["L_true"].to(device)
            is_geo = batch["is_geology"].to(device)
            alt_m = batch["altitude_m"].to(device)
            range_m = batch["slant_range_m"].to(device)

            optimizer.zero_grad()
            preds = model(imgs)

            targets = {"h_true": h_true, "L_true": L_true, "is_geology": is_geo}
            meta = {"H_s": alt_m, "R_s": range_m}

            phys_losses = loss_fn(preds, targets, meta)
            cls_loss = ce_loss_fn(preds["class_logits"], labels)
            total_loss = cls_loss + phys_losses["total_physics_loss"]

            total_loss.backward()
            optimizer.step()
            train_loss_accum += total_loss.item()

            if dry_run:
                break

        avg_train_loss = train_loss_accum / max(1, len(train_loader))

        # Validation
        model.eval()
        val_loss_accum = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch in val_loader:
                imgs = batch["image"].to(device)
                labels = batch["class_label"].to(device)
                h_true = batch["h_true"].to(device)
                L_true = batch["L_true"].to(device)
                is_geo = batch["is_geology"].to(device)
                alt_m = batch["altitude_m"].to(device)
                range_m = batch["slant_range_m"].to(device)

                preds = model(imgs)
                targets = {"h_true": h_true, "L_true": L_true, "is_geology": is_geo}
                meta = {"H_s": alt_m, "R_s": range_m}

                phys_losses = loss_fn(preds, targets, meta)
                cls_loss = ce_loss_fn(preds["class_logits"], labels)
                v_loss = cls_loss + phys_losses["total_physics_loss"]
                val_loss_accum += v_loss.item()

                preds_cls = preds["class_logits"].argmax(dim=-1)
                val_correct += (preds_cls == labels).sum().item()
                val_total += labels.size(0)

                if dry_run:
                    break

        avg_val_loss = val_loss_accum / max(1, len(val_loader))
        val_acc = (val_correct / max(1, val_total)) * 100.0

        logger.info(
            "Epoch %d/%d - Train Loss: %.4f | Val Loss: %.4f | Val Accuracy: %.1f%%",
            epoch,
            epochs,
            avg_train_loss,
            avg_val_loss,
            val_acc,
        )

        metrics_history.append(
            {"epoch": epoch, "train_loss": avg_train_loss, "val_loss": avg_val_loss, "val_acc": val_acc}
        )

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            weights_dir = Path("weights")
            weights_dir.mkdir(exist_ok=True)
            torch.save(model.state_dict(), weights_dir / "best_werb_dgrm_sadh.pt")
            logger.info("Saved best model weights to weights/best_werb_dgrm_sadh.pt")

    logger.info("Training complete!")
    return {
        "status": "success",
        "best_val_loss": best_val_loss,
        "history": metrics_history,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sonar Sentry Training")
    parser.add_argument("--config", type=str, default="configs/train_config.yaml", help="Config file")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--dry-run", action="store_true", help="Perform single batch dry run")
    args = parser.parse_args()

    train_model(config_path=args.config, epochs=args.epochs, dry_run=args.dry_run)
