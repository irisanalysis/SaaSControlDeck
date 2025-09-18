# DockerHub CI/CD Setup Instructions

This document provides step-by-step instructions for setting up and using the comprehensive DockerHub CI/CD workflow for the SaaS Control Deck project.

## 🚀 Quick Start

### 1. Prerequisites

- GitHub repository with the SaaS Control Deck code
- DockerHub account
- GitHub CLI installed (optional, for automated setup)
- Docker installed on deployment server

### 2. Setup DockerHub Secrets

**Option A: Automated Setup (Recommended)**
```bash
# Run the automated setup script
./scripts/setup-dockerhub-secrets.sh
```

**Option B: Manual Setup**
1. Go to your GitHub repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add the following secrets:
   - `DOCKERHUB_USERNAME`: Your DockerHub username
   - `DOCKERHUB_TOKEN`: DockerHub access token (recommended) or password

### 3. Create DockerHub Access Token

1. Visit [DockerHub Security Settings](https://hub.docker.com/settings/security)
2. Click "New Access Token"
3. Name: `SaaS-Control-Deck-CI`
4. Permissions: Read, Write, Delete
5. Copy the generated token and use it as `DOCKERHUB_TOKEN`

### 4. Deploy Your Application

```bash
# Deploy using the latest images
./scripts/deploy-dockerhub.sh -u YOUR_DOCKERHUB_USERNAME

# Deploy specific version
./scripts/deploy-dockerhub.sh -u YOUR_DOCKERHUB_USERNAME -t v1.2.3

# Deploy to staging environment
./scripts/deploy-dockerhub.sh -u YOUR_DOCKERHUB_USERNAME -e staging -t dev
```

## 📋 Detailed Configuration

### Environment Variables Setup

The deployment script will generate an environment template for you. Edit the `.env.production` file with your actual values:

```bash
# Edit the environment configuration
nano deployment/.env.production
```

Required variables to configure:
- Database passwords for Pro1 and Pro2
- Redis passwords for Pro1 and Pro2
- Secret keys for both projects
- OpenAI API key (if using AI features)

### DockerHub Repository Names

The CI/CD workflow will create the following repositories:
- `{username}/saascontrol-frontend`
- `{username}/saascontrol-backend-backend-pro1`
- `{username}/saascontrol-backend-backend-pro2`

Make sure these repositories exist on DockerHub or are set to auto-create.

## 🔄 CI/CD Workflow Features

### Automatic Triggers

- **Push to `main`**: Builds and pushes `latest` tag
- **Push to `develop`**: Builds and pushes `dev` tag
- **Git tags**: Builds and pushes version tags (e.g., `v1.2.3`)
- **Pull requests**: Builds images for testing (doesn't push)

### Smart Build Detection

- Only builds frontend when `frontend/` files change
- Only builds backend when `backend/` files change
- Force build all images with workflow dispatch

### Multi-Architecture Support

- Builds for both `linux/amd64` and `linux/arm64`
- Uses Docker Buildx for cross-platform builds

### Security Features

- Trivy vulnerability scanning for all images
- SARIF reports uploaded to GitHub Security tab
- Multi-stage builds for smaller, more secure images

### Build Optimization

- GitHub Actions cache for faster builds
- Docker layer caching
- Parallel builds for different services

## 🛠️ Management Scripts

### Deploy Application

```bash
# Basic deployment
./scripts/deploy-dockerhub.sh -u myusername

# Advanced deployment options
./scripts/deploy-dockerhub.sh \
  --username myusername \
  --tag v1.2.3 \
  --env production \
  --config custom.env
```

### Update Running Services

```bash
# Update all services to latest
./scripts/update-dockerhub-images.sh -u myusername

# Update specific services
./scripts/update-dockerhub-images.sh \
  -u myusername \
  -t v1.2.4 \
  -s frontend,backend-pro1
```

### Setup Secrets

```bash
# Interactive setup
./scripts/setup-dockerhub-secrets.sh
```

## 📊 Monitoring and Health Checks

### Built-in Health Checks

All services include health checks:
- **Frontend**: `GET /api/health`
- **Backend Pro1**: `GET /health` (port 8000)
- **Backend Pro2**: `GET /health` (port 8100)

### Service URLs (Default Ports)

- Frontend: http://localhost:9000
- Backend Pro1 API: http://localhost:8000
- Backend Pro1 Data: http://localhost:8001
- Backend Pro1 AI: http://localhost:8002
- Backend Pro2 API: http://localhost:8100
- Backend Pro2 Data: http://localhost:8101
- Backend Pro2 AI: http://localhost:8102

### Monitoring with Prometheus

Optional Prometheus monitoring is included:
- Prometheus: http://localhost:9090

## 🔧 Troubleshooting

### Common Issues

**1. Build Failures**
```bash
# Check GitHub Actions logs
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# Common fixes:
# - Ensure DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are set
# - Check if DockerHub repositories exist
# - Verify Dockerfile paths are correct
```

**2. Deployment Issues**
```bash
# Check container logs
docker-compose -f deployment/docker-compose.dockerhub.yml logs -f SERVICE_NAME

# Check container status
docker-compose -f deployment/docker-compose.dockerhub.yml ps

# Restart services
docker-compose -f deployment/docker-compose.dockerhub.yml restart SERVICE_NAME
```

**3. Permission Issues**
```bash
# Ensure scripts are executable
chmod +x scripts/*.sh

# Check Docker permissions
sudo usermod -aG docker $USER
# Log out and log back in
```

### Environment-Specific Issues

**Development Environment:**
- Use `dev` tag for images
- Set `ENVIRONMENT=dev`
- Use development database credentials

**Staging Environment:**
- Use `dev` or version tags
- Set `ENVIRONMENT=staging`
- Use separate staging databases

**Production Environment:**
- Use `latest` or version tags
- Set `ENVIRONMENT=production`
- Use strong, unique passwords

## 🚀 Advanced Usage

### Custom Docker Compose

Create your own compose file:
```bash
# Use custom compose file
./scripts/deploy-dockerhub.sh \
  -u myusername \
  --compose-file my-custom-compose.yml
```

### Kubernetes Deployment

The CI/CD workflow generates Kubernetes manifests:
```bash
# Download artifacts from GitHub Actions
# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.yml
```

### Blue-Green Deployment

```bash
# Deploy new version to staging
./scripts/deploy-dockerhub.sh -u myusername -t v1.2.3 -e staging

# Test staging environment
# Switch production to new version
./scripts/update-dockerhub-images.sh -u myusername -t v1.2.3 -e production
```

## 📝 Best Practices

### Version Management

1. **Use semantic versioning**: `v1.2.3`
2. **Tag releases** in GitHub to trigger automatic builds
3. **Test in staging** before promoting to production
4. **Keep previous versions** available for quick rollbacks

### Security

1. **Use access tokens** instead of passwords
2. **Regularly rotate secrets**
3. **Monitor vulnerability scans**
4. **Use specific image tags** in production (avoid `latest`)

### Performance

1. **Use multi-stage builds** (already implemented)
2. **Enable Docker BuildKit** (enabled in workflow)
3. **Leverage build cache** (configured automatically)
4. **Monitor resource usage** with Prometheus

### Backup and Recovery

1. **Regular database backups**
2. **Volume backups** for persistent data
3. **Configuration backups** (environment files)
4. **Disaster recovery testing**

## 🔗 References

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [DockerHub Documentation](https://docs.docker.com/docker-hub/)
- [SaaS Control Deck Architecture](./backend/CLAUDE.md)

## 🆘 Support

For issues specific to the SaaS Control Deck:
1. Check GitHub Actions logs
2. Review container logs
3. Verify environment configuration
4. Test health endpoints
5. Check resource usage and limits

For DockerHub/Docker issues:
1. Verify DockerHub credentials
2. Check repository permissions
3. Review Docker daemon status
4. Validate Dockerfile syntax