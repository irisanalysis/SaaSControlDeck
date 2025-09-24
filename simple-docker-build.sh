#!/bin/bash

# ===========================================
# 简化版Docker构建脚本 - 解决Buildx权限问题
# ===========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${BLUE}"
echo "==============================================="
echo "    简化版Docker构建 - 传统模式"
echo "==============================================="
echo -e "${NC}"

# 检查Docker登录
if ! docker info | grep -q "irisanalysis"; then
    log_info "登录DockerHub..."
    docker login
fi

# 构建前端镜像
log_info "构建前端镜像 (传统模式)..."
if docker build -t irisanalysis/saascontrol-frontend:latest -f frontend/Dockerfile .; then
    log_success "前端镜像构建成功"

    log_info "推送前端镜像..."
    if docker push irisanalysis/saascontrol-frontend:latest; then
        log_success "前端镜像推送成功"
    else
        log_error "前端镜像推送失败"
        exit 1
    fi
else
    log_error "前端镜像构建失败"
    exit 1
fi

# 构建后端镜像
log_info "构建后端镜像 (传统模式)..."
if docker build -t irisanalysis/saascontrol-backend:latest -f backend/backend-pro1/Dockerfile backend/backend-pro1; then
    log_success "后端镜像构建成功"

    log_info "推送后端镜像..."
    if docker push irisanalysis/saascontrol-backend:latest; then
        log_success "后端镜像推送成功"
    else
        log_error "后端镜像推送失败"
        exit 1
    fi
else
    log_error "后端镜像构建失败"
    exit 1
fi

echo -e "\n${GREEN}🎉 所有镜像构建并推送成功！${NC}"
echo -e "\n${YELLOW}DockerHub链接：${NC}"
echo "🔗 https://hub.docker.com/r/irisanalysis/saascontrol-frontend"
echo "🔗 https://hub.docker.com/r/irisanalysis/saascontrol-backend"

echo -e "\n${YELLOW}部署命令：${NC}"
echo "./deploy-from-dockerhub.sh -u irisanalysis -t latest"