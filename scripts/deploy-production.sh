#!/bin/bash
set -e

# Frontend Production Deployment Script with Blue-Green Deployment
# Usage: ./deploy-production.sh <docker-image-tag>

IMAGE_TAG=${1:-latest}
BLUE_CONTAINER="saascontroldeck-frontend-blue"
GREEN_CONTAINER="saascontroldeck-frontend-green"
NETWORK_NAME="saascontroldeck-production"
BLUE_PORT=3001
GREEN_PORT=3002
NGINX_CONFIG="/etc/nginx/sites-available/saascontroldeck.com"
BACKUP_DIR="/backups/frontend"

echo "🚀 Starting frontend production blue-green deployment..."
echo "Image tag: $IMAGE_TAG"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create backup directory
mkdir -p $BACKUP_DIR

# Create Docker network if it doesn't exist
docker network create $NETWORK_NAME 2>/dev/null || echo "Network $NETWORK_NAME already exists"

# Determine which container is currently active
CURRENT_ACTIVE=""
if docker ps --format '{{.Names}}' | grep -q $BLUE_CONTAINER; then
    if curl -f http://localhost:$BLUE_PORT/api/health > /dev/null 2>&1; then
        CURRENT_ACTIVE="blue"
        NEW_CONTAINER=$GREEN_CONTAINER
        NEW_PORT=$GREEN_PORT
        OLD_CONTAINER=$BLUE_CONTAINER
        OLD_PORT=$BLUE_PORT
    fi
elif docker ps --format '{{.Names}}' | grep -q $GREEN_CONTAINER; then
    if curl -f http://localhost:$GREEN_PORT/api/health > /dev/null 2>&1; then
        CURRENT_ACTIVE="green"
        NEW_CONTAINER=$BLUE_CONTAINER
        NEW_PORT=$BLUE_PORT
        OLD_CONTAINER=$GREEN_CONTAINER
        OLD_PORT=$GREEN_PORT
    fi
else
    # No active container, start with blue
    CURRENT_ACTIVE="none"
    NEW_CONTAINER=$BLUE_CONTAINER
    NEW_PORT=$BLUE_PORT
    OLD_CONTAINER=""
    OLD_PORT=""
fi

echo "📊 Current active: $CURRENT_ACTIVE"
echo "🎯 Deploying to: $(echo $NEW_CONTAINER | sed 's/.*-//')"

# Stop and remove the new container if it exists
docker stop $NEW_CONTAINER 2>/dev/null || echo "Container $NEW_CONTAINER not running"
docker rm $NEW_CONTAINER 2>/dev/null || echo "Container $NEW_CONTAINER already removed"

# Pull the latest image
echo "📥 Pulling latest frontend image..."
docker pull ghcr.io/irisanalysis/saascontroldeck-frontend:$IMAGE_TAG

# Start new container
echo "🚀 Starting new production container..."
docker run -d \
  --name $NEW_CONTAINER \
  --network $NETWORK_NAME \
  --restart unless-stopped \
  -p $NEW_PORT:3000 \
  -e NODE_ENV=production \
  -e NEXT_PUBLIC_ENVIRONMENT=production \
  -e NEXT_PUBLIC_APP_NAME="SaaS Control Deck" \
  -e BACKEND_PRO1_URL="http://backend-pro1-production:8000" \
  -e BACKEND_PRO2_URL="http://backend-pro2-production:8100" \
  -e NEXT_PUBLIC_CDN_URL="https://cdn.saascontroldeck.com" \
  -e NEXT_PUBLIC_ASSETS_URL="https://assets.saascontroldeck.com" \
  -e NEXT_PUBLIC_SENTRY_DSN="$SENTRY_DSN" \
  -e NEXT_PUBLIC_ANALYTICS_ID="$ANALYTICS_ID" \
  --health-cmd="curl -f http://localhost:3000/api/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  ghcr.io/irisanalysis/saascontroldeck-frontend:$IMAGE_TAG

# Wait for new container to be healthy
echo "⏳ Waiting for new container to be healthy..."
timeout=300
counter=0
while [ $counter -lt $timeout ]; do
  if docker exec $NEW_CONTAINER curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ New container is healthy!"
    break
  fi
  sleep 2
  counter=$((counter + 2))
  if [ $((counter % 30)) -eq 0 ]; then
    echo "⏳ Health check in progress... ($counter/$timeout seconds)"
  fi
