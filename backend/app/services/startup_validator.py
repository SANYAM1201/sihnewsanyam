"""Validates environment at startup. Called from main.py before app creation."""

from __future__ import annotations

import os

os.environ.setdefault("ULTRALYTICS_AUTOINSTALL", "0")
os.environ.setdefault("YOLO_OFFLINE", "1")

import importlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_FILES = {
    "models/best.pt": "optional",
    "models/gan_shadow_inpaint.pth": "optional",
}

REQUIRED_MODULES = [
    "torch",
    "ultralytics",
    "cv2",
    "numpy",
    "PIL",
    "fastapi",
    "uvicorn",
]


def validate_environment() -> None:
    errors = []

    # Files
    for path, kind in REQUIRED_FILES.items():
        if not Path(path).exists():
            msg = f"Missing file: {path}"
            if kind == "required":
                errors.append(msg)
            else:
                logger.warning(f"⚠️  {msg} (optional)")

    # Modules
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod if mod != "PIL" else "PIL")
        except ImportError:
            errors.append(f"Missing module: {mod}")

    # CUDA / Torch check
    try:
        import torch

        logger.info(f"{'✅' if torch.cuda.is_available() else '⚠️ '} CUDA available: {torch.cuda.is_available()}")
    except Exception:
        pass

    if errors:
        for e in errors:
            logger.error(f"❌ {e}")
        # When running under pytest, do not hard exit so test client can construct mock app if needed
        if "pytest" not in sys.modules:
            sys.exit(1)
    else:
        logger.info("✅ Environment OK")


def validate_config() -> None:
    try:
        from app.config import get_settings

        settings = get_settings()
        if getattr(settings, "use_supabase", False):
            if not (getattr(settings, "SUPABASE_URL", None) and getattr(settings, "SUPABASE_KEY", None)):
                logger.error("❌ Supabase enabled but credentials missing")
                if "pytest" not in sys.modules:
                    sys.exit(1)
        logger.info("✅ Config OK")
    except Exception as e:
        logger.warning(f"⚠️  Config check skipped: {e}")
