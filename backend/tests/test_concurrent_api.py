"""Concurrency tests for Sonar Sentry API endpoints."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


def _generate_valid_png_bytes(color_val: int) -> bytes:
    img = Image.new("RGB", (128, 128), color=(color_val, color_val, color_val))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


class TestConcurrency:
    def test_concurrent_health_requests(self):
        """Verify that health check handles 20 concurrent requests without race conditions."""
        with TestClient(app) as client:
            def make_health_request(idx: int):
                resp = client.get("/api/health")
                return resp.status_code, resp.json()

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_health_request, i) for i in range(20)]
                for future in as_completed(futures):
                    status_code, data = future.result()
                    assert status_code == 200
                    assert data["status"] == "ok"
                    assert "preprocessing" in data

    def test_concurrent_detect_requests(self):
        """Verify that concurrent /api/detect requests execute safely with independent state."""
        with TestClient(app) as client:
            def make_detect_request(idx: int):
                img_bytes = _generate_valid_png_bytes(50 + idx * 10)
                resp = client.post(
                    "/api/detect",
                    files={"file": (f"test_{idx}.png", img_bytes, "image/png")},
                    data={
                        "latitude": "12.9716",
                        "longitude": "80.2436",
                        "sonar_type": "Side-Scan",
                        "resolution": "0.5 m/px",
                        "depth_min": "4",
                        "depth_max": "38",
                    },
                )
                return resp.status_code, resp.json()

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(make_detect_request, i) for i in range(8)]
                for future in as_completed(futures):
                    status_code, body = future.result()
                    assert status_code == 200
                    assert body["success"] is True
                    assert body["status"] == "completed"
                    assert "run_id" in body
                    assert len(body["run_id"]) > 0


if __name__ == "__main__":
    t = TestConcurrency()
    t.test_concurrent_health_requests()
    t.test_concurrent_detect_requests()
    print("✅ Concurrent requests handled successfully")

