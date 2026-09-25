"""YOLOv8 sonar debris detector trained in Colab (sih2026_yolov8s_marine_debris)."""

from __future__ import annotations

import io
from pathlib import Path

from app.schemas.ml import BBox, Detection, ModelMetadata, PredictionResult, PreprocessedInput
from app.services.model_service import ModelService

_DEFAULT_NAMES = {
    0: "shipwreck",
    1: "pipe",
    2: "cylinder",
    3: "net",
}

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_DIR = _BACKEND_DIR
_REPO_ROOT = _BACKEND_DIR

_CANDIDATE_WEIGHTS = [
    _BACKEND_DIR / "best.pt",
    _BACKEND_DIR / "model" / "best.pt",
    _PROJECT_DIR / "model" / "best.pt",
    _BACKEND_DIR / "yolov8s.pt",
    _REPO_ROOT / "yolov8s.pt",
]

_INFER_SIZES = (640, 960)
_MODEL_CONF = 0.12
_NMS_IOU = 0.45


def _pretty_label(name: str) -> str:
    return name.replace("_", " ").strip().title()


def resolve_model_path(configured: str) -> Path:
    if configured:
        path = Path(configured)
        if path.is_file():
            return path
    for candidate in _CANDIDATE_WEIGHTS:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "No trained YOLO weights found. Place best.pt in the project model/ folder "
        "or set MODEL_PATH."
    )


def _iou(a: BBox, b: BBox) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = a.width * a.height + b.width * b.height - inter
    return inter / union if union > 0 else 0.0


def _nms(detections: list[Detection], iou_thr: float = _NMS_IOU) -> list[Detection]:
    ordered = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    for det in ordered:
        if det.bbox is None:
            kept.append(det)
            continue
        if all(k.bbox is None or _iou(det.bbox, k.bbox) < iou_thr for k in kept):
            kept.append(det)
    return kept


class SonarModelService(ModelService):
    """Ultralytics YOLOv8 wrapper around the Colab-trained sonar debris weights."""

    def __init__(self, model_path: str = "") -> None:
        self._configured_path = model_path
        self._resolved_path: Path | None = None
        self._model = None
        self._names: dict[int, str] = dict(_DEFAULT_NAMES)
        self._loaded = False

    def load(self) -> None:
        from ultralytics import YOLO

        self._resolved_path = resolve_model_path(self._configured_path)
        self._model = YOLO(str(self._resolved_path))
        names = getattr(self._model, "names", None)
        if isinstance(names, dict) and names:
            self._names = {int(k): str(v) for k, v in names.items()}
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _boxes_from_result(self, result, meta: dict | None = None) -> list[Detection]:
        detections: list[Detection] = []
        names = result.names or self._names
        boxes = result.boxes
        if boxes is None:
            return detections

        has_letterbox = bool(meta and "scale" in meta and meta.get("scale", 0) > 0)
        scale = float(meta["scale"]) if has_letterbox else 1.0
        pad_left = float(meta.get("pad_left", 0)) if has_letterbox else 0.0
        pad_top = float(meta.get("pad_top", 0)) if has_letterbox else 0.0
        orig_shape = meta.get("orig_shape") if has_letterbox else None
        orig_h = float(orig_shape[0]) if orig_shape else None
        orig_w = float(orig_shape[1]) if orig_shape else None

        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            raw_name = str(names.get(cls_id, self._names.get(cls_id, f"class_{cls_id}")))
            label = _pretty_label(raw_name)
            x1, y1, x2, y2 = xyxy

            if has_letterbox:
                x1 = (x1 - pad_left) / scale
                y1 = (y1 - pad_top) / scale
                x2 = (x2 - pad_left) / scale
                y2 = (y2 - pad_top) / scale
                if orig_w is not None and orig_h is not None:
                    x1 = max(0.0, min(orig_w, x1))
                    y1 = max(0.0, min(orig_h, y1))
                    x2 = max(0.0, min(orig_w, x2))
                    y2 = max(0.0, min(orig_h, y2))

            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            detections.append(
                Detection(
                    class_label=label,
                    confidence=round(conf, 4),
                    bbox=BBox(x=float(x1), y=float(y1), width=width, height=height),
                    area_m2=round((width * height) / 10000.0, 2),
                    position_info=f"{int(x1)},{int(y1)}",
                )
            )
        return detections

    def predict(self, input_data: PreprocessedInput) -> PredictionResult:
        if not self._loaded or self._model is None:
            raise RuntimeError("Model has not been loaded. Call load() first.")

        import numpy as np
        from PIL import Image

        raw = input_data.data
        meta = getattr(input_data, "metadata", {}) or {}
        if isinstance(raw, (bytes, bytearray)):
            source = Image.open(io.BytesIO(raw)).convert("RGB")
        elif isinstance(raw, np.ndarray):
            if raw.ndim == 3 and raw.shape[0] in (1, 3):
                # Convert CHW -> HWC
                source = np.transpose(raw, (1, 2, 0))
            else:
                source = raw
            if np.issubdtype(source.dtype, np.floating) and source.max() <= 1.05:
                source = np.clip(source * 255.0, 0, 255).astype(np.uint8)
        else:
            raise TypeError(
                f"SonarModelService expects image bytes or numpy array, got {type(raw).__name__}"
            )

        collected: list[Detection] = []
        scores: dict[str, float] = {}

        for imgsz in _INFER_SIZES:
            results = self._model.predict(
                source=source,
                imgsz=imgsz,
                conf=_MODEL_CONF,
                verbose=False,
            )
            if not results:
                continue
            collected.extend(self._boxes_from_result(results[0], meta=meta))

        detections = _nms(collected)
        for det in detections:
            scores[det.class_label] = max(scores.get(det.class_label, 0.0), det.confidence)

        if detections:
            best = max(detections, key=lambda d: d.confidence)
            return PredictionResult(
                label=best.class_label,
                confidence=best.confidence,
                raw_scores=scores,
                detections=detections,
            )

        return PredictionResult(
            label="no_detection",
            confidence=0.0,
            raw_scores=scores,
            detections=[],
        )

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="sih2026-yolov8s-marine-debris",
            version="colab-best",
            provider="sonar",
        )
