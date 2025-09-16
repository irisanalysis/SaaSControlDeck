#!/bin/bash

# ===========================================
# SaaS Control Deck - 云服务器自动化部署流水线
# ===========================================
# 完整的云服务器部署自动化脚本，包含健康检查、回滚和监控

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_ROOT="/opt/saascontroldeck"
LOG_FILE="/var/log/saascontroldeck/deploy-$(date +%Y%m%d_%H%M%S).log"

# 部署参数
ENVIRONMENT="production"
DEPLOYMENT_TYPE="cloud"
DOCKER_COMPOSE_FILE="docker/cloud-deployment/docker-compose.cloud.yml"
BACKUP_DIR="/opt/saascontroldeck/backups"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_ENABLED=true
MONITORING_ENABLED=true
NOTIFICATION_ENABLED=false

# 服务配置
declare -A SERVICES=(
    ["frontend"]="frontend-app:9000"
    ["api-pro1"]="api-gateway-pro1:8000"
    ["api-pro2"]="api-gateway-pro2:8100"
    ["data-pro1"]="data-service-pro1:8001"
    ["data-pro2"]="data-service-pro2:8101"
    ["ai-pro1"]="ai-service-pro1:8002"
    ["ai-pro2"]="ai-service-pro2:8102"
    ["postgres"]="postgres-primary:5432"
    ["redis"]="redis-cache:6379"
    ["minio"]="minio-storage:9000"
)

declare -A HEALTH_ENDPOINTS=(
    ["frontend"]="http://localhost:9000/api/health"
    ["api-pro1"]="http://localhost:8000/health"
    ["api-pro2"]="http://localhost:8100/health"
    ["data-pro1"]="http://localhost:8001/health"
    ["data-pro2"]="http://localhost:8101/health"
    ["ai-pro1"]="http://localhost:8002/health"
    ["ai-pro2"]="http://localhost:8102/health"
)

# 日志函数
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}
log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}
log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}
log_error() { 
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}
log_step() {
    echo -e "${CYAN}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}
log_deploy() {
    echo -e "${PURPLE}[DEPLOY]${NC} $1" | tee -a "$LOG_FILE"
}

# 显示帮助
show_help() {
    cat << EOF
SaaS Control Deck 云服务器自动化部署流水线

用法: $0 [选项]

选项:
    -e, --environment ENV     部署环境 (production, staging) [默认: production]
    --skip-backup            跳过部署前备份
    --skip-health-check      跳过健康检查
    --skip-monitoring        跳过监控配置
    --disable-rollback       禁用自动回滚
    --force-rebuild          强制重新构建所有镜像
    --services LIST          指定要部署的服务，用逗号分隔
    --timeout SECONDS        健康检查超时时间 [默认: 300]
    --dry-run               预览模式，不执行实际部署
    -v, --verbose           详细输出
    -h, --help              显示此帮助

示例:
    $0                                    # 完整部署到生产环境
    $0 --services frontend,api-pro1      # 仅部署指定服务
    $0 --skip-backup --force-rebuild     # 强制重建，跳过备份
    $0 --dry-run -v                      # 预览模式，详细输出

部署流程:
1. 环境检查和准备
2. 代码同步和构建
3. 数据库备份
4. 镜像构建
5. 服务部署
6. 健康检查
7. 监控配置
8. 部署验证

回滚机制:
- 自动检测部署失败
- 自动回滚到上一个稳定版本
- 保留最近5个版本的备份
EOF
}

# 解析命令行参数
parse_args() {
    SKIP_BACKUP=false
    SKIP_HEALTH_CHECK=false
    SKIP_MONITORING=false
    FORCE_REBUILD=false
    DRY_RUN=false
    VERBOSE=false
    DEPLOY_SERVICES="all"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-health-check)
                SKIP_HEALTH_CHECK=true
                shift
                ;;
            --skip-monitoring)
                SKIP_MONITORING=true
                shift
                ;;
            --disable-rollback)
                ROLLBACK_ENABLED=false
                shift
                ;;
            --force-rebuild)
                FORCE_REBUILD=true
                shift
                ;;
            --services)
                DEPLOY_SERVICES="$2"
                shift 2
                ;;
            --timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
}

