#!/usr/bin/env bash
set -euo pipefail

echo "Starting stored-proc export job..."

# --- required env ---
: "${MCP_DB_USERNAME?Missing MCP_DB_USERNAME}"
: "${MCP_DB_PASSWORD?Missing MCP_DB_PASSWORD}"
: "${MCP_DB_SERVER?Missing MCP_DB_SERVER}"
: "${MCP_DB_PORT:=1433}"
: "${MCP_DB_NAME?Missing MCP_DB_NAME}"

: "${MINIO_ENDPOINT?Missing MINIO_ENDPOINT (e.g. http://minio.minio.svc:9000)}"
: "${MINIO_BUCKET?Missing MINIO_BUCKET}"
: "${MINIO_PREFIX:=mcp_parquet}"
: "${AWS_ACCESS_KEY_ID?Missing AWS_ACCESS_KEY_ID (MinIO key)}"
: "${AWS_SECRET_ACCESS_KEY?Missing AWS_SECRET_ACCESS_KEY (MinIO secret)}"
: "${AWS_DEFAULT_REGION:=us-east-1}"

: "${DATE_START?Missing DATE_START (YYYY-MM-DD)}"
: "${DATE_END?Missing DATE_END (YYYY-MM-DD)}"

# optional: comma-separated list; default runs all
: "${PROCS:=revenue,payroll,payroll_salary,payroll_history,budget,visits,weather}"

export AWS_EC2_METADATA_DISABLED=true

WORKDIR="/work"
OUTDIR="${WORKDIR}/out"
mkdir -p "${OUTDIR}"

echo "Installing OS deps (msodbcsql18 + unixODBC)..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends curl ca-certificates gnupg apt-transport-https unixodbc unixodbc-dev

# Detect Debian version (11=bullseye, 12=bookworm)
. /etc/os-release
DEBIAN_VER="${VERSION_ID}"

echo "Debian VERSION_ID=${DEBIAN_VER}"

# Install Microsoft repo config package (adds repo + GPG key properly)
curl -fsSL "https://packages.microsoft.com/config/debian/${DEBIAN_VER}/packages-microsoft-prod.deb" -o /tmp/packages-microsoft-prod.deb
dpkg -i /tmp/packages-microsoft-prod.deb
rm -f /tmp/packages-microsoft-prod.deb

apt-get update -y
ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18

python -m pip install --no-cache-dir -U pip
python -m pip install --no-cache-dir pyodbc pandas pyarrow boto3 s3fs awscli

echo "Running exports..."
python "$(dirname "$0")/scripts/export_procs_to_parquet.py" \
  --outdir "${OUTDIR}" \
  --date-start "${DATE_START}" \
  --date-end "${DATE_END}" \
  --procs "${PROCS}"

echo "Uploading to MinIO..."
aws --endpoint-url "${MINIO_ENDPOINT}" s3 cp \
  "${OUTDIR}" "s3://${MINIO_BUCKET}/${MINIO_PREFIX}/" \
  --recursive

echo "Done. Uploaded to: s3://${MINIO_BUCKET}/${MINIO_PREFIX}/"
