#!/bin/sh
set -e

echo "[$(date -u)] Starting database backup workflow..."

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-fastapi}"
POSTGRES_DB="${POSTGRES_DB:-fastapi_learning}"
DO_SPACES_REGION="${DO_SPACES_REGION:-sgp1}"
DO_SPACES_ENDPOINT="${DO_SPACES_ENDPOINT:-https://${DO_SPACES_REGION}.digitaloceanspaces.com}"
DO_SPACES_PREFIX="${DO_SPACES_PREFIX:-backups/db}"
BACKUP_KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="mytravel_db_${TIMESTAMP}.sql.gz"
BACKUP_FILEPATH="/tmp/${BACKUP_FILENAME}"

export PGPASSWORD="$POSTGRES_PASSWORD"

echo "[$(date -u)] Dumping PostgreSQL database '${POSTGRES_DB}' from '${POSTGRES_HOST}:${POSTGRES_PORT}'..."
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip -9 > "$BACKUP_FILEPATH"

if [ ! -s "$BACKUP_FILEPATH" ]; then
    echo "[$(date -u)] Error: Backup file is empty or was not created."
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_FILEPATH" | awk '{print $5}')
echo "[$(date -u)] Database dump created successfully: ${BACKUP_FILENAME} (${BACKUP_SIZE})"

# Check if DO Spaces credentials are provided
if [ -z "$DO_SPACES_KEY" ] || [ -z "$DO_SPACES_SECRET" ] || [ -z "$DO_SPACES_BUCKET" ]; then
    echo "[$(date -u)] WARNING: DO_SPACES_KEY, DO_SPACES_SECRET, or DO_SPACES_BUCKET is not set."
    echo "[$(date -u)] Backup saved locally to ${BACKUP_FILEPATH}, skipping DO Spaces upload."
    exit 0
fi

export AWS_ACCESS_KEY_ID="$DO_SPACES_KEY"
export AWS_SECRET_ACCESS_KEY="$DO_SPACES_SECRET"
export AWS_DEFAULT_REGION="$DO_SPACES_REGION"

DESTINATION_URI="s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/${BACKUP_FILENAME}"
echo "[$(date -u)] Uploading backup to DO Spaces: ${DESTINATION_URI}..."
aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 cp "$BACKUP_FILEPATH" "$DESTINATION_URI"
echo "[$(date -u)] Upload completed successfully."

# Prune old backups older than BACKUP_KEEP_DAYS
echo "[$(date -u)] Pruning backups older than ${BACKUP_KEEP_DAYS} days from s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/..."
CUTOFF_DATE=$(date -d "@$(( $(date +%s) - BACKUP_KEEP_DAYS * 86400 ))" +%Y-%m-%d 2>/dev/null || echo "")

if [ -n "$CUTOFF_DATE" ]; then
    aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 ls "s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/" | while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $1}')
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "$FILE_DATE" ] && [ -n "$FILE_NAME" ] && [ "$FILE_DATE" \< "$CUTOFF_DATE" ]; then
            echo "[$(date -u)] Removing expired backup: ${FILE_NAME} (created ${FILE_DATE})"
            aws --endpoint-url "$DO_SPACES_ENDPOINT" s3 rm "s3://${DO_SPACES_BUCKET}/${DO_SPACES_PREFIX}/${FILE_NAME}"
        fi
    done
fi

rm -f "$BACKUP_FILEPATH"
echo "[$(date -u)] Backup and cleanup finished successfully."
