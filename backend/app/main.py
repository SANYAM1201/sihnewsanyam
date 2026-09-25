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
    from app.monitoring.metrics import (
        REQUEST_COUNT,
        REQUEST_LATENCY,
        router as metrics_router,
    )

    application.include_router(health_router)
    application.include_router(detect_router)
    application.include_router(runs_router)
    application.include_router(reports_router)
    application.include_router(predict_router)
    application.include_router(anomalies_router)
    application.include_router(metrics_router)

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
