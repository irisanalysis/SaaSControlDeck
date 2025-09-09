# Migration Guide - v1.0.0

## Overview

This is the initial release (v1.0.0) of SaaSControlDeck. No migration is required as this is a new platform.

## For New Installations

### Prerequisites

Before installing SaaSControlDeck v1.0.0, ensure you have:

- **Node.js**: Version 18.0 or higher
- **Python**: Version 3.11 or higher  
- **Docker**: Latest stable version
- **Docker Compose**: Version 2.0 or higher
- **Git**: Latest version

### Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/irisanalysis/SaaSControlDeck.git
   cd SaaSControlDeck
   ```

2. **Environment Configuration**:
   ```bash
   # Copy environment templates
   cp .env.example .env
   cp frontend/.env.local.example frontend/.env.local
   ```

3. **Install Dependencies**:
   ```bash
   # Frontend dependencies
   cd frontend && npm install
   
   # Backend dependencies (via Docker)
   cd ../backend && docker-compose build
   ```

### Configuration Files

#### Frontend Configuration
Update `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=SaaSControlDeck
GENKIT_API_KEY=your_genkit_api_key
```

#### Backend Configuration
Update `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/saascontrol
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=http://localhost:9000
```

### First-Time Setup

1. **Start Backend Services**:
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Initialize Database**:
   ```bash
   docker-compose exec api-gateway python -m alembic upgrade head
   ```

3. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Verify Installation**:
   - Frontend: http://localhost:9000
   - Backend API: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## CI/CD Setup

### GitHub Repository Configuration

1. **Set up GitHub Secrets**:
   ```
   DOCKER_USERNAME=your_docker_username
   DOCKER_PASSWORD=your_docker_password
   STAGING_HOST=your_staging_server
   PRODUCTION_HOST=your_production_server
   DATABASE_URL=your_database_url
   REDIS_URL=your_redis_url
   ```

2. **Configure Branch Protection**:
   - Enable branch protection for `main`
   - Require status checks
   - Require review from code owners
   - Enable automatic deletion of head branches

3. **Set up Environments**:
   - **Staging**: Auto-deploy from `develop` branch
   - **Production**: Manual approval required

### Monitoring Setup

1. **Prometheus Configuration**:
   - Metrics endpoint: `/metrics`
   - Default port: 9090
   - Retention: 15 days

2. **Grafana Dashboards**:
   - Application metrics dashboard
   - Infrastructure monitoring
   - Security alerts

3. **Alerting Rules**:
   - High error rate (>5%)
   - High response time (>2s)
   - Low disk space (<10%)
   - Failed deployments

## Security Configuration

### SSL/TLS Setup

1. **Development** (self-signed):
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout localhost.key -out localhost.crt
   ```

2. **Production** (Let's Encrypt):
   ```bash
   certbot --nginx -d yourdomain.com
   ```

### Firewall Rules

Configure your firewall to allow:
- **Port 80**: HTTP (redirects to HTTPS)
- **Port 443**: HTTPS
- **Port 22**: SSH (restricted IPs)
- **Port 8000-8199**: Backend APIs (internal only)

## Performance Optimization

### Frontend Optimization

1. **Build Configuration**:
   ```javascript
   // next.config.js
   module.exports = {
     experimental: {
       turbopack: true
     },
     images: {
       domains: ['your-cdn.com']
     }
   }
   ```

2. **CDN Setup**:
   - Configure Vercel CDN or Cloudflare
   - Enable static asset caching
   - Set up image optimization

### Backend Optimization

1. **Database Indexes**:
   ```sql
   CREATE INDEX idx_user_email ON users(email);
   CREATE INDEX idx_created_at ON logs(created_at);
   ```

2. **Redis Caching**:
   - Session storage: 24 hours
   - API responses: 5 minutes
   - User preferences: 1 hour

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check for port usage
   lsof -i :9000
   lsof -i :8000
   ```

2. **Docker Issues**:
   ```bash
   # Reset Docker environment
   docker-compose down -v
   docker system prune -f
   docker-compose up --build
   ```

3. **Permission Issues**:
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod +x scripts/*.sh
   ```

## Rollback Procedures

Since this is the initial release, no rollback procedures are needed. However, for future releases:

1. **Database Rollback**:
   ```bash
   python -m alembic downgrade -1
   ```

2. **Application Rollback**:
   ```bash
   git checkout v1.0.0
   docker-compose up --build
   ```

## Support Resources

- **Documentation**: `.docs/` directory
- **GitHub Issues**: Bug reports and feature requests
- **Architecture Guide**: `CLAUDE.md`
- **Deployment Guide**: `backend/DEPLOYMENT_GUIDE.md`

## Post-Installation Checklist

- [ ] All services are running
- [ ] Database is accessible
- [ ] Frontend loads correctly
- [ ] API endpoints respond
- [ ] CI/CD pipelines are configured
- [ ] Monitoring is active
- [ ] Security measures are in place
- [ ] Backups are configured
- [ ] SSL certificates are valid
- [ ] Performance metrics are collected

---

Welcome to SaaSControlDeck v1.0.0! 🚀