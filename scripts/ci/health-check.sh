#!/bin/bash

# ===========================================
# 健康检查和监控脚本
# ===========================================
# 用于检查所有服务的健康状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 默认参数
CHECK_TYPE="all"
TIMEOUT=10
VERBOSE=false
JSON_OUTPUT=false
CONTINUOUS=false
INTERVAL=30

# 服务配置
declare -A SERVICES=(
    ["frontend"]="http://localhost:9000"
    ["backend-pro1-api"]="http://localhost:8000"
    ["backend-pro1-data"]="http://localhost:8001"
    ["backend-pro1-ai"]="http://localhost:8002"
    ["backend-pro2-api"]="http://localhost:8100"
    ["backend-pro2-data"]="http://localhost:8101"
    ["backend-pro2-ai"]="http://localhost:8102"
)

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
健康检查和监控脚本

用法: $0 [选项]

选项:
    -t, --type TYPE        检查类型: frontend, backend, all (默认: all)
    -T, --timeout SECONDS  超时时间 (默认: 10秒)
    -v, --verbose          详细输出
    -j, --json             JSON格式输出
    -c, --continuous       持续监控模式
    -i, --interval SECONDS 监控间隔 (默认: 30秒)
    -h, --help             显示此帮助

示例:
    $0                     # 检查所有服务
    $0 -t frontend -v      # 详细检查前端服务
    $0 -c -i 60           # 每60秒持续监控
    $0 -j                 # JSON格式输出

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                CHECK_TYPE="$2"
                shift 2
                ;;
            -T|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -j|--json)
                JSON_OUTPUT=true
                shift
                ;;
            -c|--continuous)
                CONTINUOUS=true
                shift
                ;;
            -i|--interval)
                INTERVAL="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查单个服务
check_service() {
    local service_name="$1"
    local service_url="$2"
    local start_time=$(date +%s%N)
    
    # 基础健康检查
    local health_url="${service_url}/health"
    local ready_url="${service_url}/ready"
    
    # 检查健康状态
    local health_status="unknown"
    local health_response=""
    local health_time=0
    
    if curl -f -s -m "$TIMEOUT" "$health_url" > /tmp/health_response 2>/dev/null; then
        health_status="healthy"
        health_response=$(cat /tmp/health_response)
        local end_time=$(date +%s%N)
        health_time=$(( (end_time - start_time) / 1000000 ))
    else
        health_status="unhealthy"
        health_response="Connection failed"
    fi
    
    # 检查就绪状态
    local ready_status="unknown"
    local ready_response=""
    local ready_time=0
    
    start_time=$(date +%s%N)
    if curl -f -s -m "$TIMEOUT" "$ready_url" > /tmp/ready_response 2>/dev/null; then
        ready_status="ready"
        ready_response=$(cat /tmp/ready_response)
        local end_time=$(date +%s%N)
        ready_time=$(( (end_time - start_time) / 1000000 ))
    else
        ready_status="not_ready"
        ready_response="Connection failed"
    fi
    
    # 输出结果
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        cat << EOF
{
  "service": "$service_name",
  "url": "$service_url",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "health": {
    "status": "$health_status",
    "response_time": ${health_time},
    "response": $(echo "$health_response" | jq -R . 2>/dev/null || echo "\"$health_response\"")
  },
  "readiness": {
    "status": "$ready_status",
    "response_time": ${ready_time},
    "response": $(echo "$ready_response" | jq -R . 2>/dev/null || echo "\"$ready_response\"")
  }
}
EOF
    else
        printf "%-20s %-15s %-15s %5dms %5dms\n" \
            "$service_name" \
            "$health_status" \
            "$ready_status" \
            "$health_time" \
            "$ready_time"
        
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Health URL: $health_url"
            echo "  Ready URL: $ready_url"
            if [[ "$health_status" != "healthy" ]]; then
                echo "  Health Error: $health_response"
            fi
            if [[ "$ready_status" != "ready" ]]; then
                echo "  Ready Error: $ready_response"
            fi
            echo ""
        fi
    fi
    
    # 清理临时文件
    rm -f /tmp/health_response /tmp/ready_response
    
    # 返回状态码
    if [[ "$health_status" == "healthy" && "$ready_status" == "ready" ]]; then
        return 0
    else
        return 1
    fi
}

# 检查前端服务
check_frontend() {
    log_info "检查前端服务..."
    
    local failed=0
    local total=0
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo '{"frontend_services": ['
    else
        printf "\n%-20s %-15s %-15s %8s %8s\n" "Service" "Health" "Ready" "Health" "Ready"
        printf "%-20s %-15s %-15s %8s %8s\n" "" "" "" "(ms)" "(ms)"
        printf "%s\n" "$(printf '=%.0s' {1..75})"
    fi
    
    # 检查前端服务
    total=$((total + 1))
    if check_service "frontend" "${SERVICES[frontend]}"; then
        :
    else
        failed=$((failed + 1))
    fi
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo ']}'
    else
        echo ""
        log_info "前端服务检查完成: $((total - failed))/$total 健康"
    fi
    
    return $failed
}

