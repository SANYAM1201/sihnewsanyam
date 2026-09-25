from fastapi import APIRouter, Request

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
