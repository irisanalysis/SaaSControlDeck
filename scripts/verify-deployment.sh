#!/bin/bash

# ===========================================
# SaaS Control Deck - 部署验证脚本
# ===========================================
# 验证Docker部署的健康状态和服务可用性

set -e

# ===========================================
# 颜色定义
# ===========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===========================================
# 默认配置
# ===========================================
FRONTEND_URL="http://localhost:9000"
BACKEND_PRO1_URL="http://localhost:8000"
BACKEND_PRO2_URL="http://localhost:8100"
TIMEOUT=30
RETRY_COUNT=3
DETAILED_CHECK=false

# ===========================================
# 日志函数
# ===========================================
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

# ===========================================
# 显示帮助信息
# ===========================================
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
  --frontend-url URL     Frontend URL (default: http://localhost:9000)
  --backend-pro1-url URL Backend Pro1 URL (default: http://localhost:8000)
  --backend-pro2-url URL Backend Pro2 URL (default: http://localhost:8100)
  --timeout SECONDS      Request timeout (default: 30)
  --retry COUNT          Retry count for failed checks (default: 3)
  --detailed             Run detailed health checks
  -h, --help            Show this help message

Examples:
  $0                                         # Basic health check
  $0 --detailed                              # Detailed health check
  $0 --timeout 10 --retry 5                 # Custom timeout and retry
  $0 --frontend-url http://mydomain.com:9000 # Custom frontend URL

EOF
}

# ===========================================
# 参数解析
# ===========================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --backend-pro1-url)
            BACKEND_PRO1_URL="$2"
            shift 2
            ;;
        --backend-pro2-url)
            BACKEND_PRO2_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --retry)
            RETRY_COUNT="$2"
            shift 2
            ;;
        --detailed)
            DETAILED_CHECK=true
            shift
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

# ===========================================
# HTTP健康检查函数
# ===========================================
check_http_endpoint() {
    local url="$1"
    local service_name="$2"
    local expected_status="${3:-200}"
    local retry_count="$RETRY_COUNT"

    log_info "检查 $service_name: $url"

    for ((i=1; i<=retry_count; i++)); do
        if response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null); then
            http_code="${response: -3}"
            response_body="${response%???}"

            if [[ "$http_code" == "$expected_status" ]]; then
                log_success "$service_name 健康检查通过 (HTTP $http_code)"

                # 如果是详细检查，显示响应内容
                if [[ "$DETAILED_CHECK" == "true" && -n "$response_body" ]]; then
                    echo "  响应内容: $response_body" | head -c 200
                    echo ""
                fi
                return 0
            else
                log_warning "$service_name 返回异常状态码: $http_code (尝试 $i/$retry_count)"
            fi
        else
            log_warning "$service_name 连接失败 (尝试 $i/$retry_count)"
        fi

        if [[ $i -lt $retry_count ]]; then
            sleep 2
        fi
    done

    log_error "$service_name 健康检查失败"
    return 1
}

# ===========================================
# Docker容器状态检查
# ===========================================
check_docker_containers() {
    log_info "检查Docker容器状态..."

    local containers=(
        "saascontrol-frontend"
        "saascontrol-backend-pro1"
        "saascontrol-backend-pro2"
        "saascontrol-redis"
    )

    local all_healthy=true

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" --format "table {{.Names}}\t{{.Status}}" | grep -q "$container"; then
            local status=$(docker ps --filter "name=$container" --format "{{.Status}}")
            log_success "$container 运行中: $status"

            # 检查健康状态
            if docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
                log_success "$container 健康状态: 健康"
            elif docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "starting"; then
                log_warning "$container 健康状态: 启动中"
            else
                log_warning "$container 健康状态: 未知或不健康"
            fi
        else
            log_error "$container 未运行"
            all_healthy=false
        fi
    done

    return $([ "$all_healthy" = true ] && echo 0 || echo 1)
}

