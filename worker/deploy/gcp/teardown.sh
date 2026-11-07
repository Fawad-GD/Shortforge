#!/usr/bin/env bash
# Delete everything setup.sh created (stops all charges). Asks before deleting the bucket.
set -uo pipefail
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"; ZONE="${ZONE:-${REGION}-a}"; NAME="${NAME:-shortforge}"
BUCKET="${BUCKET:-${PROJECT_ID}-shortforge}"
gcloud compute instances delete "${NAME}" --zone "${ZONE}" --quiet
gcloud compute addresses delete "${NAME}-ip" --region "${REGION}" --quiet
gcloud compute firewall-rules delete "${NAME}-web" --quiet
gcloud iam service-accounts delete "${NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com" --quiet
read -r -p "Also DELETE bucket gs://${BUCKET} and every Short in it? Type 'yes': " ans
[ "${ans}" = "yes" ] && gcloud storage rm -r "gs://${BUCKET}"
echo "Teardown finished."
