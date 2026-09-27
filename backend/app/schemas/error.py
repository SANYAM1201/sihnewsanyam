"""Structured Error Schemas for API Error Responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error classification code")
    message: str = Field(..., description="Human readable description of the error")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional contextual details")


class ErrorResponse(BaseModel):
    error: ErrorDetail
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
