#!/bin/bash
set -e

# Comprehensive Health Check Script for SaaS Control Deck
# Usage: ./health-check.sh [environment] [verbose]

ENVIRONMENT=${1:-production}
VERBOSE=${2:-false}
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
HEALTH_CHECK_ERRORS=0

# Configuration based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    BASE_URL="https://saascontroldeck.com"
    GRAFANA_URL="https://grafana.saascontroldeck.com"
    CONTAINERS=("saascontroldeck-frontend-blue" "saascontroldeck-frontend-green" "backend-pro1-production" "backend-pro2-production" "postgres-production" "redis-production" "minio-production")
elif [ "$ENVIRONMENT" = "staging" ]; then
    BASE_URL="https://staging.saascontroldeck.com"
    GRAFANA_URL="https://staging-grafana.saascontroldeck.com"
    CONTAINERS=("saascontroldeck-frontend-staging" "backend-pro1-staging" "backend-pro2-staging" "postgres-staging" "redis-staging" "minio-staging")
else
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Valid environments: production, staging"
    exit 1
fi

echo "🏥 Starting comprehensive health check for $ENVIRONMENT environment"
echo "⏰ Timestamp: $TIMESTAMP"

# Helper function to log messages
log() {
    local level=$1
    local message=$2
    local timestamp=$(date +"%H:%M:%S")
    
    case $level in
        "INFO")
            echo "ℹ️  [$timestamp] $message"
            ;;
        "SUCCESS")
            echo "✅ [$timestamp] $message"
            ;;
        "WARNING")
            echo "⚠️  [$timestamp] $message"
            ;;
        "ERROR")
            echo "❌ [$timestamp] $message"
            HEALTH_CHECK_ERRORS=$((HEALTH_CHECK_ERRORS + 1))
            ;;
        "VERBOSE")
            if [ "$VERBOSE" = "true" ]; then
                echo "🔍 [$timestamp] $message"
            fi
            ;;
    esac
}

# Function to check HTTP endpoint with retries
check_http_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local timeout=${3:-10}
    local retries=${4:-3}
    local description=$5
    
    for i in $(seq 1 $retries); do
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout "$url" 2>/dev/null)
        
        if [ "$status_code" = "$expected_status" ]; then
            log "SUCCESS" "$description: HTTP $status_code"
            return 0
        else
            log "VERBOSE" "$description: HTTP $status_code (attempt $i/$retries)"
            if [ $i -lt $retries ]; then
                sleep 2
            fi
        fi
    done
    
    log "ERROR" "$description: Failed after $retries attempts (HTTP $status_code)"
    return 1
}

# Function to check Docker container health
check_container_health() {
    local container_name=$1
    local description=$2
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log "ERROR" "$description: Container not running"
        return 1
    fi
    
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
    
    case $health_status in
        "healthy")
            log "SUCCESS" "$description: Container healthy"
            return 0
            ;;
        "unhealthy")
            log "ERROR" "$description: Container unhealthy"
            return 1
            ;;
        "starting")
            log "WARNING" "$description: Container starting"
            return 1
            ;;
        "no-healthcheck")
            # Check if container is running
            local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null)
            if [ "$status" = "running" ]; then
                log "SUCCESS" "$description: Container running (no health check)"
                return 0
            else
                log "ERROR" "$description: Container not running ($status)"
                return 1
            fi
            ;;
        *)
            log "ERROR" "$description: Unknown health status ($health_status)"
            return 1
            ;;
    esac
}

