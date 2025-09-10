#!/bin/bash
set -e

# Frontend Production Rollback Script
# Usage: ./rollback-frontend.sh [backup-timestamp]

BACKUP_TIMESTAMP=${1:-$(ls -t /backups/frontend/deployment-*.json | head -1 | grep -o '[0-9]\{8\}-[0-9]\{6\}' | head -1)}
BLUE_CONTAINER="saascontroldeck-frontend-blue"
GREEN_CONTAINER="saascontroldeck-frontend-green"
NGINX_CONFIG="/etc/nginx/sites-available/saascontroldeck.com"
BACKUP_DIR="/backups/frontend"

echo "🔄 Starting frontend production rollback..."
echo "Backup timestamp: $BACKUP_TIMESTAMP"

# Check if backup exists
DEPLOYMENT_RECORD="$BACKUP_DIR/deployment-$BACKUP_TIMESTAMP.json"
if [ ! -f "$DEPLOYMENT_RECORD" ]; then
  echo "❌ Deployment record not found: $DEPLOYMENT_RECORD"
  echo "Available backups:"
  ls -la $BACKUP_DIR/deployment-*.json 2>/dev/null || echo "No deployment records found"
  exit 1
fi

# Read deployment record
PREVIOUS_CONTAINER=$(jq -r '.previous_container' $DEPLOYMENT_RECORD)
ACTIVE_CONTAINER=$(jq -r '.active_container' $DEPLOYMENT_RECORD)

if [ "$PREVIOUS_CONTAINER" == "null" ] || [ -z "$PREVIOUS_CONTAINER" ]; then
  echo "❌ No previous container found in deployment record"
  exit 1
fi

echo "📊 Active container: $ACTIVE_CONTAINER"
echo "🔄 Rolling back to: $PREVIOUS_CONTAINER"

# Determine ports
if [ "$PREVIOUS_CONTAINER" == "$BLUE_CONTAINER" ]; then
  ROLLBACK_PORT=3001
else
  ROLLBACK_PORT=3002
fi

# Check if rollback container exists and is healthy
if ! docker ps --format '{{.Names}}' | grep -q $PREVIOUS_CONTAINER; then
  echo "❌ Rollback container $PREVIOUS_CONTAINER is not running"
  exit 1
fi

# Test rollback container health
if ! docker exec $PREVIOUS_CONTAINER curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
  echo "❌ Rollback container is not healthy"
  exit 1
fi

echo "✅ Rollback container is healthy"

# Backup current nginx configuration
cp $NGINX_CONFIG $BACKUP_DIR/nginx-rollback-$(date +%Y%m%d-%H%M%S).conf

# Update nginx configuration to point back to previous container
echo "🔧 Updating nginx configuration for rollback..."
sed -i "s/proxy_pass http:\/\/localhost:[0-9]\+;/proxy_pass http:\/\/localhost:$ROLLBACK_PORT;/g" $NGINX_CONFIG

# Test nginx configuration
if ! nginx -t; then
  echo "❌ Nginx configuration test failed during rollback"
  exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx configuration..."
systemctl reload nginx

# Wait and test
sleep 5

# Test the production endpoint
echo "🧪 Testing production endpoint after rollback..."
for i in {1..3}; do
  if curl -f https://saascontroldeck.com/api/health > /dev/null 2>&1; then
    echo "✅ Production endpoint health check passed"
    break
  elif [ $i -eq 3 ]; then
    echo "❌ Production endpoint health check failed after rollback"
    exit 1
  else
    echo "⏳ Retrying health check... (attempt $i/3)"
    sleep 10
  fi
done

# Stop the failed container
echo "🛑 Stopping failed container: $ACTIVE_CONTAINER"
docker stop $ACTIVE_CONTAINER

# Create rollback record
cat > $BACKUP_DIR/rollback-$(date +%Y%m%d-%H%M%S).json << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "rolled_back_from": "$ACTIVE_CONTAINER",
  "rolled_back_to": "$PREVIOUS_CONTAINER",
  "rollback_reason": "manual",
  "status": "success"
}
EOF

echo "✅ Frontend production rollback completed successfully!"
echo "🌐 Production URL: https://saascontroldeck.com"
echo "📊 Active container: $PREVIOUS_CONTAINER (port $ROLLBACK_PORT)"

# Send rollback notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"🔄 Frontend production rollback completed! Active: $PREVIOUS_CONTAINER\"}" \
    $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
fi