#!/bin/bash

# Deployment script for SaaS Control Deck
# This script handles deployment to different environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_ENV="staging"
DEFAULT_PROJECT="all"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
SaaS Control Deck Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (staging|production) [default: staging]
    -p, --project PROJECT    Project to deploy (all|frontend|backend-pro1|backend-pro2) [default: all]
    -v, --version VERSION    Version/tag to deploy [default: latest]
    -d, --dry-run           Show what would be deployed without executing
    -h, --help              Show this help message
    --rollback VERSION      Rollback to a previous version
    --health-check          Run health checks only
    --scale REPLICAS        Scale services to specified replica count

EXAMPLES:
    $0 -e staging -p all                    # Deploy all services to staging
    $0 -e production -p frontend            # Deploy only frontend to production
    $0 --rollback v1.2.0                    # Rollback to version 1.2.0
    $0 --health-check                       # Run health checks on all services
    $0 --scale 3                           # Scale all services to 3 replicas

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -p|--project)
                PROJECT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --rollback)
                ROLLBACK_VERSION="$2"
                shift 2
                ;;
            --health-check)
                HEALTH_CHECK_ONLY=true
                shift
                ;;
            --scale)
                SCALE_REPLICAS="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Set defaults
    ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}
    PROJECT=${PROJECT:-$DEFAULT_PROJECT}
    VERSION=${VERSION:-latest}
    DRY_RUN=${DRY_RUN:-false}
    HEALTH_CHECK_ONLY=${HEALTH_CHECK_ONLY:-false}
}

# Validate environment
validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
        exit 1
    fi

    if [[ ! "$PROJECT" =~ ^(all|frontend|backend-pro1|backend-pro2)$ ]]; then
        log_error "Invalid project: $PROJECT. Must be 'all', 'frontend', 'backend-pro1', or 'backend-pro2'"
        exit 1
    fi

    log_info "Environment: $ENVIRONMENT"
    log_info "Project: $PROJECT"
    log_info "Version: $VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual deployment will occur"
    fi
}

# Load environment configuration
load_environment_config() {
    local config_file="$PROJECT_ROOT/.github/environments/${ENVIRONMENT}.yml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Environment configuration not found: $config_file"
        exit 1
    fi
    
    log_info "Loaded configuration for $ENVIRONMENT environment"
    
    # Set environment-specific variables
    case $ENVIRONMENT in
        staging)
            NAMESPACE="saascontroldeck-staging"
            DOMAIN="staging.saascontroldeck.com"
            API_DOMAIN="api-staging.saascontroldeck.com"
            ;;
        production)
            NAMESPACE="saascontroldeck-production"
            DOMAIN="saascontroldeck.com"
            API_DOMAIN="api.saascontroldeck.com"
            ;;
    esac
}

# Health check functions
check_service_health() {
    local service_url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Checking health of $service_name..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s --max-time 10 "$service_url/health" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    log_error "$service_name health check failed after $max_attempts attempts"
    return 1
}

# Run comprehensive health checks
run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    local failed_services=()
    
    # Frontend health check
    if [[ "$PROJECT" == "all" || "$PROJECT" == "frontend" ]]; then
        if ! check_service_health "https://$DOMAIN" "Frontend"; then
            failed_services+=("frontend")
        fi
    fi
    
    # Backend Pro1 health check
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro1" ]]; then
        if ! check_service_health "https://$API_DOMAIN/pro1" "Backend Pro1"; then
            failed_services+=("backend-pro1")
        fi
    fi
    
    # Backend Pro2 health check
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro2" ]]; then
        if ! check_service_health "https://$API_DOMAIN/pro2" "Backend Pro2"; then
            failed_services+=("backend-pro2")
        fi
    fi
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All health checks passed!"
        return 0
    else
        log_error "Health checks failed for: ${failed_services[*]}"
        return 1
    fi
}

