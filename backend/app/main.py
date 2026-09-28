import logging
import os

os.environ.setdefault("ULTRALYTICS_AUTOINSTALL", "0")
os.environ.setdefault("YOLO_OFFLINE", "1")

logger = logging.getLogger("sonar_app")

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handler
from app.config import get_settings
from app.database import init_db
from app.services.factory import create_inference_service
from app.services.inference_service import InferenceService


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    from app.services.startup_validator import validate_environment, validate_config

    validate_environment()
    validate_config()

    init_db()

    settings = get_settings()
    inference_service = create_inference_service(settings)
    application.state.inference_service = inference_service

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Sonar Sentry API",
        description="Backend for the sonar anomaly detection web application.",
        version=settings.model_version,
        lifespan=lifespan,
    )

    register_exception_handler(application)

    from app.middleware.error_handler import GlobalErrorHandlerMiddleware
    from app.middleware.rate_limit import RateLimiterMiddleware
    from app.middleware.request_id import RequestIdMiddleware

    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(GlobalErrorHandlerMiddleware)
    application.add_middleware(RateLimiterMiddleware, max_requests=200, window_seconds=60)

    application.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.routes.health import router as health_router
    from app.api.routes.detect import router as detect_router
    from app.api.routes.runs import router as runs_router
    from app.api.routes.reports import router as reports_router
    from app.api.routes.predict import router as predict_router
    from app.api.routes.anomalies import router as anomalies_router
    from app.api.routes.waterfall import router as waterfall_router
    from app.monitoring.metrics import (
        REQUEST_COUNT,
        REQUEST_LATENCY,
        router as metrics_router,
    )

    from app.api.routes.models import router as models_router
    from app.api.routes.ab import router as ab_router
    from app.api.routes.export import router as export_router
    from app.services.model_watcher import watcher as model_watcher

    from app.api.routes.v1 import router as v1_router

    application.include_router(health_router)
    application.include_router(detect_router)
    application.include_router(runs_router)
    application.include_router(reports_router)
    application.include_router(predict_router)
    application.include_router(anomalies_router)
    application.include_router(waterfall_router)
    application.include_router(metrics_router)
    application.include_router(models_router)
    application.include_router(ab_router)
    application.include_router(export_router)
    application.include_router(v1_router)

    try:
        model_watcher.start()
    except Exception as exc:
        logger.warning("Could not start model watcher: %s", exc)


    @application.middleware("http")
    async def metrics_middleware(request, call_next):
        import time

        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        return response

    return application


app = create_app()
