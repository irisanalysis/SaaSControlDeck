#!/bin/bash
set -e

# Frontend Staging Deployment Script
# Usage: ./deploy-staging.sh <docker-image-tag>

IMAGE_TAG=${1:-latest}
CONTAINER_NAME="saascontroldeck-frontend-staging"
NETWORK_NAME="saascontroldeck-staging"
PORT=3000

echo "🚀 Starting frontend staging deployment..."
echo "Image tag: $IMAGE_TAG"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create Docker network if it doesn't exist
docker network create $NETWORK_NAME 2>/dev/null || echo "Network $NETWORK_NAME already exists"

# Stop and remove existing container
echo "🛑 Stopping existing staging container..."
docker stop $CONTAINER_NAME 2>/dev/null || echo "Container $CONTAINER_NAME not running"
docker rm $CONTAINER_NAME 2>/dev/null || echo "Container $CONTAINER_NAME already removed"

# Pull the latest image
echo "📥 Pulling latest frontend image..."
docker pull ghcr.io/irisanalysis/saascontroldeck-frontend:$IMAGE_TAG

# Start new container
echo "🚀 Starting new staging container..."
docker run -d \
  --name $CONTAINER_NAME \
  --network $NETWORK_NAME \
  --restart unless-stopped \
  -p $PORT:3000 \
  -e NODE_ENV=production \
  -e NEXT_PUBLIC_ENVIRONMENT=staging \
  -e NEXT_PUBLIC_APP_NAME="SaaS Control Deck" \
  -e BACKEND_PRO1_URL="http://backend-pro1-staging:8000" \
  -e BACKEND_PRO2_URL="http://backend-pro2-staging:8100" \
  -e NEXT_PUBLIC_CDN_URL="https://cdn-staging.saascontroldeck.com" \
  -e NEXT_PUBLIC_ASSETS_URL="https://assets-staging.saascontroldeck.com" \
  --health-cmd="curl -f http://localhost:3000/api/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  ghcr.io/irisanalysis/saascontroldeck-frontend:$IMAGE_TAG

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
  if docker exec $CONTAINER_NAME curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Frontend staging deployment successful!"
    break
  fi
  sleep 2
  counter=$((counter + 2))
  echo "⏳ Health check failed, retrying... ($counter/$timeout seconds)"
done

if [ $counter -ge $timeout ]; then
  echo "❌ Deployment failed: Container not healthy after $timeout seconds"
  docker logs $CONTAINER_NAME --tail 50
  exit 1
fi

# Update nginx configuration for staging
echo "🔧 Updating nginx configuration..."
cat > /etc/nginx/sites-available/staging.saascontroldeck.com << EOF
server {
    listen 80;
    server_name staging.saascontroldeck.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.saascontroldeck.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/staging.saascontroldeck.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.saascontroldeck.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Frontend proxy
    location / {
        proxy_pass http://localhost:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API proxy for staging
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
}
EOF

# Enable site and reload nginx
ln -sf /etc/nginx/sites-available/staging.saascontroldeck.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo "✅ Frontend staging deployment completed successfully!"
echo "🌐 Staging URL: https://staging.saascontroldeck.com"
echo "📊 Container status: $(docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' --filter name=$CONTAINER_NAME)"