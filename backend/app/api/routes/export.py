"""Data Export API Endpoints."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/detections/csv")
async def export_csv(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    csv_str = ExportService(db).to_csv(run_id, limit, offset)
    return StreamingResponse(
        iter([csv_str]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=detections.csv"},
    )


@router.get("/detections/json")
async def export_json(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    json_str = ExportService(db).to_json(run_id, limit, offset)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=detections.json"},
    )


@router.get("/runs/{run_id}/report")
async def run_report(
    run_id: str,
    fmt: str = "json",
    db: Session = Depends(get_db),
) -> dict:
    try:
        svc = ExportService(db)
        report = svc.run_report(run_id)
        if fmt == "json":
            return report
        raise HTTPException(400, "Only 'json' format currently supported")
    except ValueError as e:
        raise HTTPException(404, str(e))

