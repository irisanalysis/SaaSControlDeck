#!/bin/bash

# ===========================================
# SaaS Control Deck - 现有PostgreSQL数据库集成脚本
# ===========================================
# 用于验证和配置现有PostgreSQL数据库以支持SaaS Control Deck

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 检查必要的环境变量
check_env_vars() {
    log_info "检查环境变量..."
    
    local required_vars=(
        "EXISTING_POSTGRES_CONTAINER"
        "EXISTING_POSTGRES_HOST"
        "EXISTING_POSTGRES_USER"
        "EXISTING_POSTGRES_PASSWORD"
        "SAASCONTROL_DB_PRO1"
        "SAASCONTROL_DB_PRO2"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必要的环境变量："
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_error "请在 .env.existing-db 文件中配置这些变量"
        exit 1
    fi
    
    log_success "所有必要的环境变量已配置"
}

# 检查现有PostgreSQL容器状态
check_postgres_container() {
    log_info "检查现有PostgreSQL容器状态..."
    
    if ! docker ps --filter "name=$EXISTING_POSTGRES_CONTAINER" --format "table {{.Names}}" | grep -q "$EXISTING_POSTGRES_CONTAINER"; then
        log_error "PostgreSQL容器 '$EXISTING_POSTGRES_CONTAINER' 未运行"
        log_info "可用的PostgreSQL容器："
        docker ps --filter "ancestor=postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
        exit 1
    fi
    
    log_success "PostgreSQL容器 '$EXISTING_POSTGRES_CONTAINER' 正在运行"
}

# 测试数据库连接
test_database_connection() {
    log_info "测试数据库连接..."
    
    local connection_test
    connection_test=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -c "SELECT version();" 2>&1) || {
        log_error "无法连接到PostgreSQL数据库"
        log_error "连接详情："
        log_error "  容器: $EXISTING_POSTGRES_CONTAINER"
        log_error "  用户: $EXISTING_POSTGRES_USER"
        log_error "  主机: $EXISTING_POSTGRES_HOST"
        log_error "错误信息: $connection_test"
        exit 1
    }
    
    log_success "数据库连接测试成功"
    echo "$connection_test" | head -n 1
}

# 检查数据库版本兼容性
check_postgres_version() {
    log_info "检查PostgreSQL版本兼容性..."
    
    local version_info
    version_info=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -t -c "SHOW server_version;" | xargs)
    
    local major_version
    major_version=$(echo "$version_info" | grep -oE '[0-9]+' | head -n 1)
    
    if [[ "$major_version" -lt 12 ]]; then
        log_warning "PostgreSQL版本 $version_info 可能与SaaS Control Deck不完全兼容"
        log_warning "推荐版本: PostgreSQL 12+ (当前版本: $major_version)"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "PostgreSQL版本 $version_info 兼容"
    fi
}

# 检查现有数据库
check_existing_databases() {
    log_info "检查现有数据库..."
    
    local existing_dbs
    existing_dbs=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;" | xargs)
    
    log_info "现有数据库: $existing_dbs"
    
    # 检查是否存在同名数据库
    if echo "$existing_dbs" | grep -qw "$SAASCONTROL_DB_PRO1"; then
        log_warning "数据库 '$SAASCONTROL_DB_PRO1' 已存在"
        read -p "是否覆盖现有数据库? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_warning "将覆盖数据库 '$SAASCONTROL_DB_PRO1'"
        else
            log_error "取消操作以避免覆盖现有数据"
            exit 1
        fi
    fi
    
    if echo "$existing_dbs" | grep -qw "$SAASCONTROL_DB_PRO2"; then
        log_warning "数据库 '$SAASCONTROL_DB_PRO2' 已存在"
        read -p "是否覆盖现有数据库? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_warning "将覆盖数据库 '$SAASCONTROL_DB_PRO2'"
        else
            log_error "取消操作以避免覆盖现有数据"
            exit 1
        fi
    fi
}

