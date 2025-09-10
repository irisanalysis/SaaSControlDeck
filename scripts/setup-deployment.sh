#!/bin/bash
set -e

# Quick Deployment Setup Script for SaaS Control Deck
# Usage: ./setup-deployment.sh [environment] [domain]

ENVIRONMENT=${1:-production}
DOMAIN=${2:-saascontroldeck.com}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setting up deployment for SaaS Control Deck"
echo "Environment: $ENVIRONMENT"
echo "Domain: $DOMAIN"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

# Create deployment user if it doesn't exist
if ! id "deploy" &>/dev/null; then
    echo "👤 Creating deploy user..."
    adduser --disabled-password --gecos "" deploy
    usermod -aG docker deploy
    echo "✅ Deploy user created"
else
    echo "✅ Deploy user already exists"
fi

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p /opt/saascontroldeck/{scripts,monitoring,configs,data}
mkdir -p /backups/saascontroldeck/{production,staging,emergency}
mkdir -p /var/log/saascontroldeck

# Set permissions
chown -R deploy:deploy /opt/saascontroldeck
chown -R deploy:deploy /backups/saascontroldeck
chown -R deploy:deploy /var/log/saascontroldeck

echo "✅ Directory structure created"

# Install required packages
echo "📦 Installing required packages..."
apt-get update
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    jq \
    curl \
    wget \
    htop \
    tree \
    bc \
    unzip

# Start and enable Docker
systemctl start docker
systemctl enable docker

echo "✅ Packages installed"

# Install AWS CLI for backups
if ! command -v aws &> /dev/null; then
    echo "☁️ Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
    echo "✅ AWS CLI installed"
fi

# Copy deployment files
echo "📋 Copying deployment files..."
if [ -f "$SCRIPT_DIR/../docker-compose.${ENVIRONMENT}.yml" ]; then
    cp "$SCRIPT_DIR/../docker-compose.${ENVIRONMENT}.yml" /opt/saascontroldeck/
fi

if [ -f "$SCRIPT_DIR/../.env.${ENVIRONMENT}" ]; then
    cp "$SCRIPT_DIR/../.env.${ENVIRONMENT}" /opt/saascontroldeck/
fi

cp -r "$SCRIPT_DIR/../monitoring" /opt/saascontroldeck/ 2>/dev/null || echo "Monitoring configs not found"
cp "$SCRIPT_DIR"/*.sh /opt/saascontroldeck/scripts/
chmod +x /opt/saascontroldeck/scripts/*.sh

echo "✅ Deployment files copied"

# Set up SSL certificates
echo "🔒 Setting up SSL certificates..."
if [ "$ENVIRONMENT" = "production" ]; then
    /opt/saascontroldeck/scripts/setup-ssl.sh "$DOMAIN" production
elif [ "$ENVIRONMENT" = "staging" ]; then
    /opt/saascontroldeck/scripts/setup-ssl.sh "staging.$DOMAIN" staging
fi

# Configure basic Nginx
echo "🌐 Configuring Nginx..."
if [ "$ENVIRONMENT" = "production" ]; then
    cat > /etc/nginx/sites-available/$DOMAIN << 'EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
    return 301 https://DOMAIN_PLACEHOLDER$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.DOMAIN_PLACEHOLDER;
    return 301 https://DOMAIN_PLACEHOLDER$request_uri;
}

server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    # SSL configuration will be updated by deployment script
    ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Health check endpoint
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Placeholder - will be updated by deployment script
    location / {
        return 503 "Deployment in progress";
    }
}
EOF

    # Replace placeholder with actual domain
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/$DOMAIN
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

elif [ "$ENVIRONMENT" = "staging" ]; then
    cat > /etc/nginx/sites-available/staging.$DOMAIN << 'EOF'
server {
    listen 80;
    server_name staging.DOMAIN_PLACEHOLDER;
    return 301 https://staging.DOMAIN_PLACEHOLDER$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.DOMAIN_PLACEHOLDER;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/staging.DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.DOMAIN_PLACEHOLDER/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    # Health check endpoint
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Placeholder - will be updated by deployment script
    location / {
        return 503 "Deployment in progress";
    }
}
EOF

    # Replace placeholder with actual domain
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/staging.$DOMAIN
    ln -sf /etc/nginx/sites-available/staging.$DOMAIN /etc/nginx/sites-enabled/
fi

# Test Nginx configuration
nginx -t && systemctl reload nginx || echo "⚠️ Nginx configuration issues - will be fixed during deployment"

echo "✅ Basic Nginx configuration completed"

# Set up log rotation
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/saascontroldeck << 'EOF'
/var/log/saascontroldeck/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 deploy deploy
    postrotate
        /usr/bin/docker kill --signal=USR1 $(docker ps -q --filter label=logging=true) 2>/dev/null || true
    endscript
}
EOF

echo "✅ Log rotation configured"

# Set up cron jobs for maintenance
echo "⏰ Setting up cron jobs..."
cat > /tmp/deploy-cron << EOF
# SaaS Control Deck Maintenance Cron Jobs

# Health checks every 5 minutes
*/5 * * * * /opt/saascontroldeck/scripts/health-check.sh $ENVIRONMENT >/var/log/saascontroldeck/health-check.log 2>&1

# Daily backups at 1 AM
0 1 * * * /opt/saascontroldeck/scripts/backup-${ENVIRONMENT}.sh incremental >/var/log/saascontroldeck/backup.log 2>&1

