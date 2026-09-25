"""Tests for Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app


def test_metrics_endpoint_returns_prometheus_format():
    with TestClient(app) as client:
        # Generate some traffic
        client.get("/api/health")

        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        text = resp.text
        assert "sonar_requests_total" in text
        assert "sonar_request_duration_seconds" in text