# Deploy frontend
deploy_frontend() {
    log_info "Deploying frontend..."
    
    local image="ghcr.io/$GITHUB_REPOSITORY_OWNER/saascontroldeck-frontend:$VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy frontend image: $image"
        return 0
    fi
    
    # Add your frontend deployment logic here
    # This could be:
    # - Updating Kubernetes deployments
    # - Deploying to Vercel/Netlify
    # - Updating Docker Swarm services
    # - Pushing to cloud platforms
    
    log_info "Deploying to $ENVIRONMENT environment..."
    
    # Example deployment commands (replace with your actual deployment)
    case $ENVIRONMENT in
        staging)
            # kubectl set image deployment/frontend frontend=$image -n $NAMESPACE
            log_info "Frontend deployment to staging initiated"
            ;;
        production)
            # kubectl set image deployment/frontend frontend=$image -n $NAMESPACE
            log_info "Frontend deployment to production initiated"
            ;;
    esac
    
    log_success "Frontend deployment completed"
}

# Deploy backend service
deploy_backend() {
    local service=$1
    log_info "Deploying $service..."
    
    local image="ghcr.io/$GITHUB_REPOSITORY_OWNER/saascontroldeck-$service:$VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy $service image: $image"
        return 0
    fi
    
    # Add your backend deployment logic here
    log_info "Deploying $service to $ENVIRONMENT environment..."
    
    # Example deployment commands (replace with your actual deployment)
    case $ENVIRONMENT in
        staging)
            # kubectl set image deployment/$service $service=$image -n $NAMESPACE
            log_info "$service deployment to staging initiated"
            ;;
        production)
            # kubectl set image deployment/$service $service=$image -n $NAMESPACE
            log_info "$service deployment to production initiated"
            ;;
    esac
    
    log_success "$service deployment completed"
}

# Scale services
scale_services() {
    if [[ -z "$SCALE_REPLICAS" ]]; then
        return 0
    fi
    
    log_info "Scaling services to $SCALE_REPLICAS replicas..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would scale services to $SCALE_REPLICAS replicas"
        return 0
    fi
    
    # Add your scaling logic here
    # Example: kubectl scale deployment --replicas=$SCALE_REPLICAS --all -n $NAMESPACE
    
    log_success "Services scaled to $SCALE_REPLICAS replicas"
}

# Rollback function
rollback_deployment() {
    if [[ -z "$ROLLBACK_VERSION" ]]; then
        return 0
    fi
    
    log_warning "Rolling back to version: $ROLLBACK_VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would rollback to version: $ROLLBACK_VERSION"
        return 0
    fi
    
    # Set VERSION to rollback version and deploy
    VERSION="$ROLLBACK_VERSION"
    
    # Perform rollback deployment
    if [[ "$PROJECT" == "all" || "$PROJECT" == "frontend" ]]; then
        deploy_frontend
    fi
    
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro1" ]]; then
        deploy_backend "backend-pro1"
    fi
    
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro2" ]]; then
        deploy_backend "backend-pro2"
    fi
    
    log_success "Rollback completed"
}

# Main deployment function
main_deploy() {
    log_info "Starting deployment process..."
    
    # Deploy based on project selection
    if [[ "$PROJECT" == "all" || "$PROJECT" == "frontend" ]]; then
        deploy_frontend
    fi
    
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro1" ]]; then
        deploy_backend "backend-pro1"
    fi
    
    if [[ "$PROJECT" == "all" || "$PROJECT" == "backend-pro2" ]]; then
        deploy_backend "backend-pro2"
    fi
    
    # Scale services if requested
    scale_services
    
    # Wait for deployment to settle
    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting for deployment to stabilize..."
        sleep 30
        
        # Run health checks
        if run_health_checks; then
            log_success "Deployment completed successfully!"
        else
            log_error "Deployment completed but health checks failed"
            exit 1
        fi
    fi
}

# Main execution
main() {
    parse_args "$@"
    validate_environment
    load_environment_config
    
    # Handle special operations
    if [[ "$HEALTH_CHECK_ONLY" == "true" ]]; then
        run_health_checks
        exit $?
    fi
    
    if [[ -n "$ROLLBACK_VERSION" ]]; then
        rollback_deployment
        exit $?
    fi
    
    # Normal deployment
    main_deploy
}

# Run main function with all arguments
main "$@"