# 环境检查
check_environment() {
    log_step "环境检查"
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查部署目录
    if [[ ! -d "$DEPLOY_ROOT" ]]; then
        log_error "部署目录不存在: $DEPLOY_ROOT"
        exit 1
    fi
    
    # 检查Docker服务状态
    if ! systemctl is-active --quiet docker; then
        log_info "启动Docker服务..."
        systemctl start docker
    fi
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 检查磁盘空间
    local disk_usage=$(df "$DEPLOY_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 85 ]]; then
        log_warning "磁盘使用率较高: ${disk_usage}%"
    fi
    
    # 检查内存使用
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $mem_usage -gt 85 ]]; then
        log_warning "内存使用率较高: ${mem_usage}%"
    fi
    
    log_success "环境检查完成"
}

# 代码同步
sync_code() {
    log_step "同步代码到部署目录"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 跳过代码同步"
        return 0
    fi
    
    # 确保目标目录存在
    mkdir -p "$DEPLOY_ROOT"
    
    # 同步代码（排除不需要的文件）
    rsync -av --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.next' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='logs' \
        --exclude='backups' \
        "$PROJECT_ROOT/" "$DEPLOY_ROOT/"
    
    # 复制环境配置文件
    if [[ -f "$PROJECT_ROOT/.env.cloud" ]]; then
        cp "$PROJECT_ROOT/.env.cloud" "$DEPLOY_ROOT/.env"
        log_info "已复制云环境配置文件"
    else
        log_warning "云环境配置文件不存在: .env.cloud"
    fi
    
    # 设置权限
    chown -R saascontrol:saascontrol "$DEPLOY_ROOT"
    
    log_success "代码同步完成"
}

# 创建备份
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_info "跳过备份创建"
        return 0
    fi
    
    log_step "创建部署前备份"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="$BACKUP_DIR/deploy_$timestamp"
    
    mkdir -p "$backup_path"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 备份路径: $backup_path"
        return 0
    fi
    
    # 备份Docker Compose状态
    cd "$DEPLOY_ROOT"
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps --services > "$backup_path/services.txt" 2>/dev/null; then
        log_info "已备份Docker Compose服务状态"
    fi
    
    # 备份环境变量
    if [[ -f "$DEPLOY_ROOT/.env" ]]; then
        cp "$DEPLOY_ROOT/.env" "$backup_path/.env.backup"
    fi
    
    # 备份数据库（如果PostgreSQL正在运行）
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps postgres-primary | grep -q "Up"; then
        log_info "备份PostgreSQL数据库..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres-primary pg_dumpall -U saasuser > "$backup_path/database_backup.sql" 2>/dev/null || log_warning "数据库备份失败"
    fi
    
    # 记录当前镜像版本
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep "saascontroldeck" > "$backup_path/docker_images.txt" 2>/dev/null || true
    
    # 记录Git信息
    cat > "$backup_path/deploy_info.txt" << EOF
Deployment Timestamp: $(date)
Environment: $ENVIRONMENT
Git Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Git Status: $(git status --porcelain 2>/dev/null | wc -l) uncommitted changes
Docker Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)
EOF
    
    export BACKUP_PATH="$backup_path"
    log_success "备份创建完成: $backup_path"
}

# 构建Docker镜像
build_docker_images() {
    log_step "构建Docker镜像"
    
    cd "$DEPLOY_ROOT"
    
    local build_args=""
    if [[ "$FORCE_REBUILD" == "true" ]]; then
        build_args="--no-cache"
        log_info "强制重新构建所有镜像"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 跳过镜像构建"
        return 0
    fi
    
    # 构建前端镜像
    if [[ "$DEPLOY_SERVICES" == "all" || "$DEPLOY_SERVICES" =~ "frontend" ]]; then
        log_info "构建前端镜像..."
        if [[ -f "frontend/Dockerfile" ]]; then
            docker build $build_args -t saascontroldeck-frontend:latest -f frontend/Dockerfile .
            log_success "前端镜像构建完成"
        else
            log_warning "前端Dockerfile不存在，跳过构建"
        fi
    fi
    
    # 构建后端镜像
    for project in "backend-pro1" "backend-pro2"; do
        if [[ "$DEPLOY_SERVICES" == "all" || "$DEPLOY_SERVICES" =~ "$project" ]]; then
            log_info "构建${project}镜像..."
            if [[ -d "backend/$project" && -f "backend/$project/Dockerfile" ]]; then
                cd "backend/$project"
                docker build $build_args -t "saascontroldeck-$project:latest" .
                cd "$DEPLOY_ROOT"
                log_success "${project}镜像构建完成"
            else
                log_warning "${project}目录或Dockerfile不存在，跳过构建"
            fi
        fi
    done
    
    # 清理unused镜像
    log_info "清理未使用的Docker镜像..."
    docker image prune -f > /dev/null 2>&1 || true
    
    log_success "Docker镜像构建完成"
}

# 部署服务
deploy_services() {
    log_step "部署服务到云服务器"
    
    cd "$DEPLOY_ROOT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] docker-compose -f $DOCKER_COMPOSE_FILE up -d"
        return 0
    fi
    
    # 检查Docker Compose文件
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Docker Compose文件不存在: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # 验证Docker Compose配置
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" config > /dev/null; then
        log_error "Docker Compose配置验证失败"
        exit 1
    fi
    
    # 拉取基础镜像
    log_info "拉取基础镜像..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull postgres-primary redis-cache minio-storage prometheus grafana elasticsearch kibana > /dev/null 2>&1 || log_warning "部分基础镜像拉取失败"
    
    # 创建网络和卷
    log_info "创建Docker网络和卷..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up --no-start
    
    # 启动基础设施服务
    log_deploy "启动基础设施服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres-primary redis-cache minio-storage
    
    # 等待基础服务就绪
    log_info "等待基础服务启动..."
    sleep 30
    
    # 启动应用服务
    if [[ "$DEPLOY_SERVICES" == "all" ]]; then
        log_deploy "启动所有应用服务..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        log_deploy "启动指定服务: $DEPLOY_SERVICES"
        IFS=',' read -ra SERVICE_ARRAY <<< "$DEPLOY_SERVICES"
        for service in "${SERVICE_ARRAY[@]}"; do
            docker-compose -f "$DOCKER_COMPOSE_FILE" up -d "$service"
        done
    fi
    
    # 等待服务启动
    log_info "等待服务完全启动..."
    sleep 60
    
    # 启动监控服务
    if [[ "$SKIP_MONITORING" != "true" ]]; then
        log_deploy "启动监控服务..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d prometheus grafana elasticsearch kibana
    fi
    
    log_success "服务部署完成"
}

# 健康检查
perform_health_checks() {
    if [[ "$SKIP_HEALTH_CHECK" == "true" ]]; then
        log_info "跳过健康检查"
        return 0
    fi
    
    log_step "执行健康检查"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + HEALTH_CHECK_TIMEOUT))
    local all_healthy=false
    local check_count=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        check_count=$((check_count + 1))
        log_info "健康检查第${check_count}轮..."
        
        local healthy_services=0
        local total_services=0
        
        for service in "${!HEALTH_ENDPOINTS[@]}"; do
            if [[ "$DEPLOY_SERVICES" != "all" && ! "$DEPLOY_SERVICES" =~ "$service" ]]; then
                continue
            fi
            
            total_services=$((total_services + 1))
            local endpoint="${HEALTH_ENDPOINTS[$service]}"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "[DRY RUN] 检查 $service: $endpoint"
                healthy_services=$((healthy_services + 1))
                continue
            fi
            
            local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" --max-time 10 || echo "000")
            
            if [[ "$response_code" =~ ^(200|201)$ ]]; then
                log_success "✓ $service 健康检查通过"
                healthy_services=$((healthy_services + 1))
            else
                log_warning "✗ $service 健康检查失败 (HTTP $response_code)"
            fi
        done
        
        if [[ $healthy_services -eq $total_services ]]; then
            all_healthy=true
            break
        fi
        
        log_info "健康服务: $healthy_services/$total_services，等待30秒后重试..."
        sleep 30
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        log_success "所有服务健康检查通过！"
        return 0
    else
        log_error "健康检查失败或超时"
        return 1
    fi
}

