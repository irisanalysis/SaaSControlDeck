-- =============================================================================
-- PostgreSQL Performance Monitoring Queries for SaaS Control Deck
-- =============================================================================
-- Comprehensive monitoring and diagnostic queries for database performance
-- Optimized for multi-environment (dev/stage/prod) and multi-database setup

-- =============================================================================
-- 1. CONNECTION MONITORING
-- =============================================================================

-- Current database connections by environment/database
CREATE VIEW v_connection_status AS
SELECT 
    datname as database_name,
    state,
    application_name,
    COUNT(*) as connection_count,
    MIN(backend_start) as oldest_connection,
    MAX(backend_start) as newest_connection
FROM pg_stat_activity 
WHERE datname IN ('saascontrol_dev_pro1', 'saascontrol_dev_pro2', 
                  'saascontrol_stage_pro1', 'saascontrol_stage_pro2',
                  'saascontrol_prod_pro1', 'saascontrol_prod_pro2')
GROUP BY datname, state, application_name
ORDER BY datname, connection_count DESC;

-- Connection pool health check
CREATE VIEW v_connection_pool_health AS
SELECT 
    datname as database_name,
    COUNT(*) as total_connections,
    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
    COUNT(*) FILTER (WHERE state = 'idle in transaction (aborted)') as idle_aborted,
    ROUND(AVG(EXTRACT(EPOCH FROM (now() - backend_start))), 2) as avg_connection_age_seconds
FROM pg_stat_activity 
WHERE datname IS NOT NULL
GROUP BY datname
ORDER BY total_connections DESC;

-- Long-running connections alert
CREATE VIEW v_long_running_connections AS
SELECT 
    pid,
    datname as database_name,
    usename as username,
    application_name,
    client_addr,
    state,
    backend_start,
    state_change,
    query_start,
    EXTRACT(EPOCH FROM (now() - query_start)) as query_duration_seconds,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity 
WHERE state != 'idle' 
    AND query_start < (now() - interval '30 seconds')
    AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_duration_seconds DESC;

-- =============================================================================
-- 2. QUERY PERFORMANCE MONITORING
-- =============================================================================

-- Top slow queries (requires pg_stat_statements extension)
CREATE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    min_exec_time,
    max_exec_time,
    rows as total_rows,
    ROUND(rows::numeric/calls, 2) as avg_rows_per_call,
    ROUND(100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0), 2) as hit_percent
FROM pg_stat_statements 
WHERE query NOT LIKE '%pg_stat_%'
    AND query NOT LIKE '%pg_catalog%'
    AND calls > 10
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Query performance trends (hourly aggregation)
CREATE VIEW v_query_performance_trends AS
SELECT 
    DATE_TRUNC('hour', now()) as hour,
    COUNT(*) as total_queries,
    AVG(mean_exec_time) as avg_execution_time,
    MAX(max_exec_time) as max_execution_time,
    SUM(calls) as total_calls,
    SUM(total_exec_time) as total_execution_time
FROM pg_stat_statements
WHERE queryid IS NOT NULL
GROUP BY DATE_TRUNC('hour', now())
ORDER BY hour DESC
LIMIT 24;

-- Cache hit ratio monitoring
CREATE VIEW v_cache_hit_ratio AS
SELECT 
    'Buffer Cache' as cache_type,
    ROUND(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) as hit_ratio_percent
FROM pg_stat_database
WHERE datname IN ('saascontrol_dev_pro1', 'saascontrol_dev_pro2', 
                  'saascontrol_stage_pro1', 'saascontrol_stage_pro2',
                  'saascontrol_prod_pro1', 'saascontrol_prod_pro2')

UNION ALL

SELECT 
    'Index Cache' as cache_type,
    ROUND(100.0 * sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)), 2) as hit_ratio_percent
FROM pg_statio_user_indexes;

-- =============================================================================
-- 3. TABLE AND INDEX MONITORING
-- =============================================================================

-- Table size and activity monitoring
CREATE VIEW v_table_activity AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage statistics
CREATE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 10 THEN 'LOW_USAGE'
        WHEN idx_scan < 100 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Index bloat detection (approximate)
CREATE VIEW v_index_bloat AS
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    ROUND(100.0 * (pg_relation_size(indexrelid) - pg_relation_size(indexrelid, 'main')) / 
          NULLIF(pg_relation_size(indexrelid), 0), 2) as estimated_bloat_percent
