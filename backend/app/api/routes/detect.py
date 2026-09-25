from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.exceptions import (
    FileTooLargeError,
    InferenceFailedError,
    InvalidFileTypeError,
    InvalidMetadataError,
    ModelUnavailableError,
    NoFileError,
    PreprocessingFailedError,
)
from app.config import Settings, get_settings
from app.database import get_db
from app.repositories.detection_repository import DetectionRepository
from app.repositories.run_repository import RunRepository
from app.schemas.detection import (
    DetectResponse,
    DetectionItem,
    DetectionSummary,
    ProcessingStatus,
    ScanMetadata,
    Timestamps,
)
from app.services.georeference import with_detection_coordinates
from app.services.inference_service import InferenceService
from app.services.report_service import ReportService
from app.services.result_normalizer import ResultNormalizer
from app.services.storage_service import StorageService

router = APIRouter(tags=["detect"])

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG"
_TIFF_MAGIC = b"II\x2a\x00"
_TIFF_MAGIC_BE = b"MM\x00\x2a"
_ALLOWED_MIMES = {"image/jpeg", "image/png", "image/tiff"}


def _has_valid_signature(data: bytes, content_type: str) -> bool:
    if content_type == "image/jpeg":
        return data[:3] == _JPEG_MAGIC
    if content_type == "image/png":
        return data[:4] == _PNG_MAGIC
    if content_type == "image/tiff":
        return data[:4] == _TIFF_MAGIC or data[:4] == _TIFF_MAGIC_BE
    return False


