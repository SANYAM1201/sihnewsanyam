"""API Version 1 Router Aggregator."""

from __future__ import annotations

import importlib
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

for name in ["detect", "runs", "waterfall", "health", "reports", "predict", "anomalies"]:
    mod_path = f"app.api.routes.{name}"
    try:
        mod = importlib.import_module(mod_path)
        if hasattr(mod, "router"):
            router.include_router(mod.router)
    except ImportError:
        pass
