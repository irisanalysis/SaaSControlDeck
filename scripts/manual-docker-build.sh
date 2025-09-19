#!/bin/bash

# ===========================================
# SaaS Control Deck - 手动Docker构建脚本
# ===========================================
# 用于本地构建和推送Docker镜像到DockerHub
# 当GitHub Actions失败时的备用方案

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
FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-frontend"
BACKEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-backend"
BUILD_PLATFORMS="linux/amd64,linux/arm64"
PUSH_IMAGES=false

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
  -u, --username USERNAME    DockerHub username (default: irisanalysis)
  -t, --tag TAG             Image tag (default: latest)
  -p, --push                Push images to DockerHub after building
  --platform PLATFORMS     Build platforms (default: linux/amd64,linux/arm64)
  --frontend-only          Build only frontend image
  --backend-only           Build only backend image
  -h, --help               Show this help message

Examples:
  $0 --push                                    # Build and push both images
  $0 --frontend-only --push                    # Build and push only frontend
  $0 -u myusername -t v1.0.0 --push          # Custom username and tag
  $0 --platform linux/amd64 --push           # Single platform build

EOF
}

# ===========================================
# 参数解析
# ===========================================
BUILD_FRONTEND=true
BUILD_BACKEND=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            DOCKERHUB_USERNAME="$2"
            FRONTEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-frontend"
            BACKEND_IMAGE="${DOCKERHUB_USERNAME}/saascontrol-backend"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_IMAGES=true
            shift
            ;;
        --platform)
            BUILD_PLATFORMS="$2"
            shift 2
            ;;
        --frontend-only)
            BUILD_BACKEND=false
            shift
            ;;
        --backend-only)
            BUILD_FRONTEND=false
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
# 环境检查
# ===========================================
check_requirements() {
    log_info "检查构建要求..."

    # 检查Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Buildx
    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker Buildx未安装，请启用Docker Buildx"
        exit 1
    fi

    # 检查多平台支持
    if [[ "$BUILD_PLATFORMS" == *","* ]]; then
        log_info "检查多平台构建支持..."
        if ! docker buildx ls | grep -q "docker-container"; then
            log_warning "创建多平台构建器..."
            docker buildx create --name multiplatform --use --driver docker-container
        fi
    fi

    # 如果需要推送，检查是否已登录
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        log_info "检查DockerHub登录状态..."
        if ! docker info | grep -q "Username: $DOCKERHUB_USERNAME"; then
            log_warning "未登录到DockerHub，请运行: docker login"
            echo -n "是否现在登录? (y/n): "
            read -r response
            if [[ "$response" == "y" || "$response" == "Y" ]]; then
                docker login
            else
                log_error "需要登录DockerHub才能推送镜像"
                exit 1
            fi
        fi
    fi

    log_success "环境检查通过"
}

# ===========================================
# 构建前端镜像
# ===========================================
build_frontend() {
    log_info "构建前端镜像..."

    local image_name="${FRONTEND_IMAGE}:${IMAGE_TAG}"
    local latest_tag="${FRONTEND_IMAGE}:latest"

    # 设置构建参数
    local build_args=(
        --platform "$BUILD_PLATFORMS"
        --build-arg DOCKER_BUILD=true
        --build-arg BUILDKIT_INLINE_CACHE=1
        --tag "$image_name"
    )

    # 如果标签不是latest，也添加latest标签
    if [[ "$IMAGE_TAG" != "latest" ]]; then
        build_args+=(--tag "$latest_tag")
    fi

    # 如果需要推送，添加push参数，否则只加载到本地
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        build_args+=(--push)
    else
        build_args+=(--load)
    fi

    log_info "构建命令: docker buildx build ${build_args[*]} -f frontend/Dockerfile ."

    if docker buildx build "${build_args[@]}" -f frontend/Dockerfile .; then
        log_success "前端镜像构建成功: $image_name"

        # 如果只是本地构建，显示镜像信息
        if [[ "$PUSH_IMAGES" == "false" ]]; then
            docker images | grep saascontrol-frontend | head -3
        fi
    else
        log_error "前端镜像构建失败"
        return 1
    fi
}

# ===========================================
# 构建后端镜像
# ===========================================
build_backend() {
    log_info "构建后端镜像..."

    local image_name="${BACKEND_IMAGE}:${IMAGE_TAG}"
    local latest_tag="${BACKEND_IMAGE}:latest"

    # 设置构建参数
    local build_args=(
        --platform "$BUILD_PLATFORMS"
        --build-arg BUILDKIT_INLINE_CACHE=1
        --tag "$image_name"
    )

    # 如果标签不是latest，也添加latest标签
    if [[ "$IMAGE_TAG" != "latest" ]]; then
        build_args+=(--tag "$latest_tag")
    fi

    # 如果需要推送，添加push参数，否则只加载到本地
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        build_args+=(--push)
    else
        build_args+=(--load)
    fi

    log_info "构建命令: docker buildx build ${build_args[*]} -f backend/backend-pro1/Dockerfile backend/backend-pro1"

    if docker buildx build "${build_args[@]}" -f backend/backend-pro1/Dockerfile backend/backend-pro1; then
        log_success "后端镜像构建成功: $image_name"

        # 如果只是本地构建，显示镜像信息
        if [[ "$PUSH_IMAGES" == "false" ]]; then
            docker images | grep saascontrol-backend | head -3
        fi
    else
        log_error "后端镜像构建失败"
        return 1
    fi
}

