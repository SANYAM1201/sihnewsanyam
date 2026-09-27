from __future__ import annotations

import importlib
import platform
import time
from datetime import datetime, timezone
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.schemas.response import HealthResponse, PreprocessingStatus
from app.services.inference_service import InferenceService

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    inference_service: InferenceService = request.app.state.inference_service
    settings = get_settings()

    db_status = "ok"
    try:
        from app.database import engine

        if engine is not None:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_status = "error"

    preprocessing_info = {
        "enabled": settings.sss_enable_processing,
        "bac_normalization": settings.sss_enable_bac,
        "stripe_noise_filter": settings.sss_enable_stripe_filter,
        "homomorphic_sharpening": settings.sss_enable_sharpening,
        "shadow_inpainting": settings.sss_enable_shadow_inpainting,
        "shadow_threshold": settings.sss_shadow_threshold,
        "shadow_inpaint_method": settings.sss_shadow_inpaint_method,
        "target_size": list(settings.yolo_target_size),
    }

    return HealthResponse(
        status="ok",
        model={
            "provider": inference_service.metadata().provider,
            "loaded": inference_service.is_model_loaded,
            "name": inference_service.metadata().name,
            "version": inference_service.metadata().version,
        },
        database={"status": db_status},
        preprocessing=PreprocessingStatus(**preprocessing_info),
    )


def get_system_info_safe() -> dict[str, Any]:
    """Get system info without triggering subprocess crashes."""
    try:
        system_info = {
            "status": "healthy",
            "platform": platform.system(),
            "python": platform.python_version(),
            "architecture": platform.machine(),
        }
        if psutil:
            cpu = psutil.cpu_percent(interval=0.01)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            system_info.update(
                {
                    "cpu_percent": cpu,
                    "memory_percent": mem.percent,
                    "memory_available_mb": round(mem.available / 1e6, 1),
                    "disk_percent": disk.percent,
                }
            )
        return system_info
    except Exception as e:
        return {
            "status": "degraded",
            "platform": platform.system(),
            "python": platform.python_version(),
            "error": str(e),
        }


@router.get("/api/health/detailed")
@router.get("/health/detailed")
async def detailed_health(request: Request) -> dict[str, Any]:
    t0 = time.time()

    # System metrics (safe)
    system = get_system_info_safe()


    # Dependency checks
    deps = {}
    for name, mod in [("torch", "torch"), ("opencv", "cv2"), ("ultralytics", "ultralytics")]:
        try:
            m = importlib.import_module(mod)
            deps[name] = {"status": "healthy", "version": getattr(m, "__version__", "?")}
        except Exception as e:
            deps[name] = {"status": "unhealthy", "error": str(e)}

    # Model status
    try:
        inf_svc = getattr(request.app.state, "inference_service", None)
        model_loaded = inf_svc.is_model_loaded if inf_svc else True
        model = {"status": "healthy" if model_loaded else "unhealthy"}
    except Exception as e:
        model = {"status": "unhealthy", "error": str(e)}

    # DB status
    try:
        from app.database import engine

        if engine is not None:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_check = {"status": "healthy"}
    except Exception as e:
        db_check = {"status": "unhealthy", "error": str(e)}

    all_ok = all(
        c.get("status") == "healthy"
        for c in [system, model, db_check] + list(deps.values())
    )

    return {
        "status": "healthy" if all_ok else "degraded",
        "response_time_ms": round((time.time() - t0) * 1000, 2),
        "checks": {
            "system": system,
            "dependencies": deps,
            "model": model,
            "database": db_check,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/health/ready")
@router.get("/health/ready")
async def readiness(request: Request) -> dict[str, str]:
    """Kubernetes readiness probe."""
    try:
        from app.database import engine

        if engine is not None:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/api/health/live")
@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
