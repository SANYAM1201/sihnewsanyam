"""Request ID Middleware for HTTP Request Tracing."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = str(uuid.uuid4())[:8]
        t0 = time.time()
        request.state.request_id = rid
        request.state.start_time = t0

        response = await call_next(request)
        dur = time.time() - t0

        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time"] = f"{dur:.3f}s"

        logger.info(f"{request.method} {request.url.path} rid={rid} status={response.status_code} dur={dur:.3f}s")
        return response
