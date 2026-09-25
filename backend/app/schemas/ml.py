from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PreprocessedInput:
    """Framework-independent container for preprocessed data.

    The ``data`` payload can hold any representation the downstream model
    requires (NumPy array, Torch tensor, raw list, etc.).  The rest of the
    application only interacts with this wrapper and never inspects ``data``
    directly.
    """

    data: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BBox:
    """Bounding box in pixel coordinates."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Detection:
    """A single detection from the model.

    Fields are optional because different model types (classification,
    object detection, segmentation) may not produce all of them.
    """

    class_label: str
    confidence: float
    bbox: BBox | None = None
    depth_m: float | None = None
    area_m2: float | None = None
    position_info: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PredictionResult:
    """Standardised prediction output returned by every ``ModelService``."""

    label: str
    confidence: float
    raw_scores: dict[str, float] = field(default_factory=dict)
    detections: list[Detection] = field(default_factory=list)


@dataclass(frozen=True)
class ModelMetadata:
    """Standardised metadata about a loaded model."""

    name: str
    version: str
    provider: str
