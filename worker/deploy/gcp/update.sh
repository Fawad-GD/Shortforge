#!/usr/bin/env bash
# Push new worker code to the existing VM (rebuilds and restarts it).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$(cd "${HERE}/../.." && pwd)"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"; ZONE="${ZONE:-${REGION}-a}"; NAME="${NAME:-shortforge}"
BUCKET="${BUCKET:-${PROJECT_ID}-shortforge}"
tar -C "${WORKER_DIR}" --exclude='.env' --exclude='__pycache__' --exclude='.pytest_cache' -czf /tmp/worker.tgz .
gcloud storage cp /tmp/worker.tgz "gs://${BUCKET}/_deploy/worker.tgz"
gcloud compute instances reset "${NAME}" --zone "${ZONE}" --project "${PROJECT_ID}"
echo "Restarting; the startup script rebuilds the worker (a few minutes). Your .env and token are kept."
