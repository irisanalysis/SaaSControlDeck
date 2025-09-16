#!/bin/bash

# ===========================================
# SaaS Control Deck - 字符集兼容性修复部署脚本
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 数据库配置
POSTGRES_HOST="47.79.87.199"
POSTGRES_PORT="5432"
POSTGRES_USER="jackchan"
POSTGRES_PASSWORD="secure_password_123"
POSTGRES_DB="postgres"

# 输出函数
print_header() {
    echo -e "${CYAN}=$80${NC}"
    echo -e "${CYAN}    $1${NC}"
    echo -e "${CYAN}=$80${NC}"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查字符集兼容性并创建修复版本SQL
check_and_fix_collation() {
    print_step "检查PostgreSQL服务器字符集配置..."

    # 查询服务器支持的排序规则
    local collation_query="SELECT collname FROM pg_collation WHERE collname LIKE '%utf8%' OR collname LIKE '%UTF%' ORDER BY collname;"

    print_info "查询服务器支持的字符集..."

    # 创建临时SQL文件检查字符集
    cat > /tmp/check_collation.sql << 'EOF'
-- 检查数据库服务器字符集配置
SELECT
    name,
    setting,
    context
FROM pg_settings
WHERE name IN ('lc_collate', 'lc_ctype', 'server_encoding');

-- 查看可用的排序规则
SELECT collname
FROM pg_collation
WHERE collname LIKE '%utf8%'
   OR collname LIKE '%UTF%'
   OR collname = 'C'
   OR collname = 'POSIX'
ORDER BY collname;

-- 查看template0的配置
SELECT
    datname,
    datcollate,
    datctype,
    encoding
FROM pg_database
WHERE datname = 'template0';
EOF

    # 执行检查
    local check_result
    check_result=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/check_collation.sql 2>&1)

    if [[ $? -eq 0 ]]; then
        print_success "字符集配置检查完成"
        echo "$check_result"

        # 从检查结果中提取template0的排序规则
        local template_collate
        template_collate=$(echo "$check_result" | grep "template0" | awk '{print $2}' | head -1)

        if [[ -z "$template_collate" ]]; then
            template_collate="C"
            print_warning "无法获取template0排序规则，使用默认值: C"
        else
            print_info "检测到template0排序规则: $template_collate"
        fi

        # 创建兼容版本的SQL脚本
        create_compatible_sql "$template_collate"
    else
        print_error "字符集检查失败，使用通用兼容配置"
        create_compatible_sql "C"
    fi

    # 清理临时文件
    rm -f /tmp/check_collation.sql
}

# 创建兼容的SQL脚本
create_compatible_sql() {
    local collate_rule="$1"
    local output_file="scripts/database/create-saascontrol-databases-fixed.sql"

    print_step "创建兼容的数据库创建脚本..."
    print_info "使用排序规则: $collate_rule"

    cat > "$output_file" << EOF
-- ===========================================
-- SaaS Control Deck - 三环境数据库架构创建脚本 (字符集兼容版本)
-- ===========================================
-- 目标PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT
-- 排序规则: $collate_rule (自动检测)
-- 用户: $POSTGRES_USER
-- 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

-- ===========================================
-- 1. 创建三环境数据库 (兼容版本)
-- ===========================================

-- 开发环境数据库
DROP DATABASE IF EXISTS saascontrol_dev_pro1;
DROP DATABASE IF EXISTS saascontrol_dev_pro2;

CREATE DATABASE saascontrol_dev_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

CREATE DATABASE saascontrol_dev_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

-- 测试环境数据库
DROP DATABASE IF EXISTS saascontrol_stage_pro1;
DROP DATABASE IF EXISTS saascontrol_stage_pro2;

CREATE DATABASE saascontrol_stage_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

CREATE DATABASE saascontrol_stage_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

-- 生产环境数据库
DROP DATABASE IF EXISTS saascontrol_prod_pro1;
DROP DATABASE IF EXISTS saascontrol_prod_pro2;

CREATE DATABASE saascontrol_prod_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

CREATE DATABASE saascontrol_prod_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$collate_rule'
    LC_CTYPE = '$collate_rule'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

-- ===========================================
-- 2. 创建环境专用用户
-- ===========================================

-- 开发环境用户 (较宽松权限)
DROP USER IF EXISTS saascontrol_dev_user;
CREATE USER saascontrol_dev_user WITH
    PASSWORD 'dev_pass_2024_secure'
    CREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 20;

-- 测试环境用户 (中等权限)
DROP USER IF EXISTS saascontrol_stage_user;
CREATE USER saascontrol_stage_user WITH
    PASSWORD 'stage_pass_2024_secure'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 15;

-- 生产环境用户 (严格权限)
DROP USER IF EXISTS saascontrol_prod_user;
CREATE USER saascontrol_prod_user WITH
    PASSWORD 'prod_pass_2024_very_secure_XyZ9#mK'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 50;

-- ===========================================
-- 3. 数据库权限分配
-- ===========================================

-- 开发环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO saascontrol_dev_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO saascontrol_dev_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO $POSTGRES_USER;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO $POSTGRES_USER;

-- 测试环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro1 TO saascontrol_stage_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro2 TO saascontrol_stage_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro1 TO $POSTGRES_USER;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro2 TO $POSTGRES_USER;

-- 生产环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro1 TO saascontrol_prod_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro2 TO saascontrol_prod_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro1 TO $POSTGRES_USER;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_prod2 TO $POSTGRES_USER;

-- ===========================================
-- 4. 数据库注释和标识
-- ===========================================

COMMENT ON DATABASE saascontrol_dev_pro1 IS 'SaaS Control Deck Development Environment - Pro1 Services (API Gateway, Data Service, AI Service)';
COMMENT ON DATABASE saascontrol_dev_pro2 IS 'SaaS Control Deck Development Environment - Pro2 Services (API Gateway, Data Service, AI Service)';

COMMENT ON DATABASE saascontrol_stage_pro1 IS 'SaaS Control Deck Staging Environment - Pro1 Services - CI/CD Testing';
COMMENT ON DATABASE saascontrol_stage_pro2 IS 'SaaS Control Deck Staging Environment - Pro2 Services - CI/CD Testing';

COMMENT ON DATABASE saascontrol_prod_pro1 IS 'SaaS Control Deck Production Environment - Pro1 Services - Live Production Data';
COMMENT ON DATABASE saascontrol_prod_pro2 IS 'SaaS Control Deck Production Environment - Pro2 Services - Live Production Data';

-- ===========================================
-- 执行完成提示
-- ===========================================

SELECT
    'SaaS Control Deck数据库创建完成! (字符集兼容版本)' as status,
    COUNT(*) as total_databases,
    '$(date '+%Y-%m-%d %H:%M:%S')' as created_at
FROM pg_database
WHERE datname LIKE 'saascontrol_%';
EOF

    print_success "兼容的SQL脚本已创建: $output_file"
}

