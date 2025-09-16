-- ===========================================
-- SaaS Control Deck 索引创建脚本
-- ===========================================
-- 注意: 本脚本需要在每个数据库中分别执行
-- 执行顺序: 第四步 - 创建性能优化索引
-- ===========================================

\echo '创建SaaS Control Deck数据库索引...'

-- ===========================================
-- 1. 用户管理模块索引
-- ===========================================

\echo '创建用户管理相关索引...'

-- users 表索引
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY idx_users_is_active ON users(is_active);
CREATE INDEX CONCURRENTLY idx_users_is_verified ON users(is_verified);
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);
CREATE INDEX CONCURRENTLY idx_users_last_login_at ON users(last_login_at);
CREATE INDEX CONCURRENTLY idx_users_failed_attempts ON users(failed_login_attempts) WHERE failed_login_attempts > 0;
CREATE INDEX CONCURRENTLY idx_users_locked ON users(locked_until) WHERE locked_until IS NOT NULL;

-- user_profiles 表索引
CREATE INDEX CONCURRENTLY idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX CONCURRENTLY idx_user_profiles_display_name ON user_profiles(display_name);
CREATE INDEX CONCURRENTLY idx_user_profiles_language ON user_profiles(language);
CREATE INDEX CONCURRENTLY idx_user_profiles_timezone ON user_profiles(timezone);

-- user_sessions 表索引
CREATE INDEX CONCURRENTLY idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX CONCURRENTLY idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX CONCURRENTLY idx_user_sessions_refresh_token ON user_sessions(refresh_token);
CREATE INDEX CONCURRENTLY idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX CONCURRENTLY idx_user_sessions_device_id ON user_sessions(device_id);
CREATE INDEX CONCURRENTLY idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX CONCURRENTLY idx_user_sessions_ip_address ON user_sessions(ip_address);

-- 复合索引 - 用户模块
CREATE INDEX CONCURRENTLY idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX CONCURRENTLY idx_users_active_verified ON users(is_active, is_verified);

-- ===========================================
-- 2. 项目管理模块索引
-- ===========================================

\echo '创建项目管理相关索引...'

-- projects 表索引
CREATE INDEX CONCURRENTLY idx_projects_owner_id ON projects(owner_id);
CREATE INDEX CONCURRENTLY idx_projects_slug ON projects(slug);
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
CREATE INDEX CONCURRENTLY idx_projects_visibility ON projects(visibility);
CREATE INDEX CONCURRENTLY idx_projects_created_at ON projects(created_at);
CREATE INDEX CONCURRENTLY idx_projects_updated_at ON projects(updated_at);
CREATE INDEX CONCURRENTLY idx_projects_archived_at ON projects(archived_at);
CREATE INDEX CONCURRENTLY idx_projects_tags ON projects USING GIN(tags);

-- project_members 表索引
CREATE INDEX CONCURRENTLY idx_project_members_project_id ON project_members(project_id);
CREATE INDEX CONCURRENTLY idx_project_members_user_id ON project_members(user_id);
CREATE INDEX CONCURRENTLY idx_project_members_role ON project_members(role);
CREATE INDEX CONCURRENTLY idx_project_members_joined_at ON project_members(joined_at);
CREATE INDEX CONCURRENTLY idx_project_members_last_activity ON project_members(last_activity_at);

-- project_settings 表索引
CREATE INDEX CONCURRENTLY idx_project_settings_project_id ON project_settings(project_id);
CREATE INDEX CONCURRENTLY idx_project_settings_category ON project_settings(setting_category);
CREATE INDEX CONCURRENTLY idx_project_settings_key ON project_settings(setting_key);

-- 复合索引 - 项目模块
CREATE INDEX CONCURRENTLY idx_projects_owner_status ON projects(owner_id, status);
CREATE INDEX CONCURRENTLY idx_project_members_project_role ON project_members(project_id, role);
CREATE INDEX CONCURRENTLY idx_project_settings_project_category ON project_settings(project_id, setting_category);

-- ===========================================
-- 3. AI任务管理模块索引
-- ===========================================

\echo '创建AI任务管理相关索引...'

