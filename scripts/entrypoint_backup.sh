#!/bin/sh
set -e

# Default to 19:00 UTC (02:00 AM Phnom Penh time / UTC+7)
CRON_SCHEDULE="${BACKUP_CRON:-0 19 * * *}"

echo "[$(date -u)] Initializing automated DO Spaces DB backup service..."
echo "[$(date -u)] Backup cron schedule: '${CRON_SCHEDULE}' (19:00 UTC = 02:00 AM Cambodia time)"

# Configure crontab for root
echo "${CRON_SCHEDULE} /backup_to_spaces.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/root

touch /var/log/backup.log

# Run an initial backup check or dump on startup if requested
if [ "${RUN_BACKUP_ON_STARTUP:-false}" = "true" ]; then
    echo "[$(date -u)] RUN_BACKUP_ON_STARTUP is enabled. Triggering startup backup..."
    /backup_to_spaces.sh || echo "[$(date -u)] Warning: Initial startup backup failed. Scheduled cron will continue."
fi

echo "[$(date -u)] Starting background cron daemon..."
exec crond -f -l 2
