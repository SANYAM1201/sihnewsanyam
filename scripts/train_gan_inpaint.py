"""Train U-Net Generator for Sonar Acoustic Shadow Inpainting."""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports resolve
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from app.ml.gan_modules import InpaintUNetGenerator


class SonarShadowDataset(Dataset):
    def __init__(self, data_dir: str):
        self.input_dir = Path(data_dir) / "input"
        self.target_dir = Path(data_dir) / "target"
        self.files = [f.name for f in self.input_dir.glob("*.png")] if self.input_dir.is_dir() else []

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        fname = self.files[idx]
        in_img = cv2.imread(str(self.input_dir / fname))
        target_img = cv2.imread(str(self.target_dir / fname))

        in_img = cv2.resize(in_img, (256, 256))
        target_img = cv2.resize(target_img, (256, 256))

        # Approximate mask from difference
        diff = cv2.absdiff(in_img, target_img)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray_diff, 15, 255, cv2.THRESH_BINARY)
        mask = mask.astype(np.float32) / 255.0

        # Normalization to [-1, 1]
        in_tensor = torch.from_numpy(in_img).permute(2, 0, 1).float() / 127.5 - 1.0
        mask_tensor = torch.from_numpy(mask).unsqueeze(0).float()
        target_tensor = torch.from_numpy(target_img).permute(2, 0, 1).float() / 127.5 - 1.0

        # Concatenate RGB + Mask = 4 channels
        in_4ch = torch.cat([in_tensor, mask_tensor], dim=0)
        return in_4ch, target_tensor


def train(epochs: int = 5, batch_size: int = 4, lr: float = 0.0002):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Starting GAN Shadow Inpainter training on {device}...")

    dataset_path = "datasets/shadow_gan/train"
    dataset = SonarShadowDataset(dataset_path)

    if len(dataset) == 0:
        print("Dataset not found or empty. Generating synthetic training pairs first...")
        from generate_shadow_dataset import generate_synthetic_shadows
        generate_synthetic_shadows()
        dataset = SonarShadowDataset(dataset_path)

    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    generator = InpaintUNetGenerator(in_channels=4, out_channels=3).to(device)
    criterion = nn.L1Loss()
    optimizer = torch.optim.Adam(generator.parameters(), lr=lr, betas=(0.5, 0.999))

    save_dir = Path("models")
    save_dir.mkdir(exist_ok=True)

    for epoch in range(1, epochs + 1):
        generator.train()
        total_loss = 0.0
        for in_data, target in dataloader:
            in_data = in_data.to(device)
            target = target.to(device)

            optimizer.zero_grad()
            fake = generator(in_data)
            loss = criterion(fake, target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(dataloader))
        print(f"Epoch [{epoch}/{epochs}] — Generator L1 Reconstruction Loss: {avg_loss:.4f}")

    final_path = save_dir / "gan_shadow_inpaint.pth"
    torch.save(generator.state_dict(), str(final_path))
    print(f"Model saved successfully to {final_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size)
