#!/bin/bash

# ===========================================
# SaaS Control Deck 数据库架构部署脚本
# ===========================================
# 用途: 自动化部署三环境数据库架构
# 作者: SaaS Control Deck Team
# 版本: 1.0.0
# 日期: 2025-01-12
# ===========================================

set -euo pipefail

# ===========================================
# 配置参数
# ===========================================

# 数据库连接信息
DB_HOST="47.79.87.199"
DB_PORT="5432"
SUPER_USER="jackchan"
SUPER_PASSWORD="secure_password_123"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deployment-$(date +%Y%m%d_%H%M%S).log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===========================================
# 日志函数
# ===========================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# ===========================================
# 实用函数
# ===========================================

# 检查依赖
check_dependencies() {
    log_info "检查依赖项..."
    
    if ! command -v psql &> /dev/null; then
        log_error "psql 命令未找到，请安装 PostgreSQL 客户端"
        exit 1
    fi
    
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump 命令未找到，请安装 PostgreSQL 客户端"
        exit 1
    fi
    
    log_success "依赖项检查通过"
}

# 测试数据库连接
test_connection() {
    log_info "测试数据库连接..."
    
    if PGPASSWORD="$SUPER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$SUPER_USER" -d postgres -c "SELECT version();" &> /dev/null; then
        log_success "数据库连接测试成功"
        return 0
    else
        log_error "数据库连接失败，请检查连接信息"
        return 1
    fi
}

# 执行SQL脚本
execute_sql_script() {
    local script_file="$1"
    local database="$2"
    local username="$3"
    local password="$4"
    
    if [[ ! -f "$script_file" ]]; then
        log_error "脚本文件不存在: $script_file"
        return 1
    fi
    
    log_info "执行SQL脚本: $(basename "$script_file")"
    log_info "目标数据库: $database"
    log_info "使用用户: $username"
    
    if PGPASSWORD="$password" psql -h "$DB_HOST" -p "$DB_PORT" -U "$username" -d "$database" -f "$script_file" >> "$LOG_FILE" 2>&1; then
        log_success "脚本执行成功: $(basename "$script_file")"
        return 0
    else
        log_error "脚本执行失败: $(basename "$script_file")"
        log_error "请查看日志文件: $LOG_FILE"
        return 1
    fi
}

# 验证数据库是否存在
verify_database_exists() {
    local database_name="$1"
    
    if PGPASSWORD="$SUPER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$SUPER_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$database_name'" | grep -q 1; then
        return 0
    else
        return 1
    fi
}

# 验证用户是否存在
verify_user_exists() {
    local username="$1"
    
    if PGPASSWORD="$SUPER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$SUPER_USER" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$username'" | grep -q 1; then
        return 0
    else
        return 1
    fi
}

