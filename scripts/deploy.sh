#!/bin/bash
set -e

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH. Please install Docker Desktop for Mac."
    echo "   Download: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "=== Building Docker Images ==="
docker compose build

echo "=== Starting Containers ==="
docker compose up -d

echo "=== Verifying Health ==="
for i in {1..10}; do
  if curl -s http://localhost:8000/api/health | grep -q '"status":"ok"'; then
    echo "✅ Deployment successful!"
    exit 0
  fi
  sleep 3
done

echo "❌ Deployment healthcheck timed out"
exit 1