# 执行修复后的部署
execute_fixed_deployment() {
    local sql_file="scripts/database/create-saascontrol-databases-fixed.sql"

    print_step "执行修复后的数据库创建..."

    # 执行数据库创建脚本
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file"

    if [[ $? -eq 0 ]]; then
        print_success "数据库创建成功！"

        # 验证创建结果
        print_step "验证数据库创建结果..."

        local verify_result
        verify_result=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT datname, datcollate, datctype FROM pg_database WHERE datname LIKE 'saascontrol_%' ORDER BY datname;" 2>&1)

        if [[ $? -eq 0 ]]; then
            print_success "数据库验证成功"
            echo "$verify_result"
        else
            print_warning "数据库验证失败，但创建可能成功"
        fi

        return 0
    else
        print_error "数据库创建失败"
        return 1
    fi
}

# 创建Schema
create_database_schema() {
    print_step "为所有数据库创建表结构..."

    local databases=("saascontrol_dev_pro1" "saascontrol_dev_pro2" "saascontrol_stage_pro1" "saascontrol_stage_pro2" "saascontrol_prod_pro1" "saascontrol_prod_pro2")
    local schema_file="scripts/database/saascontrol-schema.sql"

    if [[ ! -f "$schema_file" ]]; then
        print_error "Schema文件不存在: $schema_file"
        return 1
    fi

    local success_count=0
    for db in "${databases[@]}"; do
        print_info "为数据库 $db 创建表结构..."

        PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$db" -f "$schema_file" >/dev/null 2>&1

        if [[ $? -eq 0 ]]; then
            print_success "✅ $db - Schema创建成功"
            ((success_count++))
        else
            print_error "❌ $db - Schema创建失败"
        fi
    done

    print_info "Schema创建完成: $success_count/${#databases[@]} 成功"

    if [[ $success_count -eq ${#databases[@]} ]]; then
        return 0
    else
        return 1
    fi
}

# 主执行函数
main() {
    print_header "SaaS Control Deck - 字符集兼容性修复部署"

    echo "🎯 目标: 修复字符集冲突并部署数据库架构"
    echo "🌐 PostgreSQL服务器: $POSTGRES_HOST:$POSTGRES_PORT"
    echo "👤 管理员用户: $POSTGRES_USER"
    echo "📊 数据库数量: 6个 (dev/stage/prod × pro1/pro2)"
    echo "🔧 修复内容: 自动检测和适配字符集排序规则"
    echo ""

    read -p "是否继续修复并部署？ (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi

    # 1. 检查并修复字符集配置
    check_and_fix_collation

    # 2. 执行修复后的部署
    if execute_fixed_deployment; then
        print_success "数据库部署成功！"

        # 3. 创建表结构
        if create_database_schema; then
            print_success "完整部署成功！"

            print_header "部署完成总结"
            echo "✅ 数据库创建: 成功"
            echo "✅ 用户权限配置: 成功"
            echo "✅ 表结构创建: 成功"
            echo "🎉 SaaS Control Deck三环境数据库架构部署完成！"
            echo ""
            echo "📋 下一步操作："
            echo "   1. 在Firebase Studio中配置数据库连接"
            echo "   2. 复制 .env.saascontrol-multi-environment 到 .env"
            echo "   3. 启动后端服务验证连接"

        else
            print_warning "数据库创建成功，但部分Schema创建失败"
            echo "可以稍后手动创建表结构"
        fi
    else
        print_error "数据库部署失败"
        exit 1
    fi
}

# 脚本入口
main "$@"