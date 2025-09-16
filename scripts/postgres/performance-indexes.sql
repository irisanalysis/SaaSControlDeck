-- =============================================================================
-- Performance Optimized Index Strategy for SaaS Control Deck
-- =============================================================================
-- Comprehensive indexing strategy for AI workloads and multi-environment setup
-- Target: High-performance queries with minimal index maintenance overhead

-- =============================================================================
-- 1. USER MANAGEMENT INDEXES
-- =============================================================================

-- Primary user lookup indexes (frequently accessed)
CREATE INDEX CONCURRENTLY idx_users_email_active 
    ON users(email) 
    WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_users_username_active 
    ON users(username) 
    WHERE is_active = true;

-- User session management (critical for performance)
CREATE INDEX CONCURRENTLY idx_user_sessions_token_active 
    ON user_sessions(session_token) 
    WHERE is_active = true;

CREATE INDEX CONCURRENTLY idx_user_sessions_user_expires 
    ON user_sessions(user_id, expires_at) 
    WHERE is_active = true;

-- Cleanup expired sessions (maintenance optimization)
CREATE INDEX CONCURRENTLY idx_user_sessions_cleanup 
    ON user_sessions(expires_at) 
    WHERE is_active = false;

-- User profile optimization
CREATE INDEX CONCURRENTLY idx_user_profiles_user_updated 
    ON user_profiles(user_id, updated_at);

-- =============================================================================
-- 2. PROJECT MANAGEMENT INDEXES
-- =============================================================================

-- Project ownership and access patterns
CREATE INDEX CONCURRENTLY idx_projects_owner_status 
    ON projects(owner_id, status);

CREATE INDEX CONCURRENTLY idx_projects_status_updated 
    ON projects(status, updated_at);

-- Project member access optimization (multi-tenant queries)
CREATE INDEX CONCURRENTLY idx_project_members_user_role 
    ON project_members(user_id, role);

CREATE INDEX CONCURRENTLY idx_project_members_project_permissions 
    ON project_members(project_id, permissions) 
    USING GIN;

-- Project settings optimization (JSON queries)
CREATE INDEX CONCURRENTLY idx_project_settings_key_value 
    ON project_settings(project_id, setting_key) 
    INCLUDE (setting_value);

-- =============================================================================
-- 3. AI TASK MANAGEMENT INDEXES (Performance Critical)
-- =============================================================================

-- High-frequency AI task queries
CREATE INDEX CONCURRENTLY idx_ai_tasks_status_priority 
    ON ai_tasks(status, created_at) 
    WHERE status IN ('pending', 'running');

CREATE INDEX CONCURRENTLY idx_ai_tasks_project_status_created 
    ON ai_tasks(project_id, status, created_at);

CREATE INDEX CONCURRENTLY idx_ai_tasks_user_type_status 
    ON ai_tasks(user_id, task_type, status);

-- AI task completion tracking
CREATE INDEX CONCURRENTLY idx_ai_tasks_completed 
    ON ai_tasks(completed_at, task_type) 
    WHERE completed_at IS NOT NULL;

-- AI task duration analysis
CREATE INDEX CONCURRENTLY idx_ai_tasks_duration 
    ON ai_tasks((EXTRACT(EPOCH FROM (completed_at - started_at)))) 
    WHERE started_at IS NOT NULL AND completed_at IS NOT NULL;

-- AI input/output data optimization (GIN for JSON queries)
CREATE INDEX CONCURRENTLY idx_ai_tasks_input_data 
    ON ai_tasks USING GIN (input_data);

CREATE INDEX CONCURRENTLY idx_ai_tasks_output_data 
    ON ai_tasks USING GIN (output_data);

-- Error analysis index
CREATE INDEX CONCURRENTLY idx_ai_tasks_errors 
    ON ai_tasks(task_type, updated_at) 
    WHERE error_message IS NOT NULL;

-- =============================================================================
-- 4. AI MODELS AND RESULTS INDEXES
-- =============================================================================

-- Active model lookup
CREATE INDEX CONCURRENTLY idx_ai_models_active 
    ON ai_models(model_type, version) 
    WHERE is_active = true;

-- AI results performance tracking
CREATE INDEX CONCURRENTLY idx_ai_results_task_confidence 
    ON ai_results(task_id, confidence_score DESC, processing_time_ms);

CREATE INDEX CONCURRENTLY idx_ai_results_model_performance 
    ON ai_results(model_id, processing_time_ms, confidence_score);

-- Time-series optimization for AI results
CREATE INDEX CONCURRENTLY idx_ai_results_created_performance 
    ON ai_results(created_at, processing_time_ms);

-- =============================================================================
-- 5. DATA ANALYSIS INDEXES
-- =============================================================================

-- Data source management
CREATE INDEX CONCURRENTLY idx_data_sources_project_type 
    ON data_sources(project_id, source_type) 
    WHERE is_active = true;

-- Analysis job queue optimization
CREATE INDEX CONCURRENTLY idx_analysis_jobs_status_priority 
    ON analysis_jobs(status, created_at) 
    WHERE status IN ('queued', 'running');