# ===========================================
# 验证构建的镜像
# ===========================================
verify_images() {
    log_info "验证构建的镜像..."

    if [[ "$BUILD_FRONTEND" == "true" ]]; then
        log_info "验证前端镜像..."
        if docker run --rm "${FRONTEND_IMAGE}:${IMAGE_TAG}" node --version; then
            log_success "前端镜像验证通过"
        else
            log_error "前端镜像验证失败"
            return 1
        fi
    fi

    if [[ "$BUILD_BACKEND" == "true" ]]; then
        log_info "验证后端镜像..."
        if docker run --rm "${BACKEND_IMAGE}:${IMAGE_TAG}" python --version; then
            log_success "后端镜像验证通过"
        else
            log_error "后端镜像验证失败"
            return 1
        fi
    fi
}

# ===========================================
# 显示构建结果
# ===========================================
show_results() {
    echo -e "\n${GREEN}===============================================${NC}"
    echo -e "${GREEN}           构建完成 🎉${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    echo -e "${BLUE}构建详情:${NC}"
    echo "  DockerHub用户名: $DOCKERHUB_USERNAME"
    echo "  镜像标签: $IMAGE_TAG"
    echo "  构建平台: $BUILD_PLATFORMS"
    echo "  推送到DockerHub: $([ "$PUSH_IMAGES" == "true" ] && echo "是" || echo "否")"
    echo ""

    if [[ "$BUILD_FRONTEND" == "true" ]]; then
        echo -e "${YELLOW}前端镜像:${NC}"
        echo "  🖼️  ${FRONTEND_IMAGE}:${IMAGE_TAG}"
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            echo "  🖼️  ${FRONTEND_IMAGE}:latest"
        fi
        echo ""
    fi

    if [[ "$BUILD_BACKEND" == "true" ]]; then
        echo -e "${YELLOW}后端镜像:${NC}"
        echo "  ⚙️  ${BACKEND_IMAGE}:${IMAGE_TAG}"
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            echo "  ⚙️  ${BACKEND_IMAGE}:latest"
        fi
        echo ""
    fi

    if [[ "$PUSH_IMAGES" == "true" ]]; then
        echo -e "${GREEN}DockerHub链接:${NC}"
        if [[ "$BUILD_FRONTEND" == "true" ]]; then
            echo "  🔗 https://hub.docker.com/r/${DOCKERHUB_USERNAME}/saascontrol-frontend"
        fi
        if [[ "$BUILD_BACKEND" == "true" ]]; then
            echo "  🔗 https://hub.docker.com/r/${DOCKERHUB_USERNAME}/saascontrol-backend"
        fi
        echo ""
        echo -e "${YELLOW}部署命令:${NC}"
        echo "  ./deploy-from-dockerhub.sh -u $DOCKERHUB_USERNAME -t $IMAGE_TAG"
    else
        echo -e "${YELLOW}推送命令 (如需推送):${NC}"
        if [[ "$BUILD_FRONTEND" == "true" ]]; then
            echo "  docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}"
        fi
        if [[ "$BUILD_BACKEND" == "true" ]]; then
            echo "  docker push ${BACKEND_IMAGE}:${IMAGE_TAG}"
        fi
        echo ""
        echo -e "${YELLOW}或重新运行构建脚本推送:${NC}"
        echo "  $0 --push"
    fi
}

# ===========================================
# 主执行流程
# ===========================================
main() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "     SaaS Control Deck - 手动Docker构建"
    echo "==============================================="
    echo -e "${NC}"
    echo "DockerHub用户名: $DOCKERHUB_USERNAME"
    echo "镜像标签: $IMAGE_TAG"
    echo "构建平台: $BUILD_PLATFORMS"
    echo "前端构建: $([ "$BUILD_FRONTEND" == "true" ] && echo "是" || echo "否")"
    echo "后端构建: $([ "$BUILD_BACKEND" == "true" ] && echo "是" || echo "否")"
    echo "推送镜像: $([ "$PUSH_IMAGES" == "true" ] && echo "是" || echo "否")"
    echo ""

    check_requirements

    local build_failed=false

    # 构建前端
    if [[ "$BUILD_FRONTEND" == "true" ]]; then
        if ! build_frontend; then
            build_failed=true
        fi
    fi

    # 构建后端
    if [[ "$BUILD_BACKEND" == "true" ]]; then
        if ! build_backend; then
            build_failed=true
        fi
    fi

    # 如果构建失败，退出
    if [[ "$build_failed" == "true" ]]; then
        log_error "有镜像构建失败，请检查错误信息"
        exit 1
    fi

    # 验证镜像（仅在本地构建时）
    if [[ "$PUSH_IMAGES" == "false" ]]; then
        verify_images
    fi

    show_results
}

# 执行主函数
main "$@"