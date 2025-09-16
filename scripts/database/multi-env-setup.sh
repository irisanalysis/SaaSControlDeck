#!/bin/bash
# SaaS Control Deck 多环境数据库自动化部署脚本
# Usage: ./multi-env-setup.sh [development|staging|production|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查环境依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL客户端未安装，将使用Docker容器执行数据库操作"
    fi
    
    log_success "依赖检查完成"
}

# 生成环境配置文件
generate_env_config() {
    local env_name=$1
    local db_port=$2
    local api_port_start=$3
    
    log_info "生成 ${env_name} 环境配置..."
    
    local env_file="${PROJECT_ROOT}/backend/backend-pro1/.env.${env_name}"
    
    cat > "$env_file" << EOF
# SaaS Control Deck ${env_name} Environment Configuration
# Generated on $(date)

PROJECT_ID=pro1_${env_name}
ENVIRONMENT=${env_name}

# Database Configuration
DATABASE_URL=postgresql+asyncpg://saascontrol_user:saascontrol_pass@localhost:${db_port}/saascontrol_${env_name}
DATABASE_HOST=localhost
DATABASE_PORT=${db_port}
DATABASE_NAME=saascontrol_${env_name}
DATABASE_USER=saascontrol_user
DATABASE_PASSWORD=saascontrol_pass

# API Configuration
API_GATEWAY_PORT=${api_port_start}
DATA_SERVICE_PORT=$((api_port_start + 1))
AI_SERVICE_PORT=$((api_port_start + 2))

# Redis Configuration
REDIS_URL=redis://:redis_pass@localhost:$((6379 + (api_port_start - 8000) / 10))/0

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# External Services
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key}

# CORS Configuration
CORS_ORIGINS=["http://localhost:9000","https://localhost:9000"]

# Monitoring
PROMETHEUS_PORT=$((9090 + (api_port_start - 8000) / 10))

# Object Storage (MinIO)
MINIO_PORT=$((9000 + (api_port_start - 8000) / 10 * 2))
MINIO_CONSOLE_PORT=$((9001 + (api_port_start - 8000) / 10 * 2))
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
EOF

    log_success "${env_name} 环境配置文件已生成: $env_file"
}

# 创建PostgreSQL实例
setup_postgresql_instance() {
    local env_name=$1
    local db_port=$2
    
    log_info "设置 ${env_name} PostgreSQL实例 (端口: ${db_port})..."
    
    # 创建Docker Compose配置
    local compose_file="${PROJECT_ROOT}/docker/postgresql-${env_name}.yml"
    
    mkdir -p "$(dirname "$compose_file")"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  postgresql-${env_name}:
    image: postgres:15
    container_name: saascontrol-postgres-${env_name}
    restart: unless-stopped
    ports:
      - "${db_port}:5432"
    environment:
      POSTGRES_DB: saascontrol_${env_name}
      POSTGRES_USER: saascontrol_user
      POSTGRES_PASSWORD: saascontrol_pass
      POSTGRES_INITDB_ARGS: "--auth-host=md5"
    volumes:
      - saascontrol_postgres_${env_name}_data:/var/lib/postgresql/data
      - ${PROJECT_ROOT}/scripts/database/init-schema.sql:/docker-entrypoint-initdb.d/01-init-schema.sql
      - ${PROJECT_ROOT}/scripts/database/sample-data-${env_name}.sql:/docker-entrypoint-initdb.d/02-sample-data.sql
    networks:
      - saascontrol-${env_name}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U saascontrol_user -d saascontrol_${env_name}"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  saascontrol-${env_name}:
    driver: bridge

volumes:
  saascontrol_postgres_${env_name}_data:
EOF

    # 启动PostgreSQL实例
    docker-compose -f "$compose_file" up -d
    
    # 等待数据库准备就绪
    log_info "等待 ${env_name} 数据库启动..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$compose_file" exec -T "postgresql-${env_name}" pg_isready -U saascontrol_user -d "saascontrol_${env_name}" > /dev/null 2>&1; then
            log_success "${env_name} PostgreSQL实例启动成功 (端口: ${db_port})"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "等待数据库启动... (${attempt}/${max_attempts})"
        sleep 2
    done
    
    log_error "${env_name} PostgreSQL实例启动失败"
    return 1
}

# 部署后端服务
deploy_backend_services() {
    local env_name=$1
    local api_port_start=$2
    
    log_info "部署 ${env_name} 后端服务 (端口: ${api_port_start}-$((api_port_start + 2)))..."
    
    # 创建后端服务的Docker Compose配置
    local compose_file="${PROJECT_ROOT}/docker/backend-${env_name}.yml"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  api-gateway-${env_name}:
    build: 
      context: ${PROJECT_ROOT}/backend/backend-pro1
      dockerfile: Dockerfile
    container_name: saascontrol-api-gateway-${env_name}
    restart: unless-stopped
    ports:
      - "${api_port_start}:8000"
    environment:
      - SERVICE_TYPE=api-gateway
    env_file:
      - ${PROJECT_ROOT}/backend/backend-pro1/.env.${env_name}
    volumes:
      - ${PROJECT_ROOT}/backend/backend-pro1/api-gateway:/app
    networks:
      - saascontrol-${env_name}
    depends_on:
      - postgresql-${env_name}
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  data-service-${env_name}:
    build:
      context: ${PROJECT_ROOT}/backend/backend-pro1
      dockerfile: Dockerfile
    container_name: saascontrol-data-service-${env_name}
    restart: unless-stopped
    ports:
      - "$((api_port_start + 1)):8001"
    environment:
      - SERVICE_TYPE=data-service
    env_file:
      - ${PROJECT_ROOT}/backend/backend-pro1/.env.${env_name}
    volumes:
      - ${PROJECT_ROOT}/backend/backend-pro1/data-service:/app
    networks:
      - saascontrol-${env_name}
    depends_on:
      - postgresql-${env_name}
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  ai-service-${env_name}:
    build:
      context: ${PROJECT_ROOT}/backend/backend-pro1
      dockerfile: Dockerfile
    container_name: saascontrol-ai-service-${env_name}
    restart: unless-stopped
    ports:
      - "$((api_port_start + 2)):8002"
    environment:
      - SERVICE_TYPE=ai-service
    env_file:
      - ${PROJECT_ROOT}/backend/backend-pro1/.env.${env_name}
    volumes:
      - ${PROJECT_ROOT}/backend/backend-pro1/ai-service:/app
    networks:
      - saascontrol-${env_name}
    depends_on:
      - postgresql-${env_name}
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  saascontrol-${env_name}:
    external: true

EOF

    # 构建并启动后端服务
    docker-compose -f "$compose_file" up -d --build
    
    log_success "${env_name} 后端服务部署完成"
}

