#!/bin/bash
set -e

# Production Backup Script
# Usage: ./backup-production.sh [full|incremental]

BACKUP_TYPE=${1:-incremental}
BACKUP_DIR="/backups/saascontroldeck/production"
S3_BUCKET=${S3_BACKUP_BUCKET:-"saascontroldeck-backups"}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS=30

echo "🗄️ Starting production backup (type: $BACKUP_TYPE)..."

# Create backup directories
mkdir -p "$BACKUP_DIR/database"
mkdir -p "$BACKUP_DIR/redis"
mkdir -p "$BACKUP_DIR/minio"
mkdir -p "$BACKUP_DIR/application"
mkdir -p "$BACKUP_DIR/configs"

# Check if required tools are installed
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required"; exit 1; }

echo "📊 Backup started at: $(date)"

# 1. Database Backup
echo "💾 Backing up PostgreSQL database..."
docker exec postgres-production pg_dump -U ${POSTGRES_USER:-saasuser} -d ${POSTGRES_DB:-saascontroldeck_production} \
  --format=custom --compress=9 --verbose > "$BACKUP_DIR/database/postgres-$TIMESTAMP.dump"

if [ $? -eq 0 ]; then
  echo "✅ PostgreSQL backup completed"
  DB_BACKUP_SIZE=$(du -h "$BACKUP_DIR/database/postgres-$TIMESTAMP.dump" | cut -f1)
  echo "📦 Database backup size: $DB_BACKUP_SIZE"
else
  echo "❌ PostgreSQL backup failed"
  exit 1
fi

# 2. Redis Backup
echo "💾 Backing up Redis data..."
docker exec redis-production redis-cli --rdb /data/dump-backup.rdb BGSAVE
sleep 10  # Wait for background save to complete

# Wait for backup to complete
while docker exec redis-production redis-cli LASTSAVE | grep -q "$(docker exec redis-production redis-cli LASTSAVE)"; do
  echo "⏳ Waiting for Redis backup to complete..."
  sleep 5
done

docker cp redis-production:/data/dump.rdb "$BACKUP_DIR/redis/redis-$TIMESTAMP.rdb"

if [ $? -eq 0 ]; then
  echo "✅ Redis backup completed"
  REDIS_BACKUP_SIZE=$(du -h "$BACKUP_DIR/redis/redis-$TIMESTAMP.rdb" | cut -f1)
  echo "📦 Redis backup size: $REDIS_BACKUP_SIZE"
else
  echo "❌ Redis backup failed"
  exit 1
fi

# 3. MinIO Backup
echo "💾 Backing up MinIO data..."
docker exec minio-production tar czf "/data/minio-backup-$TIMESTAMP.tar.gz" -C /data .

if [ $? -eq 0 ]; then
  docker cp "minio-production:/data/minio-backup-$TIMESTAMP.tar.gz" "$BACKUP_DIR/minio/"
  docker exec minio-production rm "/data/minio-backup-$TIMESTAMP.tar.gz"
  echo "✅ MinIO backup completed"
  MINIO_BACKUP_SIZE=$(du -h "$BACKUP_DIR/minio/minio-backup-$TIMESTAMP.tar.gz" | cut -f1)
  echo "📦 MinIO backup size: $MINIO_BACKUP_SIZE"
else
  echo "❌ MinIO backup failed"
  exit 1
fi

# 4. Application Configuration Backup
echo "💾 Backing up application configurations..."
tar czf "$BACKUP_DIR/configs/configs-$TIMESTAMP.tar.gz" \
  /opt/saascontroldeck/docker-compose.production.yml \
  /opt/saascontroldeck/.env.production \
  /etc/nginx/sites-available/saascontroldeck.com \
  /etc/letsencrypt/live/saascontroldeck.com/ \
  /opt/saascontroldeck/monitoring/ \
  2>/dev/null || echo "⚠️ Some config files may be missing"

if [ $? -eq 0 ]; then
  echo "✅ Configuration backup completed"
  CONFIG_BACKUP_SIZE=$(du -h "$BACKUP_DIR/configs/configs-$TIMESTAMP.tar.gz" | cut -f1)
  echo "📦 Configuration backup size: $CONFIG_BACKUP_SIZE"
fi

# 5. Docker Images Backup (optional for full backup)
if [ "$BACKUP_TYPE" = "full" ]; then
  echo "💾 Backing up Docker images..."
  docker save ghcr.io/irisanalysis/saascontroldeck-frontend:main-latest \
    ghcr.io/irisanalysis/saascontroldeck-backend-pro1:main-latest \
    ghcr.io/irisanalysis/saascontroldeck-backend-pro2:main-latest \
    | gzip > "$BACKUP_DIR/application/docker-images-$TIMESTAMP.tar.gz"
  
  if [ $? -eq 0 ]; then
    echo "✅ Docker images backup completed"
    IMAGES_BACKUP_SIZE=$(du -h "$BACKUP_DIR/application/docker-images-$TIMESTAMP.tar.gz" | cut -f1)
    echo "📦 Docker images backup size: $IMAGES_BACKUP_SIZE"
  fi
fi