done

if [ $counter -ge $timeout ]; then
  echo "❌ Deployment failed: New container not healthy after $timeout seconds"
  docker logs $NEW_CONTAINER --tail 50
  exit 1
fi

# Run smoke tests on new container
echo "🧪 Running smoke tests on new container..."
if ! curl -f http://localhost:$NEW_PORT/ > /dev/null 2>&1; then
  echo "❌ Smoke test failed: Root endpoint not accessible"
  docker logs $NEW_CONTAINER --tail 20
  exit 1
fi

# Backup current nginx configuration
if [ -f $NGINX_CONFIG ]; then
  cp $NGINX_CONFIG $BACKUP_DIR/nginx-$(date +%Y%m%d-%H%M%S).conf
fi

# Update nginx configuration to point to new container
echo "🔧 Updating nginx configuration for blue-green switch..."
cat > $NGINX_CONFIG << EOF
server {
    listen 80;
    server_name saascontroldeck.com www.saascontroldeck.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://saascontroldeck.com\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.saascontroldeck.com;
    
    # Redirect www to non-www
    return 301 https://saascontroldeck.com\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name saascontroldeck.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/saascontroldeck.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/saascontroldeck.com/privkey.pem;
    
    # SSL optimization
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozTLS:10m;
    ssl_session_tickets off;
    
    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend proxy (Blue-Green Deployment)
    location / {
        proxy_pass http://localhost:$NEW_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend API proxy for production
    location /api/pro1/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/pro2/ {
        proxy_pass http://localhost:8100/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        proxy_pass http://localhost:$NEW_PORT;
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://localhost:$NEW_PORT;
        access_log off;
    }
}
EOF

# Test nginx configuration
if ! nginx -t; then
  echo "❌ Nginx configuration test failed. Rolling back..."
  if [ -f $BACKUP_DIR/nginx-*.conf ]; then
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/nginx-*.conf | head -1)
    cp $LATEST_BACKUP $NGINX_CONFIG
  fi
  exit 1
fi

# Reload nginx with zero downtime
echo "🔄 Reloading nginx configuration..."
systemctl reload nginx

# Wait a moment for nginx to pick up changes
sleep 5

# Test the production endpoint
echo "🧪 Testing production endpoint after nginx reload..."
for i in {1..3}; do
  if curl -f https://saascontroldeck.com/api/health > /dev/null 2>&1; then
    echo "✅ Production endpoint health check passed"
    break
  elif [ $i -eq 3 ]; then
    echo "❌ Production endpoint health check failed after 3 attempts"
    exit 1
  else
    echo "⏳ Retrying health check... (attempt $i/3)"
    sleep 10
  fi
done

# Stop old container if it exists
if [ -n "$OLD_CONTAINER" ]; then
  echo "🛑 Stopping old container: $OLD_CONTAINER"
  docker stop $OLD_CONTAINER
  
  # Keep old container for potential rollback (remove after 24h via cron)
  echo "📦 Old container kept for rollback: $OLD_CONTAINER"
fi

# Clean up old images (keep last 3)
echo "🧹 Cleaning up old Docker images..."
docker images ghcr.io/irisanalysis/saascontroldeck-frontend --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | \
  grep -v REPOSITORY | sort -k3 -r | tail -n +4 | awk '{print $1":"$2}' | \
  xargs -r docker rmi 2>/dev/null || echo "No old images to clean"

# Create deployment record
echo "📝 Creating deployment record..."
cat > $BACKUP_DIR/deployment-$(date +%Y%m%d-%H%M%S).json << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "image_tag": "$IMAGE_TAG",
  "active_container": "$NEW_CONTAINER",
  "active_port": $NEW_PORT,
  "previous_container": "$OLD_CONTAINER",
  "deployment_type": "blue-green",
  "status": "success"
}
EOF

echo "✅ Frontend production deployment completed successfully!"
echo "🌐 Production URL: https://saascontroldeck.com"
echo "📊 Active container: $NEW_CONTAINER (port $NEW_PORT)"
echo "🔄 Blue-Green deployment completed"

# Send deployment notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"🚀 Frontend production deployment successful! Active: $NEW_CONTAINER\"}" \
    $SLACK_WEBHOOK_URL > /dev/null 2>&1 || echo "Slack notification failed"
fi