# 测试用户连接
test_user_connection() {
    local database="$1"
    local username="$2"
    local password="$3"
    
    if PGPASSWORD="$password" psql -h "$DB_HOST" -p "$DB_PORT" -U "$username" -d "$database" -c "SELECT current_user, current_database();" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ===========================================
# 部署步骤
# ===========================================

# 步骤1: 创建数据库
deploy_step1_create_databases() {
    log_info "===========================================" 
    log_info "步骤1: 创建数据库"
    log_info "==========================================="
    
    execute_sql_script "${SCRIPT_DIR}/01-create-databases.sql" "postgres" "$SUPER_USER" "$SUPER_PASSWORD"
    
    # 验证数据库创建
    local databases=("saascontrol_dev_pro1" "saascontrol_dev_pro2" "saascontrol_stage_pro1" "saascontrol_stage_pro2" "saascontrol_prod_pro1" "saascontrol_prod_pro2")
    
    for db in "${databases[@]}"; do
        if verify_database_exists "$db"; then
            log_success "数据库创建成功: $db"
        else
            log_error "数据库创建失败: $db"
            return 1
        fi
    done
}

# 步骤2: 创建用户和权限
deploy_step2_create_users() {
    log_info "==========================================="
    log_info "步骤2: 创建用户和权限"
    log_info "==========================================="
    
    execute_sql_script "${SCRIPT_DIR}/02-create-users-permissions.sql" "postgres" "$SUPER_USER" "$SUPER_PASSWORD"
    
    # 验证用户创建
    local users=("saasctl_dev_pro1_user" "saasctl_dev_pro2_user" "saasctl_stage_pro1_user" "saasctl_stage_pro2_user" "saasctl_prod_pro1_user" "saasctl_prod_pro2_user")
    
    for user in "${users[@]}"; do
        if verify_user_exists "$user"; then
            log_success "用户创建成功: $user"
        else
            log_error "用户创建失败: $user"
            return 1
        fi
    done
}

# 步骤3: 创建表结构
deploy_step3_create_tables() {
    log_info "==========================================="
    log_info "步骤3: 创建表结构"
    log_info "==========================================="
    
    # 对每个数据库执行表结构脚本
    declare -A db_users=(
        ["saascontrol_dev_pro1"]="saasctl_dev_pro1_user:dev_pro1_secure_2025!"
        ["saascontrol_dev_pro2"]="saasctl_dev_pro2_user:dev_pro2_secure_2025!"
        ["saascontrol_stage_pro1"]="saasctl_stage_pro1_user:stage_pro1_secure_2025!"
        ["saascontrol_stage_pro2"]="saasctl_stage_pro2_user:stage_pro2_secure_2025!"
        ["saascontrol_prod_pro1"]="saasctl_prod_pro1_user:prod_pro1_ULTRA_secure_2025#\$%"
        ["saascontrol_prod_pro2"]="saasctl_prod_pro2_user:prod_pro2_ULTRA_secure_2025#\$%"
    )
    
    for db in "${!db_users[@]}"; do
        IFS=':' read -r username password <<< "${db_users[$db]}"
        log_info "在数据库 $db 中创建表结构..."
        execute_sql_script "${SCRIPT_DIR}/03-create-table-structure.sql" "$db" "$username" "$password" || return 1
    done
}

# 步骤4: 创建索引
deploy_step4_create_indexes() {
    log_info "==========================================="
    log_info "步骤4: 创建索引"
    log_info "==========================================="
    
    declare -A db_users=(
        ["saascontrol_dev_pro1"]="saasctl_dev_pro1_user:dev_pro1_secure_2025!"
        ["saascontrol_dev_pro2"]="saasctl_dev_pro2_user:dev_pro2_secure_2025!"
        ["saascontrol_stage_pro1"]="saasctl_stage_pro1_user:stage_pro1_secure_2025!"
        ["saascontrol_stage_pro2"]="saasctl_stage_pro2_user:stage_pro2_secure_2025!"
        ["saascontrol_prod_pro1"]="saasctl_prod_pro1_user:prod_pro1_ULTRA_secure_2025#\$%"
        ["saascontrol_prod_pro2"]="saasctl_prod_pro2_user:prod_pro2_ULTRA_secure_2025#\$%"
    )
    
    for db in "${!db_users[@]}"; do
        IFS=':' read -r username password <<< "${db_users[$db]}"
        log_info "在数据库 $db 中创建索引..."
        execute_sql_script "${SCRIPT_DIR}/04-create-indexes.sql" "$db" "$username" "$password" || return 1
    done
}

# 步骤5: 数据库配置优化
deploy_step5_optimize_config() {
    log_info "==========================================="
    log_info "步骤5: 数据库配置优化"
    log_info "==========================================="
    
    execute_sql_script "${SCRIPT_DIR}/05-database-configuration.sql" "postgres" "$SUPER_USER" "$SUPER_PASSWORD"
    
    # 重新加载配置
    log_info "重新加载 PostgreSQL 配置..."
    if PGPASSWORD="$SUPER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$SUPER_USER" -d postgres -c "SELECT pg_reload_conf();" >> "$LOG_FILE" 2>&1; then
        log_success "PostgreSQL 配置重新加载成功"
    else
        log_warning "PostgreSQL 配置重新加载失败，可能需要重启 PostgreSQL 服务"
    fi
}

# 步骤6: 启用扩展
deploy_step6_enable_extensions() {
    log_info "==========================================="
    log_info "步骤6: 启用数据库扩展"
    log_info "==========================================="
    
    declare -A db_users=(
        ["saascontrol_dev_pro1"]="saasctl_dev_pro1_user:dev_pro1_secure_2025!"
        ["saascontrol_dev_pro2"]="saasctl_dev_pro2_user:dev_pro2_secure_2025!"
        ["saascontrol_stage_pro1"]="saasctl_stage_pro1_user:stage_pro1_secure_2025!"
        ["saascontrol_stage_pro2"]="saasctl_stage_pro2_user:stage_pro2_secure_2025!"
        ["saascontrol_prod_pro1"]="saasctl_prod_pro1_user:prod_pro1_ULTRA_secure_2025#\$%"
        ["saascontrol_prod_pro2"]="saasctl_prod_pro2_user:prod_pro2_ULTRA_secure_2025#\$%"
    )
    
    for db in "${!db_users[@]}"; do
        IFS=':' read -r username password <<< "${db_users[$db]}"
        log_info "在数据库 $db 中启用扩展..."
        
        # 启用pg_stat_statements扩展
        if PGPASSWORD="$password" psql -h "$DB_HOST" -p "$DB_PORT" -U "$username" -d "$db" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" >> "$LOG_FILE" 2>&1; then
            log_success "数据库 $db 中 pg_stat_statements 扩展启用成功"
        else
            log_warning "数据库 $db 中 pg_stat_statements 扩展启用失败"
        fi
    done
}

# 部署后验证
verify_deployment() {
    log_info "==========================================="
    log_info "部署后验证"
    log_info "==========================================="
    
    local success_count=0
    local total_count=0
    
    declare -A db_users=(
        ["saascontrol_dev_pro1"]="saasctl_dev_pro1_user:dev_pro1_secure_2025!"
        ["saascontrol_dev_pro2"]="saasctl_dev_pro2_user:dev_pro2_secure_2025!"
        ["saascontrol_stage_pro1"]="saasctl_stage_pro1_user:stage_pro1_secure_2025!"
        ["saascontrol_stage_pro2"]="saasctl_stage_pro2_user:stage_pro2_secure_2025!"
        ["saascontrol_prod_pro1"]="saasctl_prod_pro1_user:prod_pro1_ULTRA_secure_2025#\$%"
        ["saascontrol_prod_pro2"]="saasctl_prod_pro2_user:prod_pro2_ULTRA_secure_2025#\$%"
    )
    
    for db in "${!db_users[@]}"; do
        IFS=':' read -r username password <<< "${db_users[$db]}"
        ((total_count++))
        
        log_info "验证数据库: $db"
        
        # 测试连接
        if test_user_connection "$db" "$username" "$password"; then
            log_success "数据库 $db 连接测试成功"
            
            # 检查表数量
            local table_count
            table_count=$(PGPASSWORD="$password" psql -h "$DB_HOST" -p "$DB_PORT" -U "$username" -d "$db" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")
            
            if [[ $table_count -gt 0 ]]; then
                log_success "数据库 $db 中存在 $table_count 个表"
                ((success_count++))
            else
                log_error "数据库 $db 中未找到表"
            fi
        else
            log_error "数据库 $db 连接测试失败"
        fi
    done
    
    log_info "==========================================="
    log_info "验证结果: $success_count/$total_count 数据库部署成功"
    
    if [[ $success_count -eq $total_count ]]; then
        return 0
    else
        return 1
    fi
}

# 生成部署报告
generate_deployment_report() {
    log_info "==========================================="
    log_info "生成部署报告"
    log_info "==========================================="
    
    local report_file="${SCRIPT_DIR}/deployment-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# SaaS Control Deck 数据库架构部署报告

## 部署信息

- **部署时间**: $(date +'%Y-%m-%d %H:%M:%S')
- **数据库服务器**: $DB_HOST:$DB_PORT
- **部署日志**: $LOG_FILE

## 数据库列表

### 开发环境
- saascontrol_dev_pro1 (用户: saasctl_dev_pro1_user)
- saascontrol_dev_pro2 (用户: saasctl_dev_pro2_user)

### 测试环境
- saascontrol_stage_pro1 (用户: saasctl_stage_pro1_user)
- saascontrol_stage_pro2 (用户: saasctl_stage_pro2_user)

### 生产环境
- saascontrol_prod_pro1 (用户: saasctl_prod_pro1_user)
- saascontrol_prod_pro2 (用户: saasctl_prod_pro2_user)

## 数据库连接信息

请参考配置文件: database-environments.env

## 后续操作

1. 配置微服务连接
2. 设置定期备份
3. 配置监控和告警
4. 安全加固和网络访问控制
5. 性能优化和调优

## 维护命令

查看数据库状态:
\`\`\`bash
psql -h $DB_HOST -U jackchan -d postgres -c "\\l | grep saascontrol"
\`\`\`

查看用户状态:
\`\`\`bash
psql -h $DB_HOST -U jackchan -d postgres -c "\\du | grep saasctl"
\`\`\`

性能监控:
\`\`\`bash
psql -h $DB_HOST -U saasctl_dev_pro1_user -d saascontrol_dev_pro1 -c "SELECT * FROM database_health_check();"
\`\`\`
EOF
    
    log_success "部署报告已生成: $report_file"
}

# ===========================================
# 主程序
# ===========================================

main() {
    echo
    echo "==========================================="
    echo "  SaaS Control Deck 数据库架构部署  "
    echo "==========================================="
    echo
    
    log_info "开始部署 SaaS Control Deck 数据库架构"
    log_info "日志文件: $LOG_FILE"
    
    # 检查依赖
    check_dependencies || exit 1
    
    # 测试连接
    test_connection || exit 1
    
    # 显示警告信息
    echo
    log_warning "注意: 此操作将在数据库服务器上创建多个数据库和用户"
    log_warning "请确保您有足够的权限并已备份现有数据"
    echo
    
    read -p "是否继续部署? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "用户取消部署"
        exit 0
    fi
    
    # 执行部署步骤
    local step_failed=false
    
    deploy_step1_create_databases || step_failed=true
    
    if [[ $step_failed == false ]]; then
        deploy_step2_create_users || step_failed=true
    fi
    
    if [[ $step_failed == false ]]; then
        deploy_step3_create_tables || step_failed=true
    fi
    
    if [[ $step_failed == false ]]; then
        deploy_step4_create_indexes || step_failed=true
    fi
    
    if [[ $step_failed == false ]]; then
        deploy_step5_optimize_config || step_failed=true
    fi
    
    if [[ $step_failed == false ]]; then
        deploy_step6_enable_extensions || step_failed=true
    fi
    
    # 验证部署
    if [[ $step_failed == false ]]; then
        if verify_deployment; then
            log_success "数据库架构部署成功！"
        else
            log_error "部署验证失败"
            step_failed=true
        fi
    fi
    
    # 生成报告
    generate_deployment_report
    
    echo
    if [[ $step_failed == false ]]; then
        log_success "==========================================="
        log_success " 数据库架构部署全部完成! "
        log_success "==========================================="
        echo
        log_info "下一步操作:"
        log_info "1. 配置微服务数据库连接"
        log_info "2. 设置定期备份任务"
        log_info "3. 配置监控和告警"
        echo
        log_info "配置文件: database-environments.env"
        log_info "详细日志: $LOG_FILE"
        
        exit 0
    else
        log_error "==========================================="
        log_error " 数据库架构部署失败! "
        log_error "==========================================="
        log_error "请检查日志文件: $LOG_FILE"
        
        exit 1
    fi
}

# 捕获信号并清理
trap 'log_error "脚本被中断"; exit 1' INT TERM

# 执行主程序
main "$@"