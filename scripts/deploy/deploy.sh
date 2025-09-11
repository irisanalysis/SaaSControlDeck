#!/bin/bash

# ===========================================
# SaaS Control Deck - 自动化部署脚本
# ===========================================
# 支持多环境部署和回滚功能

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
ENVIRONMENT="staging"
SERVICE="all"
STRATEGY="rolling"
DRY_RUN=false
VERBOSE=false
SKIP_TESTS=false
SKIP_BACKUP=false
AUTO_APPROVE=false

# 部署配置
declare -A ENVIRONMENTS=(
    ["development"]="dev"
    ["staging"]="staging"
    ["production"]="prod"
)

declare -A SERVICES=(
    ["frontend"]="frontend"
    ["backend-pro1"]="backend-pro1"
    ["backend-pro2"]="backend-pro2"
    ["all"]="frontend,backend-pro1,backend-pro2"
)

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
SaaS Control Deck 自动化部署脚本

用法: $0 [选项]

选项:
    -e, --environment ENV   部署环境: development, staging, production (默认: staging)
    -s, --service SERVICE   服务: frontend, backend-pro1, backend-pro2, all (默认: all)
    -S, --strategy STRATEGY 部署策略: rolling, blue-green, canary (默认: rolling)
    -d, --dry-run           预览模式，不执行实际部署
    -v, --verbose           详细输出
    --skip-tests            跳过测试
    --skip-backup           跳过备份
    --auto-approve          自动批准，无需确认
    -h, --help              显示此帮助

示例:
    $0                                    # 部署所有服务到staging
    $0 -e production -s frontend          # 部署前端到production
    $0 -S blue-green -v                   # 使用蓝绿部署策略，详细输出
    $0 -d                                 # 预览部署，不实际执行

部署策略说明:
    rolling    - 滚动更新 (默认)
    blue-green - 蓝绿部署
    canary     - 金丝雀发布

环境说明:
    development - 开发环境
    staging     - 预生产环境
    production  - 生产环境

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--service)
                SERVICE="$2"
                shift 2
                ;;
            -S|--strategy)
                STRATEGY="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --auto-approve)
                AUTO_APPROVE=true
                shift
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

# 验证参数
validate_args() {
    # 验证环境
    if [[ ! "${ENVIRONMENTS[$ENVIRONMENT]}" ]]; then
        log_error "无效的环境: $ENVIRONMENT"
        log_error "可用环境: ${!ENVIRONMENTS[*]}"
        exit 1
    fi

    # 验证服务
    if [[ ! "${SERVICES[$SERVICE]}" ]]; then
        log_error "无效的服务: $SERVICE"
        log_error "可用服务: ${!SERVICES[*]}"
        exit 1
    fi

    # 验证部署策略
    case $STRATEGY in
        rolling|blue-green|canary)
            ;;
        *)
            log_error "无效的部署策略: $STRATEGY"
            log_error "可用策略: rolling, blue-green, canary"
            exit 1
            ;;
    esac
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."

    local missing_deps=()

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi

    # 检查Git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi

    # 检查curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        exit 1
    fi

    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi

    log_success "依赖检查完成"
}

# 检查Git状态
check_git_status() {
    log_info "检查Git状态..."

    cd "$PROJECT_ROOT"

    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        log_warning "存在未提交的更改"
        if [[ "$AUTO_APPROVE" != "true" ]]; then
            read -p "是否继续部署? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "部署已取消"
                exit 0
            fi
        fi
    fi

    # 获取当前分支和提交
    local current_branch=$(git branch --show-current)
    local current_commit=$(git rev-parse HEAD)
    local commit_short=$(git rev-parse --short HEAD)

    log_info "当前分支: $current_branch"
    log_info "当前提交: $commit_short"

    # 验证分支策略
    case $ENVIRONMENT in
        production)
            if [[ "$current_branch" != "main" ]]; then
                log_error "生产环境只能从main分支部署"
                exit 1
            fi
            ;;
        staging)
            if [[ "$current_branch" != "main" && "$current_branch" != "develop" ]]; then
                log_warning "建议从main或develop分支部署到staging"
            fi
            ;;
    esac

    export DEPLOY_COMMIT="$current_commit"
    export DEPLOY_BRANCH="$current_branch"
}

# 运行测试
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "跳过测试"
        return 0
    fi

    log_info "运行部署前测试..."

    # 运行测试脚本
    if [[ -x "$PROJECT_ROOT/scripts/ci/run-tests.sh" ]]; then
        "$PROJECT_ROOT/scripts/ci/run-tests.sh" -ci
    else
        log_warning "测试脚本不存在，跳过测试"
    fi
}

