import io
import numpy as np
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from app.schemas.ml import BBox, Detection, PreprocessedInput
from app.services.sonar_model_service import (
    SonarModelService,
    _iou,
    _nms,
    _pretty_label,
    resolve_model_path,
)


def test_iou_and_pretty_label():
    assert _pretty_label("ship_wreck") == "Ship Wreck"
    box1 = BBox(x=0, y=0, width=10, height=10)
    box2 = BBox(x=5, y=0, width=10, height=10)
    assert 0.0 < _iou(box1, box2) < 1.0

    # Non-overlapping
    box3 = BBox(x=100, y=100, width=10, height=10)
    assert _iou(box1, box3) == 0.0


def test_nms():
    det1 = Detection(class_label="debris", confidence=0.9, bbox=BBox(x=0, y=0, width=10, height=10))
    det2 = Detection(class_label="debris", confidence=0.8, bbox=BBox(x=1, y=1, width=10, height=10))
    det3 = Detection(class_label="debris", confidence=0.7, bbox=BBox(x=100, y=100, width=10, height=10))
    filtered = _nms([det1, det2, det3], iou_thr=0.5)
    assert len(filtered) == 2
    assert filtered[0] == det1
    assert filtered[1] == det3


def test_resolve_model_path():
    # If path exists
    assert resolve_model_path("models/best.pt").is_file()

    with pytest.raises(FileNotFoundError):
        with patch("app.services.sonar_model_service._CANDIDATE_WEIGHTS", []):
            resolve_model_path("non_existent_file.pt")


def test_sonar_model_service_predict():
    svc = SonarModelService("models/best.pt")
    # Not loaded error
    with pytest.raises(RuntimeError):
        svc.predict(PreprocessedInput(data=b"test"))

    svc.load()
    assert svc.is_loaded is True
    assert svc.metadata().name == "sih2026-yolov8s-marine-debris"

    # Test predict with bytes
    img = Image.new("RGB", (64, 64), color="gray")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = svc.predict(PreprocessedInput(data=buf.getvalue()))
    assert result.label in ["no_detection", "shipwreck", "pipe", "cylinder", "net"]

    # Test predict with numpy CHW array
    arr_chw = np.zeros((3, 64, 64), dtype=np.float32)
    result_np = svc.predict(PreprocessedInput(data=arr_chw, metadata={"scale": 1.0, "pad_left": 0, "pad_top": 0}))
    assert result_np is not None
