-- ===========================================
-- SaaS Control Deck 表结构创建脚本
-- ===========================================
-- 注意: 本脚本需要在每个数据库中分别执行
-- 执行顺序: 第三步 - 创建表结构和索引
-- ===========================================

\echo '创建SaaS Control Deck数据表结构...'

-- ===========================================
-- 1. 用户管理模块
-- ===========================================

\echo '创建用户管理相关表...'

-- 用户基本信息表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_length CHECK (char_length(username) >= 3),
    CONSTRAINT users_failed_attempts_range CHECK (failed_login_attempts >= 0 AND failed_login_attempts <= 10)
);

COMMENT ON TABLE users IS '用户基本信息表 - 存储用户账户和认证信息';
COMMENT ON COLUMN users.email IS '用户邮箱地址，用于登录和通知';
COMMENT ON COLUMN users.username IS '用户名，显示名称';
COMMENT ON COLUMN users.password_hash IS '加密后的密码哈希值';
COMMENT ON COLUMN users.failed_login_attempts IS '连续登录失败次数，用于账户锁定';
COMMENT ON COLUMN users.locked_until IS '账户锁定截止时间';

-- 用户详细资料表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    bio TEXT,
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    theme_preference VARCHAR(20) DEFAULT 'system',
    notification_preferences JSONB DEFAULT '{
        "email_notifications": true,
        "push_notifications": true,
        "marketing_emails": false,
        "security_alerts": true
    }',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id)
);

COMMENT ON TABLE user_profiles IS '用户详细资料表 - 存储用户个人信息和偏好设置';
COMMENT ON COLUMN user_profiles.display_name IS '显示名称，优先级高于 first_name + last_name';
COMMENT ON COLUMN user_profiles.notification_preferences IS 'JSON格式的通知偏好设置';

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    device_id VARCHAR(255),
    device_name VARCHAR(100),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    location JSONB,
    is_active BOOLEAN DEFAULT true,
    
    CONSTRAINT sessions_expires_check CHECK (expires_at > CURRENT_TIMESTAMP)
);

COMMENT ON TABLE user_sessions IS '用户会话表 - 管理用户登录会话和访问令牌';
COMMENT ON COLUMN user_sessions.device_id IS '设备唯一标识符';
COMMENT ON COLUMN user_sessions.location IS 'JSON格式的地理位置信息';

-- ===========================================
-- 2. 项目管理模块
-- ===========================================

\echo '创建项目管理相关表...'

-- 项目信息表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active',
    visibility VARCHAR(20) DEFAULT 'private',
    settings JSONB DEFAULT '{
        "ai_features_enabled": true,
        "data_retention_days": 90,
        "auto_backup_enabled": true,
        "collaboration_enabled": true
    }',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT projects_status_check CHECK (status IN ('active', 'inactive', 'archived')),
    CONSTRAINT projects_visibility_check CHECK (visibility IN ('private', 'internal', 'public')),
    CONSTRAINT projects_slug_format CHECK (slug ~* '^[a-z0-9-]+$')
);

COMMENT ON TABLE projects IS '项目信息表 - 管理用户的数据分析项目';
COMMENT ON COLUMN projects.slug IS '项目 URL 友好的标识符';
COMMENT ON COLUMN projects.settings IS 'JSON格式的项目配置设置';

-- 项目成员表
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    permissions JSONB DEFAULT '{
        "read": true,
        "write": false,
        "admin": false,
        "delete": false
    }',
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(project_id, user_id),
    CONSTRAINT project_members_role_check CHECK (role IN ('owner', 'admin', 'editor', 'viewer', 'member'))
);

COMMENT ON TABLE project_members IS '项目成员表 - 管理项目成员和权限';
COMMENT ON COLUMN project_members.permissions IS 'JSON格式的成员权限设置';

-- 项目设置表
CREATE TABLE project_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    setting_category VARCHAR(50) NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB,
    is_encrypted BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, setting_category, setting_key)
);

