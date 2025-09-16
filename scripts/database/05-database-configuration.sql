-- ===========================================
-- SaaS Control Deck 数据库参数优化脚本
-- ===========================================
-- 注意: 本脚本需要以超级用户身份执行
-- 执行顺序: 第五步 - 数据库参数优化和配置
-- ===========================================

\echo '优化SaaS Control Deck数据库配置参数...'

-- ===========================================
-- 1. 内存和缓存优化
-- ===========================================

\echo '配置内存和缓存参数...'

-- 共享缓存区大小 (按系统内存的25%配置)
ALTER SYSTEM SET shared_buffers = '2GB';

-- 有效缓存大小 (按系统内存的75%配置)
ALTER SYSTEM SET effective_cache_size = '6GB';

-- 工作内存大小 (为排序和哈希操作优化)
ALTER SYSTEM SET work_mem = '256MB';

-- 维护工作内存 (为VACUUM和CREATE INDEX优化)
ALTER SYSTEM SET maintenance_work_mem = '1GB';

-- 自动空间回收工作者最大内存
ALTER SYSTEM SET autovacuum_work_mem = '512MB';

-- ===========================================
-- 2. 连接和并发优化
-- ===========================================

\echo '配置连接和并发参数...'

-- 最大连接数 (根据多个微服务调整)
ALTER SYSTEM SET max_connections = 500;

-- 最大并行工作者数 (按CPU核数配置)
ALTER SYSTEM SET max_parallel_workers = 8;

-- 每个查询最大并行工作者数
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- 最大并行维护工作者数
ALTER SYSTEM SET max_parallel_maintenance_workers = 4;

-- 背景工作者数量
ALTER SYSTEM SET max_worker_processes = 12;

-- ===========================================
-- 3. 查询优化器参数
-- ===========================================

\echo '配置查询优化器参数...'

-- 随机页面成本 (优化SSD性能)
ALTER SYSTEM SET random_page_cost = 1.1;

-- 顺序页面成本
ALTER SYSTEM SET seq_page_cost = 1.0;

-- CPU元组成本 (优化CPU密集型操作)
ALTER SYSTEM SET cpu_tuple_cost = 0.01;

-- CPU操作符成本
ALTER SYSTEM SET cpu_operator_cost = 0.0025;

-- CPU索引元组成本
ALTER SYSTEM SET cpu_index_tuple_cost = 0.005;

-- 启用并行查询
ALTER SYSTEM SET enable_parallel_append = on;
ALTER SYSTEM SET enable_parallel_hash = on;

-- 并行计算阈值
ALTER SYSTEM SET parallel_tuple_cost = 0.1;
ALTER SYSTEM SET parallel_setup_cost = 1000.0;

-- ===========================================
-- 4. WAL (写前日志) 优化
-- ===========================================

\echo '配置 WAL 相关参数...'

-- WAL 缓存区大小
ALTER SYSTEM SET wal_buffers = '64MB';

-- WAL 段文件最大大小
ALTER SYSTEM SET max_wal_size = '4GB';

-- WAL 段文件最小大小
ALTER SYSTEM SET min_wal_size = '1GB';

-- 检查点完成目标 (优化恢复时间)
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- WAL 写入延迟
ALTER SYSTEM SET commit_delay = 10000;

-- WAL 写入方式 (优化性能)
ALTER SYSTEM SET synchronous_commit = on;

-- ===========================================
-- 5. 自动空间回收优化
-- ===========================================

\echo '配置自动空间回收参数...'

-- 启用自动VACUUM
ALTER SYSTEM SET autovacuum = on;

-- 自动VACUUM工作者数量
ALTER SYSTEM SET autovacuum_max_workers = 6;

-- 自动VACUUM延迟时间 (秒)
ALTER SYSTEM SET autovacuum_naptime = 30;

-- 触发自动VACUUM的最小更新占比
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;

-- 触发自动ANALYZE的最小更新占比
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;

-- 自动VACUUM成本延迟 (减少对用户查询的影响)
ALTER SYSTEM SET autovacuum_vacuum_cost_delay = 10;

-- 自动VACUUM成本限制
ALTER SYSTEM SET autovacuum_vacuum_cost_limit = 2000;

-- ===========================================
-- 6. 日志和监控优化
-- ===========================================

\echo '配置日志和监控参数...'

-- 启用查询计划和执行统计
ALTER SYSTEM SET track_activities = on;
ALTER SYSTEM SET track_counts = on;
ALTER SYSTEM SET track_io_timing = on;
ALTER SYSTEM SET track_functions = 'all';

-- 记录慢查询 (超过5秒的查询)
ALTER SYSTEM SET log_min_duration_statement = 5000;

-- 记录检查点和自动VACUUM
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_autovacuum_min_duration = 1000;

-- 记录锁等待 (超过1秒)
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET deadlock_timeout = '1s';

-- 记录临时文件使用
ALTER SYSTEM SET log_temp_files = 10240; -- 10MB

-- 记录连接和断开连接
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- ===========================================
-- 7. 安全和审计参数
-- ===========================================

\echo '配置安全和审计参数...'

-- 客户端连接认证超时 (30秒)
ALTER SYSTEM SET authentication_timeout = '30s';

-- 空闲客户端连接超时 (30分钟)
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30min';

-- 记录所有SQL语句 (仅在开发环境中启用)
-- ALTER SYSTEM SET log_statement = 'all';

-- 记录错误和警告
ALTER SYSTEM SET log_min_messages = 'warning';
ALTER SYSTEM SET log_min_error_statement = 'error';

-- 启用频率限制 (防止暴力攻击)
-- 需要在 postgresql.conf 中手动配置
-- connection_limit_per_ip = 10

-- ===========================================
-- 8. 时区和国际化设置
-- ===========================================

\echo '配置时区和国际化设置...'

-- 设置时区为UTC
ALTER SYSTEM SET timezone = 'UTC';

-- 设置日志时区
ALTER SYSTEM SET log_timezone = 'UTC';

-- 设置日期格式
ALTER SYSTEM SET datestyle = 'ISO, YMD';

-- 设置语言环境
ALTER SYSTEM SET lc_messages = 'C';
ALTER SYSTEM SET lc_monetary = 'C';
ALTER SYSTEM SET lc_numeric = 'C';
ALTER SYSTEM SET lc_time = 'C';

-- ===========================================
-- 9. 扩展和特殊功能
-- ===========================================

\echo '启用扩展和特殊功能...'

-- 启用pg_stat_statements扩展 (用于查询性能分析)
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- pg_stat_statements 配置
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- 计划缓存大小
ALTER SYSTEM SET plan_cache_mode = 'auto';

-- JIT 编译优化 (适用于复杂查询)
ALTER SYSTEM SET jit = on;
ALTER SYSTEM SET jit_above_cost = 500000;
ALTER SYSTEM SET jit_optimize_above_cost = 500000;

-- ===========================================
-- 10. 环境特定参数优化
-- ===========================================

\echo '配置环境特定参数...'

-- 开发环境特定配置 (用于调试)
DO $$
BEGIN
    -- 检查是否为开发数据库
    IF current_database() LIKE '%_dev_%' THEN
        -- 开发环境启用更详细的日志
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_statement = ''mod''';
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_min_duration_statement = 1000';
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_line_prefix = ''%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ''';
        
        RAISE NOTICE '开发环境特定配置已应用到数据库: %', current_database();
    END IF;
    
    -- 检查是否为测试数据库
    IF current_database() LIKE '%_stage_%' THEN
        -- 测试环境中等的配置
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_min_duration_statement = 3000';
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_line_prefix = ''%t [%p]: [%l-1] ''';
        
        RAISE NOTICE '测试环境特定配置已应用到数据库: %', current_database();
    END IF;
    
    -- 检查是否为生产数据库
    IF current_database() LIKE '%_prod_%' THEN
        -- 生产环境严格配置
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_min_duration_statement = 10000';
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_line_prefix = ''%t [%p]: [%l-1] ''';
        EXECUTE 'ALTER DATABASE ' || current_database() || ' SET log_statement = ''none''';
        
        RAISE NOTICE '生产环境特定配置已应用到数据库: %', current_database();
    END IF;
END
$$;

-- ===========================================
-- 11. 数据库特定优化设置
-- ===========================================

\echo '配置数据库特定优化设置...'

-- 为当前数据库设置特定参数
ALTER DATABASE CURRENT SET effective_io_concurrency = 200;
ALTER DATABASE CURRENT SET random_page_cost = 1.1;
ALTER DATABASE CURRENT SET maintenance_work_mem = '1GB';
ALTER DATABASE CURRENT SET work_mem = '256MB';

-- SaaS Control Deck 特定优化
ALTER DATABASE CURRENT SET enable_partitionwise_join = on;
ALTER DATABASE CURRENT SET enable_partitionwise_aggregate = on;

-- 时间戳精度优化 (用于微秒级时间戳)
ALTER DATABASE CURRENT SET log_min_duration_statement = 1000;

-- ===========================================
-- 12. 创建性能监控视图
-- ===========================================

\echo '创建性能监控视图和函数...'

-- 数据库大小监控视图
CREATE OR REPLACE VIEW database_size_info AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    pg_stat_get_tuples_inserted((schemaname||'.'||tablename)::regclass) + 
    pg_stat_get_tuples_updated((schemaname||'.'||tablename)::regclass) + 
    pg_stat_get_tuples_deleted((schemaname||'.'||tablename)::regclass) as total_rows
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 数据库性能指标视图
CREATE OR REPLACE VIEW database_performance_info AS
SELECT 
    datname as database_name,
    numbackends as active_connections,
    xact_commit as transactions_committed,
    xact_rollback as transactions_rolled_back,
    blks_read as blocks_read,
    blks_hit as blocks_hit,
    CASE 
        WHEN (blks_read + blks_hit) = 0 THEN 0
        ELSE ROUND(100.0 * blks_hit / (blks_read + blks_hit), 2)
    END as cache_hit_ratio,
    tup_returned as tuples_returned,
    tup_fetched as tuples_fetched,
    tup_inserted as tuples_inserted,
    tup_updated as tuples_updated,
    tup_deleted as tuples_deleted
FROM pg_stat_database 
WHERE datname = current_database();

-- 连接状态监控视图
CREATE OR REPLACE VIEW connection_status_info AS
SELECT 
    state,
    COUNT(*) as connection_count,
    MAX(now() - state_change) as max_duration
FROM pg_stat_activity 
WHERE datname = current_database()
GROUP BY state
ORDER BY connection_count DESC;

-- 慢查询监控函数
CREATE OR REPLACE FUNCTION get_slow_queries(limit_count integer DEFAULT 10)
RETURNS TABLE (
    query text,
    calls bigint,
    total_time double precision,
    mean_time double precision,
    stddev_time double precision,
    rows bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.query,
        s.calls,
        s.total_exec_time as total_time,
        s.mean_exec_time as mean_time,
        s.stddev_exec_time as stddev_time,
        s.rows
    FROM pg_stat_statements s
    ORDER BY s.mean_exec_time DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 13. 数据库维护函数
-- ===========================================

\echo '创建数据库维护函数...'

-- 数据库健康检查函数
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS TABLE (
    check_name text,
    status text,
    value text,
    recommendation text
) AS $$
DECLARE
    cache_hit_ratio numeric;
    active_connections integer;
    max_connections_setting integer;
    deadlock_count bigint;
    long_running_queries integer;
BEGIN
    -- 缓存命中率检查
    SELECT CASE WHEN (blks_read + blks_hit) = 0 THEN 100
               ELSE 100.0 * blks_hit / (blks_read + blks_hit)
           END INTO cache_hit_ratio
    FROM pg_stat_database WHERE datname = current_database();
    
    RETURN QUERY SELECT 
        '缓存命中率'::text,
        CASE WHEN cache_hit_ratio > 95 THEN '优秀' 
             WHEN cache_hit_ratio > 90 THEN '良好' 
             ELSE '需要优化' END,
        cache_hit_ratio::text || '%',
        CASE WHEN cache_hit_ratio <= 90 THEN '考虑增加shared_buffers' 
             ELSE '缓存性能良好' END;
    
    -- 连接数检查
    SELECT COUNT(*) INTO active_connections FROM pg_stat_activity WHERE datname = current_database();
    SELECT setting::integer INTO max_connections_setting FROM pg_settings WHERE name = 'max_connections';
    
    RETURN QUERY SELECT 
        '连接数使用率'::text,
        CASE WHEN active_connections::numeric / max_connections_setting > 0.8 THEN '高' 
             WHEN active_connections::numeric / max_connections_setting > 0.5 THEN '中等' 
             ELSE '正常' END,
        active_connections::text || '/' || max_connections_setting::text,
        CASE WHEN active_connections::numeric / max_connections_setting > 0.8 
             THEN '考虑优化连接池或增加max_connections' 
             ELSE '连接数正常' END;
    
    -- 长时间运行查询检查
    SELECT COUNT(*) INTO long_running_queries
    FROM pg_stat_activity 
    WHERE datname = current_database()
        AND state = 'active'
        AND now() - query_start > interval '5 minutes';
    
    RETURN QUERY SELECT 
        '长时间运行查询'::text,
        CASE WHEN long_running_queries = 0 THEN '正常' 
             WHEN long_running_queries < 5 THEN '注意' 
             ELSE '警告' END,
        long_running_queries::text,
        CASE WHEN long_running_queries > 0 
             THEN '检查长时间运行的查询并考虑优化' 
             ELSE '无长时间运行查询' END;
END;
$$ LANGUAGE plpgsql;

-- 数据库清理函数
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days integer DEFAULT 90)
RETURNS TABLE (
    table_name text,
    deleted_rows bigint
) AS $$
DECLARE
    cleanup_date timestamp with time zone;
BEGIN
    cleanup_date := CURRENT_TIMESTAMP - (retention_days || ' days')::interval;
    
    -- 清理老的系统日志
    DELETE FROM system_logs WHERE created_at < cleanup_date;
    RETURN QUERY SELECT 'system_logs'::text, row_count() as deleted_rows FROM (SELECT 1) t;
    
    -- 清理老的性能指标
    DELETE FROM performance_metrics WHERE recorded_at < cleanup_date;
    RETURN QUERY SELECT 'performance_metrics'::text, row_count() as deleted_rows FROM (SELECT 1) t;
    
    -- 清理过期的用户会话
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    RETURN QUERY SELECT 'user_sessions'::text, row_count() as deleted_rows FROM (SELECT 1) t;
    
    -- 清理过期的通知
    DELETE FROM notifications WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
    RETURN QUERY SELECT 'notifications'::text, row_count() as deleted_rows FROM (SELECT 1) t;
    
    -- 执行 VACUUM ANALYZE 优化性能
    VACUUM ANALYZE system_logs;
    VACUUM ANALYZE performance_metrics;
    VACUUM ANALYZE user_sessions;
    VACUUM ANALYZE notifications;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 14. 应用配置完成验证
-- ===========================================

\echo '验证数据库配置...'

-- 显示当前重要的配置参数
SELECT 
    name,
    setting,
    unit,
    context,
    short_desc
FROM pg_settings 
WHERE name IN (
    'shared_buffers',
    'effective_cache_size', 
    'work_mem',
    'maintenance_work_mem',
    'max_connections',
    'max_parallel_workers',
    'wal_buffers',
    'checkpoint_completion_target',
    'random_page_cost',
    'effective_io_concurrency'
)
ORDER BY name;

-- 显示数据库尺寸信息
SELECT * FROM database_size_info LIMIT 10;

-- 显示数据库性能信息
SELECT * FROM database_performance_info;

-- 显示连接状态信息
SELECT * FROM connection_status_info;

-- 执行健康检查
SELECT * FROM database_health_check();

\echo '数据库配置优化完成！';
\echo '请重新加载 PostgreSQL 配置： SELECT pg_reload_conf();';
\echo '或者重启 PostgreSQL 服务以使所有配置生效。';

-- ===========================================
-- 执行说明
-- ===========================================
/*
以超级用户身份执行（只需执行一次）:
psql -h 47.79.87.199 -U jackchan -d postgres -f 05-database-configuration.sql

重新加载配置:
psql -h 47.79.87.199 -U jackchan -d postgres -c "SELECT pg_reload_conf();"

检查配置是否生效:
psql -h 47.79.87.199 -U jackchan -d postgres -c "SHOW shared_buffers;"

在每个数据库中启用pg_stat_statements:
psql -h 47.79.87.199 -U saasctl_dev_pro1_user -d saascontrol_dev_pro1 -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

性能监控命令:
-- 查看慢查询
SELECT * FROM get_slow_queries(5);

-- 数据库健康检查
SELECT * FROM database_health_check();

-- 清理旧数据
SELECT * FROM cleanup_old_data(30);

下一步:
创建环境配置文件和验证脚本
*/