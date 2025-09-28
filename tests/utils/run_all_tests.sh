#!/bin/bash
# /home/user/studio/tests/utils/run_all_tests.sh
# SaaS Control Deck 全面测试运行器 - 从根目录迁移而来
# 统一执行所有测试脚本，提供全面的系统验证
# RELEVANT FILES: tests/migration_index.md, tests/README.md

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 测试统计
TOTAL_TEST_SUITES=0
PASSED_TEST_SUITES=0
FAILED_TEST_SUITES=0
SKIPPED_TEST_SUITES=0

# 日志函数
log_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_TEST_SUITES++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_TEST_SUITES++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_skip() {
    echo -e "${YELLOW}⏭️  $1${NC}"
    ((SKIPPED_TEST_SUITES++))
}

# 初始化函数
setup_test_environment() {
    log_info "初始化测试环境..."
    
    # 设置工作目录
    cd "/home/user/studio"
    
    # 创建必要的目录
    mkdir -p tests/reports tests/logs tests/temp
    
    # 初始化配置
    if [ ! -f "tests/test_config.json" ]; then
        python3 tests/utils/test_config.py > /dev/null 2>&1
        log_info "测试配置已初始化"
    fi
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装或不在PATH中"
        exit 1
    fi
    
    log_success "测试环境初始化完成"
}

# 测试函数：快速健康检查
run_quick_health_tests() {
    log_header "🩺 执行快速健康检查测试"
    ((TOTAL_TEST_SUITES++))
    
    if python3 tests/backend/health/quick_health_check.py; then
        log_success "快速健康检查通过"
    else
        log_error "快速健康检查失败"
        return 1
    fi
}

# 测试函数：综合健康检查
run_comprehensive_health_tests() {
    log_header "📋 执行综合健康检查测试"
    ((TOTAL_TEST_SUITES++))
    
    if python3 tests/backend/health/comprehensive_health_check.py; then
        log_success "综合健康检查通过"
    else
        log_error "综合健康检查失败"
        return 1
    fi
}

# 测试函数：Studio Producer验证
run_producer_validation_tests() {
    log_header "🎭 执行Studio Producer验证测试"
    ((TOTAL_TEST_SUITES++))
    
    if python3 tests/backend/validation/producer_validation.py; then
        log_success "Studio Producer验证通过"
    else
        log_error "Studio Producer验证失败"
        return 1
    fi
}

# 测试函数：FastAPI迁移验证
run_migration_validation_tests() {
    log_header "🔄 执行FastAPI迁移验证测试"
    ((TOTAL_TEST_SUITES++))
    
    if python3 tests/migration/fastapi_migration/migration_validator.py; then
        log_success "FastAPI迁移验证通过"
    else
        log_error "FastAPI迁移验证失败"
        return 1
    fi
}

# 测试函数：API功能测试
run_api_functionality_tests() {
    log_header "🚀 执行API功能测试"
    ((TOTAL_TEST_SUITES++))
    
    if python3 tests/backend/api/fastapi_migration_test.py; then
        log_success "API功能测试通过"
    else
        log_error "API功能测试失败"
        return 1
    fi
}

# 测试函数：Docker构建测试
run_docker_build_tests() {
    log_header "🐳 执行Docker构建测试"
    ((TOTAL_TEST_SUITES++))
    
    # 检查Docker是否可用
    if ! command -v docker &> /dev/null; then
        log_skip "Docker未安装，跳过Docker构建测试"
        return 0
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_skip "Docker服务不可用，跳过Docker构建测试"
        return 0
    fi
    
    if bash tests/infrastructure/docker/build_tests/docker_build_validator.sh; then
        log_success "Docker构建测试通过"
    else
        log_error "Docker构建测试失败"
        return 1
    fi
}

# 生成测试报告
generate_test_report() {
    log_header "📄 生成测试报告"
    
    local report_file="tests/reports/all_tests_report_$(date +'%Y%m%d_%H%M%S').json"
    local success_rate=0
    
    if [ $TOTAL_TEST_SUITES -gt 0 ]; then
        success_rate=$((PASSED_TEST_SUITES * 100 / TOTAL_TEST_SUITES))
    fi
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "test_summary": {
        "total_test_suites": $TOTAL_TEST_SUITES,
        "passed_test_suites": $PASSED_TEST_SUITES,
        "failed_test_suites": $FAILED_TEST_SUITES,
        "skipped_test_suites": $SKIPPED_TEST_SUITES,
        "success_rate_percent": $success_rate
    },
    "test_environment": {
        "hostname": "$(hostname)",
        "os": "$(uname -s)",
        "python_version": "$(python3 --version 2>&1 | cut -d' ' -f2)",
        "docker_available": $(command -v docker &> /dev/null && echo "true" || echo "false")
    },
    "conclusions": {
        "overall_status": "$([ $FAILED_TEST_SUITES -eq 0 ] && echo "PASS" || echo "FAIL")",
        "ready_for_production": $([ $success_rate -ge 90 ] && echo "true" || echo "false"),
        "critical_issues": $([ $FAILED_TEST_SUITES -gt 2 ] && echo "true" || echo "false")
    }
}
EOF
    
    log_success "测试报告已生成: $report_file"
}

# 显示最终结果
show_final_results() {
    echo
    log_header "🏆 SaaS Control Deck 全面测试结果"
    
    echo -e "${PURPLE}📊 测试统计:${NC}"
    echo -e "   总测试套件: $TOTAL_TEST_SUITES"
    echo -e "   通过测试: $PASSED_TEST_SUITES"
    echo -e "   失败测试: $FAILED_TEST_SUITES"
    echo -e "   跳过测试: $SKIPPED_TEST_SUITES"
    
    if [ $TOTAL_TEST_SUITES -gt 0 ]; then
        local success_rate=$((PASSED_TEST_SUITES * 100 / TOTAL_TEST_SUITES))
        echo -e "   成功率: ${success_rate}%"
    fi
    
    echo
    if [ $FAILED_TEST_SUITES -eq 0 ]; then
        log_success "🎉 所有测试都通过了！SaaS Control Deck 在良好状态"
        echo -e "${GREEN}✨ 系统已准备好进行生产部署和用户使用${NC}"
        return 0
    elif [ $FAILED_TEST_SUITES -le 2 ]; then
        log_warning "⚠️  有少量测试失败，但系统基本可用"
        echo -e "${YELLOW}🔧 建议修复失败的测试后再进行部署${NC}"
        return 1
    else
        log_error "❌ 多个关键测试失败，系统存在重大问题"
        echo -e "${RED}🚨 禁止部署到生产环境，必须先解决所有关键问题${NC}"
        return 2
    fi
}

# 主函数
main() {
    local test_mode="${1:-full}"
    local skip_docker="${2:-false}"
    
    echo -e "${PURPLE}🚀 SaaS Control Deck - 全面测试运行器${NC}"
    echo -e "${PURPLE}==============================================${NC}"
    echo -e "${BLUE}⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}🎯 测试模式: $test_mode${NC}"
    echo
    
    # 初始化环境
    setup_test_environment
    echo
    
    # 根据模式执行不同的测试组合
    case $test_mode in
        "quick")
            log_info "🏃 快速测试模式 - 仅执行关键测试"
            run_quick_health_tests || true
            run_producer_validation_tests || true
            ;;
        "health")
            log_info "🩺 健康检查模式 - 仅执行健康相关测试"
            run_quick_health_tests || true
            run_comprehensive_health_tests || true
            ;;
        "api")
            log_info "🚀 API测试模式 - 仅执行API相关测试"
            run_quick_health_tests || true
            run_api_functionality_tests || true
            ;;
        "full"|"全面")
            log_info "📋 全面测试模式 - 执行所有测试"
            
            # 按优先级顺序执行测试
            run_quick_health_tests || true
            echo
            run_comprehensive_health_tests || true
            echo
            run_producer_validation_tests || true
            echo
            run_migration_validation_tests || true
            echo
            run_api_functionality_tests || true
            echo
            
            # Docker测试（可选）
            if [ "$skip_docker" != "true" ]; then
                run_docker_build_tests || true
                echo
            else
                log_skip "Docker测试已被跳过"
                ((TOTAL_TEST_SUITES++))
                ((SKIPPED_TEST_SUITES++))
            fi
            ;;
        *)
            log_error "未知的测试模式: $test_mode"
            echo "支持的模式: quick, health, api, full"
            exit 1
            ;;
    esac
    
    # 生成报告
    generate_test_report
    
    # 显示结果
    show_final_results
    local exit_code=$?
    
    echo
    echo -e "${BLUE}⏱️  结束时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${PURPLE}==============================================${NC}"
    
    exit $exit_code
}

# 帮助信息
show_help() {
    echo "SaaS Control Deck - 全面测试运行器"
    echo ""
    echo "用法: $0 [test_mode] [skip_docker]"
    echo ""
    echo "测试模式:"
    echo "  quick     - 快速测试（健康检查 + 基础验证）"
    echo "  health    - 健康检查测试"
    echo "  api       - API功能测试"
    echo "  full      - 全面测试（默认）"
    echo ""
    echo "参数:"
    echo "  skip_docker - 设为true则跳过Docker测试"
    echo ""
    echo "示例:"
    echo "  $0                    # 全面测试"
    echo "  $0 quick              # 快速测试"
    echo "  $0 full true          # 全面测试但跳过Docker"
}

# 命令行参数处理
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "help" ]; then
    show_help
    exit 0
fi

# 执行主函数
main "$@"
