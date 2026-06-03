#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/app/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
POSTGRES_CONTAINER="phone-automation-postgres"

# Create backup directory
mkdir -p $BACKUP_DIR/daily

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec $POSTGRES_CONTAINER pg_dump -U postgres phone_automation | gzip > $BACKUP_DIR/daily/postgres_$TIMESTAMP.sql.gz

# Backup Redis
echo "Backing up Redis..."
docker exec phone-automation-redis redis-cli BGSAVE
docker cp phone-automation-redis:/data/dump.rdb $BACKUP_DIR/daily/redis_$TIMESTAMP.rdb

# Backup uploads
echo "Backing up uploads..."
tar -czf $BACKUP_DIR/daily/uploads_$TIMESTAMP.tar.gz /app/data/uploads

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR/daily -type f -mtime +7 -delete

echo "✅ Backup completed: $TIMESTAMP"