-- ai_models 表索引
CREATE INDEX CONCURRENTLY idx_ai_models_name ON ai_models(name);
CREATE INDEX CONCURRENTLY idx_ai_models_version ON ai_models(version);
CREATE INDEX CONCURRENTLY idx_ai_models_type ON ai_models(model_type);
CREATE INDEX CONCURRENTLY idx_ai_models_provider ON ai_models(provider);
CREATE INDEX CONCURRENTLY idx_ai_models_is_active ON ai_models(is_active);
CREATE INDEX CONCURRENTLY idx_ai_models_is_deprecated ON ai_models(is_deprecated);
CREATE INDEX CONCURRENTLY idx_ai_models_created_at ON ai_models(created_at);

-- ai_tasks 表索引
CREATE INDEX CONCURRENTLY idx_ai_tasks_project_id ON ai_tasks(project_id);
CREATE INDEX CONCURRENTLY idx_ai_tasks_user_id ON ai_tasks(user_id);
CREATE INDEX CONCURRENTLY idx_ai_tasks_model_id ON ai_tasks(model_id);
CREATE INDEX CONCURRENTLY idx_ai_tasks_task_type ON ai_tasks(task_type);
CREATE INDEX CONCURRENTLY idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX CONCURRENTLY idx_ai_tasks_priority ON ai_tasks(priority);
CREATE INDEX CONCURRENTLY idx_ai_tasks_created_at ON ai_tasks(created_at);
CREATE INDEX CONCURRENTLY idx_ai_tasks_started_at ON ai_tasks(started_at);
CREATE INDEX CONCURRENTLY idx_ai_tasks_completed_at ON ai_tasks(completed_at);
CREATE INDEX CONCURRENTLY idx_ai_tasks_updated_at ON ai_tasks(updated_at);

-- ai_results 表索引
CREATE INDEX CONCURRENTLY idx_ai_results_task_id ON ai_results(task_id);
CREATE INDEX CONCURRENTLY idx_ai_results_result_type ON ai_results(result_type);
CREATE INDEX CONCURRENTLY idx_ai_results_created_at ON ai_results(created_at);
CREATE INDEX CONCURRENTLY idx_ai_results_confidence_score ON ai_results(confidence_score);

-- 复合索引 - AI模块
CREATE INDEX CONCURRENTLY idx_ai_tasks_project_status ON ai_tasks(project_id, status);
CREATE INDEX CONCURRENTLY idx_ai_tasks_user_status ON ai_tasks(user_id, status);
CREATE INDEX CONCURRENTLY idx_ai_tasks_status_priority ON ai_tasks(status, priority);
CREATE INDEX CONCURRENTLY idx_ai_models_provider_active ON ai_models(provider, is_active);

-- 部分索引 - AI模块
CREATE INDEX CONCURRENTLY idx_ai_tasks_pending ON ai_tasks(id, created_at) WHERE status = 'pending';
CREATE INDEX CONCURRENTLY idx_ai_tasks_running ON ai_tasks(id, started_at) WHERE status = 'running';
CREATE INDEX CONCURRENTLY idx_ai_tasks_high_priority ON ai_tasks(id, created_at) WHERE priority = 'high';

-- ===========================================
-- 4. 数据分析模块索引
-- ===========================================

\echo '创建数据分析相关索引...'

-- data_sources 表索引
CREATE INDEX CONCURRENTLY idx_data_sources_project_id ON data_sources(project_id);
CREATE INDEX CONCURRENTLY idx_data_sources_source_type ON data_sources(source_type);
CREATE INDEX CONCURRENTLY idx_data_sources_sync_status ON data_sources(sync_status);
CREATE INDEX CONCURRENTLY idx_data_sources_is_active ON data_sources(is_active);
CREATE INDEX CONCURRENTLY idx_data_sources_created_by ON data_sources(created_by);
CREATE INDEX CONCURRENTLY idx_data_sources_created_at ON data_sources(created_at);
CREATE INDEX CONCURRENTLY idx_data_sources_last_sync ON data_sources(last_sync_at);
CREATE INDEX CONCURRENTLY idx_data_sources_size ON data_sources(size_bytes);

