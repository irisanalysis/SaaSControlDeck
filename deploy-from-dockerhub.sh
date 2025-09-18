#!/bin/bash

# ===========================================
# SaaS Control Deck - DockerHub一键部署脚本
# ===========================================
# 该脚本用于从DockerHub快速部署SaaS Control Deck全栈应用
#
# 使用方法：
# ./deploy-from-dockerhub.sh -u your_dockerhub_username [-t tag] [-e env_file]
#
# 参数说明：
# -u: DockerHub用户名（必需）
# -t: 镜像标签（可选，默认：latest）
# -e: 环境变量文件（可选，默认：.env.dockerhub）
# -h: 显示帮助信息

set -e  # 遇到错误立即退出

# ===========================================
# 颜色定义
# ===========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===========================================
# 默认配置
# ===========================================
DOCKERHUB_USERNAME=""
IMAGE_TAG="latest"
ENV_FILE=".env.dockerhub"
COMPOSE_FILE="docker-compose.dockerhub.yml"
PROJECT_NAME="saascontrol"

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# ===========================================
# 帮助信息
# ===========================================
show_help() {
    cat << EOF
${CYAN}SaaS Control Deck - DockerHub一键部署脚本${NC}

使用方法:
    $0 -u <dockerhub_username> [选项]

必需参数:
    -u <username>     DockerHub用户名

可选参数:
    -t <tag>          镜像标签 (默认: latest)
    -e <env_file>     环境变量文件 (默认: .env.dockerhub)
    -h                显示此帮助信息

示例:
    $0 -u myusername
    $0 -u myusername -t v1.2.3
    $0 -u myusername -t staging -e .env.staging

镜像要求:
    需要在DockerHub上存在以下镜像:
    - <username>/saascontrol-frontend:<tag>
    - <username>/saascontrol-backend:<tag>

环境变量文件格式:
    GOOGLE_GENAI_API_KEY=your_api_key
    OPENAI_API_KEY=your_openai_key
    SECRET_KEY=your_secret_key
    DATABASE_URL=your_database_url
    SECONDARY_DATABASE_URL=your_secondary_database_url
    SERVER_HOST=0.0.0.0

EOF
}

# ===========================================
# 参数解析
# ===========================================
while getopts "u:t:e:h" opt; do
    case $opt in
        u)
            DOCKERHUB_USERNAME="$OPTARG"
            ;;
        t)
            IMAGE_TAG="$OPTARG"
            ;;
        e)
            ENV_FILE="$OPTARG"
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            log_error "无效选项: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# ===========================================
# 参数验证
# ===========================================
if [ -z "$DOCKERHUB_USERNAME" ]; then
    log_error "DockerHub用户名是必需的，请使用 -u 参数指定"
    show_help
    exit 1
fi

# ===========================================
# 环境检查
# ===========================================
check_requirements() {
    log_step "检查系统要求..."

    # 检查Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Docker服务状态
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi

    # 检查docker-compose配置文件
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose配置文件不存在: $COMPOSE_FILE"
        exit 1
    fi

    log_success "系统要求检查通过"
}

# ===========================================
# 环境变量配置
# ===========================================
setup_environment() {
    log_step "设置环境变量..."

    # 创建环境变量文件如果不存在
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境变量文件不存在，创建默认配置: $ENV_FILE"
        cat > "$ENV_FILE" << EOF
# ===========================================
# SaaS Control Deck - DockerHub部署环境变量
# ===========================================

# DockerHub配置
DOCKERHUB_USERNAME=$DOCKERHUB_USERNAME
IMAGE_TAG=$IMAGE_TAG

# 服务器配置
SERVER_HOST=0.0.0.0

# 数据库配置（请根据实际情况修改）
DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1
SECONDARY_DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2

# API密钥（请填写您的实际密钥）
GOOGLE_GENAI_API_KEY=your_google_genai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your-super-secret-key-32-chars-minimum

# 可选配置
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123456
EOF
        log_warning "请编辑 $ENV_FILE 文件，填写正确的API密钥和数据库连接信息"
        log_info "按任意键继续，或按Ctrl+C退出..."
        read -n 1 -s
    fi

    # 导出环境变量
    export DOCKERHUB_USERNAME="$DOCKERHUB_USERNAME"
    export IMAGE_TAG="$IMAGE_TAG"

    log_success "环境变量配置完成"
}

