# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime libraries needed by OpenCV & curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY backend/app /app/app
COPY backend/best.pt /app/best.pt
COPY model /app/model

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MODEL_PROVIDER=yolo \
    YOLO_WEIGHTS_PATH=/app/model/best.pt \
    SSS_ENABLE_PROCESSING=true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