-- analysis_jobs 表索引
CREATE INDEX CONCURRENTLY idx_analysis_jobs_project_id ON analysis_jobs(project_id);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_user_id ON analysis_jobs(user_id);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_job_type ON analysis_jobs(job_type);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_priority ON analysis_jobs(priority);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_created_at ON analysis_jobs(created_at);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_scheduled_at ON analysis_jobs(scheduled_at);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_started_at ON analysis_jobs(started_at);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_completed_at ON analysis_jobs(completed_at);

-- analysis_results 表索引
CREATE INDEX CONCURRENTLY idx_analysis_results_job_id ON analysis_results(job_id);
CREATE INDEX CONCURRENTLY idx_analysis_results_result_type ON analysis_results(result_type);
CREATE INDEX CONCURRENTLY idx_analysis_results_created_at ON analysis_results(created_at);
CREATE INDEX CONCURRENTLY idx_analysis_results_is_primary ON analysis_results(is_primary);
CREATE INDEX CONCURRENTLY idx_analysis_results_file_size ON analysis_results(file_size_bytes);

-- 复合索引 - 数据分析模块
CREATE INDEX CONCURRENTLY idx_data_sources_project_active ON data_sources(project_id, is_active);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_project_status ON analysis_jobs(project_id, status);
CREATE INDEX CONCURRENTLY idx_analysis_jobs_user_status ON analysis_jobs(user_id, status);

-- ===========================================
-- 5. 文件存储模块索引
-- ===========================================

\echo '创建文件存储相关索引...'

-- file_storage 表索引
CREATE INDEX CONCURRENTLY idx_file_storage_project_id ON file_storage(project_id);
CREATE INDEX CONCURRENTLY idx_file_storage_user_id ON file_storage(user_id);
CREATE INDEX CONCURRENTLY idx_file_storage_file_hash ON file_storage(file_hash);
CREATE INDEX CONCURRENTLY idx_file_storage_mime_type ON file_storage(mime_type);
CREATE INDEX CONCURRENTLY idx_file_storage_storage_type ON file_storage(storage_type);
CREATE INDEX CONCURRENTLY idx_file_storage_upload_status ON file_storage(upload_status);
CREATE INDEX CONCURRENTLY idx_file_storage_is_public ON file_storage(is_public);
CREATE INDEX CONCURRENTLY idx_file_storage_created_at ON file_storage(created_at);
CREATE INDEX CONCURRENTLY idx_file_storage_expires_at ON file_storage(expires_at);
CREATE INDEX CONCURRENTLY idx_file_storage_file_size ON file_storage(file_size);
CREATE INDEX CONCURRENTLY idx_file_storage_download_count ON file_storage(download_count);

-- file_metadata 表索引
CREATE INDEX CONCURRENTLY idx_file_metadata_file_id ON file_metadata(file_id);
CREATE INDEX CONCURRENTLY idx_file_metadata_category ON file_metadata(metadata_category);
CREATE INDEX CONCURRENTLY idx_file_metadata_key ON file_metadata(metadata_key);
CREATE INDEX CONCURRENTLY idx_file_metadata_extracted_by ON file_metadata(extracted_by);
CREATE INDEX CONCURRENTLY idx_file_metadata_created_at ON file_metadata(created_at);

-- 复合索引 - 文件存储模块
CREATE INDEX CONCURRENTLY idx_file_storage_project_status ON file_storage(project_id, upload_status);
CREATE INDEX CONCURRENTLY idx_file_storage_user_type ON file_storage(user_id, mime_type);
CREATE INDEX CONCURRENTLY idx_file_metadata_file_category ON file_metadata(file_id, metadata_category);

-- ===========================================
-- 6. 系统监控模块索引
-- ===========================================

\echo '创建系统监控相关索引...'