FROM pg_stat_user_indexes 
WHERE pg_relation_size(indexrelid) > 1048576  -- Only indexes > 1MB
ORDER BY pg_relation_size(indexrelid) DESC;

-- =============================================================================
-- 4. AI WORKLOAD SPECIFIC MONITORING
-- =============================================================================

-- AI task performance metrics
CREATE VIEW v_ai_task_performance AS
SELECT 
    task_type,
    status,
    COUNT(*) as task_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MIN(EXTRACT(EPOCH FROM (completed_at - started_at))) as min_duration_seconds,
    MAX(EXTRACT(EPOCH FROM (completed_at - started_at))) as max_duration_seconds,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) as median_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) as p95_duration,
    COUNT(*) FILTER (WHERE error_message IS NOT NULL) as error_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE error_message IS NOT NULL) / COUNT(*), 2) as error_rate_percent
FROM ai_tasks 
WHERE started_at IS NOT NULL AND completed_at IS NOT NULL
    AND created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY task_type, status
ORDER BY task_count DESC;

-- AI model performance comparison
CREATE VIEW v_ai_model_performance AS
SELECT 
    m.name as model_name,
    m.version,
    COUNT(r.*) as result_count,
    AVG(r.processing_time_ms) as avg_processing_time_ms,
    AVG(r.confidence_score) as avg_confidence_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.processing_time_ms) as median_processing_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY r.processing_time_ms) as p95_processing_time_ms,
    MIN(r.created_at) as first_result,
    MAX(r.created_at) as last_result
FROM ai_models m
LEFT JOIN ai_results r ON m.id = r.model_id
WHERE m.is_active = true
    AND r.created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY m.id, m.name, m.version
ORDER BY result_count DESC;

-- AI workload resource consumption
CREATE VIEW v_ai_workload_resources AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    task_type,
    COUNT(*) as task_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status IN ('pending', 'running')) as active_count,
    AVG(CASE 
        WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (completed_at - started_at))
    END) as avg_duration_seconds
FROM ai_tasks
WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY DATE_TRUNC('hour', created_at), task_type
ORDER BY hour DESC, task_count DESC;

-- =============================================================================
-- 5. SYSTEM RESOURCE MONITORING
-- =============================================================================

-- Database size monitoring by environment
CREATE VIEW v_database_sizes AS
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size,
    pg_database_size(datname) as size_bytes,
    CASE 
        WHEN datname LIKE '%_dev_%' THEN 'development'
        WHEN datname LIKE '%_stage_%' THEN 'staging'
        WHEN datname LIKE '%_prod_%' THEN 'production'
        ELSE 'other'
    END as environment,
    CASE 
        WHEN datname LIKE '%_pro1' THEN 'pro1'
        WHEN datname LIKE '%_pro2' THEN 'pro2'
        ELSE 'unknown'
    END as service_group
FROM pg_database 
WHERE datname LIKE 'saascontrol%'
ORDER BY pg_database_size(datname) DESC;

-- WAL file and archiving status
CREATE VIEW v_wal_status AS
SELECT 
    setting as wal_level
FROM pg_settings WHERE name = 'wal_level'

UNION ALL

SELECT 
    CASE 
        WHEN setting = 'on' THEN 'Archive Mode: ENABLED'
        ELSE 'Archive Mode: DISABLED'
    END
FROM pg_settings WHERE name = 'archive_mode'

UNION ALL

SELECT 
    'WAL Files Count: ' || COUNT(*)::text
FROM pg_ls_waldir()

UNION ALL

SELECT 
    'WAL Directory Size: ' || pg_size_pretty(SUM(size))
FROM pg_ls_waldir();

-- Checkpoint and background writer statistics
CREATE VIEW v_checkpoint_stats AS
SELECT 
    'Checkpoints Timed' as metric,
    checkpoints_timed::text as value
FROM pg_stat_bgwriter

UNION ALL

SELECT 
    'Checkpoints Requested' as metric,
    checkpoints_req::text as value
FROM pg_stat_bgwriter

UNION ALL

SELECT 
    'Checkpoint Write Time (ms)' as metric,
    checkpoint_write_time::text as value
FROM pg_stat_bgwriter

UNION ALL

SELECT 
    'Checkpoint Sync Time (ms)' as metric,
    checkpoint_sync_time::text as value
FROM pg_stat_bgwriter

UNION ALL

SELECT 
    'Buffers Written (Checkpoint)' as metric,
    buffers_checkpoint::text as value
FROM pg_stat_bgwriter

UNION ALL

SELECT 
    'Buffers Written (Background)' as metric,
    buffers_clean::text as value
FROM pg_stat_bgwriter;

-- =============================================================================
-- 6. LOCK MONITORING
-- =============================================================================

-- Current locks and blocking queries
CREATE VIEW v_lock_monitoring AS
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement,
    blocked_activity.application_name AS blocked_application,
    blocking_activity.application_name AS blocking_application,
    blocked_locks.mode AS blocked_mode,
    blocking_locks.mode AS blocking_mode,
    blocked_locks.locktype AS lock_type,
    blocked_locks.database AS database_id,
    blocked_locks.relation AS relation_id
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Lock wait times and deadlocks
CREATE VIEW v_lock_waits AS
SELECT 
    schemaname,
    tablename,
    'Table Locks' as lock_type,
    n_tup_ins + n_tup_upd + n_tup_del as write_operations,
    seq_scan + idx_scan as read_operations
FROM pg_stat_user_tables
WHERE n_tup_ins + n_tup_upd + n_tup_del > 0
ORDER BY write_operations DESC;

-- =============================================================================
-- 7. VACUUM AND ANALYZE MONITORING
-- =============================================================================

-- Vacuum and analyze status
CREATE VIEW v_maintenance_status AS
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    EXTRACT(EPOCH FROM (now() - last_autovacuum))/3600 as hours_since_autovacuum,
    last_analyze,
    last_autoanalyze,
    EXTRACT(EPOCH FROM (now() - last_autoanalyze))/3600 as hours_since_autoanalyze,
    vacuum_count,
    autovacuum_count,
    analyze_count,
    autoanalyze_count
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY dead_tuple_percent DESC NULLS LAST;

-- Tables needing maintenance
CREATE VIEW v_tables_needing_maintenance AS
SELECT 
    schemaname,
    tablename,
    CASE 
        WHEN dead_tuple_percent > 20 THEN 'VACUUM_NEEDED'
        WHEN dead_tuple_percent > 10 THEN 'VACUUM_SOON'
        ELSE 'OK'
    END as vacuum_recommendation,
    CASE 
        WHEN hours_since_autoanalyze > 168 THEN 'ANALYZE_NEEDED'  -- 1 week
        WHEN hours_since_autoanalyze > 72 THEN 'ANALYZE_SOON'    -- 3 days
        ELSE 'OK'
    END as analyze_recommendation,
    dead_tuple_percent,
    hours_since_autovacuum,
    hours_since_autoanalyze
FROM v_maintenance_status
WHERE dead_tuple_percent > 5 OR hours_since_autoanalyze > 72
ORDER BY dead_tuple_percent DESC;

-- =============================================================================
-- 8. ALERTING QUERIES
-- =============================================================================

-- Performance alerts (queries to use in monitoring systems)
CREATE VIEW v_performance_alerts AS
SELECT 
    'HIGH_CONNECTION_COUNT' as alert_type,
    'Connection count exceeded threshold' as message,
    connection_count as value,
    80 as threshold,
    database_name as context
FROM v_connection_pool_health
WHERE total_connections > 80

UNION ALL

SELECT 
    'LOW_CACHE_HIT_RATIO' as alert_type,
    'Cache hit ratio below threshold' as message,
    hit_ratio_percent as value,
    90 as threshold,
    cache_type as context
FROM v_cache_hit_ratio
WHERE hit_ratio_percent < 90

UNION ALL

SELECT 
    'SLOW_QUERY_DETECTED' as alert_type,
    'Query execution time exceeded threshold' as message,
    mean_exec_time as value,
    5000 as threshold,  -- 5 seconds
    LEFT(query, 50) as context
FROM v_slow_queries
WHERE mean_exec_time > 5000

UNION ALL

SELECT 
    'HIGH_AI_TASK_ERROR_RATE' as alert_type,
    'AI task error rate exceeded threshold' as message,
    error_rate_percent as value,
    10 as threshold,  -- 10%
    task_type as context
