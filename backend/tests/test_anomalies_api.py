import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_get_anomalies_not_found(client: TestClient):
    with patch("app.api.routes.anomalies._candidate_paths", return_value=[]):
        res = client.get("/api/anomalies")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "error"
        assert data["message"] == "Report not found."


def test_get_anomalies_json(client: TestClient, tmp_path: Path):
    json_file = tmp_path / "anomaly_report.json"
    json_file.write_text(json.dumps([{"id": "anomaly_1", "type": "debris"}]), encoding="utf-8")

    with patch("app.api.routes.anomalies._candidate_paths", return_value=[json_file]):
        res = client.get("/api/get_anomalies")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["data"] == [{"id": "anomaly_1", "type": "debris"}]


def test_get_anomalies_csv(client: TestClient, tmp_path: Path):
    csv_file = tmp_path / "anomaly_report.csv"
    csv_file.write_text("id,type\nanomaly_2,mine\n", encoding="utf-8")

    with patch("app.api.routes.anomalies._candidate_paths", return_value=[csv_file]):
        res = client.get("/api/anomalies")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "anomaly_2"
