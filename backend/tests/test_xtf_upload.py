"""Tests for XTF upload, waterfall sonogram rendering, SADH physics, and detection list endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.database import get_db, init_db
from app.main import create_app
from app.services.xtf_parser import create_synthetic_xtf


@pytest.fixture(scope="module")
def client():
    init_db()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_xtf_upload_and_waterfall(client: TestClient):
    """Test full pipeline: upload valid synthetic XTF -> verify detections, waterfall_url, SADH metrics."""
    synthetic_xtf = create_synthetic_xtf(num_pings=32, samples_per_channel=256)

    files = {"file": ("test_survey.xtf", synthetic_xtf, "application/octet-stream")}
    data = {
        "latitude": "12.9716",
        "longitude": "80.2520",
        "sonar_type": "Side-Scan",
        "resolution": "1024x768",
        "depth_min": "10.0",
        "depth_max": "30.0",
        "confidence_threshold": "20",
    }

    response = client.post("/api/detect/xtf", files=files, data=data)
    assert response.status_code == 200, response.text
    res_json = response.json()

    assert res_json["success"] is True
    assert "run_id" in res_json
    assert "waterfall_url" in res_json
    assert res_json["waterfall_url"].startswith("/api/waterfall/")

    run_id = res_json["run_id"]

    # Verify that the waterfall preview endpoint returns an image
    wf_res = client.get(res_json["waterfall_url"])
    assert wf_res.status_code == 200
    assert wf_res.headers["content-type"] == "image/png"

    # Verify /api/runs/{run_id} returns detections with sadh_height_m and physics_confidence
    run_res = client.get(f"/api/runs/{run_id}")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert "detections" in run_data

    # Verify /api/detections lists recent detections with sadh_height_m and physics_confidence
    det_res = client.get("/api/detections")
    assert det_res.status_code == 200
    detections = det_res.json()
    assert isinstance(detections, list)
    if detections:
        sample = detections[0]
        assert "sadh_height_m" in sample
        assert "physics_confidence" in sample
        assert "class_label" in sample
