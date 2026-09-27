"""Models Management API Endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException

from app.services.model_manager import model_manager

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
@router.get("/")
async def list_models() -> dict[str, Any]:
    return model_manager.list()



@router.post("/{name}/reload")
async def reload_model(name: str) -> dict[str, str]:
    if not model_manager.reload(name):
        raise HTTPException(404, f"Model '{name}' not found or reload failed")
    return {"status": "reloaded", "model": name}
