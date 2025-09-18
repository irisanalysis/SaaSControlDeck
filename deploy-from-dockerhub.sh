#!/bin/bash

# ===========================================
# SaaS Control Deck - DockerHub一键部署脚本
# ===========================================
# 该脚本用于从DockerHub快速部署SaaS Control Deck全栈应用

set -e  # 遇到错误立即退出

# ===========================================
# 颜色定义
# ===========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===========================================
# 默认配置
# ===========================================
DOCKERHUB_USERNAME="irisanalysis"
IMAGE_TAG="latest"
ENV_FILE=".env.dockerhub"
COMPOSE_FILE="docker-compose.dockerhub.yml"

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
            echo "Usage: $0 [-u dockerhub_username] [-t image_tag] [-e env_file]"
            echo "  -u: DockerHub username (default: irisanalysis)"
            echo "  -t: Image tag (default: latest)"
            echo "  -e: Environment file (default: .env.dockerhub)"
            exit 0
            ;;
    esac
done

# ===========================================
# 环境检查
# ===========================================
check_requirements() {
    log_info "检查系统要求..."

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

    log_success "系统要求检查通过"
}

# ===========================================
# 环境变量配置
# ===========================================
setup_environment() {
    log_info "设置环境变量..."

    # 创建环境变量文件如果不存在
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境变量文件不存在，创建默认配置: $ENV_FILE"
        cat > "$ENV_FILE" << EOF
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
EOF
        log_warning "请编辑 $ENV_FILE 文件，填写正确的API密钥"
    fi

    # 导出环境变量
    export DOCKERHUB_USERNAME="$DOCKERHUB_USERNAME"
    export IMAGE_TAG="$IMAGE_TAG"

    log_success "环境变量配置完成"
}

# ===========================================
# 拉取镜像
# ===========================================
pull_images() {
    log_info "拉取Docker镜像..."

    local frontend_image="${DOCKERHUB_USERNAME}/saascontrol-frontend:${IMAGE_TAG}"
    local backend_image="${DOCKERHUB_USERNAME}/saascontrol-backend:${IMAGE_TAG}"

    log_info "拉取前端镜像: $frontend_image"
    if ! docker pull "$frontend_image"; then
        log_error "无法拉取前端镜像: $frontend_image"
        return 1
    fi

    log_info "拉取后端镜像: $backend_image"
    if ! docker pull "$backend_image"; then
        log_error "无法拉取后端镜像: $backend_image"
        return 1
    fi

    log_success "镜像拉取完成"
}

# ===========================================
# 部署服务
# ===========================================
deploy_services() {
    log_info "部署服务..."

    # 检查compose文件
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose文件不存在: $COMPOSE_FILE"
        exit 1
    fi

    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans 2>/dev/null || true

    # 启动服务
    log_info "启动新服务..."
    if ! docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d; then
        log_error "服务启动失败"
        return 1
    fi

    log_success "服务部署完成"
}

# ===========================================
# 显示状态
# ===========================================
show_status() {
    log_info "显示服务状态..."

    echo -e "\n${GREEN}=== 服务访问地址 ===${NC}"
    echo -e "${GREEN}前端应用:${NC}     http://localhost:9000"
    echo -e "${GREEN}API文档Pro1:${NC}  http://localhost:8000/docs"
    echo -e "${GREEN}API文档Pro2:${NC}  http://localhost:8100/docs"

    echo -e "\n${GREEN}=== 管理命令 ===${NC}"
    echo -e "${YELLOW}查看日志:${NC}     docker-compose -f $COMPOSE_FILE logs -f"
    echo -e "${YELLOW}停止服务:${NC}     docker-compose -f $COMPOSE_FILE down"
    echo -e "${YELLOW}重启服务:${NC}     docker-compose -f $COMPOSE_FILE restart"
}

# ===========================================
# 主执行流程
# ===========================================
main() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "    SaaS Control Deck - DockerHub一键部署"
    echo "=================================================="
    echo -e "${NC}"
    echo "DockerHub用户名: $DOCKERHUB_USERNAME"
    echo "镜像标签: $IMAGE_TAG"
    echo ""

    check_requirements
    setup_environment

    if pull_images && deploy_services; then
        show_status
        echo -e "\n${GREEN}🎉 部署完成！${NC}"
        echo -e "${YELLOW}请访问 http://localhost:9000 查看您的应用${NC}"
    else
        log_error "部署过程中发生错误"
        echo -e "\n${YELLOW}请检查镜像是否存在于DockerHub:${NC}"
        echo "  - https://hub.docker.com/r/$DOCKERHUB_USERNAME/saascontrol-frontend"
        echo "  - https://hub.docker.com/r/$DOCKERHUB_USERNAME/saascontrol-backend"
        exit 1
    fi
}

# 执行主函数
main "$@"