import pytest
from fastapi.testclient import TestClient

from app.database import get_session, init_db
from app.main import app
from app.services.export_service import ExportService


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_export_csv(client: TestClient):
    response = client.get("/api/export/detections/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "id,detection_id" in response.text


def test_export_json(client: TestClient):
    response = client.get("/api/export/detections/json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_export_service_methods():
    db = get_session()
    try:
        svc = ExportService(db)
        csv_out = svc.to_csv()
        assert "detection_id" in csv_out
        json_out = svc.to_json()
        assert isinstance(json_out, str)
    finally:
        db.close()

