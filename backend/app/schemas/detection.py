from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    flagged = "flagged"
    reviewed = "reviewed"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class BoundingBox(BaseModel):
    x: float = Field(..., description="Left edge x coordinate")
    y: float = Field(..., description="Top edge y coordinate")
    width: float = Field(..., description="Bounding box width")
    height: float = Field(..., description="Bounding box height")


class DetectionItem(BaseModel):
    detection_id: str
    class_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    bbox: BoundingBox | None = None
    depth_m: float | None = None
    area_m2: float | None = None
    position_info: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    sadh_height_m: float | None = None
    physics_confidence: float | None = None


class DetectionSummary(BaseModel):
    total: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
    critical_risk: int = 0
    avg_confidence: float = 0.0


class ScanMetadata(BaseModel):
    filename: str
    file_size_bytes: int = 0
    latitude: float | None = None
    longitude: float | None = None
    sonar_type: str | None = None
    resolution: str | None = None
    depth_min: float | None = None
    depth_max: float | None = None


class Timestamps(BaseModel):
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None


class DetectResponse(BaseModel):
    success: bool = True
    run_id: str
    mission_id: str
    status: ProcessingStatus
    scan_metadata: ScanMetadata
    detection_summary: DetectionSummary
    detections: list[DetectionItem] = []
    model: ModelInfo | None = None
    timestamps: Timestamps | None = None


class ModelInfo(BaseModel):
    name: str
    version: str
    provider: str