@router.post("/api/detect", response_model=DetectResponse)
async def detect(
    request: Request,
    file: UploadFile | None = File(default=None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    sonar_type: str = Form(...),
    resolution: str = Form(...),
    depth_min: float = Form(...),
    depth_max: float = Form(...),
    confidence_threshold: int = Form(default=50),
    selected_classes: str = Form(default=""),
    min_object_size: int = Form(default=10),
    db: Session = Depends(get_db),
) -> DetectResponse:
    inference_service: InferenceService = request.app.state.inference_service
    settings: Settings = get_settings()
    started_at = datetime.now(timezone.utc)

    if file is None:
        raise NoFileError()

    contents = await file.read()
    if len(contents) == 0:
        raise NoFileError()

    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_MIMES:
        if contents[:4] == _PNG_MAGIC:
            content_type = "image/png"
        elif contents[:3] == _JPEG_MAGIC:
            content_type = "image/jpeg"
        elif contents[:4] in {_TIFF_MAGIC, _TIFF_MAGIC_BE}:
            content_type = "image/tiff"
    if content_type not in _ALLOWED_MIMES:
        raise InvalidFileTypeError()

    if len(contents) > settings.max_file_size_mb * 1024 * 1024:
        raise FileTooLargeError()

    if not _has_valid_signature(contents, content_type):
        raise InvalidFileTypeError()

    if depth_min >= depth_max:
        raise InvalidMetadataError("depth_min must be less than depth_max")

    if sonar_type not in settings.allowed_sonar_types:
        raise InvalidMetadataError(
            f"Invalid sonar_type. Allowed: {', '.join(settings.allowed_sonar_types)}"
        )

    if resolution not in settings.allowed_resolutions:
        raise InvalidMetadataError(
            f"Invalid resolution. Allowed: {', '.join(settings.allowed_resolutions)}"
        )

    if not inference_service.is_model_loaded:
        raise ModelUnavailableError()

    storage = StorageService()
    stored_path = storage.save_upload(contents, file.filename or "unknown")

    run_repo = RunRepository(db)
    det_repo = DetectionRepository(db)

    run = run_repo.create(
        mission_id=f"MSN-{uuid.uuid4().hex[:4].upper()}",
        filename=file.filename or "unknown",
        file_path=str(stored_path),
        file_size_bytes=len(contents),
        status="processing",
        latitude=latitude,
        longitude=longitude,
        sonar_type=sonar_type,
        resolution=resolution,
        depth_min=depth_min,
        depth_max=depth_max,
    )

    try:
        prediction_result = inference_service.predict(contents)
    except Exception:
        run_repo.update(run.id, status="failed", error_message="Inference failed")
        raise InferenceFailedError()

    normalizer = ResultNormalizer()
    detections, summary = normalizer.normalize(prediction_result)
    detections, summary = _apply_detection_filters(
        detections,
        confidence_threshold=confidence_threshold,
        selected_classes=selected_classes,
        min_object_size=min_object_size,
        normalizer=normalizer,
    )
    detections = [
        with_detection_coordinates(item, latitude, longitude, resolution)
        for item in detections
    ]
    summary = normalizer._build_summary(detections)

    model_meta = inference_service.metadata()
    completed_at = datetime.now(timezone.utc)
    duration = (completed_at - started_at).total_seconds()

    detection_dicts = [
        {
            "run_id": run.id,
            "class_label": d.class_label,
            "confidence": d.confidence,
            "risk_level": d.risk_level.value,
            "bbox_x": d.bbox.x if d.bbox else None,
            "bbox_y": d.bbox.y if d.bbox else None,
            "bbox_width": d.bbox.width if d.bbox else None,
            "bbox_height": d.bbox.height if d.bbox else None,
            "depth_m": d.depth_m,
            "area_m2": d.area_m2,
            "position_info": d.position_info,
            "latitude": d.latitude,
            "longitude": d.longitude,
        }
        for d in detections
    ]
    det_repo.create_many(detection_dicts)

    run_repo.update(
        run.id,
        status="completed",
        detection_count=summary.total,
        avg_confidence=summary.avg_confidence,
        model_name=model_meta.name,
        model_version=model_meta.version,
        model_provider=model_meta.provider,
    )

    try:
        report_service = ReportService(db)
        scan_date = started_at.strftime("%d %b %Y")
        mission_name = f"{sonar_type} Survey — {file.filename or 'unknown'}"
        report_service.create_report(
            run_id=run.id,
            mission_id=run.mission_id,
            mission_name=mission_name,
            filename=file.filename or "unknown",
            scan_date=scan_date,
            detections=detections,
            summary=summary,
            latitude=latitude,
            longitude=longitude,
            sonar_type=sonar_type,
            resolution=resolution,
            depth_min=depth_min,
            depth_max=depth_max,
            model_name=model_meta.name,
            model_version=model_meta.version,
        )
    except Exception as e:
        logger.warning("Failed to create initial report: %s", e)

    return DetectResponse(
        run_id=run.id,
        mission_id=run.mission_id,
        status=ProcessingStatus.completed,
        scan_metadata=ScanMetadata(
            filename=file.filename or "unknown",
            file_size_bytes=len(contents),
            latitude=latitude,
            longitude=longitude,
            sonar_type=sonar_type,
            resolution=resolution,
            depth_min=depth_min,
            depth_max=depth_max,
        ),
        detection_summary=summary,
        detections=detections,
        model={
            "name": model_meta.name,
            "version": model_meta.version,
            "provider": model_meta.provider,
        },
        timestamps=Timestamps(
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_seconds=round(duration, 3),
        ),
    )


_CLASS_GROUPS = {
    "debris": {
        "debris",
        "marine debris",
        "fishing net",
        "container",
        "plastic",
        "plastic bag",
        "metal fragment",
        "metal scrap",
        "metal drum",
        "tyre",
        "tire",
        "pipe",
        "bottle",
        "can",
        "cylinder",
        "net",
    },
    "shipwreck": {"shipwreck", "aircraft"},
    "rocks": {"rock", "rock formation", "rocks"},
}


def _label_matches(label: str, selected: list[str]) -> bool:
    if not selected:
        return True
    lowered = label.lower()
    allow_other = any(s.lower() == "other" for s in selected)
    matched_group = False
    for name in selected:
        key = name.lower()
        group = _CLASS_GROUPS.get(key)
        if group is None:
            if key in lowered or lowered in key:
                return True
            continue
        if any(token in lowered for token in group):
            return True
        matched_group = True
    if allow_other and not any(
        token in lowered for tokens in _CLASS_GROUPS.values() for token in tokens
    ):
        return True
    return False if matched_group or allow_other else True


def _apply_detection_filters(
    detections: list[DetectionItem],
    confidence_threshold: int,
    selected_classes: str,
    min_object_size: int,
    normalizer: ResultNormalizer,
) -> tuple[list[DetectionItem], DetectionSummary]:
    threshold = max(0, min(int(confidence_threshold), 100))
    classes = [c.strip() for c in selected_classes.split(",") if c.strip()]
    filtered: list[DetectionItem] = []
    for item in detections:
        if round(item.confidence * 100) < threshold:
            continue
        if not _label_matches(item.class_label, classes):
            continue
        size = 0.0
        if item.bbox is not None:
            size = max(item.bbox.width, item.bbox.height)
        if size and size < min_object_size:
            continue
        filtered.append(item)
    return filtered, normalizer._build_summary(filtered)
