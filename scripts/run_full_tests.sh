#!/bin/bash
set -e

echo "=== Running Full Test Suite ==="
./.venv/bin/pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term -v

echo "=== Checking Server Startup ==="
./.venv/bin/uvicorn app.main:app --port 8001 --app-dir backend &
PID=$!
sleep 3
curl -s http://localhost:8001/api/health | python3 -m json.tool
kill $PID || true

echo "=== All Checks Passed ==="
