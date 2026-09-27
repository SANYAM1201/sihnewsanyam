import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_manager import model_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_list_models(client: TestClient):
    response = client.get("/api/models/")
    assert response.status_code == 200
    data = response.json()
    assert "default" in data
    assert "loaded" in data["default"]


def test_reload_model_success(client: TestClient):
    response = client.post("/api/models/default/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reloaded"


def test_reload_model_not_found(client: TestClient):
    response = client.post("/api/models/nonexistent_model/reload")
    assert response.status_code == 404
