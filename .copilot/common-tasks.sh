#!/bin/bash
# GitHub Copilot CLI 常用任务自动化脚本
# 使用方法: ./common-tasks.sh [task_name]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查 Copilot CLI 是否可用
check_copilot() {
    if ! command -v copilot &> /dev/null; then
        log_error "GitHub Copilot CLI 未安装或未在PATH中"
        exit 1
    fi
    log_success "GitHub Copilot CLI 可用"
}

# 通用 Copilot 执行函数
execute_copilot() {
    local task="$1"
    local options="${2:---allow-all-tools}"
    
    log_info "执行任务: $task"
    
    if ! copilot -p "$task" $options; then
        log_error "任务执行失败: $task"
        return 1
    fi
    
    log_success "任务完成: $task"
}

# 任务函数定义

# 1. 项目健康检查
health_check() {
    log_info "开始项目健康检查..."
    execute_copilot "执行全面的项目健康检查：Git状态、依赖版本、服务运行状态、代码质量"
}

# 2. Git 状态检查
git_status() {
    log_info "检查Git仓库状态..."
    execute_copilot "显示详细的Git仓库状态、最近提交和分支信息"
}

# 3. 代码质量分析
code_quality() {
    log_info "执行代码质量分析..."
    execute_copilot "分析项目代码质量，检查TypeScript错误、ESLint问题，并提供改进建议"
}

# 4. 依赖管理
dependency_check() {
    log_info "检查项目依赖..."
    execute_copilot "检查package.json和pyproject.toml中的依赖，识别过期包并提供更新建议"
}

# 5. 安全扫描
security_scan() {
    log_info "执行安全扫描..."
    execute_copilot "执行安全漏洞扫描，检查依赖安全性和潜在的安全问题" "--allow-all-tools --log-level debug"
}

# 6. 性能分析
performance_analysis() {
    log_info "执行性能分析..."
    execute_copilot "分析应用性能，识别瓶颈并提供优化建议"
}

# 7. SaaS Control Deck 专用检查
saas_control_check() {
    log_info "SaaS Control Deck 专项检查..."
    execute_copilot "检查SaaS Control Deck平台状态：Next.js前端(9000端口)、FastAPI后端(8000-8199端口)、PostgreSQL数据库连接"
}

# 8. 前端专项检查
frontend_check() {
    log_info "前端专项检查..."
    execute_copilot "检查Next.js 15.3.3应用状态、Firebase Studio环境、Radix UI组件使用情况"
}

# 9. 后端专项检查
backend_check() {
    log_info "后端专项检查..."
    execute_copilot "检查FastAPI微服务状态、Docker容器运行情况、数据库连接健康度"
}

# 10. 部署前验证
pre_deploy_check() {
    log_info "部署前验证..."
    execute_copilot "执行部署前完整验证：构建测试、安全扫描、配置检查、集成测试" "--allow-all-tools --log-dir ./pre-deploy-logs"
}

# 11. 清理项目
cleanup_project() {
    log_warning "项目清理操作（谨慎执行）..."
    read -p "确认要执行项目清理吗？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        execute_copilot "安全清理项目：删除node_modules、Python缓存、临时文件，但保留重要配置" "--allow-all-tools --deny-tool 'shell(git)'"
    else
        log_info "取消项目清理操作"
    fi
}

# 12. 生成文档
generate_docs() {
    log_info "生成项目文档..."
    execute_copilot "更新项目文档：README.md、API文档、架构说明，确保与最新代码同步"
}

# 13. 自定义任务
custom_task() {
    echo -n "请输入自定义任务描述: "
    read -r custom_prompt
    if [[ -n "$custom_prompt" ]]; then
        execute_copilot "$custom_prompt"
    else
        log_error "任务描述不能为空"
    fi
}

# 显示使用帮助
show_help() {
    echo "GitHub Copilot CLI 常用任务脚本"
    echo
    echo "使用方法: $0 [task_name]"
    echo
    echo "可用任务:"
    echo "  health          - 项目健康检查"
    echo "  git             - Git状态检查"  
    echo "  quality         - 代码质量分析"
    echo "  deps            - 依赖管理检查"
    echo "  security        - 安全扫描"
    echo "  performance     - 性能分析"
    echo "  saas            - SaaS Control Deck专项检查"
    echo "  frontend        - 前端专项检查"
    echo "  backend         - 后端专项检查"
    echo "  pre-deploy      - 部署前验证"
    echo "  cleanup         - 清理项目（谨慎使用）"
    echo "  docs            - 生成文档"
    echo "  custom          - 自定义任务"
    echo "  help            - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 health       # 执行项目健康检查"
    echo "  $0 git          # 检查Git状态"
    echo "  $0 saas         # SaaS平台专项检查"
}

# 主函数
main() {
    check_copilot
    
    case "${1:-help}" in
        "health")
            health_check
            ;;
        "git")
            git_status
            ;;
        "quality")
            code_quality
            ;;
        "deps")
            dependency_check
            ;;
        "security")
            security_scan
            ;;
        "performance")
            performance_analysis
            ;;
        "saas")
            saas_control_check
            ;;
        "frontend")
            frontend_check
            ;;
        "backend")
            backend_check
            ;;
        "pre-deploy")
            pre_deploy_check
            ;;
        "cleanup")
            cleanup_project
            ;;
        "docs")
            generate_docs
            ;;
        "custom")
            custom_task
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"