COMMENT ON TABLE project_settings IS '项目设置表 - 存储项目的细粒度配置';
COMMENT ON COLUMN project_settings.setting_category IS '设置分类，如 ai, data, security';

-- ===========================================
-- 3. AI任务管理模块
-- ===========================================

\echo '创建AI任务管理相关表...'

-- AI模型表
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',
    pricing_info JSONB,
    performance_metrics JSONB,
    is_active BOOLEAN DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(name, version),
    CONSTRAINT ai_models_provider_check CHECK (provider IN ('openai', 'google', 'anthropic', 'huggingface', 'custom'))
);

COMMENT ON TABLE ai_models IS 'AI模型表 - 管理可用的AI模型和其配置';
COMMENT ON COLUMN ai_models.capabilities IS 'JSON格式的模型能力描述';

-- AI任务表
CREATE TABLE ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    model_id UUID REFERENCES ai_models(id),
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    progress_percentage INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    tokens_consumed INTEGER,
    cost_usd DECIMAL(10,4),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT ai_tasks_status_check CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'timeout')),
    CONSTRAINT ai_tasks_priority_check CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT ai_tasks_progress_check CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
);

COMMENT ON TABLE ai_tasks IS 'AI任务表 - 记录AI处理任务的执行情况';
COMMENT ON COLUMN ai_tasks.tokens_consumed IS '消耗的token数量';
COMMENT ON COLUMN ai_tasks.cost_usd IS 'AI调用成本（美元）';

-- AI结果表
CREATE TABLE ai_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id) ON DELETE CASCADE,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB,
    confidence_score DECIMAL(5,4),
    quality_metrics JSONB,
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT ai_results_confidence_check CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

COMMENT ON TABLE ai_results IS 'AI结果表 - 存储AI任务的输出结果';
COMMENT ON COLUMN ai_results.quality_metrics IS 'JSON格式的结果质量指标';

-- ===========================================
-- 4. 数据分析模块
-- ===========================================

\echo '创建数据分析相关表...'

-- 数据源表
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(100) NOT NULL,
    connection_config JSONB,
    schema_info JSONB,
    data_preview JSONB,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'never_synced',
    sync_error_message TEXT,
    row_count BIGINT,
    size_bytes BIGINT,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT data_sources_type_check CHECK (source_type IN ('csv', 'json', 'database', 'api', 'spreadsheet', 'other')),
    CONSTRAINT data_sources_sync_status_check CHECK (sync_status IN ('never_synced', 'syncing', 'synced', 'failed'))
);

COMMENT ON TABLE data_sources IS '数据源表 - 管理项目中的各种数据源';
COMMENT ON COLUMN data_sources.connection_config IS 'JSON格式的连接配置信息';

-- 数据分析作业表
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    description TEXT,
    data_source_ids UUID[] DEFAULT '{}',
    analysis_config JSONB,
    status VARCHAR(50) DEFAULT 'queued',
    priority VARCHAR(20) DEFAULT 'normal',
    progress_percentage INTEGER DEFAULT 0,
    result_summary JSONB,
    error_details JSONB,
    resource_usage JSONB,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT analysis_jobs_status_check CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT analysis_jobs_priority_check CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

COMMENT ON TABLE analysis_jobs IS '数据分析作业表 - 管理数据分析任务';
COMMENT ON COLUMN analysis_jobs.resource_usage IS 'JSON格式的资源使用情况';

-- 分析结果表
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    result_name VARCHAR(255) NOT NULL,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB,
    visualization_config JSONB,
    file_path TEXT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(255),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE analysis_results IS '分析结果表 - 存储数据分析的结果';
COMMENT ON COLUMN analysis_results.is_primary IS '是否为主要结果';

-- ===========================================
-- 5. 文件存储模块
-- ===========================================

\echo '创建文件存储相关表...'