# 创建SaaS Control Deck数据库
create_databases() {
    log_info "创建SaaS Control Deck数据库..."
    
    # 创建Pro1数据库
    log_info "创建数据库: $SAASCONTROL_DB_PRO1"
    docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS $SAASCONTROL_DB_PRO1;"
    
    docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -c "CREATE DATABASE $SAASCONTROL_DB_PRO1 WITH 
            ENCODING='UTF8' 
            LC_COLLATE='en_US.UTF-8' 
            LC_CTYPE='en_US.UTF-8' 
            TEMPLATE=template0;"
    
    log_success "数据库 '$SAASCONTROL_DB_PRO1' 创建成功"
    
    # 创建Pro2数据库
    log_info "创建数据库: $SAASCONTROL_DB_PRO2"
    docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS $SAASCONTROL_DB_PRO2;"
    
    docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d postgres \
        -c "CREATE DATABASE $SAASCONTROL_DB_PRO2 WITH 
            ENCODING='UTF8' 
            LC_COLLATE='en_US.UTF-8' 
            LC_CTYPE='en_US.UTF-8' 
            TEMPLATE=template0;"
    
    log_success "数据库 '$SAASCONTROL_DB_PRO2' 创建成功"
}

# 创建数据库表结构
create_database_schema() {
    log_info "创建数据库表结构..."
    
    # 创建基本表结构的SQL
    local schema_sql="
    -- SaaS Control Deck 基本表结构
    
    -- 用户表
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        avatar_url TEXT,
        role VARCHAR(50) DEFAULT 'user',
        is_active BOOLEAN DEFAULT true,
        email_verified BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP WITH TIME ZONE
    );
    
    -- 项目表
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        settings JSONB DEFAULT '{}',
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- AI任务表
    CREATE TABLE IF NOT EXISTS ai_tasks (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        task_type VARCHAR(100) NOT NULL,
        task_name VARCHAR(255) NOT NULL,
        input_data JSONB,
        output_data JSONB,
        status VARCHAR(50) DEFAULT 'pending',
        progress INTEGER DEFAULT 0,
        error_message TEXT,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 文件存储表
    CREATE TABLE IF NOT EXISTS file_storage (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        filename VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        file_size BIGINT,
        mime_type VARCHAR(100),
        file_hash VARCHAR(64),
        metadata JSONB DEFAULT '{}',
        is_public BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 数据分析结果表
    CREATE TABLE IF NOT EXISTS analysis_results (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        analysis_type VARCHAR(100) NOT NULL,
        analysis_name VARCHAR(255) NOT NULL,
        input_data JSONB,
        results JSONB,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 系统日志表
    CREATE TABLE IF NOT EXISTS system_logs (
        id SERIAL PRIMARY KEY,
        level VARCHAR(20) NOT NULL,
        service_name VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        metadata JSONB DEFAULT '{}',
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 创建索引以提高查询性能
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
    CREATE INDEX IF NOT EXISTS idx_ai_tasks_project_id ON ai_tasks(project_id);
    CREATE INDEX IF NOT EXISTS idx_ai_tasks_user_id ON ai_tasks(user_id);
    CREATE INDEX IF NOT EXISTS idx_ai_tasks_status ON ai_tasks(status);
    CREATE INDEX IF NOT EXISTS idx_file_storage_project_id ON file_storage(project_id);
    CREATE INDEX IF NOT EXISTS idx_file_storage_user_id ON file_storage(user_id);
    CREATE INDEX IF NOT EXISTS idx_analysis_results_project_id ON analysis_results(project_id);
    CREATE INDEX IF NOT EXISTS idx_analysis_results_user_id ON analysis_results(user_id);
    CREATE INDEX IF NOT EXISTS idx_system_logs_service_name ON system_logs(service_name);
    CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
    
    -- 创建更新时间自动更新的触发器函数
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    \$\$ language 'plpgsql';
    
    -- 为相关表创建更新触发器
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
    CREATE TRIGGER update_projects_updated_at 
        BEFORE UPDATE ON projects 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_ai_tasks_updated_at ON ai_tasks;
    CREATE TRIGGER update_ai_tasks_updated_at 
        BEFORE UPDATE ON ai_tasks 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_file_storage_updated_at ON file_storage;
    CREATE TRIGGER update_file_storage_updated_at 
        BEFORE UPDATE ON file_storage 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_analysis_results_updated_at ON analysis_results;
    CREATE TRIGGER update_analysis_results_updated_at 
        BEFORE UPDATE ON analysis_results 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    "
    
    # 在Pro1数据库中创建表结构
    log_info "在数据库 '$SAASCONTROL_DB_PRO1' 中创建表结构..."
    echo "$schema_sql" | docker exec -i "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO1"
    
    log_success "数据库 '$SAASCONTROL_DB_PRO1' 表结构创建完成"
    
    # 在Pro2数据库中创建表结构
    log_info "在数据库 '$SAASCONTROL_DB_PRO2' 中创建表结构..."
    echo "$schema_sql" | docker exec -i "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO2"
    
    log_success "数据库 '$SAASCONTROL_DB_PRO2' 表结构创建完成"
}

# 插入测试数据
insert_test_data() {
    log_info "插入测试数据..."
    
    local test_data_sql="
    -- 插入测试用户
    INSERT INTO users (email, username, password_hash, full_name, role) 
    VALUES 
        ('admin@saascontrol.com', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LehnHY5E5bRjK8G6q', 'System Administrator', 'admin'),
        ('user@saascontrol.com', 'testuser', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LehnHY5E5bRjK8G6q', 'Test User', 'user')
    ON CONFLICT (email) DO NOTHING;
    
    -- 插入测试项目
    INSERT INTO projects (name, description, owner_id) 
    VALUES 
        ('Demo Project', 'SaaS Control Deck Demo Project', 1),
        ('AI Analysis Test', 'AI Analysis Testing Project', 2)
    ON CONFLICT DO NOTHING;
    
    -- 插入系统启动日志
    INSERT INTO system_logs (level, service_name, message, metadata) 
    VALUES 
        ('INFO', 'database', 'SaaS Control Deck database initialized successfully', '{\"version\": \"1.0.0\"}'),
        ('INFO', 'database', 'Test data inserted successfully', '{\"tables\": [\"users\", \"projects\"]}');
    "
    
    # 在Pro1数据库中插入测试数据
    log_info "在数据库 '$SAASCONTROL_DB_PRO1' 中插入测试数据..."
    echo "$test_data_sql" | docker exec -i "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO1"
    
    # 在Pro2数据库中插入测试数据
    log_info "在数据库 '$SAASCONTROL_DB_PRO2' 中插入测试数据..."
    echo "$test_data_sql" | docker exec -i "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO2"
    
    log_success "测试数据插入完成"
}

# 验证数据库集成
verify_integration() {
    log_info "验证数据库集成..."
    
    # 检查Pro1数据库
    local pro1_tables
    pro1_tables=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO1" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    
    # 检查Pro2数据库
    local pro2_tables
    pro2_tables=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO2" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    
    log_success "数据库验证结果："
    echo "  - $SAASCONTROL_DB_PRO1: $pro1_tables 个表"
    echo "  - $SAASCONTROL_DB_PRO2: $pro2_tables 个表"
    
    # 测试数据查询
    local user_count
    user_count=$(docker exec "$EXISTING_POSTGRES_CONTAINER" psql \
        -h localhost \
        -U "$EXISTING_POSTGRES_USER" \
        -d "$SAASCONTROL_DB_PRO1" \
        -t -c "SELECT COUNT(*) FROM users;" | xargs)
    
    log_success "测试数据验证："
    echo "  - 用户数量: $user_count"
}

# 生成连接配置报告
generate_connection_report() {
    log_info "生成数据库连接配置报告..."
    
    local report_file="/tmp/saascontrol-db-integration-report.txt"
    
    cat > "$report_file" << EOF
SaaS Control Deck - PostgreSQL数据库集成报告
===========================================
生成时间: $(date)
操作员: $(whoami)

数据库配置信息:
- PostgreSQL容器: $EXISTING_POSTGRES_CONTAINER
- PostgreSQL主机: $EXISTING_POSTGRES_HOST
- PostgreSQL端口: ${EXISTING_POSTGRES_PORT:-5432}
- PostgreSQL用户: $EXISTING_POSTGRES_USER
- 网络名称: ${EXISTING_POSTGRES_NETWORK:-未指定}

SaaS Control Deck数据库:
- Pro1数据库: $SAASCONTROL_DB_PRO1
- Pro2数据库: $SAASCONTROL_DB_PRO2

连接字符串示例:
- Pro1: postgresql+asyncpg://$EXISTING_POSTGRES_USER:***@$EXISTING_POSTGRES_HOST:${EXISTING_POSTGRES_PORT:-5432}/$SAASCONTROL_DB_PRO1
- Pro2: postgresql+asyncpg://$EXISTING_POSTGRES_USER:***@$EXISTING_POSTGRES_HOST:${EXISTING_POSTGRES_PORT:-5432}/$SAASCONTROL_DB_PRO2

部署建议:
1. 使用 docker-compose.existing-db.yml 进行部署
2. 确保 .env.existing-db 文件中的配置与此报告一致
3. 确保现有PostgreSQL容器在部署时正在运行
4. 使用以下命令部署:
   docker-compose -f docker/cloud-deployment/docker-compose.existing-db.yml up -d

集成状态: ✅ 成功
EOF
    
    cat "$report_file"
    
    if [[ -d "/opt/saascontroldeck" ]]; then
        cp "$report_file" "/opt/saascontroldeck/db-integration-report.txt"
        log_success "报告已保存到: /opt/saascontroldeck/db-integration-report.txt"
    fi
}

# 主函数
main() {
    log_info "开始SaaS Control Deck PostgreSQL数据库集成..."
    echo "======================================="
    
    # 加载环境变量
    if [[ -f ".env.existing-db" ]]; then
        log_info "加载环境变量文件: .env.existing-db"
        set -a
        source .env.existing-db
        set +a
    else
        log_error "环境变量文件 .env.existing-db 不存在"
        log_error "请先复制并配置 .env.existing-db 文件"
        exit 1
    fi
    
    # 执行集成步骤
    check_env_vars
    check_postgres_container
    test_database_connection
    check_postgres_version
    check_existing_databases
    create_databases
    create_database_schema
    insert_test_data
    verify_integration
    generate_connection_report
    
    echo "======================================="
    log_success "SaaS Control Deck PostgreSQL数据库集成完成！"
    log_info "现在可以使用 docker-compose.existing-db.yml 进行部署"
}

# 帮助信息
show_help() {
    cat << EOF
SaaS Control Deck - 现有PostgreSQL数据库集成脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    --check-only           仅检查数据库连接，不创建数据库
    --force                强制覆盖现有数据库（谨慎使用）
    --no-test-data         不插入测试数据

环境要求:
    - Docker已安装并运行
    - 现有PostgreSQL容器正在运行
    - 已配置 .env.existing-db 文件

示例:
    $0                     # 完整的数据库集成
    $0 --check-only        # 仅检查连接
    $0 --no-test-data      # 不插入测试数据

更多信息请参考: CLOUD_DEPLOYMENT_GUIDE.md
EOF
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --check-only)
        log_info "仅执行数据库连接检查..."
        source .env.existing-db 2>/dev/null || {
            log_error "请先配置 .env.existing-db 文件"
            exit 1
        }
        check_env_vars
        check_postgres_container
        test_database_connection
        check_postgres_version
        log_success "数据库连接检查完成"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac