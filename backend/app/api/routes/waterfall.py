"""WebSocket streaming route for real-time hydrographic sonar waterfall."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.services.xtf_parser import parse_xtf_bytes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waterfall"])


class ConnectionManager:
    """Manages active WebSocket connections for live waterfall streaming."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. Total clients: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected = []
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning("Failed to send to client: %s", e)
                    disconnected.append(connection)
            else:
                disconnected.append(connection)

        for dead in disconnected:
            self.disconnect(dead)


manager = ConnectionManager()


@router.websocket("/ws/waterfall")
@router.websocket("/api/waterfall")
async def websocket_waterfall(websocket: WebSocket) -> None:
    """Live vessel acoustic streaming endpoint.

    Accepts XTF binary chunks or ping JSON messages from surveying vessels
    and broadcasts waterfall slices and real-time bounding box detections to clients.
    """
    await manager.connect(websocket)

    # Send initial welcome / handshake ping
    await websocket.send_json(
        {
            "type": "status",
            "status": "connected",
            "message": "Connected to Sonar Sentry Live Acoustic Stream",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    try:
        while True:
            # Handle text or binary messages
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                try:
                    waterfall_np, xtf_meta = parse_xtf_bytes(raw_bytes)
                    for i in range(len(waterfall_np)):
                        ping_chunk = waterfall_np[i].tolist()
                        await manager.broadcast(
                            {
                                "type": "ping",
                                "ping_number": i + 1,
                                "waterfall_chunk": ping_chunk,
                                "detections": [],
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                except Exception as e:
                    logger.debug("Raw chunk decode notice: %s", e)
            elif "text" in message and message["text"]:
                payload = json.loads(message["text"])
                # Echo / broadcast parsed vessel ping
                await manager.broadcast(
                    {
                        "type": "ping",
                        "ping_number": payload.get("ping_number", 0),
                        "waterfall_chunk": payload.get("waterfall_chunk", []),
                        "detections": payload.get("detections", []),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket handler ended: %s", exc)
        manager.disconnect(websocket)
