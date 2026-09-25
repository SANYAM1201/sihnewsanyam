"""Prometheus metrics instrumentation for Sonar Sentry pipeline."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

# Metric definitions
REQUEST_COUNT = Counter(
    "sonar_requests_total",
    "Total HTTP requests handled by Sonar Sentry API",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "sonar_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.5, 5.0],
)

PREPROCESSING_TIME = Histogram(
    "sonar_preprocessing_time_seconds",
    "Time spent in full preprocessing pipeline",
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.5, 1.0],
)

INFERENCE_TIME = Histogram(
    "sonar_inference_duration_seconds",
    "YOLOv8 acoustic object detection model inference latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

ANOMALIES_DETECTED = Counter(
    "sonar_anomalies_detected_total",
    "Total marine debris and anomaly objects detected",
    ["debris_type"],
)

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
