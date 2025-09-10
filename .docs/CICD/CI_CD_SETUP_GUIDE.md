# CI/CD Pipeline Setup Guide

This document provides instructions for setting up and configuring the comprehensive CI/CD pipeline for the SaaS Control Deck platform.

## 🏗️ Architecture Overview

The CI/CD pipeline is designed for a full-stack AI platform with:

- **Frontend**: Next.js 15.3.3 with TypeScript (Port 9000)
- **Backend**: Distributed Python microservices with FastAPI
  - backend-pro1: Ports 8000-8099
  - backend-pro2: Ports 8100-8199
- **Infrastructure**: PostgreSQL, Redis, MinIO, Ray computing, Prometheus monitoring

## 📁 Files Created

### GitHub Actions Workflows

- **`/.github/workflows/frontend-ci-cd.yml`**: Frontend build, test, and deployment pipeline
- **`/.github/workflows/backend-ci-cd.yml`**: Backend microservices CI/CD with multi-project support
- **`/.github/workflows/security-monitoring.yml`**: Comprehensive security scanning and monitoring
- **`/.github/workflows/infrastructure-monitoring.yml`**: Infrastructure health checks and auto-scaling
- **`/.github/workflows/quality-gates.yml`**: Code quality standards and coverage analysis

### Configuration Files

- **`/.github/environments/staging.yml`**: Staging environment configuration
- **`/.github/environments/production.yml`**: Production environment configuration
- **`/.github/CODEOWNERS`**: Code ownership and review requirements
- **`/.github/dependabot.yml`**: Automated dependency updates
- **`/.github/pull_request_template.md`**: Standardized PR template

### Docker and Deployment

- **`/frontend/Dockerfile`**: Multi-stage frontend container build
- **`/docker-compose.ci.yml`**: Testing environment with all services
- **`/scripts/deploy.sh`**: Deployment script with rollback capabilities

### Quality Assurance

- **`/.lighthouserc.json`**: Performance testing configuration
- **`/.markdownlint.json`**: Documentation quality standards
- **`/frontend/next.config.ts`**: Enhanced Next.js configuration

## 🚀 Quick Start

### 1. Repository Setup

Ensure your repository has the following secrets configured in GitHub Settings:

#### Staging Secrets
```
STAGING_DATABASE_URL
STAGING_REDIS_URL
STAGING_SECRET_KEY
STAGING_OPENAI_API_KEY
STAGING_GOOGLE_API_KEY
STAGING_SENTRY_DSN
STAGING_NEW_RELIC_LICENSE_KEY
STAGING_MINIO_ACCESS_KEY
STAGING_MINIO_SECRET_KEY
```

#### Production Secrets
```
PRODUCTION_DATABASE_URL
PRODUCTION_REDIS_URL
PRODUCTION_SECRET_KEY
PRODUCTION_OPENAI_API_KEY
PRODUCTION_GOOGLE_API_KEY
PRODUCTION_SENTRY_DSN
PRODUCTION_NEW_RELIC_LICENSE_KEY
PRODUCTION_DATADOG_API_KEY
PRODUCTION_MINIO_ACCESS_KEY
PRODUCTION_MINIO_SECRET_KEY
```

#### Container Registry
```
GITHUB_TOKEN  # Automatically provided by GitHub
```

### 2. Environment Protection Rules

Configure environment protection rules in GitHub:

**Staging Environment:**
- Require reviewers: `devops-team`, `senior-developers`
- Wait timer: 5 minutes
- Allowed branches: `develop`, `feature/*`, `hotfix/*`

**Production Environment:**
- Require reviewers: `devops-team`, `tech-leads`, `security-team`
- Minimum reviewers: 2
- Wait timer: 10 minutes
- Allowed branches: `main`, `hotfix/*`
- Required status checks: `security-scan`, `integration-tests`
- Deployment window: Business hours only (09:00-17:00 UTC)

### 3. Team Configuration

Set up the following GitHub teams:

- `@irisanalysis/core-team`
- `@irisanalysis/devops-team`
- `@irisanalysis/frontend-team`
- `@irisanalysis/backend-team`
- `@irisanalysis/security-team`
- `@irisanalysis/ai-team`
- `@irisanalysis/data-team`

## 🔄 Workflow Details

### Frontend CI/CD Pipeline

**Triggers:**
- Push to `main`, `develop`
- Pull requests
- Manual dispatch

**Stages:**
1. **Test & Lint**: ESLint, TypeScript checks, security audit
2. **Build**: Multi-platform Docker image build
3. **Security Scan**: Container vulnerability scanning
4. **Deploy Staging**: Automatic deployment on `develop` branch
5. **Deploy Production**: Manual approval for `main` branch
6. **Performance Monitoring**: Lighthouse CI analysis

