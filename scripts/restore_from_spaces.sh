#!/bin/sh
set -e

# Usage:
#   ./restore_from_spaces.sh                    (Lists available backups)
#   ./restore_from_spaces.sh <backup_filename>   (Restores the specified backup)

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-fastapi}"
POSTGRES_DB="${POSTGRES_DB:-fastapi_learning}"
DO_SPACES_REGION="${DO_SPACES_REGION:-sgp1}"
DO_SPACES_ENDPOINT="${DO_SPACES_ENDPOINT:-https://${DO_SPACES_REGION}.digitaloceanspaces.com}"
DO_SPACES_PREFIX="${DO_SPACES_PREFIX:-backups/db}"

if [ -z "$DO_SPACES_KEY" ] || [ -z "$DO_SPACES_SECRET" ] || [ -z "$DO_SPACES_BUCKET" ]; then
    echo "Error: DO_SPACES_KEY, DO_SPACES_SECRET, and DO_SPACES_BUCKET must be set."
    exit 1
fi

export AWS_ACCESS_KEY_ID="$DO_SPACES_KEY"
export AWS_SECRET_ACCESS_KEY="$DO_SPACES_SECRET"
export AWS_DEFAULT_REGION="$DO_SPACES_REGION"
export PGPASSWORD="$POSTGRES_PASSWORD"

TARGET_FILE="$1"

if [ -z "$TARGET_FILE" ]; then
    echo "=== Available Backups in s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/ ==="
    aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 ls "s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/"
    echo ""
    echo "To restore a backup, re-run with filename:"
    echo "  ./restore_from_spaces.sh <filename.sql.gz>"
    exit 0
fi

LOCAL_TMP="/tmp/${TARGET_FILE}"
echo "[$(date -u)] Downloading backup s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/${TARGET_FILE}..."
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 cp "s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/${TARGET_FILE}" "$LOCAL_TMP"

echo "[$(date -u)] Restoring into '${POSTGRES_DB}' on '${POSTGRES_HOST}'..."
gunzip -c "$LOCAL_TMP" | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"

rm -f "$LOCAL_TMP"
echo "[$(date -u)] Database restored successfully from ${TARGET_FILE}."