# ===========================================
# 服务健康检查
# ===========================================
check_services() {
    log_info "开始服务健康检查..."

    local check_results=()

    # 检查前端服务
    if check_http_endpoint "$FRONTEND_URL/api/health" "前端服务"; then
        check_results+=("frontend:success")
    else
        check_results+=("frontend:failed")
    fi

    # 检查后端Pro1服务
    if check_http_endpoint "$BACKEND_PRO1_URL/health" "后端Pro1服务"; then
        check_results+=("backend-pro1:success")
    else
        check_results+=("backend-pro1:failed")
    fi

    # 检查后端Pro2服务
    if check_http_endpoint "$BACKEND_PRO2_URL/health" "后端Pro2服务"; then
        check_results+=("backend-pro2:success")
    else
        check_results+=("backend-pro2:failed")
    fi

    # 如果启用详细检查，检查API文档端点
    if [[ "$DETAILED_CHECK" == "true" ]]; then
        log_info "详细检查: API文档端点..."

        check_http_endpoint "$BACKEND_PRO1_URL/docs" "后端Pro1 API文档" || true
        check_http_endpoint "$BACKEND_PRO2_URL/docs" "后端Pro2 API文档" || true

        # 检查详细健康状态
        if check_http_endpoint "$FRONTEND_URL/api/health?detailed=true" "前端详细健康检查"; then
            log_success "前端详细健康检查通过"
        fi

        if check_http_endpoint "$BACKEND_PRO1_URL/health/detailed" "后端Pro1详细健康检查"; then
            log_success "后端Pro1详细健康检查通过"
        fi

        if check_http_endpoint "$BACKEND_PRO2_URL/health/detailed" "后端Pro2详细健康检查"; then
            log_success "后端Pro2详细健康检查通过"
        fi
    fi

    # 统计结果
    local success_count=0
    local total_count=0
    for result in "${check_results[@]}"; do
        total_count=$((total_count + 1))
        if [[ "$result" == *":success" ]]; then
            success_count=$((success_count + 1))
        fi
    done

    echo ""
    if [[ $success_count -eq $total_count ]]; then
        log_success "所有核心服务健康检查通过 ($success_count/$total_count)"
        return 0
    else
        log_error "部分服务健康检查失败 ($success_count/$total_count)"
        return 1
    fi
}

# ===========================================
# 显示系统信息
# ===========================================
show_system_info() {
    if [[ "$DETAILED_CHECK" == "true" ]]; then
        log_info "系统信息..."

        echo -e "${YELLOW}Docker信息:${NC}"
        docker version --format "  Docker: {{.Server.Version}}" 2>/dev/null || echo "  Docker: 无法获取版本信息"

        echo -e "${YELLOW}容器资源使用:${NC}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10 || echo "  无法获取容器统计信息"

        echo -e "${YELLOW}磁盘使用:${NC}"
        df -h / | tail -1 | awk '{print "  根分区: " $5 " 已使用 (" $3 "/" $2 ")"}'

        echo ""
    fi
}

# ===========================================
# 生成报告
# ===========================================
generate_report() {
    echo -e "\n${GREEN}===============================================${NC}"
    echo -e "${GREEN}           部署验证报告${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    echo -e "${BLUE}检查配置:${NC}"
    echo "  前端URL: $FRONTEND_URL"
    echo "  后端Pro1 URL: $BACKEND_PRO1_URL"
    echo "  后端Pro2 URL: $BACKEND_PRO2_URL"
    echo "  超时时间: ${TIMEOUT}秒"
    echo "  重试次数: $RETRY_COUNT"
    echo "  详细检查: $([ "$DETAILED_CHECK" = true ] && echo "开启" || echo "关闭")"
    echo ""

    echo -e "${BLUE}服务端点:${NC}"
    echo "  🌐 前端应用: $FRONTEND_URL"
    echo "  ⚙️  API Pro1: $BACKEND_PRO1_URL/docs"
    echo "  ⚙️  API Pro2: $BACKEND_PRO2_URL/docs"
    echo "  🔍 健康检查: $FRONTEND_URL/api/health?detailed=true"
    echo ""

    echo -e "${YELLOW}推荐命令:${NC}"
    echo "  查看容器日志: docker-compose -f docker-compose.dockerhub.yml logs -f"
    echo "  重启服务: docker-compose -f docker-compose.dockerhub.yml restart"
    echo "  停止服务: docker-compose -f docker-compose.dockerhub.yml down"
    echo ""
}

# ===========================================
# 主执行流程
# ===========================================
main() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "        SaaS Control Deck - 部署验证"
    echo "==============================================="
    echo -e "${NC}"

    local overall_success=true

    # 检查Docker容器状态
    if ! check_docker_containers; then
        overall_success=false
    fi

    echo ""

    # 检查服务健康状态
    if ! check_services; then
        overall_success=false
    fi

    # 显示系统信息
    show_system_info

    # 生成报告
    generate_report

    # 返回结果
    if [[ "$overall_success" == "true" ]]; then
        echo -e "${GREEN}🎉 部署验证成功！所有服务运行正常。${NC}"
        exit 0
    else
        echo -e "${RED}❌ 部署验证失败！请检查上述错误信息。${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"