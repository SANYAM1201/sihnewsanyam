"""A/B Testing API Endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.services.ab_testing import get_variant, list_tests

router = APIRouter(prefix="/api/ab", tags=["ab_testing"])


@router.get("")
@router.get("/")
@router.get("/tests")
async def all_tests() -> dict[str, Any]:
    return list_tests()


@router.get("/tests/{test}/variant")
@router.get("/{test}")
async def variant(test: str, session_id: str = "anon") -> dict[str, str | None]:
    return {"experiment": test, "test": test, "variant": get_variant(test, session_id)}

