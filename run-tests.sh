#!/bin/bash

# 测试套件运行脚本
# 为数据源连接功能提供便捷的测试执行工具
# 支持不同类型的测试和环境配置
# RELEVANT FILES: TESTING_GUIDE.md, comprehensive-test-suite.yml, .env.test

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "🧪 数据源连接功能测试套件运行器"
    echo ""
    echo "用法: $0 [选项] [测试类型]"
    echo ""
    echo "测试类型:"
    echo "  unit           运行单元测试"
    echo "  integration    运行集成测试"
    echo "  e2e           运行端到端测试"
    echo "  performance   运行性能测试"
    echo "  all           运行所有测试"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --verbose  详细输出"
    echo "  -c, --coverage 生成覆盖率报告"
    echo "  -w, --watch    监视模式"
    echo "  --setup        仅设置测试环境"
    echo "  --cleanup      清理测试环境"
    echo ""
    echo "示例:"
    echo "  $0 unit -c              # 运行单元测试并生成覆盖率"
    echo "  $0 e2e -v               # 运行E2E测试，详细输出"
    echo "  $0 all                  # 运行所有测试"
    echo "  $0 --setup              # 仅设置环境"
}

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查依赖
check_dependencies() {
    log_info "检查环境依赖..."

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装。请安装 Node.js 18+."
        exit 1
    fi

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 未安装。请安装 Python 3.11+."
        exit 1
    fi

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker 未安装。某些集成测试可能会失败。"
    fi

    log_success "依赖检查完成"
}

# 设置测试环境
setup_environment() {
    log_info "设置测试环境..."

    # 复制测试环境配置
    if [ ! -f .env.test ]; then
        log_error ".env.test 文件不存在。请先创建测试环境配置。"
        exit 1
    fi

    # 启动测试数据库
    if command -v docker &> /dev/null; then
        log_info "启动测试数据库..."
        docker-compose up -d postgres redis || log_warning "数据库启动失败，某些测试可能失败"

        # 等待数据库就绪
        log_info "等待数据库就绪..."
        sleep 10

        # 验证数据库连接
        if PGPASSWORD=postgres123 psql -h localhost -p 5432 -U postgres -d test_db -c "SELECT 1;" &> /dev/null; then
            log_success "数据库连接正常"
        else
            log_warning "数据库连接失败"
        fi
    fi

    # 安装前端依赖
    if [ ! -d "frontend/node_modules" ]; then
        log_info "安装前端依赖..."
        cd frontend && npm install && cd ..
    fi

    # 安装后端依赖
    if [ ! -d "backend/backend-pro1/.venv" ]; then
        log_info "安装后端依赖..."
        cd backend/backend-pro1 && pip install -r requirements.txt && cd ../..
    fi

    # 安装Playwright浏览器
    if [ ! -d "frontend/node_modules/.cache/playwright" ]; then
        log_info "安装Playwright浏览器..."
        cd frontend && npx playwright install && cd ..
    fi

    log_success "测试环境设置完成"
}

# 清理测试环境
cleanup_environment() {
    log_info "清理测试环境..."

    # 停止数据库服务
    if command -v docker &> /dev/null; then
        docker-compose down -v 2>/dev/null || true
    fi

    # 清理测试临时文件
    rm -rf frontend/test-results/ 2>/dev/null || true
    rm -rf frontend/playwright-report/ 2>/dev/null || true
    rm -rf backend/backend-pro1/htmlcov/ 2>/dev/null || true
    rm -rf backend/backend-pro1/.coverage 2>/dev/null || true

    log_success "环境清理完成"
}

# 运行前端单元测试
run_frontend_unit_tests() {
    log_info "运行前端单元测试..."
    cd frontend

    local cmd="npm run test:unit -- --run"

    if [ "$COVERAGE" = "true" ]; then
        cmd="npm run test:coverage"
    fi

    if [ "$VERBOSE" = "true" ]; then
        cmd="$cmd --reporter=verbose"
    fi

    if [ "$WATCH" = "true" ]; then
        cmd="npm run test:watch"
    fi

    eval $cmd
    cd ..
    log_success "前端单元测试完成"
}

# 运行后端单元测试
run_backend_unit_tests() {
    log_info "运行后端单元测试..."
    cd backend/backend-pro1

    local cmd="pytest tests/unit/"

    if [ "$COVERAGE" = "true" ]; then
        cmd="pytest tests/unit/ --cov=app --cov-report=html --cov-report=term"
    fi

    if [ "$VERBOSE" = "true" ]; then
        cmd="$cmd -v"
    fi

    eval $cmd
    cd ../..
    log_success "后端单元测试完成"
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."

    # 确保数据库运行
    setup_environment

    # 前端集成测试
    log_info "运行前端集成测试..."
    cd frontend
    npm run test:integration -- --run
    cd ..

    # 后端集成测试
    log_info "运行后端集成测试..."
    cd backend/backend-pro1

    local cmd="pytest tests/integration/"

    if [ "$COVERAGE" = "true" ]; then
        cmd="pytest tests/integration/ --cov=app --cov-report=html --cov-report=term"
    fi

    if [ "$VERBOSE" = "true" ]; then
        cmd="$cmd -v"
    fi

    eval $cmd
    cd ../..

    log_success "集成测试完成"
}

# 运行端到端测试
run_e2e_tests() {
    log_info "运行端到端测试..."

    # 设置环境
    setup_environment

    # 启动后端服务
    log_info "启动后端服务..."
    cd backend/backend-pro1
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres123@localhost:5432/test_db"
    export REDIS_URL="redis://localhost:6379/15"
    export SECRET_KEY="test-secret-key-for-ci-only-32-chars"
    export ENVIRONMENT="test"

    uvicorn data_service.app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ../..

    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 15

    # 验证后端健康状态
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi

    # 运行E2E测试
    cd frontend

    local cmd="npm run test:e2e"

    if [ "$VERBOSE" = "true" ]; then
        cmd="npm run test:e2e:ui"
    fi

    eval $cmd

    # 清理
    cd ..
    kill $BACKEND_PID 2>/dev/null || true

    log_success "端到端测试完成"
}

# 运行性能测试
run_performance_tests() {
    log_info "运行性能测试..."

    # 设置环境
    setup_environment

    # 启动后端服务进行性能测试
    log_info "启动后端服务进行性能测试..."
    cd backend/backend-pro1
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres123@localhost:5432/test_db"
    export REDIS_URL="redis://localhost:6379/15"
    export SECRET_KEY="test-secret-key-for-ci-only-32-chars"
    export ENVIRONMENT="test"

    uvicorn data_service.app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ../..

    sleep 15

    # 安装Apache Bench
    if ! command -v ab &> /dev/null; then
        log_info "安装Apache Bench..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install apache2 2>/dev/null || log_warning "请手动安装Apache Bench"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            sudo apt-get update && sudo apt-get install -y apache2-utils 2>/dev/null || log_warning "请手动安装Apache Bench"
        fi
    fi

    # 运行性能测试
    log_info "执行性能基准测试..."

    # 健康检查性能
    if command -v ab &> /dev/null; then
        ab -n 1000 -c 10 http://localhost:8000/health > health_performance.txt || true
        log_info "健康检查性能测试完成"

        # 显示结果
        if [ -f health_performance.txt ]; then
            grep "Requests per second" health_performance.txt || echo "性能数据收集完成"
        fi
    else
        log_warning "Apache Bench 未安装，跳过性能测试"
    fi

    # 清理
    kill $BACKEND_PID 2>/dev/null || true

    log_success "性能测试完成"
}

# 运行所有测试
run_all_tests() {
    log_info "运行完整测试套件..."

    run_frontend_unit_tests
    run_backend_unit_tests
    run_integration_tests
    run_e2e_tests
    run_performance_tests

    log_success "所有测试完成！"
}

# 解析命令行参数
COVERAGE=false
VERBOSE=false
WATCH=false
SETUP_ONLY=false
CLEANUP_ONLY=false
TEST_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -w|--watch)
            WATCH=true
            shift
            ;;
        --setup)
            SETUP_ONLY=true
            shift
            ;;
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        unit|integration|e2e|performance|all)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主执行逻辑
main() {
    log_info "🧪 数据源连接功能测试套件启动"

    # 仅清理
    if [ "$CLEANUP_ONLY" = "true" ]; then
        cleanup_environment
        exit 0
    fi

    # 检查依赖
    check_dependencies

    # 仅设置环境
    if [ "$SETUP_ONLY" = "true" ]; then
        setup_environment
        exit 0
    fi

    # 设置测试环境
    setup_environment

    # 根据测试类型执行
    case $TEST_TYPE in
        unit)
            run_frontend_unit_tests
            run_backend_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        performance)
            run_performance_tests
            ;;
        all|"")
            run_all_tests
            ;;
        *)
            log_error "无效的测试类型: $TEST_TYPE"
            show_help
            exit 1
            ;;
    esac

    log_success "🎉 测试套件执行完成！"
}

# 错误处理
trap 'log_error "测试执行过程中发生错误"; cleanup_environment; exit 1' ERR

# 执行主函数
main "$@"