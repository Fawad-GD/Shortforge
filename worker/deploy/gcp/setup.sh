#!/usr/bin/env bash
# One-command Google Cloud setup. Run it in Cloud Shell (https://shell.cloud.google.com)
# from the worker/ folder:   bash deploy/gcp/setup.sh
#
# Creates: a Cloud Storage bucket (auto-expiring outputs), a least-privilege service
# account, a static IP, a firewall rule (80/443 only) and one VM running the worker
# with automatic HTTPS. Re-running is safe; use update.sh to push new code.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$(cd "${HERE}/../.." && pwd)"

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
[ -n "${PROJECT_ID}" ] || { echo "No project selected. Run: gcloud config set project YOUR_PROJECT_ID"; exit 1; }
REGION="${REGION:-us-central1}"          # us-central1 / us-east1 / us-west1 keep Cloud Storage in the free tier
ZONE="${ZONE:-${REGION}-a}"
NAME="${NAME:-shortforge}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-2}"   # 2 vCPU / 8 GB. e2-micro is free but too small (see docs)
DISK_GB="${DISK_GB:-50}"
BUCKET="${BUCKET:-${PROJECT_ID}-shortforge}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"   # finished Shorts older than this are deleted from the bucket
WHISPER_MODEL="${WHISPER_MODEL:-small}"  # use "base" or "tiny" on small machines
SA="${NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Project ${PROJECT_ID}, ${ZONE}, ${MACHINE_TYPE}, bucket gs://${BUCKET}"
gcloud services enable compute.googleapis.com storage.googleapis.com --project "${PROJECT_ID}"

if gcloud compute instances describe "${NAME}" --zone "${ZONE}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  echo "VM '${NAME}' already exists. To deploy new code run: bash deploy/gcp/update.sh"; exit 0
fi

echo "==> Bucket"
gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1 || \
  gcloud storage buckets create "gs://${BUCKET}" --location "${REGION}" \
    --uniform-bucket-level-access --public-access-prevention --project "${PROJECT_ID}"
LIFECYCLE="$(mktemp)"
cat > "${LIFECYCLE}" <<JSON
{"rule":[{"action":{"type":"Delete"},"condition":{"age":${RETENTION_DAYS},"matchesPrefix":["users/"]}}]}
JSON
gcloud storage buckets update "gs://${BUCKET}" --lifecycle-file="${LIFECYCLE}"

echo "==> Service account (can only touch this bucket)"
gcloud iam service-accounts describe "${SA}" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "${NAME}-sa" --display-name "ShortForge worker" --project "${PROJECT_ID}"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member "serviceAccount:${SA}" --role roles/storage.objectAdmin >/dev/null

echo "==> Network"
gcloud compute addresses describe "${NAME}-ip" --region "${REGION}" >/dev/null 2>&1 || \
  gcloud compute addresses create "${NAME}-ip" --region "${REGION}" --project "${PROJECT_ID}"
IP="$(gcloud compute addresses describe "${NAME}-ip" --region "${REGION}" --format='value(address)')"
gcloud compute firewall-rules describe "${NAME}-web" >/dev/null 2>&1 || \
  gcloud compute firewall-rules create "${NAME}-web" --allow tcp:80,tcp:443 \
    --target-tags "${NAME}" --project "${PROJECT_ID}"

echo "==> Uploading worker code"
tar -C "${WORKER_DIR}" --exclude='.env' --exclude='__pycache__' --exclude='.pytest_cache' -czf /tmp/worker.tgz .
gcloud storage cp /tmp/worker.tgz "gs://${BUCKET}/_deploy/worker.tgz"

TOKEN="$(openssl rand -hex 32)"
echo "==> Creating VM"
gcloud compute instances create "${NAME}" --project "${PROJECT_ID}" --zone "${ZONE}" \
  --machine-type "${MACHINE_TYPE}" --image-family debian-12 --image-project debian-cloud \
  --boot-disk-size "${DISK_GB}GB" --boot-disk-type pd-balanced \
  --address "${IP}" --tags "${NAME}" \
  --service-account "${SA}" --scopes storage-rw \
  --metadata "sf-bucket=${BUCKET},sf-whisper=${WHISPER_MODEL},sf-token=${TOKEN}" \
  --metadata-from-file "startup-script=${HERE}/startup.sh"

DOMAIN="${IP//./-}.sslip.io"
cat <<DONE

==========================================================================
 Done. The VM is installing Docker and building the worker (about 8-12 min).

 Add these TWO secrets to your website's backend, then redeploy it:
   WORKER_URL                = https://${DOMAIN}
   SHORTFORGE_ACCESS_TOKEN   = ${TOKEN}

 Check it:      curl https://${DOMAIN}/health
 Watch the build: gcloud compute ssh ${NAME} --zone ${ZONE} -- sudo journalctl -u google-startup-scripts -f
 Then open your site -> System status: everything should say Online.
==========================================================================
DONE