FROM v_ai_task_performance
WHERE error_rate_percent > 10

UNION ALL

SELECT 
    'VACUUM_NEEDED' as alert_type,
    'Table has high dead tuple percentage' as message,
    dead_tuple_percent as value,
    20 as threshold,
    tablename as context
FROM v_maintenance_status
WHERE dead_tuple_percent > 20;

-- =============================================================================
-- 9. HEALTH CHECK FUNCTIONS
-- =============================================================================

-- Overall database health check function
CREATE OR REPLACE FUNCTION check_database_health()
RETURNS TABLE (
    check_name text,
    status text,
    message text,
    details jsonb
) AS $$
BEGIN
    -- Connection health
    RETURN QUERY
    SELECT 
        'connection_count'::text,
        CASE WHEN total_connections > 100 THEN 'WARNING'
             WHEN total_connections > 150 THEN 'CRITICAL'
             ELSE 'OK' END,
        format('Total connections: %s', total_connections),
        jsonb_build_object('count', total_connections, 'active', active_connections)
    FROM v_connection_pool_health
    WHERE database_name = current_database();
    
    -- Cache hit ratio
    RETURN QUERY
    SELECT 
        'cache_hit_ratio'::text,
        CASE WHEN hit_ratio_percent < 80 THEN 'CRITICAL'
             WHEN hit_ratio_percent < 90 THEN 'WARNING'
             ELSE 'OK' END,
        format('Cache hit ratio: %s%%', hit_ratio_percent),
        jsonb_build_object('hit_ratio', hit_ratio_percent)
    FROM v_cache_hit_ratio
    WHERE cache_type = 'Buffer Cache';
    
    -- Slow queries
    RETURN QUERY
    SELECT 
        'slow_queries'::text,
        CASE WHEN COUNT(*) > 10 THEN 'WARNING'
             WHEN COUNT(*) > 20 THEN 'CRITICAL'
             ELSE 'OK' END,
        format('Slow queries count: %s', COUNT(*)),
        jsonb_agg(jsonb_build_object('query', LEFT(query, 100), 'time', mean_exec_time))
    FROM v_slow_queries
    WHERE mean_exec_time > 1000;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. AUTOMATED MONITORING SETUP
-- =============================================================================

-- Create monitoring schema for storing historical data
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Historical performance metrics table
CREATE TABLE IF NOT EXISTS monitoring.performance_history (
    id SERIAL PRIMARY KEY,
    database_name text,
    metric_name text,
    metric_value numeric,
    recorded_at timestamp with time zone DEFAULT now()
);

-- Function to record performance metrics
CREATE OR REPLACE FUNCTION monitoring.record_performance_metrics()
RETURNS void AS $$
BEGIN
    -- Record connection counts
    INSERT INTO monitoring.performance_history (database_name, metric_name, metric_value)
    SELECT database_name, 'connection_count', total_connections
    FROM v_connection_pool_health;
    
    -- Record cache hit ratios
    INSERT INTO monitoring.performance_history (database_name, metric_name, metric_value)
    SELECT current_database(), 'cache_hit_ratio', hit_ratio_percent
    FROM v_cache_hit_ratio
    WHERE cache_type = 'Buffer Cache';
    
    -- Record slow query counts
    INSERT INTO monitoring.performance_history (database_name, metric_name, metric_value)
    SELECT current_database(), 'slow_query_count', COUNT(*)
    FROM v_slow_queries;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- USAGE EXAMPLES
-- =============================================================================

/*
-- Monitor current connection status
SELECT * FROM v_connection_status;

-- Check for slow queries
SELECT * FROM v_slow_queries LIMIT 10;

-- Monitor AI task performance
SELECT * FROM v_ai_task_performance;

-- Check database health
SELECT * FROM check_database_health();

-- Monitor cache performance
SELECT * FROM v_cache_hit_ratio;

-- Check for tables needing maintenance
SELECT * FROM v_tables_needing_maintenance;

-- Monitor locks and blocking
SELECT * FROM v_lock_monitoring;

-- Get performance alerts
SELECT * FROM v_performance_alerts;

-- Record performance metrics (run every 5 minutes)
SELECT monitoring.record_performance_metrics();
*/