# 验证环境健康状态
verify_environment_health() {
    local env_name=$1
    local api_port_start=$2
    local db_port=$3
    
    log_info "验证 ${env_name} 环境健康状态..."
    
    # 验证数据库连接
    if docker exec "saascontrol-postgres-${env_name}" pg_isready -U saascontrol_user -d "saascontrol_${env_name}" > /dev/null 2>&1; then
        log_success "✅ ${env_name} PostgreSQL (端口: ${db_port}) - 连接正常"
    else
        log_error "❌ ${env_name} PostgreSQL (端口: ${db_port}) - 连接失败"
        return 1
    fi
    
    # 验证API服务
    local services=("api-gateway" "data-service" "ai-service")
    local ports=("$api_port_start" "$((api_port_start + 1))" "$((api_port_start + 2))")
    
    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local port="${ports[$i]}"
        
        local max_attempts=10
        local attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -f -s "http://localhost:${port}/health" > /dev/null 2>&1; then
                log_success "✅ ${env_name} ${service} (端口: ${port}) - 服务正常"
                break
            fi
            
            attempt=$((attempt + 1))
            if [ $attempt -eq $max_attempts ]; then
                log_error "❌ ${env_name} ${service} (端口: ${port}) - 服务异常"
                return 1
            fi
            
            sleep 3
        done
    done
    
    log_success "🎉 ${env_name} 环境健康检查通过"
    return 0
}

# 主函数：设置单个环境
setup_environment() {
    local env_name=$1
    
    case $env_name in
        "development")
            local db_port=5433
            local api_port_start=8010
            ;;
        "staging")
            local db_port=5434
            local api_port_start=8020
            ;;
        "production")
            local db_port=5432
            local api_port_start=8000
            ;;
        *)
            log_error "无效的环境名称: $env_name (支持: development, staging, production)"
            return 1
            ;;
    esac
    
    log_info "开始设置 ${env_name} 环境..."
    
    # 生成环境配置
    generate_env_config "$env_name" "$db_port" "$api_port_start"
    
    # 设置PostgreSQL实例
    setup_postgresql_instance "$env_name" "$db_port"
    
    # 部署后端服务
    deploy_backend_services "$env_name" "$api_port_start"
    
    # 等待服务启动
    sleep 10
    
    # 验证环境健康状态
    verify_environment_health "$env_name" "$api_port_start" "$db_port"
    
    log_success "🎉 ${env_name} 环境设置完成!"
    echo ""
    echo "访问地址:"
    echo "  API Gateway: http://localhost:${api_port_start}"
    echo "  Data Service: http://localhost:$((api_port_start + 1))"
    echo "  AI Service: http://localhost:$((api_port_start + 2))"
    echo "  PostgreSQL: localhost:${db_port}"
    echo ""
}

# 显示使用帮助
show_usage() {
    echo "SaaS Control Deck 多环境数据库自动化部署脚本"
    echo ""
    echo "用法:"
    echo "  $0 [environment]"
    echo ""
    echo "环境选项:"
    echo "  development  - 设置开发环境 (用于Firebase Studio远程连接)"
    echo "  staging      - 设置暂存环境 (用于CI/CD测试)"
    echo "  production   - 设置生产环境 (用于正式部署)"
    echo "  all          - 设置所有环境"
    echo ""
    echo "示例:"
    echo "  $0 development    # 设置开发环境"
    echo "  $0 all           # 设置所有环境"
    echo ""
}

# 主程序入口
main() {
    local environment=${1:-""}
    
    if [ -z "$environment" ]; then
        show_usage
        exit 1
    fi
    
    log_info "🚀 SaaS Control Deck 多环境数据库部署开始"
    echo "================================================"
    
    # 检查依赖
    check_dependencies
    
    case $environment in
        "development"|"staging"|"production")
            setup_environment "$environment"
            ;;
        "all")
            setup_environment "development"
            setup_environment "staging" 
            setup_environment "production"
            ;;
        *)
            log_error "无效的环境参数: $environment"
            show_usage
            exit 1
            ;;
    esac
    
    echo "================================================"
    log_success "🎉 SaaS Control Deck 多环境数据库部署完成!"
    echo ""
    echo "下一步:"
    echo "1. 更新Firebase Studio项目的API URL配置"
    echo "2. 配置GitHub Actions的环境变量和Secrets"
    echo "3. 运行环境健康检查: ./scripts/ci/health-check.sh"
    echo ""
}

# 脚本执行入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi