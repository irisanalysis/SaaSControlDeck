#!/bin/bash
# SaaS Control Deck 多环境数据同步脚本
# Usage: ./environment-sync.sh [sync_type] [source_env] [target_env]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 颜色输出
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 环境配置映射
declare -A ENV_DB_PORTS
ENV_DB_PORTS["development"]=5433
ENV_DB_PORTS["staging"]=5434
ENV_DB_PORTS["production"]=5432

declare -A ENV_DB_NAMES
ENV_DB_NAMES["development"]="saascontrol_dev"
ENV_DB_NAMES["staging"]="saascontrol_staging" 
ENV_DB_NAMES["production"]="saascontrol_prod"

# 获取数据库连接信息
get_db_connection() {
    local env_name=$1
    local db_port=${ENV_DB_PORTS[$env_name]}
    local db_name=${ENV_DB_NAMES[$env_name]}
    
    echo "postgresql://saascontrol_user:saascontrol_pass@localhost:${db_port}/${db_name}"
}

# 验证环境有效性
validate_environment() {
    local env_name=$1
    
    if [[ ! " development staging production " =~ " $env_name " ]]; then
        log_error "无效的环境名称: $env_name (支持: development, staging, production)"
        return 1
    fi
    
    local db_port=${ENV_DB_PORTS[$env_name]}
    local db_name=${ENV_DB_NAMES[$env_name]}
    
    # 检查数据库连接
    if ! docker exec "saascontrol-postgres-${env_name}" pg_isready -U saascontrol_user -d "$db_name" > /dev/null 2>&1; then
        log_error "${env_name} 环境数据库不可用 (端口: ${db_port})"
        return 1
    fi
    
    return 0
}

# 数据脱敏处理
sanitize_data() {
    local sql_file=$1
    
    log_info "对数据进行脱敏处理..."
    
    # 创建脱敏后的SQL文件
    local sanitized_file="${sql_file}.sanitized"
    
    # 脱敏处理规则
    sed -E '
        # 邮箱脱敏
        s/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/test_user@example.com/g
        # 手机号脱敏
        s/\b1[3-9]\d{9}\b/13800000000/g
        # 身份证号脱敏
        s/\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b/110000000000000000/g
        # 密码hash脱敏 (保持格式)
        s/\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}/\$2b\$12\$testhashedpasswordfordevlopment12345/g
        # IP地址脱敏
        s/\b([0-9]{1,3}\.){3}[0-9]{1,3}\b/127.0.0.1/g
        # API密钥脱敏
        s/sk-[a-zA-Z0-9]{48}/sk-test1234567890abcdef1234567890abcdef12345678/g
    ' "$sql_file" > "$sanitized_file"
    
    echo "$sanitized_file"
}

