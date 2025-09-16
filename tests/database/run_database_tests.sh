#!/bin/bash

# ===========================================
# SaaS Control Deck 数据库测试执行脚本
# ===========================================
# 用途: 执行完整的数据库测试套件
# 环境: 支持所有6个数据库环境
# ===========================================

set -e  # 遇到错误时停止执行

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
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

log_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
SaaS Control Deck 数据库测试执行脚本

用法:
    $0 [选项] [测试模块...]

选项:
    -e, --env ENV           指定测试环境 (dev_pro1, dev_pro2, stage_pro1, stage_pro2, prod_pro1, prod_pro2)
    -a, --all-envs          测试所有环境
    -f, --fast              快速测试模式 (跳过性能和慢速测试)
    -v, --verbose           详细输出模式
    -p, --performance       仅运行性能测试
    -c, --coverage          生成测试覆盖率报告
    -r, --report            生成详细测试报告
    -h, --help              显示此帮助信息

测试模块:
    connections             数据库连接测试
    permissions             用户权限测试
    schema                  Schema完整性测试
    constraints             约束和索引测试
    crud                    CRUD操作测试
    performance             性能测试
    concurrent              并发操作测试
    firebase                Firebase Studio集成测试

示例:
    $0 -e dev_pro1                    # 测试开发环境pro1
    $0 -a -f                          # 快速测试所有环境
    $0 -e stage_pro1 connections crud # 测试特定模块
    $0 -p                             # 仅运行性能测试
    $0 -r -c                          # 生成报告和覆盖率

EOF
}

# 检查依赖
check_dependencies() {
    log_section "检查依赖"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        log_error "pytest 未安装"
        log_info "请运行: pip install pytest pytest-asyncio pytest-cov"
        exit 1
    fi
    
    # 检查asyncpg
    if ! python3 -c "import asyncpg" &> /dev/null; then
        log_error "asyncpg 未安装"
        log_info "请运行: pip install asyncpg"
        exit 1
    fi
    
    log_success "所有依赖检查通过"
}

# 检查数据库连接
check_database_connectivity() {
    local env_name=$1
    log_info "检查 $env_name 数据库连接..."
    
    # 从环境文件读取配置
    local env_file="$PROJECT_ROOT/scripts/database/database-environments.env"
    if [[ ! -f "$env_file" ]]; then
        log_warning "环境配置文件不存在: $env_file"
        return 1
    fi
    
    # 设置环境变量
    export TEST_DB_ENVIRONMENT=$env_name
    
    # 使用Python快速测试连接
    local connection_test=$(python3 -c "
import asyncio
import asyncpg
import os
import sys

env_configs = {
    'dev_pro1': {'user': 'saasctl_dev_pro1_user', 'password': 'dev_pro1_secure_2025!', 'db': 'saascontrol_dev_pro1'},
    'dev_pro2': {'user': 'saasctl_dev_pro2_user', 'password': 'dev_pro2_secure_2025!', 'db': 'saascontrol_dev_pro2'},
    'stage_pro1': {'user': 'saasctl_stage_pro1_user', 'password': 'stage_pro1_secure_2025!', 'db': 'saascontrol_stage_pro1'},
    'stage_pro2': {'user': 'saasctl_stage_pro2_user', 'password': 'stage_pro2_secure_2025!', 'db': 'saascontrol_stage_pro2'},
    'prod_pro1': {'user': 'saasctl_prod_pro1_user', 'password': 'prod_pro1_ULTRA_secure_2025#\$%', 'db': 'saascontrol_prod_pro1'},
    'prod_pro2': {'user': 'saasctl_prod_pro2_user', 'password': 'prod_pro2_ULTRA_secure_2025#\$%', 'db': 'saascontrol_prod_pro2'}
}

async def test_connection():
    env = '$env_name'
    if env not in env_configs:
        print('FAIL: Unknown environment')
        return
    
    config = env_configs[env]
    conn_str = f\"postgresql://{config['user']}:{config['password']}@47.79.87.199:5432/{config['db']}\"
    
    try:
        conn = await asyncpg.connect(conn_str)
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print('OK' if result == 1 else 'FAIL')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test_connection())
")
    
    if [[ "$connection_test" == "OK" ]]; then
        log_success "$env_name 数据库连接正常"
        return 0
    else
        log_error "$env_name 数据库连接失败: $connection_test"
        return 1
    fi
}

