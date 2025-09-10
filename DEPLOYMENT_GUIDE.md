# SaaS Control Deck - Multi-Environment Deployment Guide

This comprehensive guide covers the complete deployment strategy for the full-stack AI platform across multiple environments.

## 📋 Table of Contents

- [Overview](#overview)
- [Environment Architecture](#environment-architecture)
- [Prerequisites](#prerequisites)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [Vercel Deployment (Testing)](#vercel-deployment-testing)
- [Cloud Server Deployment](#cloud-server-deployment)
- [Monitoring & Alerting](#monitoring--alerting)
- [Backup & Disaster Recovery](#backup--disaster-recovery)
- [Security Configuration](#security-configuration)
- [Troubleshooting](#troubleshooting)

## 🏗️ Overview

The deployment architecture supports four environments:

1. **Development**: Local development (Firebase Studio - Port 9000)
2. **Testing**: Vercel deployment (automatic from `develop` branch)
3. **Staging**: Cloud server staging environment
4. **Production**: Cloud server production environment with blue-green deployment

## 🌐 Environment Architecture

### Development Environment
- **Platform**: Firebase Studio with Nix architecture
- **Port**: 9000 (auto-managed)
- **Frontend**: Next.js with hot reload
- **Backend**: Docker Compose development setup

### Testing Environment (Vercel)
- **Platform**: Vercel
- **Domain**: Auto-generated Vercel URLs
- **Backend**: Points to staging cloud server APIs
- **Deployment**: Automatic on `develop` branch push

### Staging Environment (Cloud Server)
- **Platform**: Cloud server with Docker Compose
- **Domain**: staging.saascontroldeck.com
- **Deployment**: Blue-green deployment simulation
- **Purpose**: Final testing before production

### Production Environment (Cloud Server)
- **Platform**: Cloud server with advanced orchestration
- **Domain**: saascontroldeck.com
- **Deployment**: True blue-green deployment with rollback
- **Features**: High availability, monitoring, backup

## 🔧 Prerequisites

### Local Development
- Node.js 20.x
- Docker and Docker Compose
- Git
- Firebase Studio (for development environment)

### Cloud Server Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Nginx installed
- 4+ CPU cores, 16GB+ RAM (production)
- 2+ CPU cores, 8GB+ RAM (staging)
- SSL certificates (Let's Encrypt)

### Required Tools
```bash
# Install on cloud server
apt-get update
apt-get install -y docker.io docker-compose nginx certbot python3-certbot-nginx jq curl

# Install AWS CLI (for backups)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## 🔑 GitHub Secrets Configuration

Configure the following secrets in your GitHub repository:

### Vercel Configuration
```
VERCEL_TOKEN=your_vercel_api_token
VERCEL_ORG_ID=your_vercel_org_id
VERCEL_PROJECT_ID=your_vercel_project_id
```

### Cloud Server Configuration
```
CLOUD_SERVER_HOST=your_cloud_server_ip
CLOUD_SERVER_USER=deploy_user
CLOUD_SERVER_SSH_KEY=your_private_ssh_key
```

### Container Registry
```
# GitHub Container Registry (automatically available)
GITHUB_TOKEN=automatically_provided
```

### Database Configuration
```
POSTGRES_HOST=localhost
POSTGRES_USER=saasuser
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=saascontroldeck_production
REDIS_PASSWORD=redis_password_here
```

### External Services
```
MINIO_ACCESS_KEY=minio_access_key
MINIO_SECRET_KEY=minio_secret_key
SENTRY_DSN=your_sentry_dsn
BACKEND_SENTRY_DSN=your_backend_sentry_dsn
ANALYTICS_ID=your_analytics_id
GRAFANA_PASSWORD=grafana_admin_password
GRAFANA_SECRET_KEY=grafana_secret_key
```

### Backup Configuration
```
S3_BACKUP_BUCKET=saascontroldeck-backups
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

### Notifications
```
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

## 🚀 Vercel Deployment (Testing)

### Setup Process

1. **Link Vercel to GitHub**:
   ```bash
   npm install -g vercel
   vercel login
   vercel --prod  # Link to GitHub repository
   ```

2. **Configure Vercel Project**:
   - Set build command: `npm run build`
   - Set output directory: `frontend/.next`
   - Set install command: `npm ci`

3. **Environment Variables in Vercel**:
   ```
   NEXT_PUBLIC_ENVIRONMENT=vercel
   NEXT_PUBLIC_APP_NAME=SaaS Control Deck
   BACKEND_PRO1_URL=https://api-staging.saascontroldeck.com/pro1
   BACKEND_PRO2_URL=https://api-staging.saascontroldeck.com/pro2
   GOOGLE_GENAI_API_KEY=your_google_ai_api_key
   ```

### Automatic Deployment

The GitHub Actions workflow automatically deploys to Vercel when:
- Push to `develop` branch
- Manual workflow dispatch with `vercel-staging` environment

### Monitoring Vercel Deployments

- **Dashboard**: https://vercel.com/dashboard
- **Deployment logs**: Available in Vercel dashboard
- **Performance**: Lighthouse CI runs automatically

## 🏗️ Cloud Server Deployment

### Initial Server Setup

1. **Create deployment user**:
   ```bash
   sudo adduser deploy
   sudo usermod -aG docker deploy
   sudo mkdir -p /home/deploy/.ssh
   # Add your public SSH key to /home/deploy/.ssh/authorized_keys
   ```

2. **Create directory structure**:
   ```bash
   sudo mkdir -p /opt/saascontroldeck
   sudo mkdir -p /backups/saascontroldeck
   sudo chown -R deploy:deploy /opt/saascontroldeck
   sudo chown -R deploy:deploy /backups/saascontroldeck
   ```

3. **Upload configuration files**:
   ```bash
   scp docker-compose.staging.yml deploy@your-server:/opt/saascontroldeck/
   scp docker-compose.production.yml deploy@your-server:/opt/saascontroldeck/
   scp .env.staging deploy@your-server:/opt/saascontroldeck/
   scp .env.production deploy@your-server:/opt/saascontroldeck/
   scp -r monitoring/ deploy@your-server:/opt/saascontroldeck/
   scp -r scripts/ deploy@your-server:/opt/saascontroldeck/
   ```

### SSL Certificate Setup

```bash
# Run on cloud server
sudo /opt/saascontroldeck/scripts/setup-ssl.sh saascontroldeck.com production
sudo /opt/saascontroldeck/scripts/setup-ssl.sh staging.saascontroldeck.com staging
```

### Staging Deployment

```bash
# Manual deployment
cd /opt/saascontroldeck
docker-compose -f docker-compose.staging.yml up -d

# Or using deployment script
./scripts/deploy-staging.sh main-latest
```

### Production Deployment

Production uses blue-green deployment:

```bash
# Automatic via GitHub Actions on main branch push
# Or manual deployment
./scripts/deploy-production.sh main-latest
```

## 📊 Monitoring & Alerting

### Metrics Collection

- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboards and visualization
- **Node Exporter**: System metrics
- **cAdvisor**: Container metrics

### Access Points

- **Production Grafana**: https://grafana.saascontroldeck.com
- **Staging Grafana**: https://staging-grafana.saascontroldeck.com
- **Prometheus**: Internal access only (port 9090/9091)

### Key Dashboards

1. **System Overview**: CPU, memory, disk, network
2. **Application Performance**: Response times, error rates
3. **Database Performance**: Query performance, connections
4. **Frontend Metrics**: Page load times, user interactions
5. **Security Monitoring**: Failed logins, suspicious activity

### Alerting Rules

Alerts are configured for:
- High CPU usage (>80% for 5 minutes)
- High memory usage (>90% for 5 minutes)
- Disk space low (<10% free)
- Service downtime
- SSL certificate expiration
- Database connection issues
- High error rates (>5% for 5 minutes)

## 🗄️ Backup & Disaster Recovery

### Automated Backups

**Production Backup Schedule**:
- **Full Backup**: Weekly (Sunday 1 AM)
- **Incremental Backup**: Daily (1 AM)
- **Retention**: 30 days local, 90 days S3

**Backup Components**:
- PostgreSQL database
- Redis cache data
- MinIO object storage
- Application configurations
- SSL certificates
- Docker images (full backup only)

### Backup Execution

```bash
# Manual backup
sudo /opt/saascontroldeck/scripts/backup-production.sh full

# Scheduled via cron
0 1 * * * /opt/saascontroldeck/scripts/backup-production.sh incremental
0 1 * * 0 /opt/saascontroldeck/scripts/backup-production.sh full
```

### Disaster Recovery

```bash
# Full system recovery
sudo /opt/saascontroldeck/scripts/disaster-recovery.sh 20241201-120000 full

# Data-only recovery
sudo /opt/saascontroldeck/scripts/disaster-recovery.sh 20241201-120000 data-only

# Config-only recovery
sudo /opt/saascontroldeck/scripts/disaster-recovery.sh 20241201-120000 config-only
```

### Recovery Testing

- **Monthly**: Test backup integrity
- **Quarterly**: Full disaster recovery simulation
- **Annually**: Multi-region failover test

## 🔒 Security Configuration

### SSL/TLS Configuration

- **Certificates**: Let's Encrypt with automatic renewal
- **Protocols**: TLS 1.2 and 1.3 only
- **Ciphers**: Modern cipher suites
- **HSTS**: Enabled with 2-year max-age
- **OCSP Stapling**: Enabled

### Security Headers

```nginx
add_header Strict-Transport-Security "max-age=63072000" always;
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'";
```

### Access Control

- **SSH**: Key-based authentication only
- **Database**: Network isolation within Docker
- **API**: JWT tokens with expiration
- **Admin Panels**: IP whitelist + strong passwords

### Security Monitoring

- **Failed login attempts**: Monitored and alerted
- **SSL certificate expiry**: Weekly checks
- **Vulnerability scanning**: Container images scanned
- **Dependency audits**: NPM audit in CI/CD

## 🔧 Troubleshooting

### Common Issues

#### Deployment Failures

**Symptom**: GitHub Actions deployment fails
```bash
# Check deployment logs in GitHub Actions
# SSH to server and check container status
docker ps -a
docker logs <container_name>
```

**Solution**:
1. Check container logs for specific errors
2. Verify environment variables
3. Ensure sufficient resources
4. Check network connectivity

#### Service Health Check Failures

**Symptom**: Health checks fail after deployment
```bash
# Test health endpoints manually
curl -f http://localhost:3000/api/health
curl -f http://localhost:8000/health
curl -f http://localhost:8100/health
```

**Solution**:
1. Check application startup logs
2. Verify database connectivity
3. Check Redis connectivity
4. Ensure all environment variables are set

#### SSL Certificate Issues

**Symptom**: SSL certificate errors
```bash
# Check certificate status
sudo certbot certificates
sudo certbot renew --dry-run

# Test SSL configuration
openssl s_client -connect saascontroldeck.com:443 -servername saascontroldeck.com
```

**Solution**:
1. Renew certificates manually
2. Check Nginx configuration
3. Verify domain DNS settings
4. Restart Nginx service

#### Database Connection Issues

**Symptom**: Cannot connect to database
```bash
# Check database container
docker exec postgres-production pg_isready -U saasuser

# Check network connectivity
docker network ls
docker network inspect saascontroldeck-production
```

**Solution**:
1. Check database container status
2. Verify network configuration
3. Check connection string format
4. Review database logs

### Rollback Procedures

#### Frontend Rollback

```bash
# Automatic rollback (part of deployment process)
# Manual rollback
sudo /opt/saascontroldeck/scripts/rollback-frontend.sh

# Check rollback status
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

#### Database Rollback

```bash
# Restore from backup
sudo /opt/saascontroldeck/scripts/disaster-recovery.sh 20241201-120000 data-only

# Verify data integrity
docker exec postgres-production psql -U saasuser -d saascontroldeck_production -c "SELECT COUNT(*) FROM users;"
```

### Performance Issues

#### High CPU Usage

```bash
# Check container resource usage
docker stats

# Check system resources
top
htop
```

#### High Memory Usage

```bash
# Check memory usage per container
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check system memory
free -h
```

#### Slow Database Queries

```bash
# Check PostgreSQL slow queries
docker exec postgres-production psql -U saasuser -d saascontroldeck_production -c "
SELECT query, mean_time, rows, 100.0 * shared_blks_hit / 
NULLIF(shared_blks_hit + shared_blks_read, 0) AS hit_percent 
FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Getting Help

1. **Check logs**: Always start with application and system logs
2. **GitHub Issues**: Report bugs and feature requests
3. **Documentation**: Review this guide and inline comments
4. **Monitoring**: Use Grafana dashboards for insights
5. **Community**: Engage with the project community

### Emergency Contacts

- **Production Issues**: [emergency-email@saascontroldeck.com]
- **Security Issues**: [security@saascontroldeck.com]
- **Infrastructure**: [infrastructure@saascontroldeck.com]

---

## 📚 Additional Resources

- [Backend Deployment Guide](backend/DEPLOYMENT_GUIDE.md)
- [Monitoring Setup Guide](monitoring/README.md)
- [Security Best Practices](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

**Next Steps**:
1. Configure GitHub secrets
2. Set up cloud server infrastructure
3. Deploy to staging environment
4. Run integration tests
5. Deploy to production
6. Set up monitoring and alerts
7. Test backup and recovery procedures

This deployment guide ensures a robust, scalable, and secure deployment of the SaaS Control Deck platform across all environments.