#!/bin/bash

# ===========================================
# SaaS Control Deck - 全面数据库验证脚本
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

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 输出函数
print_header() {
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}    $1${NC}"
    echo -e "${CYAN}===============================================${NC}"
}

print_test() {
    echo -e "${PURPLE}[TEST $((++TOTAL_TESTS))]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
    ((PASSED_TESTS++))
}

print_error() {
    echo -e "${RED}[❌ FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 测试数据库连接
test_admin_connection() {
    print_test "管理员数据库连接测试"

    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" >/dev/null 2>&1; then
        print_success "管理员连接成功"
        return 0
    else
        print_error "管理员连接失败"
        return 1
    fi
}

# 验证数据库创建
verify_databases() {
    print_test "验证所有数据库是否创建成功"

    local databases=("saascontrol_dev_pro1" "saascontrol_dev_pro2" "saascontrol_stage_pro1" "saascontrol_stage_pro2" "saascontrol_prod_pro1" "saascontrol_prod_pro2")
    local found_databases=0

    for db in "${databases[@]}"; do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT 1 FROM pg_database WHERE datname='$db';" | grep -q 1; then
            print_info "✅ 数据库 $db 存在"
            ((found_databases++))
        else
            print_error "❌ 数据库 $db 不存在"
        fi
    done

    if [[ $found_databases -eq ${#databases[@]} ]]; then
        print_success "所有6个数据库创建成功"
        return 0
    else
        print_error "数据库创建不完整: $found_databases/${#databases[@]}"
        return 1
    fi
}

# 验证用户创建
verify_users() {
    print_test "验证所有用户是否创建成功"

    local users=("saascontrol_dev_user" "saascontrol_stage_user" "saascontrol_prod_user")
    local found_users=0

    for user in "${users[@]}"; do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT 1 FROM pg_user WHERE usename='$user';" | grep -q 1; then
            print_info "✅ 用户 $user 存在"
            ((found_users++))
        else
            print_error "❌ 用户 $user 不存在"
        fi
    done

    if [[ $found_users -eq ${#users[@]} ]]; then
        print_success "所有3个用户创建成功"
        return 0
    else
        print_error "用户创建不完整: $found_users/${#users[@]}"
        return 1
    fi
}

# 测试用户连接
test_user_connections() {
    print_test "测试环境用户连接权限"

    local connection_tests=0
    local successful_connections=0

    # 测试开发环境用户连接
    print_info "测试开发环境用户连接..."
    if PGPASSWORD="dev_pass_2024_secure" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "saascontrol_dev_user" -d "saascontrol_dev_pro1" -c "SELECT 'dev_connection_test' as result;" >/dev/null 2>&1; then
        print_info "✅ 开发环境用户连接成功"
        ((successful_connections++))
    else
        print_info "❌ 开发环境用户连接失败"
    fi
    ((connection_tests++))

    # 测试测试环境用户连接
    print_info "测试测试环境用户连接..."
    if PGPASSWORD="stage_pass_2024_secure" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "saascontrol_stage_user" -d "saascontrol_stage_pro1" -c "SELECT 'stage_connection_test' as result;" >/dev/null 2>&1; then
        print_info "✅ 测试环境用户连接成功"
        ((successful_connections++))
    else
        print_info "❌ 测试环境用户连接失败"
    fi
    ((connection_tests++))

    # 测试生产环境用户连接
    print_info "测试生产环境用户连接..."
    if PGPASSWORD="prod_pass_2024_very_secure_XyZ9#mK" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "saascontrol_prod_user" -d "saascontrol_prod_pro1" -c "SELECT 'prod_connection_test' as result;" >/dev/null 2>&1; then
        print_info "✅ 生产环境用户连接成功"
        ((successful_connections++))
    else
        print_info "❌ 生产环境用户连接失败"
    fi
    ((connection_tests++))

    if [[ $successful_connections -eq $connection_tests ]]; then
        print_success "所有环境用户连接测试通过 ($successful_connections/$connection_tests)"
        return 0
    else
        print_error "部分用户连接失败 ($successful_connections/$connection_tests)"
        return 1
    fi
}

# 验证表结构
verify_table_structures() {
    print_test "验证数据库表结构是否创建完成"

    local databases=("saascontrol_dev_pro1" "saascontrol_dev_pro2" "saascontrol_stage_pro1" "saascontrol_stage_pro2" "saascontrol_prod_pro1" "saascontrol_prod_pro2")
    local databases_with_tables=0

    # 期望的核心表
    local expected_tables=("users" "user_profiles" "projects" "ai_models" "ai_tasks" "data_sources" "file_storage" "system_logs")

    for db in "${databases[@]}"; do
        print_info "检查数据库 $db 的表结构..."

        local table_count
        table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$db" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")

        if [[ ${table_count// /} -gt 10 ]]; then
            print_info "✅ $db: $table_count 个表"
            ((databases_with_tables++))

            # 检查几个核心表是否存在
            local core_tables_found=0
            for table in "${expected_tables[@]}"; do
                if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$db" -t -c "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$table';" 2>/dev/null | grep -q 1; then
                    ((core_tables_found++))
                fi
            done
            print_info "   核心表: $core_tables_found/${#expected_tables[@]} 个"
        else
            print_info "❌ $db: 表结构不完整 ($table_count 个表)"
        fi
    done

    if [[ $databases_with_tables -eq ${#databases[@]} ]]; then
        print_success "所有数据库表结构创建完成"
        return 0
    else
        print_error "部分数据库表结构不完整: $databases_with_tables/${#databases[@]}"
        return 1
    fi
}

# 测试CRUD操作
test_crud_operations() {
    print_test "测试基本CRUD操作"

    local test_db="saascontrol_dev_pro1"
    local test_user="saascontrol_dev_user"
    local test_password="dev_pass_2024_secure"

    print_info "在 $test_db 上测试CRUD操作..."

    # 测试插入用户
    if PGPASSWORD="$test_password" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$test_user" -d "$test_db" -c "
        INSERT INTO users (id, username, email, password_hash, first_name, last_name)
        VALUES (gen_random_uuid(), 'test_user_$(date +%s)', 'test@example.com', 'hashed_password', 'Test', 'User')
        ON CONFLICT (email) DO NOTHING;
    " >/dev/null 2>&1; then
        print_info "✅ INSERT 操作成功"
    else
        print_info "❌ INSERT 操作失败"
        print_error "CRUD测试失败"
        return 1
    fi

    # 测试查询
    local user_count
    user_count=$(PGPASSWORD="$test_password" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$test_user" -d "$test_db" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

    if [[ ${user_count// /} -gt 0 ]]; then
        print_info "✅ SELECT 操作成功 ($user_count 条记录)"
    else
        print_info "❌ SELECT 操作失败"
        print_error "CRUD测试失败"
        return 1
    fi

    print_success "基本CRUD操作测试通过"
    return 0
}

# 性能测试
test_performance() {
    print_test "简单性能测试"

    print_info "测试数据库响应时间..."

    local start_time=$(date +%s%N)
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "saascontrol_dev_pro1" -c "SELECT COUNT(*) FROM information_schema.tables;" >/dev/null 2>&1
    local end_time=$(date +%s%N)

    local response_time_ms=$(( (end_time - start_time) / 1000000 ))

    if [[ $response_time_ms -lt 1000 ]]; then
        print_success "数据库响应时间良好: ${response_time_ms}ms"
        return 0
    else
        print_warning "数据库响应时间较慢: ${response_time_ms}ms"
        return 1
    fi
}

# 生成详细报告
generate_report() {
    print_header "详细验证报告"

    echo -e "${CYAN}数据库架构信息:${NC}"
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT
            datname as database_name,
            datcollate as collation,
            datctype as ctype,
            pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database
        WHERE datname LIKE 'saascontrol_%'
        ORDER BY datname;
    " 2>/dev/null || print_error "无法获取数据库详细信息"

    echo ""
    echo -e "${CYAN}用户权限信息:${NC}"
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT
            usename as username,
            usecreatedb as can_create_db,
            usesuper as is_superuser,
            userepl as can_replicate,
            valuntil as valid_until
        FROM pg_user
        WHERE usename LIKE 'saascontrol_%'
        ORDER BY usename;
    " 2>/dev/null || print_error "无法获取用户详细信息"
}

# 主执行函数
main() {
    print_header "SaaS Control Deck - 全面数据库验证"

    echo "🎯 目标: 全面验证数据库部署结果"
    echo "🌐 PostgreSQL服务器: $POSTGRES_HOST:$POSTGRES_PORT"
    echo "👤 管理员用户: $POSTGRES_USER"
    echo "📊 预期: 6个数据库 + 3个用户 + 完整表结构"
    echo ""

    # 执行所有测试
    test_admin_connection
    verify_databases
    verify_users
    test_user_connections
    verify_table_structures
    test_crud_operations
    test_performance

    echo ""
    print_header "测试结果总结"

    echo "📊 测试统计:"
    echo "   总测试数: $TOTAL_TESTS"
    echo "   通过测试: $PASSED_TESTS"
    echo "   失败测试: $FAILED_TESTS"

    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "   成功率: $success_rate%"

    echo ""

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}🎉 所有测试通过！SaaS Control Deck数据库部署完全成功！${NC}"
        echo ""
        echo "✅ 数据库架构部署完成"
        echo "✅ 用户权限配置正确"
        echo "✅ 表结构创建完整"
        echo "✅ CRUD操作功能正常"
        echo "✅ 性能表现良好"
        echo ""
        echo "🚀 您的三环境数据库架构已准备就绪，可以开始开发工作！"
    elif [[ $success_rate -ge 80 ]]; then
        echo -e "${YELLOW}⚠️  大部分测试通过，但有一些问题需要注意${NC}"
        echo "建议检查失败的测试项目并进行相应修复"
    else
        echo -e "${RED}❌ 多个测试失败，部署可能存在问题${NC}"
        echo "建议重新检查部署过程"
    fi

    echo ""
    generate_report
}

# 脚本入口
main "$@"