# 运行测试套件
run_test_suite() {
    local env_name=$1
    local test_modules=("${@:2}")
    
    log_section "运行测试套件: $env_name"
    
    # 设置环境变量
    export TEST_DB_ENVIRONMENT=$env_name
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 构建pytest命令
    local pytest_cmd="python3 -m pytest"
    local test_args=()
    
    # 添加基本参数
    test_args+=("-v")
    test_args+=("--tb=short")
    test_args+=("--durations=10")
    
    # 根据选项添加参数
    if [[ "$VERBOSE" == "true" ]]; then
        test_args+=("-s")
    fi
    
    if [[ "$FAST_MODE" == "true" ]]; then
        test_args+=("-m" "not slow and not performance")
    fi
    
    if [[ "$PERFORMANCE_ONLY" == "true" ]]; then
        test_args+=("-m" "performance")
    fi
    
    if [[ "$GENERATE_COVERAGE" == "true" ]]; then
        test_args+=("--cov=$TEST_DIR")
        test_args+=("--cov-report=html:$TEST_DIR/coverage_html")
        test_args+=("--cov-report=term")
    fi
    
    # 添加测试文件
    if [[ ${#test_modules[@]} -eq 0 ]]; then
        # 运行所有测试
        test_args+=("$TEST_DIR")
    else
        # 运行指定模块
        for module in "${test_modules[@]}"; do
            case $module in
                "connections")
                    test_args+=("$TEST_DIR/test_database_connections.py")
                    test_args+=("$TEST_DIR/test_user_permissions.py")
                    ;;
                "permissions")
                    test_args+=("$TEST_DIR/test_user_permissions.py")
                    ;;
                "schema")
                    test_args+=("$TEST_DIR/test_schema_integrity.py")
                    ;;
                "constraints")
                    test_args+=("$TEST_DIR/test_constraints_and_indexes.py")
                    ;;
                "crud")
                    test_args+=("$TEST_DIR/test_users_crud.py")
                    test_args+=("$TEST_DIR/test_projects_crud.py")
                    test_args+=("$TEST_DIR/test_ai_tasks_crud.py")
                    test_args+=("$TEST_DIR/test_file_storage_crud.py")
                    ;;
                "performance")
                    test_args+=("$TEST_DIR/test_query_performance.py")
                    ;;
                "concurrent")
                    test_args+=("$TEST_DIR/test_concurrent_operations.py")
                    ;;
                "firebase")
                    test_args+=("$TEST_DIR/test_firebase_studio_integration.py")
                    ;;
                *)
                    log_warning "未知测试模块: $module"
                    ;;
            esac
        done
    fi
    
    # 执行测试
    log_info "执行命令: $pytest_cmd ${test_args[*]}"
    
    local start_time=$(date +%s)
    
    if $pytest_cmd "${test_args[@]}"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "$env_name 测试完成 (耗时: ${duration}s)"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_error "$env_name 测试失败 (耗时: ${duration}s)"
        return 1
    fi
}

# 生成测试报告
generate_test_report() {
    log_section "生成测试报告"
    
    local report_dir="$TEST_DIR/reports"
    mkdir -p "$report_dir"
    
    local report_file="$report_dir/database_test_report_$(date +%Y%m%d_%H%M%S).html"
    
    # 运行测试并生成HTML报告
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    python3 -m pytest "$TEST_DIR" \
        --html="$report_file" \
        --self-contained-html \
        --tb=short \
        -v
    
    if [[ -f "$report_file" ]]; then
        log_success "测试报告已生成: $report_file"
    else
        log_error "测试报告生成失败"
    fi
}

# 主函数
main() {
    # 默认设置
    ENVIRONMENTS=()
    TEST_MODULES=()
    FAST_MODE=false
    VERBOSE=false
    PERFORMANCE_ONLY=false
    GENERATE_COVERAGE=false
    GENERATE_REPORT=false
    TEST_ALL_ENVS=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENTS+=("$2")
                shift 2
                ;;
            -a|--all-envs)
                TEST_ALL_ENVS=true
                shift
                ;;
            -f|--fast)
                FAST_MODE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -p|--performance)
                PERFORMANCE_ONLY=true
                shift
                ;;
            -c|--coverage)
                GENERATE_COVERAGE=true
                shift
                ;;
            -r|--report)
                GENERATE_REPORT=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                TEST_MODULES+=("$1")
                shift
                ;;
        esac
    done
    
    # 设置默认环境
    if [[ ${#ENVIRONMENTS[@]} -eq 0 && "$TEST_ALL_ENVS" != "true" ]]; then
        ENVIRONMENTS=("dev_pro1")
    fi
    
    if [[ "$TEST_ALL_ENVS" == "true" ]]; then
        ENVIRONMENTS=("dev_pro1" "dev_pro2" "stage_pro1" "stage_pro2" "prod_pro1" "prod_pro2")
    fi
    
    # 显示配置
    log_section "测试配置"
    log_info "环境: ${ENVIRONMENTS[*]}"
    log_info "模块: ${TEST_MODULES[*]:-所有模块}"
    log_info "快速模式: $FAST_MODE"
    log_info "详细输出: $VERBOSE"
    log_info "仅性能测试: $PERFORMANCE_ONLY"
    log_info "生成覆盖率: $GENERATE_COVERAGE"
    log_info "生成报告: $GENERATE_REPORT"
    
    # 检查依赖
    check_dependencies
    
    # 特殊处理：仅生成报告
    if [[ "$GENERATE_REPORT" == "true" && ${#ENVIRONMENTS[@]} -eq 0 ]]; then
        generate_test_report
        exit 0
    fi
    
    # 运行测试
    local total_success=0
    local total_tests=0
    local failed_envs=()
    
    for env in "${ENVIRONMENTS[@]}"; do
        total_tests=$((total_tests + 1))
        
        # 检查数据库连接
        if ! check_database_connectivity "$env"; then
            failed_envs+=("$env")
            continue
        fi
        
        # 运行测试
        if run_test_suite "$env" "${TEST_MODULES[@]}"; then
            total_success=$((total_success + 1))
        else
            failed_envs+=("$env")
        fi
    done
    
    # 生成报告
    if [[ "$GENERATE_REPORT" == "true" ]]; then
        generate_test_report
    fi
    
    # 总结
    log_section "测试总结"
    log_info "总测试环境: $total_tests"
    log_success "成功环境: $total_success"
    
    if [[ ${#failed_envs[@]} -gt 0 ]]; then
        log_error "失败环境: ${failed_envs[*]}"
        exit 1
    else
        log_success "所有测试通过!"
        exit 0
    fi
}

# 执行主函数
main "$@"