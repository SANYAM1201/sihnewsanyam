#!/bin/bash
set -e

BASE_URL="http://localhost:8000"

echo "=== Validating API Endpoints on $BASE_URL ==="

# Health checks
echo -n "Health (/api/health): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" | grep -q "200" && echo "✅" || echo "❌"

echo -n "Health Detailed (/api/health/detailed): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/detailed" | grep -q "200" && echo "✅" || echo "❌"

echo -n "Health Ready (/api/health/ready): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/ready" | grep -q "200" && echo "✅" || echo "❌"

echo -n "Health Live (/api/health/live): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/live" | grep -q "200" && echo "✅" || echo "❌"

# Detection (file only - with auto-default metadata)
echo -n "Detect (/api/detect): "
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/detect" -F "file=@backend/tests/data/test_0.png" | grep -q "200" && echo "✅" || echo "❌"

# Models
echo -n "Models (/api/models): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/models" | grep -q "200" && echo "✅" || echo "❌"

# AB Testing
echo -n "AB Testing (/api/ab): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/ab" | grep -q "200" && echo "✅" || echo "❌"

# Export
echo -n "Export CSV (/api/export/detections/csv): "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/export/detections/csv" | grep -q "200" && echo "✅" || echo "❌"

echo ""
echo "=== All API endpoints validated successfully! ==="
