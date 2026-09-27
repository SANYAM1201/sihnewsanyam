"""Central registry for all ML models. Load once, reuse everywhere."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CONFIGS = {
    "default": {"path": "models/best.pt", "type": "yolo"},
    "100khz": {"path": "models/yolov8s_100khz.pt", "type": "yolo"},
    "400khz": {"path": "models/yolov8s_400khz.pt", "type": "yolo"},
    "900khz": {"path": "models/yolov8s_900khz.pt", "type": "yolo"},
}


class ModelManager:
    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        for name, cfg in _CONFIGS.items():
            if Path(cfg["path"]).exists():
                try:
                    from ultralytics import YOLO

                    self._models[name] = YOLO(cfg["path"])
                    logger.info(f"✅ Loaded model: {name}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load model {name}: {e}")

    def get(self, name: str = "default") -> Any | None:
        return self._models.get(name) or self._models.get("default")

    def reload(self, name: str) -> bool:
        cfg = _CONFIGS.get(name)
        if not cfg or not Path(cfg["path"]).exists():
            return False
        try:
            from ultralytics import YOLO

            self._models[name] = YOLO(cfg["path"])
            logger.info(f"🔄 Reloaded model: {name}")
            return True
        except Exception as e:
            logger.error(f"❌ Reload failed for model {name}: {e}")
            return False

    def list(self) -> dict[str, Any]:
        return {name: {"loaded": name in self._models, **cfg} for name, cfg in _CONFIGS.items()}


model_manager = ModelManager()
