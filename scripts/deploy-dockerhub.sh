#!/bin/bash

# SaaS Control Deck - DockerHub Deployment Script
# Simplified deployment using pre-built DockerHub images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Default values
DOCKERHUB_USERNAME=""
IMAGE_TAG="latest"
ENVIRONMENT="production"
CONFIG_FILE=""
COMPOSE_FILE="docker-compose.dockerhub.yml"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -u, --username USERNAME    DockerHub username (required)"
    echo "  -t, --tag TAG             Image tag to deploy (default: latest)"
    echo "  -e, --env ENVIRONMENT     Environment: dev, staging, production (default: production)"
    echo "  -c, --config CONFIG_FILE  Custom environment config file"
    echo "  -f, --compose-file FILE   Custom docker-compose file (default: docker-compose.dockerhub.yml)"
    echo "  -h, --help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -u myusername                          # Deploy latest images"
    echo "  $0 -u myusername -t v1.2.3               # Deploy specific version"
    echo "  $0 -u myusername -e staging -t dev       # Deploy dev images to staging environment"
    echo "  $0 -u myusername -c custom.env           # Use custom environment file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            DOCKERHUB_USERNAME="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -f|--compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$DOCKERHUB_USERNAME" ]; then
    print_error "DockerHub username is required. Use -u or --username option."
    show_usage
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    print_error "Invalid environment. Must be: dev, staging, or production"
    exit 1
fi

echo "🚀 SaaS Control Deck - DockerHub Deployment"
echo "==========================================="
print_info "DockerHub Username: ${DOCKERHUB_USERNAME}"
print_info "Image Tag: ${IMAGE_TAG}"
print_info "Environment: ${ENVIRONMENT}"
print_info "Compose File: ${COMPOSE_FILE}"
echo

# Create deployment directory if it doesn't exist
mkdir -p deployment

# Generate docker-compose file for DockerHub deployment
print_info "Generating Docker Compose configuration..."

cat > deployment/${COMPOSE_FILE} << EOF
version: '3.8'

services:
  frontend:
    image: ${DOCKERHUB_USERNAME}/saascontrol-frontend:${IMAGE_TAG}
    container_name: saascontrol-frontend-${ENVIRONMENT}
    ports:
      - "\${FRONTEND_PORT:-9000}:9000"
    environment:
      - NODE_ENV=${ENVIRONMENT}
      - NEXT_TELEMETRY_DISABLED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9000/api/health"]
      interval: 30s
      timeout: 30s
      retries: 3
      start_period: 40s
    networks:
      - saascontrol-network

  backend-pro1:
    image: ${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro1:${IMAGE_TAG}
    container_name: saascontrol-backend-pro1-${ENVIRONMENT}
    ports:
      - "\${BACKEND_PRO1_API_PORT:-8000}:8000"
      - "\${BACKEND_PRO1_DATA_PORT:-8001}:8001"
      - "\${BACKEND_PRO1_AI_PORT:-8002}:8002"
    environment:
      - PROJECT_ID=pro1
      - API_GATEWAY_PORT=8000
      - DATA_SERVICE_PORT=8001
      - AI_SERVICE_PORT=8002
      - DATABASE_URL=\${DATABASE_URL_PRO1}
      - REDIS_URL=\${REDIS_URL_PRO1}
      - SECRET_KEY=\${SECRET_KEY_PRO1}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
    restart: unless-stopped
    depends_on:
      - postgres-pro1
      - redis-pro1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 30s
      retries: 3
      start_period: 40s
    networks:
      - saascontrol-network

  backend-pro2:
    image: ${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro2:${IMAGE_TAG}
    container_name: saascontrol-backend-pro2-${ENVIRONMENT}
    ports:
      - "\${BACKEND_PRO2_API_PORT:-8100}:8100"
      - "\${BACKEND_PRO2_DATA_PORT:-8101}:8101"
      - "\${BACKEND_PRO2_AI_PORT:-8102}:8102"
    environment:
      - PROJECT_ID=pro2
      - API_GATEWAY_PORT=8100
      - DATA_SERVICE_PORT=8101
      - AI_SERVICE_PORT=8102
      - DATABASE_URL=\${DATABASE_URL_PRO2}
      - REDIS_URL=\${REDIS_URL_PRO2}
      - SECRET_KEY=\${SECRET_KEY_PRO2}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
    restart: unless-stopped
    depends_on:
      - postgres-pro2
      - redis-pro2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 30s
      retries: 3
      start_period: 40s
    networks:
      - saascontrol-network

  # Database Services
  postgres-pro1:
    image: postgres:15-alpine
    container_name: saascontrol-postgres-pro1-${ENVIRONMENT}
    environment:
      - POSTGRES_DB=\${POSTGRES_DB_PRO1:-ai_platform_pro1}
      - POSTGRES_USER=\${POSTGRES_USER_PRO1:-postgres}
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD_PRO1}
    volumes:
      - postgres_data_pro1_${ENVIRONMENT}:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "\${POSTGRES_PORT_PRO1:-5432}:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER_PRO1:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - saascontrol-network

  postgres-pro2:
    image: postgres:15-alpine
    container_name: saascontrol-postgres-pro2-${ENVIRONMENT}
    environment:
      - POSTGRES_DB=\${POSTGRES_DB_PRO2:-ai_platform_pro2}
      - POSTGRES_USER=\${POSTGRES_USER_PRO2:-postgres}
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD_PRO2}
    volumes:
      - postgres_data_pro2_${ENVIRONMENT}:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "\${POSTGRES_PORT_PRO2:-5433}:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER_PRO2:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - saascontrol-network

  # Cache Services
  redis-pro1:
    image: redis:7-alpine
    container_name: saascontrol-redis-pro1-${ENVIRONMENT}
    command: redis-server --requirepass \${REDIS_PASSWORD_PRO1}
    ports:
      - "\${REDIS_PORT_PRO1:-6379}:6379"
    volumes:
      - redis_data_pro1_${ENVIRONMENT}:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - saascontrol-network

  redis-pro2:
    image: redis:7-alpine
    container_name: saascontrol-redis-pro2-${ENVIRONMENT}
    command: redis-server --requirepass \${REDIS_PASSWORD_PRO2}
    ports:
      - "\${REDIS_PORT_PRO2:-6380}:6379"
    volumes:
      - redis_data_pro2_${ENVIRONMENT}:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - saascontrol-network

  # Monitoring (Optional)
  prometheus:
    image: prom/prometheus:latest
    container_name: saascontrol-prometheus-${ENVIRONMENT}
    ports:
      - "\${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data_${ENVIRONMENT}:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - saascontrol-network

