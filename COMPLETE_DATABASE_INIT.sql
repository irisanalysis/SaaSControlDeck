-- SaaS Control Deck 完整数据库初始化脚本
-- 执行环境: PostgreSQL 数据库管理工具 (pgAdmin, DBeaver, 等)
-- 数据库: saascontrol_dev_pro1
-- 执行用户: 需要具有CREATE权限的用户

-- ===========================================
-- 第一步：创建必要的扩展
-- ===========================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===========================================
-- 第二步：创建基础表结构
-- ===========================================

-- 用户主表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 用户配置表
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据集表
CREATE TABLE IF NOT EXISTS datasets (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(50),
    schema_info JSONB,
    upload_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- ===========================================
-- 第三步：添加数据源扩展字段
-- ===========================================

-- 为datasets表添加数据源功能扩展字段
ALTER TABLE datasets
ADD COLUMN IF NOT EXISTS type VARCHAR(50) NOT NULL DEFAULT 'csv' CHECK (type IN ('csv', 'json', 'excel', 'parquet')),
ADD COLUMN IF NOT EXISTS rows_count INTEGER,
ADD COLUMN IF NOT EXISTS columns_count INTEGER,
ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'uploading'
    CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64), -- SHA256 hash for duplicate detection
ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS encoding VARCHAR(50) DEFAULT 'utf-8',
ADD COLUMN IF NOT EXISTS delimiter VARCHAR(10), -- for CSV files
ADD COLUMN IF NOT EXISTS has_header BOOLEAN DEFAULT true, -- for CSV files
ADD COLUMN IF NOT EXISTS preview_data JSONB, -- cached preview data
ADD COLUMN IF NOT EXISTS error_details TEXT, -- error messages during processing
ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITH TIME ZONE;

-- ===========================================
-- 第四步：创建数据源管理相关表
-- ===========================================

-- 数据源列信息表
CREATE TABLE IF NOT EXISTS dataset_columns (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    column_index INTEGER NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- string, number, date, boolean, null
    is_nullable BOOLEAN DEFAULT true,
    unique_count INTEGER DEFAULT 0,
    missing_count INTEGER DEFAULT 0,
    min_value TEXT,
    max_value TEXT,
    avg_value NUMERIC,
    std_value NUMERIC,
    sample_values TEXT[], -- array of sample values
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据源文件上传会话表（用于跟踪上传进度）
CREATE TABLE IF NOT EXISTS upload_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_size BIGINT DEFAULT 0,
    chunk_size INTEGER DEFAULT 1048576, -- 1MB chunks
    total_chunks INTEGER NOT NULL,
    uploaded_chunks INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'processing', 'completed', 'failed', 'cancelled')),
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE SET NULL,
    temp_file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '24 hours'
);

-- 数据质量检查结果表
CREATE TABLE IF NOT EXISTS data_quality_checks (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
    check_type VARCHAR(100) NOT NULL, -- missing_values, duplicates, outliers, data_types
    column_name VARCHAR(255), -- null for dataset-level checks
    severity VARCHAR(20) NOT NULL DEFAULT 'info'
        CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    affected_rows INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 分析任务表
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 分析结果表
CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    result_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    file_references TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API调用日志表
CREATE TABLE IF NOT EXISTS api_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time INTEGER, -- 毫秒
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 系统指标表
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- 第五步：创建索引（性能优化）
-- ===========================================

-- 用户相关索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 用户配置索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- 会话索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- 项目索引
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- 数据集索引
CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_datasets_upload_status ON datasets(upload_status);
CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(type);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_file_hash ON datasets(file_hash);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at);

-- 数据集列信息索引
CREATE INDEX IF NOT EXISTS idx_dataset_columns_dataset_id ON dataset_columns(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_columns_name ON dataset_columns(column_name);
CREATE INDEX IF NOT EXISTS idx_dataset_columns_type ON dataset_columns(data_type);

-- 上传会话索引
CREATE INDEX IF NOT EXISTS idx_upload_sessions_user_id ON upload_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_status ON upload_sessions(status);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_created_at ON upload_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_expires_at ON upload_sessions(expires_at);

-- 数据质量检查索引
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_dataset_id ON data_quality_checks(dataset_id);
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_type ON data_quality_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_severity ON data_quality_checks(severity);

-- 分析任务索引
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analysis_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_project_id ON analysis_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_created_at ON analysis_tasks(created_at);

-- 分析结果索引
CREATE INDEX IF NOT EXISTS idx_analysis_results_task_id ON analysis_results(task_id);

-- API日志索引
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);

-- 系统指标索引
CREATE INDEX IF NOT EXISTS idx_system_metrics_service_name ON system_metrics(service_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);

-- ===========================================
-- 第六步：创建触发器函数
-- ===========================================

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ===========================================
-- 第七步：应用触发器
-- ===========================================

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_upload_sessions_updated_at BEFORE UPDATE ON upload_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- 第八步：插入示例数据（开发环境）
-- ===========================================

-- 创建示例用户（开发环境）
INSERT INTO users (email, password_hash, email_verified, is_active)
VALUES
    ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdeXhR8Qn/C9U/G', true, true)
ON CONFLICT (email) DO NOTHING;

-- 获取插入的用户ID并创建关联数据
DO $$
DECLARE
    admin_user_id BIGINT;
BEGIN
    SELECT id INTO admin_user_id FROM users WHERE email = 'admin@example.com';

    IF admin_user_id IS NOT NULL THEN
        -- 创建用户配置
        INSERT INTO user_profiles (user_id, first_name, last_name)
        VALUES (admin_user_id, 'Admin', 'User')
        ON CONFLICT DO NOTHING;

        -- 创建示例项目
        INSERT INTO projects (user_id, name, description, status)
        VALUES (admin_user_id, 'Demo Project', '示例项目用于测试数据管理功能', 'active')
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- ===========================================
-- 第九步：创建实用函数
-- ===========================================

-- 创建清理过期上传会话的函数
CREATE OR REPLACE FUNCTION cleanup_expired_upload_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM upload_sessions
    WHERE expires_at < NOW() AND status NOT IN ('completed');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 第十步：权限设置（如果需要）
-- ===========================================

-- 为开发用户授予必要权限（需要管理员权限执行）
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO saascontrol_dev_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO saascontrol_dev_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO saascontrol_dev_user;

-- ===========================================
-- 初始化完成确认
-- ===========================================

-- 显示创建的表
SELECT
    'SaaS Control Deck 数据库初始化完成!' as message,
    COUNT(*) as total_tables
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- 显示所有表
SELECT table_name as created_tables
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;