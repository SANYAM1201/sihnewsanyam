"""End-to-End integration test suite for Sonar Sentry."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.database import init_db
from app.main import create_app
from app.services.xtf_parser import create_synthetic_xtf


@pytest.fixture(scope="module")
def client():
    init_db()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_complete_sonar_pipeline(client: TestClient):
    # 1. Health check
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # 2. Upload test PNG sonar scan
    img = Image.new("RGB", (640, 640), color=(128, 128, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    upload_res = client.post(
        "/api/detect",
        files={"file": ("mission_scan_01.png", img_bytes, "image/png")},
        data={
            "latitude": "13.0628",
            "longitude": "80.3582",
            "sonar_type": "Side-Scan",
            "resolution": "0.5 m/px",
            "depth_min": "4.0",
            "depth_max": "38.0",
            "confidence_threshold": "20",
        },
    )
    assert upload_res.status_code == 200, upload_res.text
    run_id = upload_res.json()["run_id"]
    assert run_id

    # 3. Retrieve run and verify SADH fields
    run_res = client.get(f"/api/runs/{run_id}")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["run_id"] == run_id

    # 4. Upload Triton XTF file
    xtf_bytes = create_synthetic_xtf(num_pings=32, samples_per_channel=256)
    xtf_res = client.post(
        "/api/detect/xtf",
        files={"file": ("survey_track.xtf", xtf_bytes, "application/octet-stream")},
        data={
            "latitude": "12.9716",
            "longitude": "80.2520",
            "sonar_type": "SSS-Dual",
            "resolution": "1024x768",
            "depth_min": "5.0",
            "depth_max": "25.0",
            "confidence_threshold": "15",
        },
    )
    assert xtf_res.status_code == 200
    xtf_json = xtf_res.json()
    assert xtf_json["waterfall_url"].startswith("/api/waterfall/")

    # 5. Fetch rendered waterfall sonogram
    waterfall_res = client.get(xtf_json["waterfall_url"])
    assert waterfall_res.status_code == 200
    assert waterfall_res.headers["content-type"] == "image/png"

    # 6. Check detections endpoint
    det_res = client.get("/api/detections")
    assert det_res.status_code == 200
    assert isinstance(det_res.json(), list)

    # 7. WebSocket handshake
    with client.websocket_connect("/ws/waterfall") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "status"
        assert msg["status"] == "connected"
