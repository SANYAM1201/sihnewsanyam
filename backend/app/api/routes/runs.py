from __future__ import annotations

import logging
import math
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.exceptions import ReportNotFoundError, RunNotFoundError
from app.database import get_db
from app.repositories.detection_repository import DetectionRepository
from app.repositories.run_repository import RunRepository
from app.schemas.detection import (
    BoundingBox,
    DetectionItem,
    DetectionSummary,
    RiskLevel,
    ScanMetadata,
    Timestamps,
)
from app.schemas.run import PaginationMeta, RunDetail, RunListResponse, RunSummary
from app.schemas.report import ReportInstanceCreate
from app.services.georeference import with_detection_coordinates
from app.services.report_service import ReportService

router = APIRouter(tags=["runs"])


def _detection_item(run, detection) -> DetectionItem:
    bbox = (
        BoundingBox(
            x=detection.bbox_x,
            y=detection.bbox_y,
            width=detection.bbox_width,
            height=detection.bbox_height,
        )
        if detection.bbox_x is not None
        else None
    )
    item = DetectionItem(
        detection_id=detection.id,
        class_label=detection.class_label,
        confidence=detection.confidence,
        risk_level=RiskLevel(detection.risk_level),
        bbox=bbox,
        depth_m=detection.depth_m,
        area_m2=detection.area_m2,
        position_info=detection.position_info,
        sadh_height_m=detection.sadh_height_m,
        physics_confidence=detection.physics_confidence,
    )
    return with_detection_coordinates(
        item,
        run.latitude,
        run.longitude,
        run.resolution,
    )