### Backend CI/CD Pipeline

**Features:**
- **Change Detection**: Only builds affected services
- **Parallel Testing**: Runs tests for both backend projects simultaneously
- **Multi-stage Building**: Optimized Docker images
- **Integration Tests**: Full-stack integration testing
- **Security Scanning**: Dependency and container security

**Services:**
- API Gateway (Port 8000/8100)
- Data Service (Port 8001/8101)
- AI Service (Port 8002/8102)
- Celery Workers
- Monitoring (Prometheus)

### Security & Monitoring

**Daily Scans:**
- Dependency vulnerability scanning
- Docker image security analysis
- Secret scanning with TruffleHog
- License compliance checking
- CodeQL security analysis

**Infrastructure Monitoring:**
- Health checks every 6 hours
- Auto-scaling based on metrics
- Resource utilization tracking
- Alert notifications

## 🛠️ Deployment Process

### Automatic Deployment

**Staging:**
- Triggered on push to `develop` branch
- Automatic health checks
- E2E test execution

**Production:**
- Manual approval required
- Blue-green deployment strategy
- Comprehensive monitoring
- Automatic rollback on failure

### Manual Deployment

Use the deployment script for manual deployments:

```bash
# Deploy all services to staging
./scripts/deploy.sh -e staging -p all

# Deploy only frontend to production
./scripts/deploy.sh -e production -p frontend

# Rollback to previous version
./scripts/deploy.sh --rollback v1.2.0

# Scale services
./scripts/deploy.sh --scale 3

# Health check only
./scripts/deploy.sh --health-check
```

## 📊 Quality Gates

### Code Quality Standards

**Frontend:**
- ESLint compliance
- TypeScript strict mode
- Prettier formatting
- Performance budgets

**Backend:**
- Black code formatting
- isort import sorting
- Flake8 linting
- MyPy type checking
- Bandit security scanning
- 80% test coverage minimum

### Performance Requirements

- Lighthouse Performance Score: >80
- First Contentful Paint: <2s
- Largest Contentful Paint: <2.5s
- Cumulative Layout Shift: <0.1
- Total Blocking Time: <300ms

### Security Requirements

- No high/critical vulnerabilities
- Secret scanning clean
- Container security scan passed
- Dependency audit clean

## 🔧 Monitoring & Observability

### Application Performance

- **Frontend**: Lighthouse CI, bundle analysis
- **Backend**: Response time, throughput, error rates
- **Infrastructure**: CPU, memory, disk utilization
- **Database**: Query performance, connection pooling

### Alerting

**Critical Alerts:**
- Service unavailability
- High error rates (>5%)
- Response time degradation (>2s)
- Resource exhaustion (>90%)

**Warning Alerts:**
- Performance degradation
- Security vulnerabilities
- High resource usage (>80%)
- Test failures

### Dashboards

- Application Overview
- Infrastructure Health
- Business Metrics
- Security Metrics

## 🔄 Maintenance

### Regular Tasks

**Daily:**
- Dependency security scans
- Health checks
- Performance monitoring

**Weekly:**
- Dependency updates (Dependabot)
- Performance reviews
- Security review

**Monthly:**
- Infrastructure optimization
- Cost analysis
- Disaster recovery testing

### Troubleshooting

**Common Issues:**

1. **Build Failures:**
   - Check dependency versions
   - Verify environment variables
   - Review test failures

2. **Deployment Issues:**
   - Verify secrets configuration
   - Check health endpoints
   - Review resource limits

3. **Performance Problems:**
   - Analyze bundle size
   - Check database queries
   - Review caching strategies

## 📈 Scaling Considerations

### Horizontal Scaling

**Frontend:**
- CDN distribution
- Multiple replicas
- Load balancing

**Backend:**
- Service replication
- Database read replicas
- Cache clustering

### Vertical Scaling

- Resource limits adjustment
- Performance optimization
- Database tuning

## 🔒 Security Best Practices

1. **Secrets Management:**
   - Use GitHub Secrets
   - Rotate credentials regularly
   - Environment separation

2. **Container Security:**
   - Multi-stage builds
   - Non-root users
   - Minimal base images

3. **Network Security:**
   - Service mesh
   - Network policies
   - TLS encryption

4. **Access Control:**
   - RBAC implementation
   - Code ownership
   - Review requirements

## 📞 Support

For issues with the CI/CD pipeline:

1. Check GitHub Actions logs
2. Review monitoring dashboards
3. Contact the DevOps team
4. Create an issue in the repository

---

This CI/CD pipeline provides a production-ready deployment system with comprehensive monitoring, security, and quality assurance. Regular maintenance and monitoring ensure optimal performance and security for the SaaS Control Deck platform.