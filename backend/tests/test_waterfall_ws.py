import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.waterfall import ConnectionManager


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_websocket_waterfall_json_message(client: TestClient):
    with client.websocket_connect("/ws/waterfall") as websocket:
        # Check initial handshake message
        handshake = websocket.receive_json()
        assert handshake["type"] == "status"
        assert handshake["status"] == "connected"

        # Send text json ping
        msg = {
            "ping_number": 42,
            "waterfall_chunk": [10, 20, 30],
            "detections": []
        }
        websocket.send_text(json.dumps(msg))

        # Receive broadcast ping
        broadcast = websocket.receive_json()
        assert broadcast["type"] == "ping"
        assert broadcast["ping_number"] == 42
        assert broadcast["waterfall_chunk"] == [10, 20, 30]


def test_websocket_waterfall_bytes_message(client: TestClient):
    with client.websocket_connect("/ws/waterfall") as websocket:
        _ = websocket.receive_json()
        # Send raw invalid bytes (should catch gracefully without disconnecting)
        websocket.send_bytes(b"non_xtf_test_data")
