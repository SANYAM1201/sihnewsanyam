import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ab_testing import get_config, record, list_tests, get_variant


@pytest.fixture
def client():
    return TestClient(app)


def test_list_ab_tests_endpoint(client: TestClient):
    response = client.get("/api/ab/tests")
    assert response.status_code == 200
    data = response.json()
    assert "detection_model" in data
    assert "dsp_pipeline" in data


def test_get_ab_variant_endpoint(client: TestClient):
    response = client.get("/api/ab/tests/detection_model/variant?session_id=user123")
    assert response.status_code == 200
    data = response.json()
    assert data["test"] == "detection_model"
    assert data["variant"] in ["default", "400khz"]


def test_ab_testing_service_get_config():
    cfg = get_config("dsp_pipeline", session_id="test_sess")
    assert cfg is not None
    assert "bac" in cfg


def test_ab_testing_record():
    record("detection_model", "default", {"latency_ms": 42.0})