@router.get("/api/runs", response_model=RunListResponse)
def list_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RunListResponse:
    repo = RunRepository(db)
    items, total = repo.list(page=page, page_size=page_size, status=status)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    run_items = [
        RunSummary(
            run_id=r.id,
            mission_id=r.mission_id,
            filename=r.filename,
            status=r.status,
            detection_count=r.detection_count,
            file_size_bytes=r.file_size_bytes,
            latitude=r.latitude,
            longitude=r.longitude,
            created_at=r.created_at.isoformat() if r.created_at else "",
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        )
        for r in items
    ]

    return RunListResponse(
        items=run_items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/api/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict:
    repo = RunRepository(db)
    run = repo.get(run_id)
    if run is None:
        raise RunNotFoundError()

    det_repo = DetectionRepository(db)
    orm_detections = det_repo.list_by_run(run_id)

    detections = [_detection_item(run, d) for d in orm_detections]

    high_risk = sum(1 for d in detections if d.risk_level in (RiskLevel.high, RiskLevel.critical))
    medium_risk = sum(1 for d in detections if d.risk_level == RiskLevel.medium)
    low_risk = sum(1 for d in detections if d.risk_level == RiskLevel.low)
    avg_conf = (
        round(sum(d.confidence for d in detections) / len(detections), 4)
        if detections
        else 0.0
    )

    return {
        "run_id": run.id,
        "mission_id": run.mission_id,
        "filename": run.filename,
        "file_size_bytes": run.file_size_bytes,
        "status": run.status,
        "scan_metadata": ScanMetadata(
            filename=run.filename,
            file_size_bytes=run.file_size_bytes,
            latitude=run.latitude,
            longitude=run.longitude,
            sonar_type=run.sonar_type,
            resolution=run.resolution,
            depth_min=run.depth_min,
            depth_max=run.depth_max,
        ),
        "detection_summary": DetectionSummary(
            total=len(detections),
            high_risk=high_risk,
            medium_risk=medium_risk,
            low_risk=low_risk,
            avg_confidence=avg_conf,
        ),
        "detections": detections,
        "model": {
            "name": run.model_name,
            "version": run.model_version,
            "provider": run.model_provider,
        },
        "created_at": run.created_at.isoformat() if run.created_at else "",
        "updated_at": run.updated_at.isoformat() if run.updated_at else "",
    }


@router.get("/api/runs/{run_id}/file")
def get_run_file(run_id: str, db: Session = Depends(get_db)) -> FileResponse:
    repo = RunRepository(db)
    run = repo.get(run_id)
    if run is None:
        raise RunNotFoundError()
    path = Path(run.file_path)
    if not path.is_file():
        raise RunNotFoundError()

    # If it is a Triton XTF file, serve the rendered PNG waterfall preview
    # so standard web browsers and <img> tags render the sonogram immediately
    if path.suffix.lower() == ".xtf":
        waterfall_path = path.with_name(f"{path.stem}_waterfall.png")
        if waterfall_path.is_file():
            return FileResponse(
                waterfall_path,
                filename=f"{path.stem}_waterfall.png",
                media_type="image/png",
                content_disposition_type="inline",
            )
        try:
            import cv2
            from app.services.xtf_parser import parse_xtf_bytes
            waterfall_np, _ = parse_xtf_bytes(path.read_bytes())
            success, png_bytes = cv2.imencode(".png", waterfall_np)
            if success:
                waterfall_path.write_bytes(png_bytes.tobytes())
                return FileResponse(
                    waterfall_path,
                    filename=f"{path.stem}_waterfall.png",
                    media_type="image/png",
                    content_disposition_type="inline",
                )
        except Exception as exc:
            logger.debug("Failed serving waterfall annotated file: %s", exc)

    media = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(
        path,
        filename=run.filename,
        media_type=media,
        content_disposition_type="inline",
    )


@router.get("/api/waterfall/{run_id}")
def get_waterfall(run_id: str, db: Session = Depends(get_db)) -> FileResponse:
    return get_run_file(run_id, db)


@router.get("/api/detections")
def get_all_detections(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    det_repo = DetectionRepository(db)
    detections = det_repo.list_all(limit=limit)
    return [
        {
            "id": d.id,
            "detection_id": d.id,
            "run_id": d.run_id,
            "class_label": d.class_label,
            "confidence": d.confidence,
            "risk_level": d.risk_level,
            "bbox": {
                "x": d.bbox_x,
                "y": d.bbox_y,
                "width": d.bbox_width,
                "height": d.bbox_height,
            }
            if d.bbox_x is not None
            else None,
            "depth_m": d.depth_m,
            "area_m2": d.area_m2,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "sadh_height_m": d.sadh_height_m,
            "physics_confidence": d.physics_confidence,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in detections
    ]



@router.get("/api/map/points")
def list_map_points(
    page_size: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    run_repo = RunRepository(db)
    det_repo = DetectionRepository(db)
    runs, _total = run_repo.list(page=1, page_size=page_size)
    items = []
    for run in runs:
        for detection in det_repo.list_by_run(run.id):
            item = _detection_item(run, detection)
            if item.latitude is None or item.longitude is None:
                continue
            items.append(
                {
                    "id": item.detection_id,
                    "run_id": run.id,
                    "mission_id": run.mission_id,
                    "filename": run.filename,
                    "class_label": item.class_label,
                    "confidence": item.confidence,
                    "risk_level": item.risk_level.value,
                    "latitude": item.latitude,
                    "longitude": item.longitude,
                    "depth_m": item.depth_m,
                    "image_url": getattr(detection, "image_url", None),
                    "mask_url": getattr(detection, "mask_url", None),
                }
            )
    return {"items": items}


@router.post("/api/runs/{run_id}/instances")
def create_run_instance(
    run_id: str,
    payload: ReportInstanceCreate,
    db: Session = Depends(get_db),
) -> dict:
    run = RunRepository(db).get(run_id)
    if run is None:
        raise RunNotFoundError()
    try:
        item = ReportService(db).create_threshold_instance(
            run_id, payload.confidence_threshold
        )
    except ValueError:
        raise ReportNotFoundError()
    return item.model_dump()


@router.delete("/api/runs/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)) -> Response:
    deleted = ReportService(db).delete_run(run_id)
    if not deleted:
        raise RunNotFoundError()
    return Response(status_code=204)