-- 为分区表创建分区 (日志表按月分区)
-- 当前月份分区
CREATE TABLE IF NOT EXISTS system_logs_y2025m01 PARTITION OF system_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    
CREATE TABLE IF NOT EXISTS system_logs_y2025m02 PARTITION OF system_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    
CREATE TABLE IF NOT EXISTS system_logs_y2025m03 PARTITION OF system_logs
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- system_logs 分区表索引
CREATE INDEX CONCURRENTLY idx_system_logs_service_name ON system_logs(service_name);
CREATE INDEX CONCURRENTLY idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX CONCURRENTLY idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX CONCURRENTLY idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX CONCURRENTLY idx_system_logs_session_id ON system_logs(session_id);
CREATE INDEX CONCURRENTLY idx_system_logs_request_id ON system_logs(request_id);
CREATE INDEX CONCURRENTLY idx_system_logs_ip_address ON system_logs(ip_address);

-- 为性能指标表创建分区
CREATE TABLE IF NOT EXISTS performance_metrics_y2025m01 PARTITION OF performance_metrics
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    
CREATE TABLE IF NOT EXISTS performance_metrics_y2025m02 PARTITION OF performance_metrics
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    
CREATE TABLE IF NOT EXISTS performance_metrics_y2025m03 PARTITION OF performance_metrics
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- performance_metrics 分区表索引
CREATE INDEX CONCURRENTLY idx_performance_metrics_service_name ON performance_metrics(service_name);
CREATE INDEX CONCURRENTLY idx_performance_metrics_metric_name ON performance_metrics(metric_name);
CREATE INDEX CONCURRENTLY idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);
CREATE INDEX CONCURRENTLY idx_performance_metrics_metric_value ON performance_metrics(metric_value);

-- 为审计跟踪表创建分区
CREATE TABLE IF NOT EXISTS audit_trails_y2025m01 PARTITION OF audit_trails
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    
CREATE TABLE IF NOT EXISTS audit_trails_y2025m02 PARTITION OF audit_trails
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    
CREATE TABLE IF NOT EXISTS audit_trails_y2025m03 PARTITION OF audit_trails
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- audit_trails 分区表索引
CREATE INDEX CONCURRENTLY idx_audit_trails_user_id ON audit_trails(user_id);
CREATE INDEX CONCURRENTLY idx_audit_trails_action ON audit_trails(action);
CREATE INDEX CONCURRENTLY idx_audit_trails_resource_type ON audit_trails(resource_type);
CREATE INDEX CONCURRENTLY idx_audit_trails_resource_id ON audit_trails(resource_id);
CREATE INDEX CONCURRENTLY idx_audit_trails_created_at ON audit_trails(created_at);
CREATE INDEX CONCURRENTLY idx_audit_trails_ip_address ON audit_trails(ip_address);
CREATE INDEX CONCURRENTLY idx_audit_trails_session_id ON audit_trails(session_id);

-- 复合索引 - 系统监控模块
CREATE INDEX CONCURRENTLY idx_system_logs_service_level_time ON system_logs(service_name, log_level, created_at);
CREATE INDEX CONCURRENTLY idx_performance_metrics_service_metric_time ON performance_metrics(service_name, metric_name, recorded_at);
CREATE INDEX CONCURRENTLY idx_audit_trails_user_created_at ON audit_trails(user_id, created_at);
CREATE INDEX CONCURRENTLY idx_audit_trails_resource_created_at ON audit_trails(resource_type, resource_id, created_at);

-- ===========================================
-- 7. 通知系统索引
-- ===========================================

\echo '创建通知系统相关索引...'

-- notifications 表索引
CREATE INDEX CONCURRENTLY idx_notifications_user_id ON notifications(user_id);
CREATE INDEX CONCURRENTLY idx_notifications_type ON notifications(type);
CREATE INDEX CONCURRENTLY idx_notifications_is_read ON notifications(is_read);
CREATE INDEX CONCURRENTLY idx_notifications_priority ON notifications(priority);
CREATE INDEX CONCURRENTLY idx_notifications_created_at ON notifications(created_at);
CREATE INDEX CONCURRENTLY idx_notifications_expires_at ON notifications(expires_at);
CREATE INDEX CONCURRENTLY idx_notifications_read_at ON notifications(read_at);

