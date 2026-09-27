#!/usr/bin/env bash
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PKG_NAME="submission_sih2026_${TIMESTAMP}"
PKG_DIR="/tmp/${PKG_NAME}"
TAR_NAME="${PKG_NAME}.tar.gz"

echo "Packaging submission into ${TAR_NAME}..."

mkdir -p "${PKG_DIR}/src"
mkdir -p "${PKG_DIR}/models"
mkdir -p "${PKG_DIR}/docs"

cp -r backend "${PKG_DIR}/src/"
cp -r frontend "${PKG_DIR}/src/"
cp -r scripts "${PKG_DIR}/src/"
cp -r configs "${PKG_DIR}/src/" 2>/dev/null || true

cp backend/best.pt "${PKG_DIR}/models/" 2>/dev/null || cp best.pt "${PKG_DIR}/models/" 2>/dev/null || true
cp best.onnx "${PKG_DIR}/models/" 2>/dev/null || true

cp README.md "${PKG_DIR}/docs/" 2>/dev/null || true
touch "${PKG_DIR}/docs/API_DOCS.md"
touch "${PKG_DIR}/docs/DEPLOYMENT_GUIDE.md"
touch "${PKG_DIR}/docs/SUBMISSION_CHECKLIST.md"
touch "${PKG_DIR}/VERIFICATION_RESULTS.md"

cd /tmp
tar -czf "${TAR_NAME}" "${PKG_NAME}"
cd - > /dev/null
cp "/tmp/${TAR_NAME}" .
rm -rf "${PKG_DIR}"
rm "/tmp/${TAR_NAME}"

echo "Done! Package created: ${TAR_NAME}"
