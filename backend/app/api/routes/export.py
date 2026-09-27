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
@router.get("/csv")
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


@router.get("/geojson")
@router.get("/runs/{run_id}/geojson")
async def export_geojson(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict:
    return ExportService(db).to_geojson(run_id, limit, offset)


@router.get("/dossier")
@router.get("/runs/{run_id}/dossier")
async def export_dossier(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from pathlib import Path
    pdf_path = ExportService(db).generate_dossier_pdf(run_id)
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        raise HTTPException(500, "Failed to generate Naval Dossier PDF")

    def iter_file():
        with open(path_obj, "rb") as f:
            yield from f

    return StreamingResponse(
        iter_file(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={path_obj.name}"},
    )


@router.get("/detection/{detection_id}")
async def export_single_detection(
    detection_id: str,
    db: Session = Depends(get_db),
) -> dict:
    from app.models.orm import Detection
    det = db.query(Detection).filter(Detection.id == detection_id).first()
    if not det:
        raise HTTPException(404, f"Detection {detection_id} not found")
    return {
        "id": det.id,
        "run_id": det.run_id,
        "class_label": det.class_label,
        "confidence": det.confidence,
        "risk_level": det.risk_level,
        "bbox": {
            "x": det.bbox_x,
            "y": det.bbox_y,
            "width": det.bbox_width,
            "height": det.bbox_height,
        },
        "georeference": {
            "latitude": det.latitude,
            "longitude": det.longitude,
            "position_info": det.position_info,
        },
        "physics": {
            "sadh_height_m": det.sadh_height_m,
            "physics_confidence": det.physics_confidence,
            "verified": (det.physics_confidence or 1.0) >= 0.6,
        },
        "created_at": str(det.created_at),
    }


@router.get("/swath")
@router.get("/runs/{run_id}/swath")
async def export_swath(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    from app.models.orm import Run
    from app.services.geospatial.geotiff_service import GeoTIFFService
    import numpy as np

    run = db.query(Run).filter(Run.id == run_id).first() if run_id else db.query(Run).first()
    origin_lat = (run.latitude if run and run.latitude else 18.921984)
    origin_lon = (run.longitude if run and run.longitude else 72.834654)

    svc = GeoTIFFService()
    # Generate swath mosaic
    synthetic_waterfall = np.random.randint(60, 200, (400, 800, 3), dtype=np.uint8)
    res = svc.generate_swath_geotiff(
        synthetic_waterfall,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        heading=45.0,
        swath_width_m=100.0,
        output_filename=f"swath_{run.id if run else 'active'}.tif"
    )
    return res