-- 文件存储表
CREATE TABLE file_storage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) UNIQUE,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(255),
    storage_type VARCHAR(50) DEFAULT 'local',
    storage_config JSONB,
    upload_status VARCHAR(50) DEFAULT 'completed',
    download_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT file_storage_type_check CHECK (storage_type IN ('local', 's3', 'minio', 'gcs')),
    CONSTRAINT file_storage_status_check CHECK (upload_status IN ('uploading', 'completed', 'failed', 'deleted')),
    CONSTRAINT file_storage_size_check CHECK (file_size > 0)
);

COMMENT ON TABLE file_storage IS '文件存储表 - 管理上传和存储的文件';
COMMENT ON COLUMN file_storage.file_hash IS 'SHA-256文件哈希值，用于重复检测';

-- 文件元数据表
CREATE TABLE file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_storage(id) ON DELETE CASCADE,
    metadata_category VARCHAR(50) NOT NULL,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value JSONB,
    extracted_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(file_id, metadata_category, metadata_key)
);

COMMENT ON TABLE file_metadata IS '文件元数据表 - 存储文件的元数据信息';
COMMENT ON COLUMN file_metadata.extracted_by IS '元数据提取方式或工具';

-- ===========================================
-- 6. 系统监控模块
-- ===========================================

\echo '创建系统监控相关表...'

-- 系统日志表
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id),
    session_id UUID,
    request_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT system_logs_level_check CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
) PARTITION BY RANGE (created_at);

COMMENT ON TABLE system_logs IS '系统日志表 - 记录系统运行日志';
COMMENT ON COLUMN system_logs.request_id IS '请求链跟踪ID';

-- 性能指标表
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (service_name, metric_name, recorded_at)
) PARTITION BY RANGE (recorded_at);

COMMENT ON TABLE performance_metrics IS '性能指标表 - 记录系统性能指标';

-- 审计跟踪表
CREATE TABLE audit_trails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    request_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX (user_id, created_at),
    INDEX (resource_type, resource_id, created_at)
) PARTITION BY RANGE (created_at);

COMMENT ON TABLE audit_trails IS '审计跟踪表 - 记录系统操作审计日志';

-- ===========================================
-- 7. 通知系统
-- ===========================================

\echo '创建通知系统相关表...'

-- 通知表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'normal',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT notifications_priority_check CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    INDEX (user_id, is_read, created_at)
);

COMMENT ON TABLE notifications IS '通知表 - 管理用户通知';

-- ===========================================
-- 8. 创建更新时间触发器
-- ===========================================

\echo '创建更新时间触发器...'

-- 更新 updated_at 字段的通用函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_settings_updated_at BEFORE UPDATE ON project_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_models_updated_at BEFORE UPDATE ON ai_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_tasks_updated_at BEFORE UPDATE ON ai_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_jobs_updated_at BEFORE UPDATE ON analysis_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_file_storage_updated_at BEFORE UPDATE ON file_storage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

\echo '表结构创建完成！请继续执行索引创建脚本。';

-- ===========================================
-- 执行说明
-- ===========================================
/*
对每个数据库执行此脚本:

# 开发环境
psql -h 47.79.87.199 -U saasctl_dev_pro1_user -d saascontrol_dev_pro1 -f 03-create-table-structure.sql
psql -h 47.79.87.199 -U saasctl_dev_pro2_user -d saascontrol_dev_pro2 -f 03-create-table-structure.sql

# 测试环境
psql -h 47.79.87.199 -U saasctl_stage_pro1_user -d saascontrol_stage_pro1 -f 03-create-table-structure.sql
psql -h 47.79.87.199 -U saasctl_stage_pro2_user -d saascontrol_stage_pro2 -f 03-create-table-structure.sql

# 生产环境
psql -h 47.79.87.199 -U saasctl_prod_pro1_user -d saascontrol_prod_pro1 -f 03-create-table-structure.sql
psql -h 47.79.87.199 -U saasctl_prod_pro2_user -d saascontrol_prod_pro2 -f 03-create-table-structure.sql

下一步:
执行 04-create-indexes.sql 创建索引
*/