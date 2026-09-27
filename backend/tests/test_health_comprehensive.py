import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoints_basic(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "database" in data
    assert "preprocessing" in data

    # Test alias /health
    res_alias = client.get("/health")
    assert res_alias.status_code == 200


def test_health_detailed_endpoint(client: TestClient):
    res = client.get("/api/health/detailed")
    assert res.status_code == 200
    data = res.json()
    assert "system" in data["checks"]
    assert "dependencies" in data["checks"]
    assert "model" in data["checks"]
    assert "database" in data["checks"]
    assert "response_time_ms" in data


def test_health_ready_and_live(client: TestClient):
    res_ready = client.get("/api/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json() == {"status": "ready"}

    res_live = client.get("/api/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"


def test_health_db_error(client: TestClient):
    with patch("app.database.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception("DB down")
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["database"]["status"] == "error"

        # readiness should return 503 on db failure
        res_ready = client.get("/api/health/ready")
        assert res_ready.status_code == 503
