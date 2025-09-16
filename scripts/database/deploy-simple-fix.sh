#!/bin/bash

# ===========================================
# SaaS Control Deck - 简化修复部署脚本
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

# 根据服务器输出，直接使用正确的排序规则
COLLATE_RULE="en_US.utf8"

# 输出函数
print_header() {
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}    $1${NC}"
    echo -e "${CYAN}===============================================${NC}"
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

# 测试数据库连接
test_connection() {
    print_step "测试数据库连接..."

    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" >/dev/null 2>&1; then
        print_success "数据库连接成功"
        return 0
    else
        print_error "数据库连接失败"
        return 1
    fi
}

# 创建兼容的SQL脚本
create_fixed_sql() {
    local output_file="scripts/database/create-saascontrol-databases-simple-fix.sql"

    print_step "创建修复版SQL脚本..."
    print_info "使用排序规则: $COLLATE_RULE"

    cat > "$output_file" << EOF
-- ===========================================
-- SaaS Control Deck - 简化修复版数据库创建脚本
-- ===========================================
-- 目标PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT
-- 排序规则: $COLLATE_RULE (从服务器输出确认)
-- 用户: $POSTGRES_USER
-- 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

-- ===========================================
-- 1. 清理可能存在的数据库和用户
-- ===========================================

-- 删除可能存在的数据库
DROP DATABASE IF EXISTS saascontrol_dev_pro1;
DROP DATABASE IF EXISTS saascontrol_dev_pro2;
DROP DATABASE IF EXISTS saascontrol_stage_pro1;
DROP DATABASE IF EXISTS saascontrol_stage_pro2;
DROP DATABASE IF EXISTS saascontrol_prod_pro1;
DROP DATABASE IF EXISTS saascontrol_prod_pro2;

-- 删除可能存在的用户
DROP USER IF EXISTS saascontrol_dev_user;
DROP USER IF EXISTS saascontrol_stage_user;
DROP USER IF EXISTS saascontrol_prod_user;

-- ===========================================
-- 2. 创建三环境数据库
-- ===========================================

-- 开发环境数据库
CREATE DATABASE saascontrol_dev_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

CREATE DATABASE saascontrol_dev_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

-- 测试环境数据库
CREATE DATABASE saascontrol_stage_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

CREATE DATABASE saascontrol_stage_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

-- 生产环境数据库
CREATE DATABASE saascontrol_prod_pro1
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

CREATE DATABASE saascontrol_prod_pro2
    WITH OWNER = $POSTGRES_USER
    ENCODING = 'UTF8'
    LC_COLLATE = '$COLLATE_RULE'
    LC_CTYPE = '$COLLATE_RULE'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

-- ===========================================
-- 3. 创建环境专用用户
-- ===========================================

-- 开发环境用户 (较宽松权限)
CREATE USER saascontrol_dev_user WITH
    PASSWORD 'dev_pass_2024_secure'
    CREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 20;

-- 测试环境用户 (中等权限)
CREATE USER saascontrol_stage_user WITH
    PASSWORD 'stage_pass_2024_secure'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 15;

-- 生产环境用户 (严格权限)
CREATE USER saascontrol_prod_user WITH
    PASSWORD 'prod_pass_2024_very_secure_XyZ9#mK'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 50;

-- ===========================================
-- 4. 数据库权限分配
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
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro2 TO $POSTGRES_USER;

-- ===========================================
-- 5. 数据库注释和标识
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
    'SaaS Control Deck数据库创建完成! (简化修复版本)' as status,
    COUNT(*) as total_databases,
    '$(date '+%Y-%m-%d %H:%M:%S')' as created_at
FROM pg_database
WHERE datname LIKE 'saascontrol_%';
EOF

    print_success "修复版SQL脚本已创建: $output_file"
}

# 执行数据库创建
execute_database_creation() {
    local sql_file="scripts/database/create-saascontrol-databases-simple-fix.sql"

    print_step "执行数据库创建..."

    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file"; then
        print_success "数据库创建成功！"
        return 0
    else
        print_error "数据库创建失败"
        return 1
    fi
}

# 验证数据库创建结果
verify_databases() {
    print_step "验证数据库创建结果..."

    local verify_result
    verify_result=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT
        datname,
        datcollate,
        datctype
    FROM pg_database
    WHERE datname LIKE 'saascontrol_%'
    ORDER BY datname;" 2>&1)

    if [[ $? -eq 0 ]]; then
        print_success "数据库验证成功"
        echo "$verify_result"

        # 计算创建的数据库数量
        local db_count
        db_count=$(echo "$verify_result" | grep -c "saascontrol_")

        if [[ $db_count -eq 6 ]]; then
            print_success "✅ 所有6个数据库创建成功"
            return 0
        else
            print_warning "⚠️ 只创建了 $db_count/6 个数据库"
            return 1
        fi
    else
        print_error "数据库验证失败"
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
    for db in "\${databases[@]}"; do
        print_info "为数据库 $db 创建表结构..."

        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$db" -f "$schema_file" >/dev/null 2>&1; then
            print_success "✅ $db - Schema创建成功"
            ((success_count++))
        else
            print_error "❌ $db - Schema创建失败"
        fi
    done

    print_info "Schema创建完成: $success_count/\${#databases[@]} 成功"

    if [[ $success_count -eq \${#databases[@]} ]]; then
        return 0
    else
        return 1
    fi
}

# 生成环境配置文件
generate_env_config() {
    print_step "生成环境配置文件..."

    cat > ".env.deployed" << EOF
# SaaS Control Deck - 多环境数据库配置
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# 排序规则: $COLLATE_RULE

# ===========================================
# 开发环境配置 (Firebase Studio)
# ===========================================
DEV_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"
DEV_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"

# ===========================================
# 测试环境配置
# ===========================================
STAGE_DATABASE_URL="postgresql+asyncpg://saascontrol_stage_user:stage_pass_2024_secure@47.79.87.199:5432/saascontrol_stage_pro1"
STAGE_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_stage_user:stage_pass_2024_secure@47.79.87.199:5432/saascontrol_stage_pro2"

# ===========================================
# 生产环境配置
# ===========================================
PROD_DATABASE_URL="postgresql+asyncpg://saascontrol_prod_user:prod_pass_2024_very_secure_XyZ9#mK@47.79.87.199:5432/saascontrol_prod_pro1"
PROD_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_prod_user:prod_pass_2024_very_secure_XyZ9#mK@47.79.87.199:5432/saascontrol_prod_pro2"

# ===========================================
# Firebase Studio 默认配置
# ===========================================
DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"
SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"

# ===========================================
# 连接池配置
# ===========================================
DEV_MIN_POOL_SIZE=2
DEV_MAX_POOL_SIZE=10
STAGE_MIN_POOL_SIZE=3
STAGE_MAX_POOL_SIZE=15
PROD_MIN_POOL_SIZE=5
PROD_MAX_POOL_SIZE=50
EOF

    print_success "环境配置文件已生成: .env.deployed"
}

# 主执行函数
main() {
    print_header "SaaS Control Deck - 简化修复部署"

    echo "🎯 目标: 修复字符集冲突并部署数据库架构"
    echo "🌐 PostgreSQL服务器: $POSTGRES_HOST:$POSTGRES_PORT"
    echo "👤 管理员用户: $POSTGRES_USER"
    echo "📊 数据库数量: 6个 (dev/stage/prod × pro1/pro2)"
    echo "🔧 排序规则: $COLLATE_RULE (从服务器输出确认)"
    echo ""

    read -p "是否继续修复并部署？ (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi

    # 1. 测试连接
    if ! test_connection; then
        exit 1
    fi

    # 2. 创建修复版SQL
    create_fixed_sql

    # 3. 执行数据库创建
    if ! execute_database_creation; then
        exit 1
    fi

    # 4. 验证数据库创建
    if ! verify_databases; then
        print_warning "数据库验证有问题，但继续Schema创建"
    fi

    # 5. 创建表结构
    if create_database_schema; then
        print_success "完整部署成功！"

        # 6. 生成配置文件
        generate_env_config

        print_header "部署完成总结"
        echo "✅ 数据库创建: 成功"
        echo "✅ 用户权限配置: 成功"
        echo "✅ 表结构创建: 成功"
        echo "✅ 环境配置生成: 成功"
        echo "🎉 SaaS Control Deck三环境数据库架构部署完成！"
        echo ""
        echo "📋 下一步操作："
        echo "   1. 复制 .env.deployed 到 .env"
        echo "   2. 在Firebase Studio中配置数据库连接"
        echo "   3. 启动后端服务验证连接"

    else
        print_warning "数据库创建成功，但Schema创建有问题"
        echo "可以稍后手动创建表结构"
    fi
}

# 脚本入口
main "$@"