# Function to check database connectivity
check_database() {
    local container_name=$1
    local db_user=${2:-saasuser}
    local db_name=${3:-saascontroldeck_${ENVIRONMENT}}
    
    if docker exec "$container_name" pg_isready -U "$db_user" -d "$db_name" > /dev/null 2>&1; then
        log "SUCCESS" "Database connectivity: PostgreSQL responding"
        
        # Check database size and connections
        if [ "$VERBOSE" = "true" ]; then
            local db_size=$(docker exec "$container_name" psql -U "$db_user" -d "$db_name" -t -c "SELECT pg_size_pretty(pg_database_size('$db_name'));" 2>/dev/null | xargs)
            local connections=$(docker exec "$container_name" psql -U "$db_user" -d "$db_name" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs)
            log "VERBOSE" "Database size: $db_size, Active connections: $connections"
        fi
        return 0
    else
        log "ERROR" "Database connectivity: PostgreSQL not responding"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    local container_name=$1
    
    if docker exec "$container_name" redis-cli ping > /dev/null 2>&1; then
        log "SUCCESS" "Redis connectivity: Redis responding"
        
        if [ "$VERBOSE" = "true" ]; then
            local memory_usage=$(docker exec "$container_name" redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
            local connected_clients=$(docker exec "$container_name" redis-cli info clients | grep "connected_clients" | cut -d: -f2 | tr -d '\r')
            log "VERBOSE" "Redis memory usage: $memory_usage, Connected clients: $connected_clients"
        fi
        return 0
    else
        log "ERROR" "Redis connectivity: Redis not responding"
        return 1
    fi
}

# Function to check MinIO health
check_minio() {
    local container_name=$1
    
    if docker exec "$container_name" curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        log "SUCCESS" "MinIO connectivity: MinIO responding"
        return 0
    else
        log "ERROR" "MinIO connectivity: MinIO not responding"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    log "INFO" "Checking system resources"
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log "WARNING" "High CPU usage: ${cpu_usage}%"
    else
        log "SUCCESS" "CPU usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo $memory_info | awk '{print $2}')
    local used_mem=$(echo $memory_info | awk '{print $3}')
    local mem_usage=$(echo "scale=1; $used_mem * 100 / $total_mem" | bc)
    
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        log "WARNING" "High memory usage: ${mem_usage}%"
    else
        log "SUCCESS" "Memory usage: ${mem_usage}%"
    fi
    
    # Disk usage
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        log "WARNING" "High disk usage: ${disk_usage}%"
    else
        log "SUCCESS" "Disk usage: ${disk_usage}%"
    fi
    
    # Docker daemon
    if docker info > /dev/null 2>&1; then
        log "SUCCESS" "Docker daemon: Running"
    else
        log "ERROR" "Docker daemon: Not running"
    fi
}

# Function to check SSL certificates
check_ssl_certificates() {
    log "INFO" "Checking SSL certificates"
    
    local domains=()
    if [ "$ENVIRONMENT" = "production" ]; then
        domains=("saascontroldeck.com" "grafana.saascontroldeck.com")
    else
        domains=("staging.saascontroldeck.com")
    fi
    
    for domain in "${domains[@]}"; do
        local expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ $days_until_expiry -le 7 ]; then
            log "ERROR" "SSL certificate for $domain expires in $days_until_expiry days"
        elif [ $days_until_expiry -le 30 ]; then
            log "WARNING" "SSL certificate for $domain expires in $days_until_expiry days"
        else
            log "SUCCESS" "SSL certificate for $domain is valid for $days_until_expiry days"
        fi
    done
}

# Main health check execution
log "INFO" "Starting health checks..."

# 1. System Resources Check
check_system_resources

# 2. Container Health Checks
log "INFO" "Checking container health"
for container in "${CONTAINERS[@]}"; do
    check_container_health "$container" "$container"
done

# 3. Database Health Check
if [ "$ENVIRONMENT" = "production" ]; then
    check_database "postgres-production" "saasuser" "saascontroldeck_production"
else
    check_database "postgres-staging" "saasuser" "saascontroldeck_staging"
fi

# 4. Redis Health Check
if [ "$ENVIRONMENT" = "production" ]; then
    check_redis "redis-production"
else
    check_redis "redis-staging"
fi

# 5. MinIO Health Check
if [ "$ENVIRONMENT" = "production" ]; then
    check_minio "minio-production"
else
    check_minio "minio-staging"
fi

