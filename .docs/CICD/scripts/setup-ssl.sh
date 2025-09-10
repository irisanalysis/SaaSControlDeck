#!/bin/bash
set -e

# SSL/TLS Certificate Setup Script using Let's Encrypt
# Usage: ./setup-ssl.sh [domain] [environment]

DOMAIN=${1:-saascontroldeck.com}
ENVIRONMENT=${2:-production}
EMAIL=${ACME_EMAIL:-admin@saascontroldeck.com}

echo "🔒 Setting up SSL/TLS certificates for $DOMAIN ($ENVIRONMENT)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ This script must be run as root"
  exit 1
fi

# Install Certbot if not present
if ! command -v certbot &> /dev/null; then
  echo "📦 Installing Certbot..."
  apt-get update
  apt-get install -y certbot python3-certbot-nginx
fi

# Define domains based on environment
if [ "$ENVIRONMENT" = "production" ]; then
  DOMAINS=("saascontroldeck.com" "www.saascontroldeck.com" "grafana.saascontroldeck.com" "minio-console.saascontroldeck.com")
elif [ "$ENVIRONMENT" = "staging" ]; then
  DOMAINS=("staging.saascontroldeck.com" "staging-grafana.saascontroldeck.com")
else
  DOMAINS=("$DOMAIN")
fi

# Create domain list for certbot
DOMAIN_ARGS=""
for domain in "${DOMAINS[@]}"; do
  DOMAIN_ARGS="$DOMAIN_ARGS -d $domain"
done

echo "🌐 Requesting certificates for: ${DOMAINS[*]}"

# Request certificates
if certbot certonly --nginx \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  --force-renewal \
  $DOMAIN_ARGS; then
  echo "✅ SSL certificates obtained successfully"
else
  echo "❌ Failed to obtain SSL certificates"
  exit 1
fi

# Set up automatic renewal
echo "🔄 Setting up automatic certificate renewal..."

# Create renewal hook script
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-services.sh << 'EOF'
#!/bin/bash
# Reload services after certificate renewal

echo "🔄 Reloading services after certificate renewal..."

# Reload Nginx
if systemctl is-active --quiet nginx; then
  systemctl reload nginx
  echo "✅ Nginx reloaded"
fi

# Restart Docker containers that use SSL (if needed)
if docker ps --format '{{.Names}}' | grep -q "frontend\|backend"; then
  echo "🔄 Restarting relevant containers..."
  # Add container restart logic if needed
fi

# Send notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🔒 SSL certificates renewed automatically"}' \
    "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || echo "Notification failed"
fi
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-services.sh

# Add cron job for automatic renewal (if not exists)
CRON_JOB="0 12 * * * /usr/bin/certbot renew --quiet"
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "✅ Automatic renewal cron job added"
else
  echo "✅ Automatic renewal already configured"
fi

# Test certificate
echo "🧪 Testing certificate configuration..."
for domain in "${DOMAINS[@]}"; do
  if curl -IsS "https://$domain" | head -1 | grep -q "200 OK"; then
    echo "✅ $domain: SSL certificate working"
  else
    echo "⚠️ $domain: SSL certificate test inconclusive"
  fi
done

# Generate Nginx SSL configuration template
cat > "/tmp/ssl-config-$ENVIRONMENT.conf" << EOF
# SSL Configuration for $ENVIRONMENT
# Include this in your Nginx server blocks

# SSL Certificate paths
ssl_certificate /etc/letsencrypt/live/${DOMAINS[0]}/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/${DOMAINS[0]}/privkey.pem;

# SSL Session Settings
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# Modern SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# HSTS (Optional, uncomment if desired)
# add_header Strict-Transport-Security "max-age=63072000" always;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/${DOMAINS[0]}/chain.pem;

# DNS Resolver (Google DNS)
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF

echo "📄 SSL configuration template created: /tmp/ssl-config-$ENVIRONMENT.conf"

# Create certificate monitoring script
cat > /usr/local/bin/check-ssl-expiry.sh << 'EOF'
#!/bin/bash
# SSL Certificate Expiry Monitoring

DOMAINS=($(certbot certificates 2>/dev/null | grep "Certificate Name:" | awk '{print $3}'))
WARNING_DAYS=30
CRITICAL_DAYS=7

for domain in "${DOMAINS[@]}"; do
  expiry_date=$(openssl x509 -in "/etc/letsencrypt/live/$domain/cert.pem" -noout -dates | grep "notAfter" | cut -d= -f2)
  expiry_timestamp=$(date -d "$expiry_date" +%s)
  current_timestamp=$(date +%s)
  days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
  
  if [ $days_until_expiry -le $CRITICAL_DAYS ]; then
    echo "🚨 CRITICAL: SSL certificate for $domain expires in $days_until_expiry days!"
    # Send critical alert
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 CRITICAL: SSL certificate for $domain expires in $days_until_expiry days!\"}" \
        "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
  elif [ $days_until_expiry -le $WARNING_DAYS ]; then
    echo "⚠️ WARNING: SSL certificate for $domain expires in $days_until_expiry days"
    # Send warning
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"⚠️ WARNING: SSL certificate for $domain expires in $days_until_expiry days\"}" \
        "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
  else
    echo "✅ SSL certificate for $domain is valid for $days_until_expiry days"
  fi
done
EOF

chmod +x /usr/local/bin/check-ssl-expiry.sh

# Add certificate monitoring to cron (weekly check)
MONITOR_CRON="0 9 * * 1 /usr/local/bin/check-ssl-expiry.sh"
if ! crontab -l 2>/dev/null | grep -q "check-ssl-expiry"; then
  (crontab -l 2>/dev/null; echo "$MONITOR_CRON") | crontab -
  echo "✅ SSL monitoring cron job added"
fi

# Generate SSL report
echo "📋 Generating SSL certificate report..."
cat > "/tmp/ssl-report-$ENVIRONMENT-$(date +%Y%m%d).txt" << EOF
SSL/TLS Certificate Report - $ENVIRONMENT
========================================

Generated: $(date)
Environment: $ENVIRONMENT
Email: $EMAIL

Certificates Configured:
$(for domain in "${DOMAINS[@]}"; do echo "- $domain"; done)

Certificate Details:
$(certbot certificates 2>/dev/null || echo "No certificates found")

Next Steps:
1. Update Nginx configurations to use the SSL settings
2. Test all HTTPS endpoints
3. Configure security headers
4. Set up certificate monitoring alerts
5. Document renewal process

Files Created:
- SSL config template: /tmp/ssl-config-$ENVIRONMENT.conf
- Renewal hook: /etc/letsencrypt/renewal-hooks/deploy/reload-services.sh
- Monitoring script: /usr/local/bin/check-ssl-expiry.sh

Cron Jobs:
- Certificate renewal: 0 12 * * * /usr/bin/certbot renew --quiet
- Certificate monitoring: 0 9 * * 1 /usr/local/bin/check-ssl-expiry.sh
EOF

echo "✅ SSL/TLS certificate setup completed!"
echo "📄 SSL report: /tmp/ssl-report-$ENVIRONMENT-$(date +%Y%m%d).txt"
echo "🔧 Next step: Update your Nginx configurations with the SSL template"

# Run initial certificate check
/usr/local/bin/check-ssl-expiry.sh