networks:
  saascontrol-network:
    driver: bridge
    name: saascontrol-network-${ENVIRONMENT}

volumes:
  postgres_data_pro1_${ENVIRONMENT}:
    name: saascontrol-postgres-pro1-${ENVIRONMENT}
  postgres_data_pro2_${ENVIRONMENT}:
    name: saascontrol-postgres-pro2-${ENVIRONMENT}
  redis_data_pro1_${ENVIRONMENT}:
    name: saascontrol-redis-pro1-${ENVIRONMENT}
  redis_data_pro2_${ENVIRONMENT}:
    name: saascontrol-redis-pro2-${ENVIRONMENT}
  prometheus_data_${ENVIRONMENT}:
    name: saascontrol-prometheus-${ENVIRONMENT}
EOF

print_success "Docker Compose configuration generated: deployment/${COMPOSE_FILE}"

# Generate environment file template if config file is not provided
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="deployment/.env.${ENVIRONMENT}"

    if [ ! -f "$CONFIG_FILE" ]; then
        print_info "Generating environment configuration template..."

        cat > $CONFIG_FILE << 'EOF'
# SaaS Control Deck Environment Configuration
# Copy this file to .env.production, .env.staging, or .env.dev and fill in your values

# Frontend Configuration
FRONTEND_PORT=9000

# Backend Pro1 Configuration
BACKEND_PRO1_API_PORT=8000
BACKEND_PRO1_DATA_PORT=8001
BACKEND_PRO1_AI_PORT=8002

# Backend Pro2 Configuration
BACKEND_PRO2_API_PORT=8100
BACKEND_PRO2_DATA_PORT=8101
BACKEND_PRO2_AI_PORT=8102

# Database Configuration Pro1
POSTGRES_DB_PRO1=ai_platform_pro1
POSTGRES_USER_PRO1=postgres
POSTGRES_PASSWORD_PRO1=your_secure_password_pro1_here
POSTGRES_PORT_PRO1=5432
DATABASE_URL_PRO1=postgresql+asyncpg://postgres:your_secure_password_pro1_here@postgres-pro1:5432/ai_platform_pro1

# Database Configuration Pro2
POSTGRES_DB_PRO2=ai_platform_pro2
POSTGRES_USER_PRO2=postgres
POSTGRES_PASSWORD_PRO2=your_secure_password_pro2_here
POSTGRES_PORT_PRO2=5433
DATABASE_URL_PRO2=postgresql+asyncpg://postgres:your_secure_password_pro2_here@postgres-pro2:5432/ai_platform_pro2

# Redis Configuration
REDIS_PASSWORD_PRO1=your_redis_password_pro1_here
REDIS_PASSWORD_PRO2=your_redis_password_pro2_here
REDIS_PORT_PRO1=6379
REDIS_PORT_PRO2=6380
REDIS_URL_PRO1=redis://:your_redis_password_pro1_here@redis-pro1:6379/0
REDIS_URL_PRO2=redis://:your_redis_password_pro2_here@redis-pro2:6379/0

