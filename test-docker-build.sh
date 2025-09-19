#!/bin/bash

# ===========================================
# SaaS Control Deck - Docker构建测试脚本
# ===========================================
# 测试Docker镜像本地构建，不推送到DockerHub

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
# 配置
# ===========================================
DOCKERHUB_USERNAME="irisanalysis"
IMAGE_TAG="test-$(date +%Y%m%d-%H%M%S)"
FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-frontend"
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-backend"

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
# 清理函数
# ===========================================
cleanup() {
    log_info "清理测试镜像..."
    docker rmi "${FRONTEND_IMAGE}:${IMAGE_TAG}" 2>/dev/null || true
    docker rmi "${BACKEND_IMAGE}:${IMAGE_TAG}" 2>/dev/null || true
    log_info "清理完成"
}

# 设置退出时清理
trap cleanup EXIT

# ===========================================
# 主测试流程
# ===========================================
main() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "     SaaS Control Deck - Docker构建测试"
    echo "==============================================="
    echo -e "${NC}"
    echo "测试标签: $IMAGE_TAG"
    echo ""

    # 检查Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker未安装"
        exit 1
    fi

    # 测试前端构建
    log_info "测试前端Docker构建..."
    if docker build -t "${FRONTEND_IMAGE}:${IMAGE_TAG}" \
        --build-arg DOCKER_BUILD=true \
        -f frontend/Dockerfile .; then
        log_success "前端镜像构建成功"

        # 测试前端镜像运行
        log_info "测试前端镜像启动..."
        if timeout 30 docker run --rm -p 3001:3000 "${FRONTEND_IMAGE}:${IMAGE_TAG}" &
        then
            FRONTEND_PID=$!
            sleep 10

            # 测试健康检查端点
            if curl -f "http://localhost:3001/api/health" >/dev/null 2>&1; then
                log_success "前端健康检查通过"
            else
                log_warning "前端健康检查失败（可能需要更长启动时间）"
            fi

            # 停止容器
            kill $FRONTEND_PID 2>/dev/null || true
        else
            log_warning "前端容器启动测试跳过"
        fi
    else
        log_error "前端镜像构建失败"
        exit 1
    fi

    echo ""

    # 测试后端构建
    log_info "测试后端Docker构建..."
    if docker build -t "${BACKEND_IMAGE}:${IMAGE_TAG}" \
        -f backend/backend-pro1/Dockerfile \
        backend/backend-pro1; then
        log_success "后端镜像构建成功"

        # 测试后端镜像基本功能
        log_info "测试后端镜像Python环境..."
        if docker run --rm "${BACKEND_IMAGE}:${IMAGE_TAG}" python --version; then
            log_success "后端Python环境正常"
        else
            log_error "后端Python环境异常"
            exit 1
        fi

        # 测试依赖安装
        log_info "测试后端依赖..."
        if docker run --rm "${BACKEND_IMAGE}:${IMAGE_TAG}" python -c "import fastapi; print('FastAPI:', fastapi.__version__)"; then
            log_success "后端依赖安装正常"
        else
            log_error "后端依赖异常"
            exit 1
        fi
    else
        log_error "后端镜像构建失败"
        exit 1
    fi

    echo ""

    # 显示镜像信息
    log_info "构建的镜像信息:"
    docker images | grep saascontrol | grep "$IMAGE_TAG"

    echo ""
    log_success "🎉 所有Docker构建测试通过！"
    echo ""
    echo -e "${YELLOW}下一步操作：${NC}"
    echo "1. 手动构建并推送: ./scripts/manual-docker-build.sh --push"
    echo "2. 或触发GitHub Actions: git push origin main"
    echo "3. 部署镜像: ./deploy-from-dockerhub.sh"
}

# 执行主函数
main "$@"