# 创建备份
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warning "跳过备份"
        return 0
    fi

    log_info "创建部署备份..."

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="$PROJECT_ROOT/backups/deploy_$timestamp"

    mkdir -p "$backup_dir"

    # 备份当前Docker镜像标签
    if command -v docker &> /dev/null; then
        docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" \
            | grep "saascontroldeck" > "$backup_dir/docker_images.txt" || true
    fi

    # 备份配置文件
    cp -r "$PROJECT_ROOT/docker/" "$backup_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/.env.example" "$backup_dir/" 2>/dev/null || true

    # 记录Git信息
    cat > "$backup_dir/git_info.txt" << EOF
Branch: $(git branch --show-current)
Commit: $(git rev-parse HEAD)
Timestamp: $(date)
Environment: $ENVIRONMENT
Service: $SERVICE
Strategy: $STRATEGY
EOF

    log_success "备份已创建: $backup_dir"
    export BACKUP_DIR="$backup_dir"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."

    local services_to_build=(${SERVICES[$SERVICE]//,/ })

    for service in "${services_to_build[@]}"; do
        case $service in
            frontend)
                build_frontend_image
                ;;
            backend-pro1|backend-pro2)
                build_backend_image "$service"
                ;;
        esac
    done
}

# 构建前端镜像
build_frontend_image() {
    log_info "构建前端镜像..."

    cd "$PROJECT_ROOT"

    local image_tag="saascontroldeck-frontend:${DEPLOY_COMMIT:0:8}"
    local latest_tag="saascontroldeck-frontend:latest"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] docker build -t $image_tag -t $latest_tag -f frontend/Dockerfile ."
    else
        docker build -t "$image_tag" -t "$latest_tag" -f frontend/Dockerfile .
        log_success "前端镜像构建完成: $image_tag"
    fi

    export FRONTEND_IMAGE="$image_tag"
}

# 构建后端镜像
build_backend_image() {
    local project="$1"
    log_info "构建后端镜像: $project..."

    cd "$PROJECT_ROOT/backend/$project"

    # 构建各个服务镜像
    local services=("api-gateway" "data-service" "ai-service")

    for svc in "${services[@]}"; do
        local image_tag="saascontroldeck-$project-$svc:${DEPLOY_COMMIT:0:8}"
        local latest_tag="saascontroldeck-$project-$svc:latest"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] docker build -t $image_tag -t $latest_tag -f $svc/Dockerfile ."
        else
            docker build -t "$image_tag" -t "$latest_tag" -f "$svc/Dockerfile" .
            log_success "$project $svc 镜像构建完成: $image_tag"
        fi
    done
}

# 滚动更新部署
deploy_rolling() {
    log_info "执行滚动更新部署..."

    local services_to_deploy=(${SERVICES[$SERVICE]//,/ })

    for service in "${services_to_deploy[@]}"; do
        log_info "部署服务: $service"

        case $service in
            frontend)
                deploy_frontend_rolling
                ;;
            backend-pro1|backend-pro2)
                deploy_backend_rolling "$service"
                ;;
        esac
    done
}

# 前端滚动部署
deploy_frontend_rolling() {
    log_info "前端滚动部署..."

    if [[ "$ENVIRONMENT" == "production" ]]; then
        # 生产环境使用Docker部署
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] docker-compose -f docker/environments/docker-compose.production.yml up -d frontend"
        else
            cd "$PROJECT_ROOT"
            docker-compose -f docker/environments/docker-compose.production.yml up -d frontend
        fi
    else
        # 其他环境可能使用Vercel
        log_info "前端将通过Vercel自动部署"
    fi
}

# 后端滚动部署
deploy_backend_rolling() {
    local project="$1"
    log_info "后端滚动部署: $project..."

    cd "$PROJECT_ROOT/backend/$project"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] docker-compose up -d"
    else
        # 更新环境变量
        if [[ -f ".env.$ENVIRONMENT" ]]; then
            cp ".env.$ENVIRONMENT" .env
        fi

        # 滚动更新
        docker-compose up -d

        # 等待服务健康
        sleep 30
        "$PROJECT_ROOT/scripts/ci/health-check.sh" -t backend
    fi
}

# 蓝绿部署
deploy_blue_green() {
    log_info "执行蓝绿部署..."
    log_warning "蓝绿部署策略需要额外配置，当前使用滚动更新"
    deploy_rolling
}