# 生产数据同步到暂存环境（脱敏）
sync_prod_to_staging() {
    log_info "开始生产环境到暂存环境的数据同步（脱敏）..."
    
    # 验证环境
    if ! validate_environment "production" || ! validate_environment "staging"; then
        return 1
    fi
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="${PROJECT_ROOT}/backups"
    local backup_file="${backup_dir}/prod_to_staging_${timestamp}.sql"
    local sanitized_file="${backup_file}.sanitized"
    
    mkdir -p "$backup_dir"
    
    # 1. 备份生产数据
    log_info "导出生产环境数据..."
    docker exec "saascontrol-postgres-production" pg_dump \
        -U saascontrol_user \
        -d saascontrol_prod \
        --clean --if-exists \
        > "$backup_file"
    
    if [ ! -s "$backup_file" ]; then
        log_error "生产环境数据导出失败"
        return 1
    fi
    
    log_success "生产环境数据导出完成: $backup_file"
    
    # 2. 数据脱敏
    sanitized_file=$(sanitize_data "$backup_file")
    log_success "数据脱敏处理完成: $sanitized_file"
    
    # 3. 导入到暂存环境
    log_info "导入数据到暂存环境..."
    docker exec -i "saascontrol-postgres-staging" psql \
        -U saascontrol_user \
        -d saascontrol_staging \
        < "$sanitized_file"
    
    if [ $? -eq 0 ]; then
        log_success "数据同步完成: 生产环境 → 暂存环境（脱敏）"
        
        # 4. 验证同步结果
        local prod_count=$(docker exec "saascontrol-postgres-production" psql \
            -U saascontrol_user -d saascontrol_prod \
            -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
        local staging_count=$(docker exec "saascontrol-postgres-staging" psql \
            -U saascontrol_user -d saascontrol_staging \
            -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
        
        log_info "同步验证: 生产环境用户数=$prod_count, 暂存环境用户数=$staging_count"
        
        # 5. 清理临时文件
        rm -f "$backup_file" "$sanitized_file"
        log_info "临时文件已清理"
    else
        log_error "数据同步失败"
        return 1
    fi
}

# 重置开发环境数据
reset_dev_environment() {
    log_info "开始重置开发环境数据..."
    
    if ! validate_environment "development"; then
        return 1
    fi
    
    local sample_data_file="${PROJECT_ROOT}/scripts/database/sample-data-development.sql"
    
    # 检查样例数据文件是否存在
    if [ ! -f "$sample_data_file" ]; then
        log_warning "开发环境样例数据文件不存在，创建基础样例数据..."
        create_dev_sample_data "$sample_data_file"
    fi
    
    # 1. 清空开发数据库
    log_info "清空开发环境数据..."
    docker exec "saascontrol-postgres-development" psql \
        -U saascontrol_user -d saascontrol_dev \
        -c "TRUNCATE TABLE users, user_profiles, projects, datasets, analysis_tasks, analysis_results, api_logs RESTART IDENTITY CASCADE;"
    
    # 2. 导入样例数据
    log_info "导入开发环境样例数据..."
    docker exec -i "saascontrol-postgres-development" psql \
        -U saascontrol_user -d saascontrol_dev \
        < "$sample_data_file"
    
    if [ $? -eq 0 ]; then
        log_success "开发环境数据重置完成"
        
        # 验证数据
        local dev_user_count=$(docker exec "saascontrol-postgres-development" psql \
            -U saascontrol_user -d saascontrol_dev \
            -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
        
        log_info "开发环境用户数: $dev_user_count"
    else
        log_error "开发环境数据重置失败"
        return 1
    fi
}

# 创建开发环境样例数据
create_dev_sample_data() {
    local sample_file=$1
    
    cat > "$sample_file" << 'EOF'
-- SaaS Control Deck 开发环境样例数据
-- Generated for development testing

-- 插入测试用户
INSERT INTO users (id, email, username, hashed_password, is_active, created_at, updated_at) VALUES
(1, 'dev@example.com', 'developer', '$2b$12$testhashedpasswordfordevlopment12345', true, NOW(), NOW()),
(2, 'test@example.com', 'tester', '$2b$12$testhashedpasswordfordevlopment12345', true, NOW(), NOW()),
(3, 'admin@example.com', 'admin', '$2b$12$testhashedpasswordfordevlopment12345', true, NOW(), NOW());

-- 插入用户档案
INSERT INTO user_profiles (user_id, first_name, last_name, phone, created_at, updated_at) VALUES
(1, 'Dev', 'User', '13800000001', NOW(), NOW()),
(2, 'Test', 'User', '13800000002', NOW(), NOW()),
(3, 'Admin', 'User', '13800000003', NOW(), NOW());

-- 插入测试项目
INSERT INTO projects (id, name, description, owner_id, created_at, updated_at) VALUES
(1, 'Development Project', 'Sample project for development testing', 1, NOW(), NOW()),
(2, 'Test Project', 'Sample project for testing features', 2, NOW(), NOW()),
(3, 'Demo Project', 'Demo project for showcasing features', 3, NOW(), NOW());

-- 插入测试数据集
INSERT INTO datasets (id, name, file_path, file_size, project_id, uploaded_by, created_at) VALUES
(1, 'sample-data.csv', '/data/sample-data.csv', 1024, 1, 1, NOW()),
(2, 'test-dataset.json', '/data/test-dataset.json', 2048, 2, 2, NOW()),
(3, 'demo-analytics.xlsx', '/data/demo-analytics.xlsx', 4096, 3, 3, NOW());

-- 插入分析任务样例
INSERT INTO analysis_tasks (id, name, task_type, status, project_id, created_by, created_at, updated_at) VALUES
(1, 'Data Quality Check', 'quality_analysis', 'completed', 1, 1, NOW(), NOW()),
(2, 'Trend Analysis', 'trend_analysis', 'processing', 2, 2, NOW(), NOW()),
(3, 'Predictive Modeling', 'ml_prediction', 'pending', 3, 3, NOW(), NOW());

-- 插入分析结果样例
INSERT INTO analysis_results (id, task_id, result_data, created_at) VALUES
(1, 1, '{"data_quality_score": 0.95, "issues_found": 2, "recommendations": ["Remove duplicates", "Handle missing values"]}', NOW()),
(2, 2, '{"trend_direction": "upward", "confidence": 0.87, "forecast_data": [1, 2, 3, 4, 5]}', NOW());

-- 重置序列
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('projects_id_seq', (SELECT MAX(id) FROM projects));
SELECT setval('datasets_id_seq', (SELECT MAX(id) FROM datasets));
SELECT setval('analysis_tasks_id_seq', (SELECT MAX(id) FROM analysis_tasks));
SELECT setval('analysis_results_id_seq', (SELECT MAX(id) FROM analysis_results));
EOF

    log_success "开发环境样例数据文件已创建: $sample_file"
}

# 数据库Schema同步
sync_database_schema() {
    local source_env=$1
    local target_env=$2
    
    log_info "同步数据库Schema: ${source_env} → ${target_env}"
    
    if ! validate_environment "$source_env" || ! validate_environment "$target_env"; then
        return 1
    fi
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local schema_file="${PROJECT_ROOT}/backups/schema_${source_env}_${timestamp}.sql"
    
    mkdir -p "$(dirname "$schema_file")"
    
    # 1. 导出源环境Schema
    log_info "导出 ${source_env} 环境Schema..."
    docker exec "saascontrol-postgres-${source_env}" pg_dump \
        -U saascontrol_user \
        -d "${ENV_DB_NAMES[$source_env]}" \
        --schema-only \
        --clean --if-exists \
        > "$schema_file"
    
    # 2. 应用到目标环境
    log_info "应用Schema到 ${target_env} 环境..."
    docker exec -i "saascontrol-postgres-${target_env}" psql \
        -U saascontrol_user \
        -d "${ENV_DB_NAMES[$target_env]}" \
        < "$schema_file"
    
    if [ $? -eq 0 ]; then
        log_success "Schema同步完成: ${source_env} → ${target_env}"
        rm -f "$schema_file"
    else
        log_error "Schema同步失败"
        return 1
    fi
}

# 显示环境状态
show_environment_status() {
    echo "==============================================="
    echo "SaaS Control Deck 多环境数据库状态"
    echo "==============================================="
    
    for env in "production" "staging" "development"; do
        local db_port=${ENV_DB_PORTS[$env]}
        local db_name=${ENV_DB_NAMES[$env]}
        
        echo ""
        echo "🔧 $env 环境:"
        echo "   数据库端口: $db_port"
        echo "   数据库名称: $db_name"
        
        # 检查数据库状态
        if docker exec "saascontrol-postgres-${env}" pg_isready -U saascontrol_user -d "$db_name" > /dev/null 2>&1; then
            echo "   状态: ✅ 运行中"
            
            # 获取数据统计
            local user_count=$(docker exec "saascontrol-postgres-${env}" psql \
                -U saascontrol_user -d "$db_name" \
                -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "N/A")
            local project_count=$(docker exec "saascontrol-postgres-${env}" psql \
                -U saascontrol_user -d "$db_name" \
                -t -c "SELECT COUNT(*) FROM projects;" 2>/dev/null | tr -d ' ' || echo "N/A")
            
            echo "   用户数量: $user_count"
            echo "   项目数量: $project_count"
        else
            echo "   状态: ❌ 不可用"
        fi
    done
    
    echo ""
    echo "==============================================="
}

# 显示使用帮助
show_usage() {
    echo "SaaS Control Deck 多环境数据同步脚本"
    echo ""
    echo "用法:"
    echo "  $0 [操作类型] [参数...]"
    echo ""
    echo "操作类型:"
    echo "  prod-to-staging     - 生产环境同步到暂存环境（脱敏）"
    echo "  reset-dev          - 重置开发环境数据（样例数据）"
    echo "  sync-schema        - 同步数据库Schema"
    echo "  status             - 显示所有环境状态"
    echo ""
    echo "示例:"
    echo "  $0 prod-to-staging              # 生产数据同步到暂存（脱敏）"
    echo "  $0 reset-dev                   # 重置开发环境"
    echo "  $0 sync-schema production staging  # 同步Schema from生产 to暂存"
    echo "  $0 status                      # 查看环境状态"
    echo ""
}

# 主程序入口
main() {
    local operation=${1:-""}
    
    case $operation in
        "prod-to-staging")
            sync_prod_to_staging
            ;;
        "reset-dev")
            reset_dev_environment
            ;;
        "sync-schema")
            local source_env=$2
            local target_env=$3
            if [ -z "$source_env" ] || [ -z "$target_env" ]; then
                log_error "Schema同步需要指定源环境和目标环境"
                echo "用法: $0 sync-schema [source_env] [target_env]"
                exit 1
            fi
            sync_database_schema "$source_env" "$target_env"
            ;;
        "status")
            show_environment_status
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            log_error "无效的操作类型: $operation"
            show_usage
            exit 1
            ;;
    esac
}

# 脚本执行入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi