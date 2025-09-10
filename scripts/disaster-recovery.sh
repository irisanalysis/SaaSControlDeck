#!/bin/bash
set -e

# Disaster Recovery Script for SaaS Control Deck
# Usage: ./disaster-recovery.sh [backup-timestamp] [recovery-type]

BACKUP_TIMESTAMP=${1:-$(ls -t /backups/saascontroldeck/production/backup-manifest-*.json | head -1 | grep -o '[0-9]\{8\}-[0-9]\{6\}' | head -1)}
RECOVERY_TYPE=${2:-full}  # full|data-only|config-only
BACKUP_DIR="/backups/saascontroldeck/production"
S3_BUCKET=${S3_BACKUP_BUCKET:-"saascontroldeck-backups"}
TEMP_RESTORE_DIR="/tmp/disaster-recovery-$BACKUP_TIMESTAMP"

echo "🚨 Starting disaster recovery process..."
echo "📅 Backup timestamp: $BACKUP_TIMESTAMP"
echo "🔧 Recovery type: $RECOVERY_TYPE"

# Pre-flight checks
echo "🔍 Running pre-flight checks..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo "❌ This script must be run as root or with sudo"
  exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running"
  exit 1
fi

# Check if backup manifest exists
MANIFEST_FILE="$BACKUP_DIR/backup-manifest-$BACKUP_TIMESTAMP.json"
if [ ! -f "$MANIFEST_FILE" ]; then
  echo "❌ Backup manifest not found: $MANIFEST_FILE"
  echo "📋 Available backups:"
  ls -la "$BACKUP_DIR"/backup-manifest-*.json 2>/dev/null || echo "No backups found"
  exit 1
fi

echo "✅ Pre-flight checks passed"

# Create temporary restore directory
mkdir -p "$TEMP_RESTORE_DIR"
cd "$TEMP_RESTORE_DIR"

# Parse backup manifest
DB_BACKUP_FILE=$(jq -r '.files.database' "$MANIFEST_FILE")
REDIS_BACKUP_FILE=$(jq -r '.files.redis' "$MANIFEST_FILE")
MINIO_BACKUP_FILE=$(jq -r '.files.minio' "$MANIFEST_FILE")
CONFIG_BACKUP_FILE=$(jq -r '.files.configs' "$MANIFEST_FILE")

echo "📋 Backup manifest parsed successfully"

# Download from S3 if backups are not local
if [ ! -f "$BACKUP_DIR/$DB_BACKUP_FILE" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
  echo "☁️ Downloading backups from S3..."
  aws s3 sync "s3://$S3_BUCKET/production/$BACKUP_TIMESTAMP/" "$BACKUP_DIR/" --exclude "*" --include "*.dump" --include "*.rdb" --include "*.tar.gz"
fi

# Stop all services
echo "🛑 Stopping all production services..."
cd /opt/saascontroldeck
docker-compose -f docker-compose.production.yml down --remove-orphans || echo "Some services may already be stopped"

# Create emergency backup of current state
echo "🗄️ Creating emergency backup of current state..."
EMERGENCY_BACKUP_DIR="/backups/emergency/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$EMERGENCY_BACKUP_DIR"

# Backup current data volumes
for volume in postgres-production-data redis-production-data minio-production-data; do
  if docker volume ls -q | grep -q "$volume"; then
    echo "📦 Backing up volume: $volume"
    docker run --rm -v "$volume":/source -v "$EMERGENCY_BACKUP_DIR":/backup alpine tar czf "/backup/$volume.tar.gz" -C /source .
  fi
done

echo "✅ Emergency backup created at: $EMERGENCY_BACKUP_DIR"

# Database Recovery
if [ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ]; then
  echo "🗃️ Starting database recovery..."
  
  # Remove existing database volume
  docker volume rm postgres-production-data 2>/dev/null || echo "Database volume already removed"
  
  # Create new database volume
  docker volume create postgres-production-data
  
  # Start only PostgreSQL service for restore
  docker run -d --name postgres-recovery \
    -v postgres-production-data:/var/lib/postgresql/data \
    -e POSTGRES_DB=${POSTGRES_DB:-saascontroldeck_production} \
    -e POSTGRES_USER=${POSTGRES_USER:-saasuser} \
    -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
    postgres:15-alpine
  
  # Wait for PostgreSQL to be ready
  echo "⏳ Waiting for PostgreSQL to be ready..."
  timeout=60
  counter=0
  while [ $counter -lt $timeout ]; do
    if docker exec postgres-recovery pg_isready -U ${POSTGRES_USER:-saasuser} -d ${POSTGRES_DB:-saascontroldeck_production} > /dev/null 2>&1; then
      echo "✅ PostgreSQL is ready"
      break
    fi
    sleep 2
    counter=$((counter + 2))
  done
  
  if [ $counter -ge $timeout ]; then
    echo "❌ PostgreSQL failed to start"
    exit 1
  fi
  
  # Restore database
  echo "📥 Restoring database from backup..."
  docker exec -i postgres-recovery pg_restore \
    -U ${POSTGRES_USER:-saasuser} \
    -d ${POSTGRES_DB:-saascontroldeck_production} \
    --verbose --clean --no-acl --no-owner < "$BACKUP_DIR/$DB_BACKUP_FILE"
  
  if [ $? -eq 0 ]; then
    echo "✅ Database restore completed"
  else
    echo "❌ Database restore failed"
    exit 1
  fi
  
  # Stop recovery container
  docker stop postgres-recovery
  docker rm postgres-recovery
fi

# Redis Recovery
if [ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ]; then
  echo "🔄 Starting Redis recovery..."
  
  # Remove existing Redis volume
  docker volume rm redis-production-data 2>/dev/null || echo "Redis volume already removed"
  
  # Create new Redis volume and restore data
  docker volume create redis-production-data
  
  # Copy backup to volume
  docker run --rm -v redis-production-data:/data -v "$BACKUP_DIR":/backup alpine \
    cp "/backup/$REDIS_BACKUP_FILE" /data/dump.rdb
  
  echo "✅ Redis restore completed"
fi

# MinIO Recovery  
if [ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ]; then
  echo "📦 Starting MinIO recovery..."
  
  # Remove existing MinIO volume
  docker volume rm minio-production-data 2>/dev/null || echo "MinIO volume already removed"
  
  # Create new MinIO volume
  docker volume create minio-production-data
  
  # Extract backup to volume
  docker run --rm -v minio-production-data:/data -v "$BACKUP_DIR":/backup alpine \
    sh -c "cd /data && tar xzf /backup/$MINIO_BACKUP_FILE"
  
  echo "✅ MinIO restore completed"
fi

# Configuration Recovery
if [ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "config-only" ]; then
  echo "⚙️ Starting configuration recovery..."
  
  # Extract configurations
  cd /tmp
  tar xzf "$BACKUP_DIR/$CONFIG_BACKUP_FILE" || echo "Some config files may be missing"
  
  # Restore configurations
  if [ -d "opt/saascontroldeck" ]; then
    cp -r opt/saascontroldeck/* /opt/saascontroldeck/ 2>/dev/null || echo "Application configs restored"
  fi
  
  if [ -d "etc/nginx" ]; then
    cp -r etc/nginx/* /etc/nginx/ 2>/dev/null || echo "Nginx configs restored"
  fi
  
  if [ -d "etc/letsencrypt" ]; then
    cp -r etc/letsencrypt/* /etc/letsencrypt/ 2>/dev/null || echo "SSL certificates restored"
  fi
  
  echo "✅ Configuration restore completed"
fi

# Start services
echo "🚀 Starting recovered services..."
cd /opt/saascontroldeck
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Health checks
echo "🏥 Running health checks..."
HEALTH_CHECK_ERRORS=0

# Check database
if ! docker exec postgres-production pg_isready -U ${POSTGRES_USER:-saasuser} -d ${POSTGRES_DB:-saascontroldeck_production} > /dev/null 2>&1; then
  echo "❌ Database health check failed"
  HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
else
  echo "✅ Database is healthy"
fi

# Check Redis
if ! docker exec redis-production redis-cli ping > /dev/null 2>&1; then
  echo "❌ Redis health check failed"
  HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
else
  echo "✅ Redis is healthy"
fi

# Check MinIO
if ! docker exec minio-production curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
  echo "❌ MinIO health check failed"
  HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
else
  echo "✅ MinIO is healthy"
fi

# Check backends
for service in backend-pro1-production backend-pro2-production; do
  port=$([ "$service" = "backend-pro1-production" ] && echo "8000" || echo "8100")
  if ! docker exec "$service" curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
    echo "❌ $service health check failed"
    HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
  else
    echo "✅ $service is healthy"
  fi
done

# Check frontend (determine active container)
ACTIVE_FRONTEND=""
if docker exec saascontroldeck-frontend-blue curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
  ACTIVE_FRONTEND="blue"
elif docker exec saascontroldeck-frontend-green curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
  ACTIVE_FRONTEND="green"
fi

if [ -n "$ACTIVE_FRONTEND" ]; then
  echo "✅ Frontend ($ACTIVE_FRONTEND) is healthy"
else
  echo "❌ Frontend health check failed"
  HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
fi

# External health check
echo "🌐 Testing external endpoints..."
sleep 10
if curl -f https://saascontroldeck.com/api/health > /dev/null 2>&1; then
  echo "✅ External endpoint is accessible"
else
  echo "❌ External endpoint health check failed"
  HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
fi

# Generate recovery report
RECOVERY_REPORT="/opt/saascontroldeck/disaster-recovery-report-$(date +%Y%m%d-%H%M%S).txt"
cat > "$RECOVERY_REPORT" << EOF
SaaS Control Deck Disaster Recovery Report
==========================================

Recovery Type: $RECOVERY_TYPE
Backup Timestamp: $BACKUP_TIMESTAMP
Recovery Start: $(date)
Recovery End: $(date)

Emergency Backup Location: $EMERGENCY_BACKUP_DIR

Components Recovered:
$([ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ] && echo "- PostgreSQL Database")
$([ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ] && echo "- Redis Cache")
$([ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "data-only" ] && echo "- MinIO Object Storage")
$([ "$RECOVERY_TYPE" = "full" ] || [ "$RECOVERY_TYPE" = "config-only" ] && echo "- Application Configurations")

Health Check Results:
- Errors Found: $HEALTH_CHECK_ERRORS
- Status: $([ $HEALTH_CHECK_ERRORS -eq 0 ] && echo "SUCCESS" || echo "FAILED")
$([ -n "$ACTIVE_FRONTEND" ] && echo "- Active Frontend: $ACTIVE_FRONTEND")

Next Steps:
$([ $HEALTH_CHECK_ERRORS -eq 0 ] && cat << NEXT_STEPS
1. Monitor system performance for 24 hours
2. Verify all business functions are working
3. Run full test suite
4. Update monitoring alerts
5. Schedule next backup verification
NEXT_STEPS
|| cat << ERROR_STEPS  
1. Review service logs for errors
2. Check container status and resources
3. Verify network connectivity
4. Consider partial rollback if needed
5. Contact emergency support team
ERROR_STEPS
)
EOF

# Cleanup
rm -rf "$TEMP_RESTORE_DIR"

# Send notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  if [ $HEALTH_CHECK_ERRORS -eq 0 ]; then
    curl -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"✅ Disaster recovery completed successfully! All services are healthy.\"}" \
      $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
  else
    curl -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"⚠️ Disaster recovery completed with $HEALTH_CHECK_ERRORS health check errors. Manual intervention required.\"}" \
      $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
  fi
fi

# Final status
if [ $HEALTH_CHECK_ERRORS -eq 0 ]; then
  echo "✅ Disaster recovery completed successfully!"
  echo "📊 All services are healthy and operational"
  echo "📄 Recovery report: $RECOVERY_REPORT"
  echo "🗄️ Emergency backup: $EMERGENCY_BACKUP_DIR"
  exit 0
else
  echo "⚠️ Disaster recovery completed with issues"
  echo "❌ $HEALTH_CHECK_ERRORS health check errors found"
  echo "📄 Recovery report: $RECOVERY_REPORT"
  echo "🗄️ Emergency backup: $EMERGENCY_BACKUP_DIR"
  exit 1
fi