# 6. Create backup manifest
echo "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/backup-manifest-$TIMESTAMP.json" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "backup_type": "$BACKUP_TYPE",
  "files": {
    "database": "database/postgres-$TIMESTAMP.dump",
    "redis": "redis/redis-$TIMESTAMP.rdb",
    "minio": "minio/minio-backup-$TIMESTAMP.tar.gz",
    "configs": "configs/configs-$TIMESTAMP.tar.gz"
    $([ "$BACKUP_TYPE" = "full" ] && echo ', "docker_images": "application/docker-images-'$TIMESTAMP'.tar.gz"')
  },
  "sizes": {
    "database": "$DB_BACKUP_SIZE",
    "redis": "$REDIS_BACKUP_SIZE",
    "minio": "$MINIO_BACKUP_SIZE",
    "configs": "$CONFIG_BACKUP_SIZE"
    $([ "$BACKUP_TYPE" = "full" ] && [ -n "$IMAGES_BACKUP_SIZE" ] && echo ', "docker_images": "'$IMAGES_BACKUP_SIZE'"')
  },
  "environment": "production",
  "status": "completed"
}
EOF

# 7. Upload to S3 (if configured)
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "☁️ Uploading backups to S3..."
  
  aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/production/$TIMESTAMP/" \
    --storage-class STANDARD_IA \
    --exclude "*.tmp" \
    --exclude "*.log"
  
  if [ $? -eq 0 ]; then
    echo "✅ S3 upload completed"
    echo "🌐 S3 location: s3://$S3_BUCKET/production/$TIMESTAMP/"
  else
    echo "❌ S3 upload failed"
  fi
else
  echo "⚠️ S3 credentials not configured, skipping cloud backup"
fi

# 8. Cleanup old backups
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.json" -mtime +$RETENTION_DAYS -delete

# 9. Verify backup integrity
echo "🔍 Verifying backup integrity..."
BACKUP_ERRORS=0

# Verify database backup
if ! pg_restore --list "$BACKUP_DIR/database/postgres-$TIMESTAMP.dump" > /dev/null 2>&1; then
  echo "❌ Database backup verification failed"
  BACKUP_ERRORS=$((BACKUP_ERRORS + 1))
else
  echo "✅ Database backup verified"
fi

# Verify Redis backup
if [ ! -f "$BACKUP_DIR/redis/redis-$TIMESTAMP.rdb" ]; then
  echo "❌ Redis backup file not found"
  BACKUP_ERRORS=$((BACKUP_ERRORS + 1))
else
  echo "✅ Redis backup file verified"
fi

# Verify MinIO backup
if ! tar -tzf "$BACKUP_DIR/minio/minio-backup-$TIMESTAMP.tar.gz" > /dev/null 2>&1; then
  echo "❌ MinIO backup verification failed"
  BACKUP_ERRORS=$((BACKUP_ERRORS + 1))
else
  echo "✅ MinIO backup verified"
fi

# 10. Generate backup report
TOTAL_BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
BACKUP_END_TIME=$(date)

cat > "$BACKUP_DIR/backup-report-$TIMESTAMP.txt" << EOF
SaaS Control Deck Production Backup Report
==========================================

Backup Type: $BACKUP_TYPE
Start Time: $(date -d "$BACKUP_START_TIME" 2>/dev/null || echo "N/A")
End Time: $BACKUP_END_TIME
Duration: $(($(date +%s) - $(date -d "$BACKUP_START_TIME" +%s) 2>/dev/null || echo 0)) seconds

Backup Location: $BACKUP_DIR
Total Backup Size: $TOTAL_BACKUP_SIZE
S3 Location: s3://$S3_BUCKET/production/$TIMESTAMP/

Components Backed Up:
- PostgreSQL Database: $DB_BACKUP_SIZE
- Redis Cache: $REDIS_BACKUP_SIZE  
- MinIO Object Storage: $MINIO_BACKUP_SIZE
- Application Configs: $CONFIG_BACKUP_SIZE
$([ "$BACKUP_TYPE" = "full" ] && [ -n "$IMAGES_BACKUP_SIZE" ] && echo "- Docker Images: $IMAGES_BACKUP_SIZE")

Verification Results:
- Errors Found: $BACKUP_ERRORS
- Status: $([ $BACKUP_ERRORS -eq 0 ] && echo "SUCCESS" || echo "FAILED")

Next Steps:
- Backups are retained for $RETENTION_DAYS days locally
- S3 backups follow lifecycle policies
- Test restore procedures monthly
EOF

# 11. Send notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  if [ $BACKUP_ERRORS -eq 0 ]; then
    curl -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"✅ Production backup completed successfully ($BACKUP_TYPE) - Size: $TOTAL_BACKUP_SIZE\"}" \
      $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
  else
    curl -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"❌ Production backup completed with $BACKUP_ERRORS errors ($BACKUP_TYPE)\"}" \
      $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
  fi
fi

if [ $BACKUP_ERRORS -eq 0 ]; then
  echo "✅ Production backup completed successfully!"
  echo "📊 Total backup size: $TOTAL_BACKUP_SIZE"
  echo "📁 Backup location: $BACKUP_DIR"
  exit 0
else
  echo "❌ Production backup completed with $BACKUP_ERRORS errors"
  exit 1
fi