# Security Configuration
SECRET_KEY_PRO1=your_super_secret_key_32_chars_minimum_pro1
SECRET_KEY_PRO2=your_super_secret_key_32_chars_minimum_pro2

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Monitoring
PROMETHEUS_PORT=9090
EOF

        print_warning "Environment template created: $CONFIG_FILE"
        print_warning "Please edit this file and add your actual configuration values!"
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Use docker-compose or docker compose based on availability
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Function to check if environment file exists and has required variables
check_env_file() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Environment file not found: $CONFIG_FILE"
        print_info "Please create the environment file with required variables."
        return 1
    fi

    # Check for required variables
    required_vars=(
        "POSTGRES_PASSWORD_PRO1"
        "POSTGRES_PASSWORD_PRO2"
        "REDIS_PASSWORD_PRO1"
        "REDIS_PASSWORD_PRO2"
        "SECRET_KEY_PRO1"
        "SECRET_KEY_PRO2"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$CONFIG_FILE" || grep -q "^${var}=.*_here" "$CONFIG_FILE"; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "The following required environment variables are missing or have placeholder values:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_info "Please update $CONFIG_FILE with actual values."
        return 1
    fi

    return 0
}

# Verify environment configuration
print_info "Checking environment configuration..."
if ! check_env_file; then
    print_error "Environment configuration check failed."
    print_info "Please fix the configuration and run the script again."
    exit 1
fi

print_success "Environment configuration verified."

# Pull latest images
print_info "Pulling Docker images from DockerHub..."

images=(
    "${DOCKERHUB_USERNAME}/saascontrol-frontend:${IMAGE_TAG}"
    "${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro1:${IMAGE_TAG}"
    "${DOCKERHUB_USERNAME}/saascontrol-backend-backend-pro2:${IMAGE_TAG}"
)

for image in "${images[@]}"; do
    print_info "Pulling $image..."
    if docker pull "$image"; then
        print_success "✓ $image"
    else
        print_error "Failed to pull $image"
        print_info "Make sure the image exists on DockerHub and you have access to it."
        exit 1
    fi
done

print_success "All images pulled successfully."

# Start services
print_info "Starting SaaS Control Deck services..."

cd deployment

if $DOCKER_COMPOSE_CMD --env-file "$CONFIG_FILE" -f "$COMPOSE_FILE" up -d; then
    print_success "Services started successfully!"
else
    print_error "Failed to start services."
    exit 1
fi

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Health checks
print_info "Performing health checks..."

health_checks=(
    "http://localhost:${FRONTEND_PORT:-9000}/api/health:Frontend"
    "http://localhost:${BACKEND_PRO1_API_PORT:-8000}/health:Backend Pro1"
    "http://localhost:${BACKEND_PRO2_API_PORT:-8100}/health:Backend Pro2"
)

all_healthy=true

for check in "${health_checks[@]}"; do
    IFS=':' read -r url service <<< "$check"
    print_info "Checking $service..."

    if curl -f -s "$url" > /dev/null; then
        print_success "✓ $service is healthy"
    else
        print_warning "✗ $service health check failed"
        all_healthy=false
    fi
done

echo
if [ "$all_healthy" = true ]; then
    print_success "🎉 All services are healthy and ready!"
else
    print_warning "Some services may not be ready yet. Check the logs for more details."
fi

# Show deployment summary
echo
print_info "Deployment Summary:"
print_info "=================="
print_info "Environment: $ENVIRONMENT"
print_info "Images Tag: $IMAGE_TAG"
print_info "Frontend: http://localhost:${FRONTEND_PORT:-9000}"
print_info "Backend Pro1: http://localhost:${BACKEND_PRO1_API_PORT:-8000}"
print_info "Backend Pro2: http://localhost:${BACKEND_PRO2_API_PORT:-8100}"
echo

# Show useful commands
echo "📋 Useful Commands:"
echo "=================="
echo "View logs:           $DOCKER_COMPOSE_CMD --env-file $CONFIG_FILE -f $COMPOSE_FILE logs -f"
echo "Stop services:       $DOCKER_COMPOSE_CMD --env-file $CONFIG_FILE -f $COMPOSE_FILE down"
echo "Restart service:     $DOCKER_COMPOSE_CMD --env-file $CONFIG_FILE -f $COMPOSE_FILE restart [service_name]"
echo "View status:         $DOCKER_COMPOSE_CMD --env-file $CONFIG_FILE -f $COMPOSE_FILE ps"
echo "Update images:       $0 -u $DOCKERHUB_USERNAME -t $IMAGE_TAG -e $ENVIRONMENT"
echo

print_success "Deployment completed successfully! 🚀"