-- 复合索引 - 通知系统
CREATE INDEX CONCURRENTLY idx_notifications_user_read_created ON notifications(user_id, is_read, created_at);
CREATE INDEX CONCURRENTLY idx_notifications_user_priority ON notifications(user_id, priority);
CREATE INDEX CONCURRENTLY idx_notifications_type_priority ON notifications(type, priority);

-- 部分索引 - 通知系统
CREATE INDEX CONCURRENTLY idx_notifications_unread ON notifications(user_id, created_at) WHERE is_read = false;
CREATE INDEX CONCURRENTLY idx_notifications_high_priority ON notifications(user_id, created_at) WHERE priority IN ('high', 'urgent');
CREATE INDEX CONCURRENTLY idx_notifications_unexpired ON notifications(user_id, created_at) WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP;

-- ===========================================
-- 8. JSON 字段索引 (高级索引)
-- ===========================================

\echo '创建 JSON 字段索引...'

-- projects.settings JSON 索引
CREATE INDEX CONCURRENTLY idx_projects_settings_ai_enabled ON projects USING GIN((settings->'ai_features_enabled'));
CREATE INDEX CONCURRENTLY idx_projects_settings_backup_enabled ON projects USING GIN((settings->'auto_backup_enabled'));

-- user_profiles.notification_preferences JSON 索引
CREATE INDEX CONCURRENTLY idx_user_profiles_email_notifications ON user_profiles USING GIN((notification_preferences->'email_notifications'));

-- ai_tasks.input_data 和 output_data JSON 索引 (需要时才创建，避免过度索引)
-- CREATE INDEX CONCURRENTLY idx_ai_tasks_input_data ON ai_tasks USING GIN(input_data);
-- CREATE INDEX CONCURRENTLY idx_ai_tasks_output_data ON ai_tasks USING GIN(output_data);

-- system_logs.metadata JSON 索引 (根据具体查询需要创建)
-- CREATE INDEX CONCURRENTLY idx_system_logs_metadata ON system_logs USING GIN(metadata);

-- ===========================================
-- 9. 全文搜索索引 (可选)
-- ===========================================

\echo '创建全文搜索索引...'

-- 创建全文搜索配置
CREATE TEXT SEARCH CONFIGURATION saascontrol_search (COPY = english);

-- 项目名称和描述的全文搜索
CREATE INDEX CONCURRENTLY idx_projects_fulltext_search 
    ON projects 
    USING GIN(to_tsvector('saascontrol_search', COALESCE(name, '') || ' ' || COALESCE(description, '')));

-- 用户资料的全文搜索
CREATE INDEX CONCURRENTLY idx_user_profiles_fulltext_search 
    ON user_profiles 
    USING GIN(to_tsvector('saascontrol_search', 
        COALESCE(display_name, '') || ' ' || 
        COALESCE(first_name, '') || ' ' || 
        COALESCE(last_name, '') || ' ' || 
        COALESCE(bio, '')
    ));

-- AI任务名称的全文搜索
CREATE INDEX CONCURRENTLY idx_ai_tasks_fulltext_search 
    ON ai_tasks 
    USING GIN(to_tsvector('saascontrol_search', 
        COALESCE(task_name, '') || ' ' || 
        COALESCE(error_message, '')
    ));

-- ===========================================
-- 10. 索引维护和优化脚本
-- ===========================================

\echo '创建索引维护函数...'

-- 创建索引使用统计函数
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE (
    schemaname text,
    tablename text,
    indexname text,
    num_rows bigint,
    table_size text,
    index_size text,
    unique_indexes integer,
    number_of_scans bigint,
    tuples_read bigint,
    tuples_fetched bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname::text,
        s.tablename::text,
        s.indexname::text,
        pg_stat_get_tuples_inserted(c.oid) + pg_stat_get_tuples_updated(c.oid) + pg_stat_get_tuples_deleted(c.oid) as num_rows,
        pg_size_pretty(pg_total_relation_size(c.oid))::text as table_size,
        pg_size_pretty(pg_relation_size(i.indexrelid))::text as index_size,
        CASE WHEN ix.indisunique THEN 1 ELSE 0 END as unique_indexes,
        s.idx_scan as number_of_scans,
        s.idx_tup_read as tuples_read,
        s.idx_tup_fetch as tuples_fetched
    FROM pg_stat_user_indexes s
    JOIN pg_class c ON c.oid = s.relid
    JOIN pg_index ix ON ix.indexrelid = s.indexrelid
    JOIN pg_class i ON i.oid = s.indexrelid
    ORDER BY s.idx_scan ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_index_usage_stats() IS '获取数据库索引使用统计信息';

-- 创建未使用索引检测函数
CREATE OR REPLACE FUNCTION find_unused_indexes()
RETURNS TABLE (
    schemaname text,
    tablename text,
    indexname text,
    index_size text,
    index_scans bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname::text,
        s.tablename::text,
        s.indexname::text,
        pg_size_pretty(pg_relation_size(s.indexrelid))::text,
        s.idx_scan
    FROM pg_stat_user_indexes s
    JOIN pg_index i ON i.indexrelid = s.indexrelid
    WHERE s.idx_scan < 10 -- 使用次数少于10次
        AND NOT i.indisunique -- 非唯一索引
        AND NOT i.indisprimary -- 非主键索引
    ORDER BY s.idx_scan ASC, pg_relation_size(s.indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_unused_indexes() IS '查找可能未使用的索引';

-- 创建索引重复检测函数
CREATE OR REPLACE FUNCTION find_duplicate_indexes()
RETURNS TABLE (
    size text,
    idx1 text,
    idx2 text,
    idx1_def text,
    idx2_def text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pg_size_pretty(pg_relation_size(i1.indexrelid))::text as size,
        i1.indexname::text as idx1,
        i2.indexname::text as idx2,
        pg_get_indexdef(i1.indexrelid)::text as idx1_def,
        pg_get_indexdef(i2.indexrelid)::text as idx2_def
    FROM pg_stat_user_indexes i1
    JOIN pg_stat_user_indexes i2 ON i1.relid = i2.relid 
        AND i1.indexrelid > i2.indexrelid
    JOIN pg_index idx1 ON idx1.indexrelid = i1.indexrelid
    JOIN pg_index idx2 ON idx2.indexrelid = i2.indexrelid
    WHERE idx1.indkey::text = idx2.indkey::text
        AND NOT idx1.indisunique
        AND NOT idx2.indisunique;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_duplicate_indexes() IS '查找重复的索引';

-- ===========================================
-- 11. 索引创建完成验证
-- ===========================================

\echo '验证索引创建结果...'

-- 统计所有表的索引数量
SELECT 
    schemaname,
    tablename,
    COUNT(*) as index_count,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
GROUP BY schemaname, tablename
ORDER BY index_count DESC;

-- 显示最大的索引
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 10;

\echo '索引创建完成！请继续执行数据库配置优化脚本。';

-- ===========================================
-- 执行说明
-- ===========================================
/*
对每个数据库执行此脚本:

# 开发环境
psql -h 47.79.87.199 -U saasctl_dev_pro1_user -d saascontrol_dev_pro1 -f 04-create-indexes.sql
psql -h 47.79.87.199 -U saasctl_dev_pro2_user -d saascontrol_dev_pro2 -f 04-create-indexes.sql

# 测试环境
psql -h 47.79.87.199 -U saasctl_stage_pro1_user -d saascontrol_stage_pro1 -f 04-create-indexes.sql
psql -h 47.79.87.199 -U saasctl_stage_pro2_user -d saascontrol_stage_pro2 -f 04-create-indexes.sql

# 生产环境
psql -h 47.79.87.199 -U saasctl_prod_pro1_user -d saascontrol_prod_pro1 -f 04-create-indexes.sql
psql -h 47.79.87.199 -U saasctl_prod_pro2_user -d saascontrol_prod_pro2 -f 04-create-indexes.sql

性能监控:
-- 查看索引使用情况
SELECT * FROM get_index_usage_stats();

-- 查找未使用的索引
SELECT * FROM find_unused_indexes();

-- 查找重复索引
SELECT * FROM find_duplicate_indexes();

下一步:
执行 05-database-configuration.sql 进行数据库参数优化
*/