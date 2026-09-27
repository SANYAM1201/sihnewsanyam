"""Generate test synthetic images for testing."""

import os
import cv2
import numpy as np


def generate_test_images(output_dir: str = "backend/tests/data") -> None:
    os.makedirs(output_dir, exist_ok=True)
    for i in range(5):
        img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        cv2.imwrite(f"{output_dir}/test_{i}.png", img)
        print(f"✅ Generated {output_dir}/test_{i}.png")

    with open(f"{output_dir}/corrupt.png", "wb") as f:
        f.write(b"\x00\x01\x02\x03")
    print(f"✅ Generated {output_dir}/corrupt.png (for error testing)")


if __name__ == "__main__":
    generate_test_images()