CREATE INDEX CONCURRENTLY idx_analysis_jobs_project_type 
    ON analysis_jobs(project_id, job_type, status);

-- Analysis job duration tracking
CREATE INDEX CONCURRENTLY idx_analysis_jobs_duration 
    ON analysis_jobs((EXTRACT(EPOCH FROM (completed_at - started_at)))) 
    WHERE started_at IS NOT NULL AND completed_at IS NOT NULL;

-- Analysis configuration optimization (JSON)
CREATE INDEX CONCURRENTLY idx_analysis_jobs_config 
    ON analysis_jobs USING GIN (analysis_config);

-- Analysis results optimization
CREATE INDEX CONCURRENTLY idx_analysis_results_job_type 
    ON analysis_results(job_id, result_type);

CREATE INDEX CONCURRENTLY idx_analysis_results_data 
    ON analysis_results USING GIN (result_data);

-- =============================================================================
-- 6. FILE STORAGE INDEXES
-- =============================================================================

-- File access patterns
CREATE INDEX CONCURRENTLY idx_file_storage_project_user 
    ON file_storage(project_id, user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_file_storage_type_size 
    ON file_storage(mime_type, file_size);

-- Storage type optimization
CREATE INDEX CONCURRENTLY idx_file_storage_storage_path 
    ON file_storage(storage_type, file_path);

-- File metadata search (JSON optimization)
CREATE INDEX CONCURRENTLY idx_file_metadata_search 
    ON file_metadata(file_id, metadata_key) 
    INCLUDE (metadata_value);

CREATE INDEX CONCURRENTLY idx_file_metadata_values 
    ON file_metadata USING GIN (metadata_value);

-- =============================================================================
-- 7. SYSTEM MONITORING INDEXES (High Volume)
-- =============================================================================

-- System logs time-series optimization (partitioned table support)
CREATE INDEX CONCURRENTLY idx_system_logs_service_time 
    ON system_logs(service_name, created_at DESC);

CREATE INDEX CONCURRENTLY idx_system_logs_level_time 
    ON system_logs(log_level, created_at DESC) 
    WHERE log_level IN ('ERROR', 'CRITICAL');

-- User activity tracking
CREATE INDEX CONCURRENTLY idx_system_logs_user_activity 
    ON system_logs(user_id, created_at DESC) 
    WHERE user_id IS NOT NULL;

-- Log search optimization (GIN for JSON metadata)
CREATE INDEX CONCURRENTLY idx_system_logs_metadata 
    ON system_logs USING GIN (metadata);

-- Performance metrics time-series (optimized for monitoring queries)
CREATE INDEX CONCURRENTLY idx_performance_metrics_service_metric 
    ON performance_metrics(service_name, metric_name, recorded_at DESC);

CREATE INDEX CONCURRENTLY idx_performance_metrics_time_value 
    ON performance_metrics(recorded_at DESC, metric_value) 
    INCLUDE (service_name, metric_name);

-- Performance alerting optimization
CREATE INDEX CONCURRENTLY idx_performance_metrics_alerts 
    ON performance_metrics(service_name, metric_name, metric_value) 
    WHERE recorded_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours');

-- Tags optimization for monitoring
CREATE INDEX CONCURRENTLY idx_performance_metrics_tags 
    ON performance_metrics USING GIN (tags);

-- =============================================================================
-- 8. AUDIT TRAIL INDEXES
-- =============================================================================

-- Audit trail access patterns
CREATE INDEX CONCURRENTLY idx_audit_trails_user_action 
    ON audit_trails(user_id, action, created_at DESC);

CREATE INDEX CONCURRENTLY idx_audit_trails_resource 
    ON audit_trails(resource_type, resource_id, created_at DESC);

-- Security audit optimization
CREATE INDEX CONCURRENTLY idx_audit_trails_security 
    ON audit_trails(ip_address, created_at DESC, action) 
    WHERE action LIKE '%login%' OR action LIKE '%auth%';

-- Change tracking optimization (JSON)
CREATE INDEX CONCURRENTLY idx_audit_trails_changes 
    ON audit_trails USING GIN (old_values, new_values);

-- =============================================================================
-- 9. SPECIALIZED INDEXES FOR AI WORKLOADS
-- =============================================================================

-- Text search optimization (full-text search on AI content)
CREATE INDEX CONCURRENTLY idx_ai_tasks_fulltext 
    ON ai_tasks USING GIN (to_tsvector('english', task_name || ' ' || COALESCE(error_message, '')));

-- AI task correlation analysis
CREATE INDEX CONCURRENTLY idx_ai_tasks_correlation 
    ON ai_tasks(project_id, task_type, status, (EXTRACT(HOUR FROM created_at)));

-- Performance percentile tracking
CREATE INDEX CONCURRENTLY idx_ai_results_percentiles 
    ON ai_results(model_id, processing_time_ms) 
    WHERE processing_time_ms IS NOT NULL;

-- =============================================================================
-- 10. COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =============================================================================

-- Dashboard overview queries (multi-table optimization)
CREATE INDEX CONCURRENTLY idx_dashboard_overview 
    ON ai_tasks(user_id, status, task_type, created_at DESC) 
    INCLUDE (completed_at);

-- Project analytics optimization
CREATE INDEX CONCURRENTLY idx_project_analytics 
    ON ai_tasks(project_id, status, task_type) 
    INCLUDE (started_at, completed_at, error_message);

-- User activity summary
CREATE INDEX CONCURRENTLY idx_user_activity_summary 
    ON ai_tasks(user_id, created_at DESC) 
    INCLUDE (task_type, status);

-- =============================================================================
-- 11. PARTIAL INDEXES FOR SPECIFIC CONDITIONS
-- =============================================================================

-- Active sessions only (reduces index size significantly)
CREATE INDEX CONCURRENTLY idx_active_sessions_only 
    ON user_sessions(user_id, session_token) 
    WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP;

-- Recent AI tasks (hot data optimization)
CREATE INDEX CONCURRENTLY idx_recent_ai_tasks 
    ON ai_tasks(status, task_type, created_at DESC) 
    WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '7 days');

