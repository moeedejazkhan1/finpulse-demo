#!/bin/sh
# Run once by the one-shot `minio-init` compose service (mc client image)
# to create the raw zone bucket. Idempotent: `mc mb --ignore-existing`.
set -e

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing local/finpulse-raw
echo "finpulse-raw bucket ready"
