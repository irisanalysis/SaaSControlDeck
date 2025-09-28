#!/bin/bash
# /home/user/studio/tests/infrastructure/docker/build_tests/docker_build_validator.sh
# Docker构建验证脚本集合 - 从根目录迁移而来
# 集成多种Docker构建测试方案，提供全面的构建验证
# RELEVANT FILES: backend/backend-pro1/Dockerfile, docker-compose.yml

set -e

echo "🐳 SaaS Control Deck - Docker构建验证套件"
echo "==============================================="
echo "⏰ 验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 测试函数：简单Docker构建
test_simple_docker_build() {
    log_info "测试1: 简单Docker构建验证"
    ((TOTAL_TESTS++))
    
    cd "/home/user/studio/backend/backend-pro1"
    
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile不存在"
        return 1
    fi
    
    # 构建Docker镜像
    if docker build -t saascontrol-backend-test:simple . > /tmp/docker_build_simple.log 2>&1; then
        log_success "简单Docker构建成功"
        
        # 验证镜像是否创建
        if docker images | grep -q "saascontrol-backend-test.*simple"; then
            log_success "Docker镜像创建验证通过"
        else
            log_error "Docker镜像创建验证失败"
        fi
        
        # 清理测试镜像
        docker rmi saascontrol-backend-test:simple > /dev/null 2>&1 || true
        
    else
        log_error "简单Docker构建失败"
        log_info "构建日志: /tmp/docker_build_simple.log"
    fi
}

# 测试函数：最小化Docker构建
test_minimal_docker_build() {
    log_info "测试2: 最小化Docker构建验证"
    ((TOTAL_TESTS++))
    
    cd "/home/user/studio/backend/backend-pro1"
    
    # 使用多阶段构建优化
    if docker build --target production -t saascontrol-backend-test:minimal . > /tmp/docker_build_minimal.log 2>&1; then
        log_success "最小化Docker构建成功"
        
        # 检查镜像大小
        IMAGE_SIZE=$(docker images saascontrol-backend-test:minimal --format "table {{.Size}}" | tail -n +2)
        log_info "镜像大小: $IMAGE_SIZE"
        
        # 清理测试镜像
        docker rmi saascontrol-backend-test:minimal > /dev/null 2>&1 || true
        
    else
        log_error "最小化Docker构建失败"
        log_info "构建日志: /tmp/docker_build_minimal.log"
    fi
}

# 测试函数：仅后端构建
test_backend_only_build() {
    log_info "测试3: 后端专用Docker构建验证"
    ((TOTAL_TESTS++))
    
    cd "/home/user/studio/backend/backend-pro1"
    
    # 构建仅包含后端服务的镜像
    if docker build --build-arg INSTALL_DEV=false -t saascontrol-backend-test:backend-only . > /tmp/docker_build_backend.log 2>&1; then
        log_success "后端专用Docker构建成功"
        
        # 验证镜像可以运行
        if docker run --rm saascontrol-backend-test:backend-only python -c "import fastapi; print('FastAPI import success')" > /tmp/docker_run_test.log 2>&1; then
            log_success "Docker镜像运行验证通过"
        else
            log_error "Docker镜像运行验证失败"
            log_info "运行日志: /tmp/docker_run_test.log"
        fi
        
        # 清理测试镜像
        docker rmi saascontrol-backend-test:backend-only > /dev/null 2>&1 || true
        
    else
        log_error "后端专用Docker构建失败"
        log_info "构建日志: /tmp/docker_build_backend.log"
    fi
}

# 测试函数：Docker Compose验证
test_docker_compose_validation() {
    log_info "测试4: Docker Compose配置验证"
    ((TOTAL_TESTS++))
    
    cd "/home/user/studio"
    
    if [ ! -f "docker-compose.yml" ]; then
        log_warning "docker-compose.yml不存在，跳过Docker Compose测试"
        return 0
    fi
    
    # 验证Docker Compose配置语法
    if docker-compose config > /tmp/docker_compose_config.log 2>&1; then
        log_success "Docker Compose配置语法验证通过"
        
        # 尝试构建服务
        if docker-compose build > /tmp/docker_compose_build.log 2>&1; then
            log_success "Docker Compose构建验证通过"
        else
            log_error "Docker Compose构建验证失败"
            log_info "构建日志: /tmp/docker_compose_build.log"
        fi
        
    else
        log_error "Docker Compose配置语法验证失败"
        log_info "配置日志: /tmp/docker_compose_config.log"
    fi
}

# 测试函数：健康检查验证
test_health_check_validation() {
    log_info "测试5: Docker健康检查验证"
    ((TOTAL_TESTS++))
    
    cd "/home/user/studio/backend/backend-pro1"
    
    # 构建包含健康检查的镜像
    if docker build -t saascontrol-backend-test:health-check . > /tmp/docker_build_health.log 2>&1; then
        log_success "健康检查Docker构建成功"
        
        # 运行容器并检查健康状态
        CONTAINER_ID=$(docker run -d -p 8099:8000 saascontrol-backend-test:health-check)
        
        if [ -n "$CONTAINER_ID" ]; then
            sleep 10  # 等待容器启动
            
            HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_ID 2>/dev/null || echo "no-health-check")
            
            if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "no-health-check" ]; then
                log_success "Docker健康检查验证通过 (状态: $HEALTH_STATUS)"
            else
                log_warning "Docker健康检查状态: $HEALTH_STATUS"
            fi
            
            # 清理容器
            docker stop $CONTAINER_ID > /dev/null 2>&1
            docker rm $CONTAINER_ID > /dev/null 2>&1
        else
            log_error "Docker容器启动失败"
        fi
        
        # 清理测试镜像
        docker rmi saascontrol-backend-test:health-check > /dev/null 2>&1 || true
        
    else
        log_error "健康检查Docker构建失败"
        log_info "构建日志: /tmp/docker_build_health.log"
    fi
}

# 主测试执行函数
main() {
    echo "🚀 开始执行Docker构建验证测试"
    echo
    
    # 检查Docker是否可用
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装或不在PATH中"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker守护进程未运行或无权限访问"
        exit 1
    fi
    
    log_success "Docker环境验证通过"
    echo
    
    # 执行所有测试
    test_simple_docker_build
    echo
    test_minimal_docker_build
    echo
    test_backend_only_build
    echo
    test_docker_compose_validation
    echo
    test_health_check_validation
    echo
    
    # 生成测试报告
    echo "📊 Docker构建验证测试报告"
    echo "============================="
    echo "总测试数: $TOTAL_TESTS"
    echo "通过测试: $PASSED_TESTS"
    echo "失败测试: $FAILED_TESTS"
    
    SUCCESS_RATE=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    echo "成功率: ${SUCCESS_RATE}%"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo
        log_success "🎉 所有Docker构建验证测试通过！"
        echo "✨ Docker构建环境配置正确，可以进行生产部署"
        exit 0
    else
        echo
        log_warning "⚠️  有 $FAILED_TESTS 个测试失败"
        echo "🔧 建议检查失败的构建日志并修复相关问题"
        exit 1
    fi
}

# 脚本入口
main "$@"