-- Failed tasks analysis
CREATE INDEX CONCURRENTLY idx_failed_tasks_analysis 
    ON ai_tasks(task_type, created_at DESC, error_message) 
    WHERE status = 'failed' AND error_message IS NOT NULL;

-- =============================================================================
-- 12. COVERING INDEXES (Include Clause Optimization)
-- =============================================================================

-- Covering index for AI task status queries
CREATE INDEX CONCURRENTLY idx_ai_tasks_status_covering 
    ON ai_tasks(project_id, status) 
    INCLUDE (task_name, created_at, updated_at);

-- Covering index for user profile queries
CREATE INDEX CONCURRENTLY idx_user_profile_covering 
    ON users(email) 
    INCLUDE (username, is_active, created_at) 
    WHERE is_active = true;

-- =============================================================================
-- 13. FUNCTIONAL INDEXES FOR COMPUTED VALUES
-- =============================================================================

-- Task duration functional index
CREATE INDEX CONCURRENTLY idx_task_duration_functional 
    ON ai_tasks((EXTRACT(EPOCH FROM (completed_at - started_at)))) 
    WHERE completed_at IS NOT NULL AND started_at IS NOT NULL;

-- Lowercase email search
CREATE INDEX CONCURRENTLY idx_users_email_lower 
    ON users(LOWER(email)) 
    WHERE is_active = true;

-- File size categories
CREATE INDEX CONCURRENTLY idx_file_size_category 
    ON file_storage((CASE 
        WHEN file_size < 1048576 THEN 'small'
        WHEN file_size < 52428800 THEN 'medium' 
        ELSE 'large' 
    END));

-- =============================================================================
-- 14. INDEXES FOR MAINTENANCE OPERATIONS
-- =============================================================================

-- Vacuum optimization (dead tuple cleanup)
CREATE INDEX CONCURRENTLY idx_maintenance_cleanup_logs 
    ON system_logs(created_at) 
    WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '30 days');

CREATE INDEX CONCURRENTLY idx_maintenance_cleanup_metrics 
    ON performance_metrics(recorded_at) 
    WHERE recorded_at < (CURRENT_TIMESTAMP - INTERVAL '90 days');

-- Archive optimization
CREATE INDEX CONCURRENTLY idx_archive_old_tasks 
    ON ai_tasks(created_at) 
    WHERE status IN ('completed', 'failed', 'cancelled') 
    AND created_at < (CURRENT_TIMESTAMP - INTERVAL '1 year');

-- =============================================================================
-- INDEX MAINTENANCE QUERIES
-- =============================================================================

-- Check index usage statistics
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes 
-- ORDER BY idx_scan DESC;

-- Find unused indexes (run periodically)
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) AS size
-- FROM pg_stat_user_indexes 
-- WHERE idx_scan = 0 
--   AND schemaname = 'public'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- Check index bloat
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) AS size,
--     pg_size_pretty(pg_total_relation_size(indexrelid)) AS total_size
-- FROM pg_stat_user_indexes 
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- =============================================================================
-- NOTES FOR INDEX STRATEGY
-- =============================================================================

/*
1. All indexes created with CONCURRENTLY to avoid blocking operations
2. Partial indexes used where appropriate to reduce size and improve performance  
3. GIN indexes for JSON columns to support complex queries
4. Covering indexes (INCLUDE clause) to avoid table lookups
5. Functional indexes for computed values and transformations
6. Time-series optimization for monitoring data
7. Multi-column indexes ordered by selectivity (most selective first)
8. Specialized indexes for AI workload patterns
9. Maintenance indexes for cleanup operations
10. Regular monitoring of index usage and performance impact

Index Naming Convention:
- idx_<table>_<columns>_<condition>
- Use descriptive names that indicate purpose
- Include condition information for partial indexes
*/