# 金丝雀发布
deploy_canary() {
    log_info "执行金丝雀发布..."
    log_warning "金丝雀发布策略需要额外配置，当前使用滚动更新"
    deploy_rolling
}

# 部署后验证
post_deploy_validation() {
    log_info "执行部署后验证..."

    # 等待服务启动
    sleep 30

    # 健康检查
    if [[ -x "$PROJECT_ROOT/scripts/ci/health-check.sh" ]]; then
        if "$PROJECT_ROOT/scripts/ci/health-check.sh" -t "$SERVICE"; then
            log_success "健康检查通过"
        else
            log_error "健康检查失败"
            return 1
        fi
    fi

    # 冒烟测试
    run_smoke_tests

    log_success "部署后验证完成"
}

# 冒烟测试
run_smoke_tests() {
    log_info "运行冒烟测试..."

    # 基础API测试
    local endpoints=(
        "http://localhost:9000/api/health"
        "http://localhost:8000/health"
        "http://localhost:8100/health"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null; then
            log_success "✓ $endpoint"
        else
            log_warning "✗ $endpoint (可能服务未启动)"
        fi
    done
}

# 生成部署报告
generate_deploy_report() {
    log_info "生成部署报告..."

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$PROJECT_ROOT/deploy-report-$timestamp.md"

    cat > "$report_file" << EOF
# 部署报告

## 基本信息
- **部署时间**: $(date)
- **环境**: $ENVIRONMENT
- **服务**: $SERVICE
- **策略**: $STRATEGY
- **分支**: $DEPLOY_BRANCH
- **提交**: $DEPLOY_COMMIT

## 部署参数
- 预览模式: $DRY_RUN
- 跳过测试: $SKIP_TESTS
- 跳过备份: $SKIP_BACKUP
- 自动批准: $AUTO_APPROVE

## 镜像信息
EOF

    if [[ "$SERVICE" == "all" || "$SERVICE" == "frontend" ]]; then
        echo "- Frontend: $FRONTEND_IMAGE" >> "$report_file"
    fi

    echo "" >> "$report_file"
    echo "## 服务状态" >> "$report_file"

    # 添加健康检查结果
    if command -v curl &> /dev/null; then
        echo "### 健康检查" >> "$report_file"
        for endpoint in "http://localhost:9000/api/health" "http://localhost:8000/health"; do
            if curl -f -s "$endpoint" > /dev/null 2>&1; then
                echo "- ✅ $endpoint" >> "$report_file"
            else
                echo "- ❌ $endpoint" >> "$report_file"
            fi
        done
    fi

    echo "" >> "$report_file"
    echo "## 备份信息" >> "$report_file"
    if [[ -n "$BACKUP_DIR" ]]; then
        echo "- 备份位置: $BACKUP_DIR" >> "$report_file"
    else
        echo "- 未创建备份" >> "$report_file"
    fi

    log_success "部署报告已生成: $report_file"
}

# 显示部署摘要
show_deploy_summary() {
    echo ""
    echo "================================================"
    echo "              部署摘要"
    echo "================================================"
    echo "环境: $ENVIRONMENT"
    echo "服务: $SERVICE"
    echo "策略: $STRATEGY"
    echo "分支: $DEPLOY_BRANCH"
    echo "提交: ${DEPLOY_COMMIT:0:8}"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "模式: 预览模式 (未实际执行)"
    fi
    echo "================================================"
}

# 确认部署
confirm_deployment() {
    if [[ "$AUTO_APPROVE" == "true" || "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    show_deploy_summary
    echo ""
    read -p "确认执行部署? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
}

# 主函数
main() {
    echo "================================================"
    echo "    SaaS Control Deck - 自动化部署系统"
    echo "================================================"

    parse_args "$@"
    validate_args

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "运行在预览模式"
    fi

    check_dependencies
    check_git_status
    confirm_deployment

    # 部署前步骤
    run_tests
    create_backup
    build_images

    # 执行部署
    case $STRATEGY in
        rolling)
            deploy_rolling
            ;;
        blue-green)
            deploy_blue_green
            ;;
        canary)
            deploy_canary
            ;;
    esac

    # 部署后步骤
    if [[ "$DRY_RUN" != "true" ]]; then
        post_deploy_validation
    fi

    generate_deploy_report
    show_deploy_summary

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        log_success "预览完成！使用 --dry-run=false 执行实际部署"
    else
        log_success "部署完成！"
    fi
    echo "================================================"
}

# 错误处理
trap 'log_error "部署过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"