# Weekly full backups on Sunday at 1 AM
0 1 * * 0 /opt/saascontroldeck/scripts/backup-${ENVIRONMENT}.sh full >/var/log/saascontroldeck/backup-full.log 2>&1

# SSL certificate checks weekly
0 9 * * 1 /usr/local/bin/check-ssl-expiry.sh >/var/log/saascontroldeck/ssl-check.log 2>&1

# Docker system cleanup monthly
0 2 1 * * /usr/bin/docker system prune -af >/var/log/saascontroldeck/docker-cleanup.log 2>&1

# Log rotation
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/saascontroldeck
EOF

# Install cron jobs for deploy user
sudo -u deploy crontab /tmp/deploy-cron
rm /tmp/deploy-cron

echo "✅ Cron jobs configured"

# Create systemd service for automatic startup
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/saascontroldeck.service << EOF
[Unit]
Description=SaaS Control Deck Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/saascontroldeck
ExecStart=/usr/bin/docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.${ENVIRONMENT}.yml down
TimeoutStartSec=0
User=deploy
Group=deploy

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable saascontroldeck.service

echo "✅ Systemd service created"

# Set up firewall rules
echo "🛡️ Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp

# Allow specific ports for monitoring (only from localhost)
ufw allow from 127.0.0.1 to any port 9090  # Prometheus
ufw allow from 127.0.0.1 to any port 3000  # Grafana

echo "✅ Firewall configured"

# Create initial environment file template
if [ ! -f "/opt/saascontroldeck/.env.$ENVIRONMENT" ]; then
    echo "📝 Creating environment file template..."
    cat > "/opt/saascontroldeck/.env.$ENVIRONMENT" << EOF
# SaaS Control Deck Environment Configuration - $ENVIRONMENT
# Fill in the values below before deployment

# Database Configuration
POSTGRES_USER=saasuser
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=saascontroldeck_${ENVIRONMENT}

# Redis Configuration
REDIS_PASSWORD=CHANGE_THIS_PASSWORD

# MinIO Configuration
MINIO_ACCESS_KEY=CHANGE_THIS_ACCESS_KEY
MINIO_SECRET_KEY=CHANGE_THIS_SECRET_KEY

# Monitoring
GRAFANA_PASSWORD=CHANGE_THIS_PASSWORD
$([ "$ENVIRONMENT" = "production" ] && echo "GRAFANA_SECRET_KEY=CHANGE_THIS_SECRET_KEY")

# External Services
SENTRY_DSN=
BACKEND_SENTRY_DSN=
ANALYTICS_ID=

# Notifications
SLACK_WEBHOOK_URL=

# Backup Configuration (Production only)
$([ "$ENVIRONMENT" = "production" ] && cat << PROD_ENV
S3_BACKUP_BUCKET=saascontroldeck-backups
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
PROD_ENV
)
EOF

    chown deploy:deploy "/opt/saascontroldeck/.env.$ENVIRONMENT"
    chmod 600 "/opt/saascontroldeck/.env.$ENVIRONMENT"
    echo "⚠️  IMPORTANT: Edit /opt/saascontroldeck/.env.$ENVIRONMENT with your actual values"
fi

# Generate deployment summary
echo ""
echo "🎉 Deployment setup completed successfully!"
echo ""
echo "📋 Setup Summary:"
echo "=================="
echo "Environment: $ENVIRONMENT"
echo "Domain: $DOMAIN"
echo "Deploy User: deploy"
echo "Application Directory: /opt/saascontroldeck"
echo "Backup Directory: /backups/saascontroldeck"
echo "Log Directory: /var/log/saascontroldeck"
echo ""
echo "🔧 Next Steps:"
echo "=============="
echo "1. Edit environment file: /opt/saascontroldeck/.env.$ENVIRONMENT"
echo "2. Configure GitHub secrets for CI/CD deployment"
echo "3. Push code to trigger automated deployment"
echo "4. Or run manual deployment:"
echo "   sudo -u deploy /opt/saascontroldeck/scripts/deploy-${ENVIRONMENT}.sh"
echo ""
echo "🏥 Health Check:"
echo "==============="
echo "Run: /opt/saascontroldeck/scripts/health-check.sh $ENVIRONMENT"
echo ""
echo "📊 Monitoring:"
echo "============="
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Grafana: https://grafana.$DOMAIN"
    echo "Application: https://$DOMAIN"
else
    echo "Grafana: https://staging-grafana.$DOMAIN"
    echo "Application: https://staging.$DOMAIN"
fi
echo ""
echo "🆘 Emergency Procedures:"
echo "======================="
echo "Rollback: /opt/saascontroldeck/scripts/rollback-frontend.sh"
echo "Disaster Recovery: /opt/saascontroldeck/scripts/disaster-recovery.sh"
echo "Backup: /opt/saascontroldeck/scripts/backup-${ENVIRONMENT}.sh"
echo ""

# Final security reminder
echo "🔒 SECURITY REMINDERS:"
echo "====================="
echo "1. Change all default passwords in .env.$ENVIRONMENT"
echo "2. Configure proper backup encryption"
echo "3. Set up monitoring alerts"
echo "4. Review and customize firewall rules"
echo "5. Test disaster recovery procedures"
echo ""

echo "✅ Setup completed! Review the above information and proceed with configuration."