# ===========================================
# 镜像检查和拉取
# ===========================================
pull_images() {
    log_step "检查并拉取Docker镜像..."

    local frontend_image="${DOCKERHUB_USERNAME}/saascontrol-frontend:${IMAGE_TAG}"
    local backend_image="${DOCKERHUB_USERNAME}/saascontrol-backend:${IMAGE_TAG}"

    log_info "拉取前端镜像: $frontend_image"
    if ! docker pull "$frontend_image"; then
        log_error "无法拉取前端镜像: $frontend_image"
        log_error "请确保镜像存在于DockerHub上"
        exit 1
    fi

    log_info "拉取后端镜像: $backend_image"
    if ! docker pull "$backend_image"; then
        log_error "无法拉取后端镜像: $backend_image"
        log_error "请确保镜像存在于DockerHub上"
        exit 1
    fi

    log_success "所有镜像拉取完成"
}

# ===========================================
# 服务部署
# ===========================================
deploy_services() {
    log_step "部署服务..."

    # 停止现有服务（如果存在）
    log_info "停止现有服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" down --remove-orphans 2>/dev/null || true

    # 启动服务
    log_info "启动新服务..."
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d; then
        log_error "服务启动失败"
        exit 1
    fi

    log_success "服务部署完成"
}

# ===========================================
# 健康检查
# ===========================================
wait_for_services() {
    log_step "等待服务启动..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "健康检查 ($attempt/$max_attempts)..."

        # 检查前端服务
        if curl -f -s http://localhost:9000/api/health >/dev/null 2>&1; then
            log_success "前端服务健康检查通过"
            frontend_ready=true
        else
            frontend_ready=false
        fi

        # 检查后端服务Pro1
        if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
            log_success "后端Pro1服务健康检查通过"
            backend1_ready=true
        else
            backend1_ready=false
        fi

        # 检查后端服务Pro2
        if curl -f -s http://localhost:8100/health >/dev/null 2>&1; then
            log_success "后端Pro2服务健康检查通过"
            backend2_ready=true
        else
            backend2_ready=false
        fi

        if [ "$frontend_ready" = true ] && [ "$backend1_ready" = true ] && [ "$backend2_ready" = true ]; then
            log_success "所有服务健康检查通过！"
            return 0
        fi

        log_info "等待服务启动... (${attempt}s)"
        sleep 2
        attempt=$((attempt + 1))
    done

    log_warning "部分服务可能尚未完全启动，请检查服务状态"
}

# ===========================================
# 服务状态显示
# ===========================================
show_status() {
    log_step "显示服务状态..."

    echo -e "\n${CYAN}=== 容器状态 ===${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT_NAME" ps

    echo -e "\n${CYAN}=== 服务访问地址 ===${NC}"
    echo -e "${GREEN}前端应用:${NC}     http://localhost:9000"
    echo -e "${GREEN}API文档Pro1:${NC}  http://localhost:8000/docs"
    echo -e "${GREEN}API文档Pro2:${NC}  http://localhost:8100/docs"
    echo -e "${GREEN}Redis管理:${NC}    redis://localhost:6379"
    echo -e "${GREEN}MinIO管理:${NC}    http://localhost:9002"

    echo -e "\n${CYAN}=== 管理命令 ===${NC}"
    echo -e "${YELLOW}查看日志:${NC}     docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME logs -f"
    echo -e "${YELLOW}停止服务:${NC}     docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME down"
    echo -e "${YELLOW}重启服务:${NC}     docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME restart"
    echo -e "${YELLOW}查看状态:${NC}     docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME ps"
}

# ===========================================
# 清理函数
# ===========================================
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "部署过程中发生错误"
        log_info "查看详细日志: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE -p $PROJECT_NAME logs"
    fi
}

trap cleanup EXIT

# ===========================================
# 主执行流程
# ===========================================
main() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "    SaaS Control Deck - DockerHub一键部署"
    echo "=================================================="
    echo -e "${NC}"
    echo "DockerHub用户名: $DOCKERHUB_USERNAME"
    echo "镜像标签: $IMAGE_TAG"
    echo "环境变量文件: $ENV_FILE"
    echo ""

    check_requirements
    setup_environment
    pull_images
    deploy_services
    wait_for_services
    show_status

    echo -e "\n${GREEN}🎉 部署完成！${NC}"
    echo -e "${YELLOW}请访问 http://localhost:9000 查看您的应用${NC}"
}

# 执行主函数
main "$@"