#!/bin/bash

# SaaS Control Deck - DockerHub Image Update Script
# Quick script to update running services with new images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Default values
DOCKERHUB_USERNAME=""
IMAGE_TAG="latest"
ENVIRONMENT="production"
COMPOSE_FILE="docker-compose.dockerhub.yml"
SERVICES=""

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -u, --username USERNAME    DockerHub username (required)"
    echo "  -t, --tag TAG             New image tag to deploy (default: latest)"
    echo "  -e, --env ENVIRONMENT     Environment: dev, staging, production (default: production)"
    echo "  -s, --services SERVICES   Specific services to update (comma-separated)"
    echo "  -f, --compose-file FILE   Docker compose file (default: docker-compose.dockerhub.yml)"
    echo "  -h, --help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -u myusername -t v1.2.3                    # Update all services to v1.2.3"
    echo "  $0 -u myusername -s frontend,backend-pro1     # Update only frontend and backend-pro1"
    echo "  $0 -u myusername -t latest -e staging         # Update staging environment to latest"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username) DOCKERHUB_USERNAME="$2"; shift 2 ;;
        -t|--tag) IMAGE_TAG="$2"; shift 2 ;;
        -e|--env) ENVIRONMENT="$2"; shift 2 ;;
        -s|--services) SERVICES="$2"; shift 2 ;;
        -f|--compose-file) COMPOSE_FILE="$2"; shift 2 ;;
        -h|--help) show_usage; exit 0 ;;
        *) print_error "Unknown option: $1"; show_usage; exit 1 ;;
    esac
done

if [ -z "$DOCKERHUB_USERNAME" ]; then
    print_error "DockerHub username is required."
    show_usage
    exit 1
fi

echo "🔄 SaaS Control Deck - Image Update"
echo "===================================="
print_info "DockerHub Username: ${DOCKERHUB_USERNAME}"
print_info "New Image Tag: ${IMAGE_TAG}"
print_info "Environment: ${ENVIRONMENT}"
echo

# Check if deployment directory exists
if [ ! -d "deployment" ]; then
    print_error "Deployment directory not found. Please run deploy-dockerhub.sh first."
    exit 1
fi

cd deployment

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Determine Docker Compose command
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Determine services to update
if [ -z "$SERVICES" ]; then
    UPDATE_SERVICES=("frontend" "backend-pro1" "backend-pro2")
else
    IFS=',' read -ra UPDATE_SERVICES <<< "$SERVICES"
fi

print_info "Services to update: ${UPDATE_SERVICES[*]}"

# Pull new images
print_info "Pulling new Docker images..."

for service in "${UPDATE_SERVICES[@]}"; do
    case $service in
        frontend)
            image="${DOCKERHUB_USERNAME}/saascontrol-frontend:${IMAGE_TAG}"
            ;;
        backend-pro1)
            image="${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro1:${IMAGE_TAG}"
            ;;
        backend-pro2)
            image="${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro2:${IMAGE_TAG}"
            ;;
        *)
            print_warning "Unknown service: $service, skipping..."
            continue
            ;;
    esac

    print_info "Pulling $image..."
    if docker pull "$image"; then
        print_success "✓ $image"
    else
        print_error "Failed to pull $image"
        exit 1
    fi
done

# Update services with zero downtime
print_info "Updating services..."

for service in "${UPDATE_SERVICES[@]}"; do
    print_info "Updating $service..."

    # Update the service
    if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps "$service"; then
        print_success "✓ $service updated"

        # Wait a bit for the service to start
        sleep 10

        # Perform health check
        case $service in
            frontend)
                health_url="http://localhost:9000/api/health"
                ;;
            backend-pro1)
                health_url="http://localhost:8000/health"
                ;;
            backend-pro2)
                health_url="http://localhost:8100/health"
                ;;
        esac

        # Check health
        for i in {1..12}; do  # 12 * 5 = 60 seconds timeout
            if curl -f -s "$health_url" > /dev/null; then
                print_success "✓ $service is healthy"
                break
            fi
            if [ $i -eq 12 ]; then
                print_warning "✗ $service health check timeout"
                print_info "Service may still be starting up. Check logs: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs $service"
            else
                sleep 5
            fi
        done
    else
        print_error "Failed to update $service"
        exit 1
    fi
done

# Clean up old images
print_info "Cleaning up old Docker images..."
docker image prune -f

print_success "🎉 Update completed successfully!"

# Show status
print_info "Current service status:"
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps

echo
print_info "To view logs: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f [service_name]"
print_info "To rollback: Run this script again with the previous image tag"