# 6. HTTP Endpoint Checks
log "INFO" "Checking HTTP endpoints"

# Main application endpoints
check_http_endpoint "$BASE_URL" 200 10 3 "Main application"
check_http_endpoint "$BASE_URL/api/health" 200 10 3 "Frontend health endpoint"
check_http_endpoint "$BASE_URL/api/pro1/health" 200 10 3 "Backend Pro1 health endpoint"
check_http_endpoint "$BASE_URL/api/pro2/health" 200 10 3 "Backend Pro2 health endpoint"

# Monitoring endpoints
check_http_endpoint "$GRAFANA_URL" 200 10 3 "Grafana dashboard"

# 7. SSL Certificate Checks
check_ssl_certificates

# 8. Application-Specific Checks
log "INFO" "Running application-specific checks"

# Check if frontend can connect to backends
if curl -s "$BASE_URL/api/pro1/health" | grep -q "healthy\|ok"; then
    log "SUCCESS" "Frontend-to-Backend Pro1 connectivity"
else
    log "ERROR" "Frontend-to-Backend Pro1 connectivity failed"
fi

if curl -s "$BASE_URL/api/pro2/health" | grep -q "healthy\|ok"; then
    log "SUCCESS" "Frontend-to-Backend Pro2 connectivity"
else
    log "ERROR" "Frontend-to-Backend Pro2 connectivity failed"
fi

# 9. Performance Checks (if verbose)
if [ "$VERBOSE" = "true" ]; then
    log "INFO" "Running performance checks"
    
    # Check response times
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' "$BASE_URL")
    if (( $(echo "$response_time > 3.0" | bc -l) )); then
        log "WARNING" "Slow response time: ${response_time}s"
    else
        log "SUCCESS" "Response time: ${response_time}s"
    fi
    
    # Check container resource usage
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | while IFS= read -r line; do
        log "VERBOSE" "Container stats: $line"
    done
fi

# 10. Generate Health Report
HEALTH_REPORT="/tmp/health-check-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).json"
cat > "$HEALTH_REPORT" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "environment": "$ENVIRONMENT",
  "health_check_errors": $HEALTH_CHECK_ERRORS,
  "status": "$([ $HEALTH_CHECK_ERRORS -eq 0 ] && echo "healthy" || echo "unhealthy")",
  "checks_performed": [
    "system_resources",
    "container_health",
    "database_connectivity", 
    "redis_connectivity",
    "minio_connectivity",
    "http_endpoints",
    "ssl_certificates",
    "application_connectivity"
  ],
  "endpoints_checked": [
    "$BASE_URL",
    "$BASE_URL/api/health",
    "$BASE_URL/api/pro1/health",
    "$BASE_URL/api/pro2/health",
    "$GRAFANA_URL"
  ],
  "containers_checked": $(printf '%s\n' "${CONTAINERS[@]}" | jq -R . | jq -s .),
  "next_check_recommended": "$(date -d '+1 hour' -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

# Summary
echo ""
echo "🏥 Health Check Summary"
echo "======================="
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $TIMESTAMP"
echo "Errors Found: $HEALTH_CHECK_ERRORS"
echo "Status: $([ $HEALTH_CHECK_ERRORS -eq 0 ] && echo "HEALTHY ✅" || echo "UNHEALTHY ❌")"
echo "Report: $HEALTH_REPORT"

# Send notification if configured
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    if [ $HEALTH_CHECK_ERRORS -eq 0 ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"✅ Health check passed for $ENVIRONMENT environment\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || echo "Slack notification failed"
    else
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"❌ Health check failed for $ENVIRONMENT environment with $HEALTH_CHECK_ERRORS errors\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || echo "Slack notification failed"
    fi
fi

# Exit with error code if health checks failed
if [ $HEALTH_CHECK_ERRORS -eq 0 ]; then
    log "SUCCESS" "All health checks passed!"
    exit 0
else
    log "ERROR" "Health check completed with $HEALTH_CHECK_ERRORS errors"
    exit 1
fi