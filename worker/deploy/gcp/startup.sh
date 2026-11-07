#!/bin/bash
# Runs on the VM at every boot (Compute Engine "startup-script"). Idempotent.
# Fetches the worker code from your bucket, builds it, and (re)starts it behind HTTPS.
set -euxo pipefail

md() { curl -fsS -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/$1"; }
BUCKET="$(md instance/attributes/sf-bucket)"
WHISPER="$(md instance/attributes/sf-whisper)"
IP="$(md instance/network-interfaces/0/access-configs/0/external-ip)"
DOMAIN_NAME="${IP//./-}.sslip.io"   # free wildcard DNS: 34-1-2-3.sslip.io -> 34.1.2.3

# Small machines need swap or Whisper/FFmpeg get OOM-killed.
if [ "$(awk '/MemTotal/{print int($2/1024/1024)}' /proc/meminfo)" -lt 6 ] && [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

command -v docker >/dev/null 2>&1 || curl -fsSL https://get.docker.com | sh

mkdir -p /opt/shortforge && cd /opt/shortforge
ACCESS="$(md instance/service-accounts/default/token | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')"
curl -fsS -H "Authorization: Bearer ${ACCESS}" \
  "https://storage.googleapis.com/storage/v1/b/${BUCKET}/o/_deploy%2Fworker.tgz?alt=media" -o worker.tgz
tar -xzf worker.tgz && rm -f worker.tgz

setenv() {  # setenv KEY VALUE  -> set or replace a line in .env
  if grep -q "^$1=" .env; then sed -i "s|^$1=.*|$1=$2|" .env; else echo "$1=$2" >> .env; fi
}
if [ ! -f .env ]; then
  cp .env.example .env
  setenv SHORTFORGE_ACCESS_TOKEN "$(md instance/attributes/sf-token)"   # only on first boot
  chmod 600 .env
fi
setenv CLIPIFY_WHISPER_MODEL "${WHISPER}"
setenv GCS_BUCKET "${BUCKET}"
setenv DOMAIN "${DOMAIN_NAME}"

docker compose --profile https up -d --build