# 部署验证
verify_deployment() {
    log_step "部署验证"
    
    cd "$DEPLOY_ROOT"
    
    # 检查Docker服务状态
    log_info "检查Docker服务状态..."
    local failed_services=()
    
    while IFS= read -r service; do
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            failed_services+=("$service")
        fi
    done < <(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --services)
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "以下服务状态异常: ${failed_services[*]}"
        return 1
    fi
    
    # 检查容器资源使用
    log_info "检查容器资源使用情况..."
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10
    
    # 检查日志中的错误
    log_info "检查应用日志..."
    local error_count=0
    
    for service in frontend-app api-gateway-pro1 api-gateway-pro2; do
        local container_errors=$(docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50 "$service" 2>/dev/null | grep -i "error\|exception\|failed" | wc -l || echo "0")
        if [[ $container_errors -gt 0 ]]; then
            log_warning "$service 容器发现 $container_errors 个错误日志条目"
            error_count=$((error_count + container_errors))
        fi
    done
    
    if [[ $error_count -gt 10 ]]; then
        log_warning "发现较多错误日志，建议检查应用状态"
    fi
    
    # 测试关键业务功能
    log_info "测试关键业务功能..."
    
    if [[ "$DRY_RUN" != "true" ]]; then
        # 测试前端访问
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:9000" --max-time 10 | grep -E "^(200|301|302)$" > /dev/null; then
            log_success "✓ 前端服务可访问"
        else
            log_error "✗ 前端服务访问失败"
            return 1
        fi
        
        # 测试API服务
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" --max-time 10 | grep -E "^200$" > /dev/null; then
            log_success "✓ API服务正常"
        else
            log_error "✗ API服务异常"
            return 1
        fi
    fi
    
    log_success "部署验证完成"
}

# 配置监控
setup_monitoring() {
    if [[ "$SKIP_MONITORING" == "true" ]]; then
        log_info "跳过监控配置"
        return 0
    fi
    
    log_step "配置监控系统"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 跳过监控配置"
        return 0
    fi
    
    cd "$DEPLOY_ROOT"
    
    # 检查Prometheus是否运行
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps prometheus | grep -q "Up"; then
        log_info "Prometheus监控服务已运行"
        
        # 测试Prometheus连接
        if curl -s "http://localhost:9090/api/v1/query?query=up" --max-time 10 > /dev/null; then
            log_success "✓ Prometheus监控正常"
        else
            log_warning "✗ Prometheus监控连接失败"
        fi
    else
        log_warning "Prometheus监控服务未运行"
    fi
    
    # 检查Grafana是否运行
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps grafana | grep -q "Up"; then
        log_info "Grafana仪表板服务已运行"
        log_info "Grafana访问地址: http://localhost:3000"
    fi
    
    # 配置日志收集
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps elasticsearch | grep -q "Up"; then
        log_info "Elasticsearch日志系统已运行"
        log_info "Kibana访问地址: http://localhost:5601"
    fi
    
    log_success "监控配置完成"
}

# 发送通知
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ "$NOTIFICATION_ENABLED" != "true" ]]; then
        return 0
    fi
    
    # 这里可以集成邮件、Slack、钉钉等通知服务
    log_info "发送部署通知: $status - $message"
    
    # 示例：发送邮件通知
    # echo "$message" | mail -s "SaaS Control Deck 部署通知 - $status" admin@yourdomain.com
}