# 检查后端服务
check_backend() {
    log_info "检查后端服务..."
    
    local failed=0
    local total=0
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo '{"backend_services": ['
        local first=true
    else
        printf "\n%-20s %-15s %-15s %8s %8s\n" "Service" "Health" "Ready" "Health" "Ready"
        printf "%-20s %-15s %-15s %8s %8s\n" "" "" "" "(ms)" "(ms)"
        printf "%s\n" "$(printf '=%.0s' {1..75})"
    fi
    
    # 检查所有后端服务
    for service in backend-pro1-api backend-pro1-data backend-pro1-ai backend-pro2-api backend-pro2-data backend-pro2-ai; do
        total=$((total + 1))
        
        if [[ "$JSON_OUTPUT" == "true" ]]; then
            if [[ "$first" != "true" ]]; then
                echo ","
            fi
            first=false
        fi
        
        if check_service "$service" "${SERVICES[$service]}"; then
            :
        else
            failed=$((failed + 1))
        fi
    done
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo ']}'
    else
        echo ""
        log_info "后端服务检查完成: $((total - failed))/$total 健康"
    fi
    
    return $failed
}

# 检查所有服务
check_all() {
    local frontend_failed=0
    local backend_failed=0
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo '{'
        echo '"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",'
        echo '"check_type": "all",'
    fi
    
    # 检查前端
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        check_frontend
        echo ','
        check_backend
    else
        check_frontend
        frontend_failed=$?
        
        check_backend
        backend_failed=$?
    fi
    
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo '}'
    else
        local total_failed=$((frontend_failed + backend_failed))
        if [[ $total_failed -eq 0 ]]; then
            log_success "所有服务运行正常"
        else
            log_warning "$total_failed 个服务存在问题"
        fi
    fi
    
    return $((frontend_failed + backend_failed))
}

# 生成健康报告
generate_health_report() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="health-report-$timestamp.json"
    
    log_info "生成健康检查报告..."
    
    # 临时启用JSON输出
    local original_json_output=$JSON_OUTPUT
    JSON_OUTPUT=true
    
    check_all > "$report_file"
    
    # 恢复原始设置
    JSON_OUTPUT=$original_json_output
    
    log_success "健康检查报告已生成: $report_file"
}

# 持续监控
continuous_monitoring() {
    log_info "开始持续监控 (间隔: ${INTERVAL}秒, Ctrl+C 停止)"
    
    local iteration=1
    
    while true; do
        echo ""
        log_info "=== 监控迭代 #$iteration ($(date)) ==="
        
        check_all
        local exit_code=$?
        
        if [[ $exit_code -eq 0 ]]; then
            log_success "所有服务正常"
        else
            log_warning "发现 $exit_code 个问题"
        fi
        
        echo ""
        log_info "等待 $INTERVAL 秒..."
        sleep "$INTERVAL"
        
        iteration=$((iteration + 1))
    done
}

# 主函数
main() {
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo "================================================"
        echo "    SaaS Control Deck - 健康检查和监控"
        echo "================================================"
    fi
    
    parse_args "$@"
    
    # 检查依赖
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi
    
    if [[ "$JSON_OUTPUT" == "true" && ! command -v jq &> /dev/null ]]; then
        log_warning "建议安装 jq 以获得更好的JSON处理"
    fi
    
    # 执行检查
    case $CHECK_TYPE in
        frontend)
            if [[ "$CONTINUOUS" == "true" ]]; then
                while true; do
                    check_frontend
                    sleep "$INTERVAL"
                done
            else
                check_frontend
            fi
            ;;
        backend)
            if [[ "$CONTINUOUS" == "true" ]]; then
                while true; do
                    check_backend
                    sleep "$INTERVAL"
                done
            else
                check_backend
            fi
            ;;
        all)
            if [[ "$CONTINUOUS" == "true" ]]; then
                continuous_monitoring
            else
                check_all
            fi
            ;;
        *)
            log_error "无效的检查类型: $CHECK_TYPE"
            show_help
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo ""
        echo "================================================"
        if [[ $exit_code -eq 0 ]]; then
            log_success "健康检查完成，所有服务正常"
        else
            log_warning "健康检查完成，发现 $exit_code 个问题"
        fi
        echo "================================================"
    fi
    
    exit $exit_code
}

# 信号处理
trap 'echo ""; log_info "收到中断信号，正在退出..."; exit 0' INT TERM

# 执行主函数
main "$@"