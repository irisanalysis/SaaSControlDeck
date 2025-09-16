-- ===========================================
-- SaaS Control Deck 数据库初始化脚本
-- ===========================================
-- 为云服务器部署创建必要的数据库和用户

-- 创建应用数据库用户
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles 
      WHERE rolname = 'saasuser') THEN
      
      CREATE ROLE saasuser LOGIN PASSWORD 'CHANGE_DATABASE_PASSWORD_SECURE_PASSWORD_HERE';
   END IF;
END
$do$;

-- 创建主数据库
CREATE DATABASE saascontroldeck_production
    WITH OWNER = saasuser
         ENCODING = 'UTF8'
         LC_COLLATE = 'en_US.UTF-8'
         LC_CTYPE = 'en_US.UTF-8'
         TEMPLATE = template0;

-- 创建Pro1项目数据库
CREATE DATABASE ai_platform_pro1
    WITH OWNER = saasuser
         ENCODING = 'UTF8'
         LC_COLLATE = 'en_US.UTF-8'
         LC_CTYPE = 'en_US.UTF-8'
         TEMPLATE = template0;

-- 创建Pro2项目数据库
CREATE DATABASE ai_platform_pro2
    WITH OWNER = saasuser
         ENCODING = 'UTF8'
         LC_COLLATE = 'en_US.UTF-8'
         LC_CTYPE = 'en_US.UTF-8'
         TEMPLATE = template0;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE saascontroldeck_production TO saasuser;
GRANT ALL PRIVILEGES ON DATABASE ai_platform_pro1 TO saasuser;
GRANT ALL PRIVILEGES ON DATABASE ai_platform_pro2 TO saasuser;

-- 连接到主数据库并设置扩展
\c saascontroldeck_production

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 创建应用schema
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION saasuser;
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION saasuser;
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION saasuser;

-- 授予schema权限
GRANT ALL ON SCHEMA app TO saasuser;
GRANT ALL ON SCHEMA audit TO saasuser;
GRANT ALL ON SCHEMA analytics TO saasuser;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON TABLES TO saasuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON SEQUENCES TO saasuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO saasuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO saasuser;

-- 创建用户表
CREATE TABLE IF NOT EXISTS app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON app.users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON app.users(created_at);

-- 创建项目表
CREATE TABLE IF NOT EXISTS app.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    project_type VARCHAR(50) DEFAULT 'standard',
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建AI会话表
CREATE TABLE IF NOT EXISTS app.ai_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES app.projects(id) ON DELETE CASCADE,
    session_type VARCHAR(50) DEFAULT 'chat',
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建AI消息表
CREATE TABLE IF NOT EXISTS app.ai_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES app.ai_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    model VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建文件存储表
CREATE TABLE IF NOT EXISTS app.files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES app.projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    storage_path VARCHAR(500),
    storage_provider VARCHAR(50) DEFAULT 'minio',
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit.activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建分析表
CREATE TABLE IF NOT EXISTS analytics.usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app.users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES app.projects(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date DATE GENERATED ALWAYS AS (timestamp::DATE) STORED
);

-- 创建性能监控表
CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ai_sessions_user_id ON app.ai_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_project_id ON app.ai_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_session_id ON app.ai_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_created_at ON app.ai_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_files_user_id ON app.files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_project_id ON app.files(project_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON audit.activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON audit.activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_stats_date ON analytics.usage_stats(date);
CREATE INDEX IF NOT EXISTS idx_usage_stats_event_type ON analytics.usage_stats(event_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_service ON analytics.performance_metrics(service_name, metric_name, timestamp);

-- 创建GIN索引用于JSONB查询
CREATE INDEX IF NOT EXISTS idx_projects_settings_gin ON app.projects USING gin(settings);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_metadata_gin ON app.ai_sessions USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_ai_messages_metadata_gin ON app.ai_messages USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_files_metadata_gin ON app.files USING gin(metadata);

-- 创建更新时间戳的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器自动更新updated_at字段
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON app.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON app.projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_sessions_updated_at 
    BEFORE UPDATE ON app.ai_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建分区表（用于大数据量的日志表）
-- 按月分区activity_logs表
CREATE TABLE IF NOT EXISTS audit.activity_logs_template (
    LIKE audit.activity_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建当月分区
DO $$
DECLARE
    start_date DATE := date_trunc('month', CURRENT_DATE);
    end_date DATE := start_date + INTERVAL '1 month';
    partition_name TEXT := 'activity_logs_' || to_char(start_date, 'YYYY_MM');
BEGIN
    EXECUTE format('CREATE TABLE IF NOT EXISTS audit.%I PARTITION OF audit.activity_logs_template 
                    FOR VALUES FROM (%L) TO (%L)', 
                   partition_name, start_date, end_date);
END $$;

-- 创建视图用于常用查询
CREATE OR REPLACE VIEW app.user_stats AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.created_at,
    COUNT(DISTINCT p.id) as project_count,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(DISTINCT m.id) as message_count,
    MAX(u.last_login) as last_login
FROM app.users u
LEFT JOIN app.projects p ON u.id = p.owner_id
LEFT JOIN app.ai_sessions s ON u.id = s.user_id
LEFT JOIN app.ai_messages m ON s.id = m.session_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.created_at;

-- 创建管理员用户（默认密码需要在首次登录时更改）
INSERT INTO app.users (email, password_hash, first_name, last_name, role, is_verified)
VALUES (
    'admin@saascontroldeck.com',
    crypt('ChangeMe123!', gen_salt('bf')),
    'System',
    'Administrator',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- ===========================================
-- Pro1 数据库初始化
-- ===========================================
\c ai_platform_pro1

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector" IF EXISTS;

-- 创建schema
CREATE SCHEMA IF NOT EXISTS pro1 AUTHORIZATION saasuser;
GRANT ALL ON SCHEMA pro1 TO saasuser;

-- 创建Pro1特定的表结构
CREATE TABLE IF NOT EXISTS pro1.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    connection_params JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pro1.analysis_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_source_id UUID REFERENCES pro1.data_sources(id),
    job_type VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ===========================================
-- Pro2 数据库初始化
-- ===========================================
\c ai_platform_pro2

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector" IF EXISTS;

-- 创建schema
CREATE SCHEMA IF NOT EXISTS pro2 AUTHORIZATION saasuser;
GRANT ALL ON SCHEMA pro2 TO saasuser;

-- 创建Pro2特定的表结构
CREATE TABLE IF NOT EXISTS pro2.ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    version VARCHAR(50) DEFAULT '1.0',
    model_data BYTEA,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'training',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pro2.predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES pro2.ml_models(id),
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 完成数据库初始化
\c saascontroldeck_production

-- 记录初始化完成
INSERT INTO audit.activity_logs (action, resource_type, details) 
VALUES ('database_initialized', 'system', '{"databases": ["saascontroldeck_production", "ai_platform_pro1", "ai_platform_pro2"], "timestamp": "' || CURRENT_TIMESTAMP || '"}');