# 回滚部署
rollback_deployment() {
    if [[ "$ROLLBACK_ENABLED" != "true" ]]; then
        log_error "自动回滚已禁用，请手动处理"
        return 1
    fi
    
    log_step "执行自动回滚"
    
    if [[ -z "$BACKUP_PATH" ]]; then
        log_error "没有备份信息，无法执行回滚"
        return 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 执行回滚到: $BACKUP_PATH"
        return 0
    fi
    
    cd "$DEPLOY_ROOT"
    
    # 停止当前服务
    log_info "停止当前服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down || true
    
    # 恢复环境配置
    if [[ -f "$BACKUP_PATH/.env.backup" ]]; then
        cp "$BACKUP_PATH/.env.backup" "$DEPLOY_ROOT/.env"
        log_info "已恢复环境配置"
    fi
    
    # 恢复数据库
    if [[ -f "$BACKUP_PATH/database_backup.sql" ]]; then
        log_info "恢复数据库备份..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres-primary
        sleep 30
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres-primary psql -U saasuser -d postgres < "$BACKUP_PATH/database_backup.sql" || log_warning "数据库恢复失败"
    fi
    
    # 重启服务
    log_info "重启服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_success "回滚完成"
    send_notification "ROLLBACK" "部署已回滚到: $(basename "$BACKUP_PATH")"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份文件..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        # 保留最近5个备份
        find "$BACKUP_DIR" -name "deploy_*" -type d -mtime +5 -exec rm -rf {} + 2>/dev/null || true
        log_info "旧备份清理完成"
    fi
}

# 显示部署摘要
show_deployment_summary() {
    local deployment_status="$1"
    local start_time="$2"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo "================================================"
    echo "         SaaS Control Deck 部署摘要"
    echo "================================================"
    echo ""
    echo "部署状态: $deployment_status"
    echo "部署环境: $ENVIRONMENT"
    echo "部署类型: $DEPLOYMENT_TYPE"
    echo "部署时间: $(date -d "@$start_time" '+%Y-%m-%d %H:%M:%S') - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "部署耗时: ${duration}秒"
    echo ""
    echo "部署服务: $DEPLOY_SERVICES"
    echo "Docker Compose文件: $DOCKER_COMPOSE_FILE"
    echo "部署目录: $DEPLOY_ROOT"
    echo "日志文件: $LOG_FILE"
    
    if [[ -n "$BACKUP_PATH" ]]; then
        echo "备份位置: $BACKUP_PATH"
    fi
    
    echo ""
    echo "服务访问地址:"
    echo "  前端应用: http://localhost:9000"
    echo "  API Pro1: http://localhost:8000"
    echo "  API Pro2: http://localhost:8100"
    echo "  Grafana监控: http://localhost:3000"
    echo "  Prometheus: http://localhost:9090"
    echo "  Kibana日志: http://localhost:5601"
    echo ""
    echo "================================================"
}

# 主函数
main() {
    local start_time=$(date +%s)
    
    echo "================================================"
    echo "   SaaS Control Deck 云服务器自动化部署"
    echo "================================================"
    
    parse_args "$@"
    
    # 创建日志文件
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "部署开始时间: $(date)" > "$LOG_FILE"
    
    log_deploy "开始云服务器部署流水线..."
    log_info "日志文件: $LOG_FILE"
    
    # 执行部署流程
    if check_environment && \
       sync_code && \
       create_backup && \
       build_docker_images && \
       deploy_services && \
       perform_health_checks && \
       verify_deployment && \
       setup_monitoring; then
        
        cleanup_old_backups
        show_deployment_summary "SUCCESS" "$start_time"
        send_notification "SUCCESS" "SaaS Control Deck云服务器部署成功完成"
        
        log_success "🎉 云服务器部署完成！"
        exit 0
    else
        log_error "部署过程中发生错误"
        
        if [[ "$ROLLBACK_ENABLED" == "true" && "$DRY_RUN" != "true" ]]; then
            log_warning "尝试自动回滚..."
            if rollback_deployment; then
                show_deployment_summary "ROLLBACK" "$start_time"
                send_notification "FAILED" "部署失败，已自动回滚"
            else
                show_deployment_summary "FAILED" "$start_time"
                send_notification "CRITICAL" "部署失败，回滚也失败，需要手动干预"
            fi
        else
            show_deployment_summary "FAILED" "$start_time"
        fi
        
        log_error "❌ 云服务器部署失败！"
        exit 1
    fi
}

# 错误处理
trap 'log_error "部署过程中发生错误，请查看日志: $LOG_FILE"; exit 1' ERR

# 执行主函数
main "$@"