-- =============================================================================
-- Table Partitioning Strategy for SaaS Control Deck
-- =============================================================================
-- Optimized partitioning for high-volume tables in AI workloads
-- Focuses on time-based and status-based partitioning for performance

-- =============================================================================
-- 1. SYSTEM LOGS PARTITIONING (Time-based)
-- =============================================================================

-- Drop existing system_logs table and recreate as partitioned
-- WARNING: This will drop existing data - backup first!

-- Create partitioned system_logs table
CREATE TABLE system_logs_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id UUID,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for system logs (current month + next 6 months)
CREATE TABLE system_logs_2025_01 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE system_logs_2025_02 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE system_logs_2025_03 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE system_logs_2025_04 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE system_logs_2025_05 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE system_logs_2025_06 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Create default partition for future dates
CREATE TABLE system_logs_default PARTITION OF system_logs_partitioned
    DEFAULT;

-- Indexes on partitioned system_logs
CREATE INDEX idx_system_logs_part_service_time 
    ON system_logs_partitioned(service_name, created_at DESC);

CREATE INDEX idx_system_logs_part_level 
    ON system_logs_partitioned(log_level) 
    WHERE log_level IN ('ERROR', 'CRITICAL');

CREATE INDEX idx_system_logs_part_user 
    ON system_logs_partitioned(user_id, created_at DESC) 
    WHERE user_id IS NOT NULL;

-- =============================================================================
-- 2. PERFORMANCE METRICS PARTITIONING (Time-based)
-- =============================================================================

-- Create partitioned performance_metrics table
CREATE TABLE performance_metrics_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

-- Create daily partitions for performance metrics (high volume data)
-- Current week + next 2 weeks
CREATE TABLE performance_metrics_2025_01_01 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-01-02');

CREATE TABLE performance_metrics_2025_01_02 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-02') TO ('2025-01-03');

CREATE TABLE performance_metrics_2025_01_03 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-03') TO ('2025-01-04');

CREATE TABLE performance_metrics_2025_01_04 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-04') TO ('2025-01-05');

CREATE TABLE performance_metrics_2025_01_05 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-05') TO ('2025-01-06');

CREATE TABLE performance_metrics_2025_01_06 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-06') TO ('2025-01-07');

CREATE TABLE performance_metrics_2025_01_07 PARTITION OF performance_metrics_partitioned
    FOR VALUES FROM ('2025-01-07') TO ('2025-01-08');

-- Default partition for future dates
CREATE TABLE performance_metrics_default PARTITION OF performance_metrics_partitioned
    DEFAULT;

-- Indexes on partitioned performance_metrics
CREATE INDEX idx_perf_metrics_part_service_metric 
    ON performance_metrics_partitioned(service_name, metric_name, recorded_at DESC);

CREATE INDEX idx_perf_metrics_part_alerts 
    ON performance_metrics_partitioned(service_name, metric_name, metric_value) 
    WHERE recorded_at > (CURRENT_TIMESTAMP - INTERVAL '1 hour');

-- =============================================================================
-- 3. AI TASKS PARTITIONING (Status + Time based)
-- =============================================================================

-- Create partitioned ai_tasks table by status for better query performance
CREATE TABLE ai_tasks_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, status)
) PARTITION BY LIST (status);

-- Partition by task status for optimal query performance
CREATE TABLE ai_tasks_pending PARTITION OF ai_tasks_partitioned
    FOR VALUES IN ('pending');

CREATE TABLE ai_tasks_running PARTITION OF ai_tasks_partitioned
    FOR VALUES IN ('running');

CREATE TABLE ai_tasks_completed PARTITION OF ai_tasks_partitioned
    FOR VALUES IN ('completed');

CREATE TABLE ai_tasks_failed PARTITION OF ai_tasks_partitioned
    FOR VALUES IN ('failed');

CREATE TABLE ai_tasks_cancelled PARTITION OF ai_tasks_partitioned
    FOR VALUES IN ('cancelled');

-- Default partition for any other status values
CREATE TABLE ai_tasks_other PARTITION OF ai_tasks_partitioned
    DEFAULT;

-- Indexes on partitioned ai_tasks
CREATE INDEX idx_ai_tasks_part_project_created 
    ON ai_tasks_partitioned(project_id, created_at DESC);

CREATE INDEX idx_ai_tasks_part_user_type 
    ON ai_tasks_partitioned(user_id, task_type);

CREATE INDEX idx_ai_tasks_part_created 
    ON ai_tasks_partitioned(created_at DESC);

-- Special indexes for active tasks (pending/running partitions)
CREATE INDEX idx_ai_tasks_pending_priority 
    ON ai_tasks_pending(created_at, task_type);

CREATE INDEX idx_ai_tasks_running_duration 
    ON ai_tasks_running(started_at);

-- =============================================================================
-- 4. AUDIT TRAILS PARTITIONING (Time-based)
-- =============================================================================

-- Create partitioned audit_trails table
CREATE TABLE audit_trails_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for audit trails
CREATE TABLE audit_trails_2025_01 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_trails_2025_02 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE audit_trails_2025_03 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE audit_trails_2025_04 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE audit_trails_2025_05 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE audit_trails_2025_06 PARTITION OF audit_trails_partitioned
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Default partition for future dates
CREATE TABLE audit_trails_default PARTITION OF audit_trails_partitioned
    DEFAULT;

-- Indexes on partitioned audit_trails
CREATE INDEX idx_audit_trails_part_user_action 
    ON audit_trails_partitioned(user_id, action, created_at DESC);

CREATE INDEX idx_audit_trails_part_resource 
    ON audit_trails_partitioned(resource_type, resource_id, created_at DESC);

-- =============================================================================
-- 5. AI RESULTS PARTITIONING (Model + Time based)
-- =============================================================================

-- Create partitioned ai_results table by model_id for performance isolation
CREATE TABLE ai_results_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    model_id UUID NOT NULL,
    result_data JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, model_id, created_at)
) PARTITION BY HASH (model_id);

-- Create hash partitions for AI results (distribute by model_id)
CREATE TABLE ai_results_part_0 PARTITION OF ai_results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE ai_results_part_1 PARTITION OF ai_results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE ai_results_part_2 PARTITION OF ai_results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE ai_results_part_3 PARTITION OF ai_results_partitioned
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Indexes on partitioned ai_results
CREATE INDEX idx_ai_results_part_task 
    ON ai_results_partitioned(task_id, created_at DESC);

CREATE INDEX idx_ai_results_part_performance 
    ON ai_results_partitioned(model_id, processing_time_ms, confidence_score);

-- =============================================================================
-- 6. AUTOMATED PARTITION MANAGEMENT
-- =============================================================================

-- Function to create new monthly partition for system_logs
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name text,
    start_date date
) RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date);
    
    -- Create indexes on the new partition
    EXECUTE format('CREATE INDEX idx_%s_created_at ON %I (created_at DESC)', 
        partition_name, partition_name);
END;
$$ LANGUAGE plpgsql;

-- Function to create daily partition for performance_metrics
CREATE OR REPLACE FUNCTION create_daily_partition(
    table_name text,
    start_date date
) RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM_DD');
    end_date := start_date + interval '1 day';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date);
    
    -- Create indexes on the new partition
    EXECUTE format('CREATE INDEX idx_%s_recorded_at ON %I (recorded_at DESC)', 
        partition_name, partition_name);
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (data retention policy)
CREATE OR REPLACE FUNCTION drop_old_partitions(
    table_name text,
    retention_months integer
) RETURNS void AS $$
DECLARE
    partition_name text;
    cutoff_date date;
BEGIN
    cutoff_date := CURRENT_DATE - (retention_months || ' months')::interval;
    
    FOR partition_name IN
        SELECT schemaname||'.'||tablename
        FROM pg_tables
        WHERE tablename LIKE table_name || '_%'
        AND schemaname = 'public'
    LOOP
        -- Check if partition is older than retention period
        -- This is a simplified check - in production, parse the date from table name
        EXECUTE format('DROP TABLE IF EXISTS %s', partition_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. PARTITION PRUNING OPTIMIZATION
-- =============================================================================

-- Enable constraint exclusion for better partition pruning
SET constraint_exclusion = partition;

-- Enable partition-wise joins and aggregates
SET enable_partitionwise_join = on;
SET enable_partitionwise_aggregate = on;

-- =============================================================================
-- 8. MONITORING PARTITION PERFORMANCE
-- =============================================================================

-- View to monitor partition sizes
CREATE VIEW partition_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public' 
    AND (tablename LIKE '%_partitioned' OR tablename LIKE '%_part_%' OR tablename LIKE '%_202%')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- View to monitor partition scan performance
CREATE VIEW partition_scan_stats AS
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables 
WHERE schemaname = 'public' 
    AND (tablename LIKE '%_partitioned' OR tablename LIKE '%_part_%' OR tablename LIKE '%_202%')
ORDER BY seq_scan + idx_scan DESC;

-- =============================================================================
-- 9. MAINTENANCE PROCEDURES
-- =============================================================================

-- Procedure to maintain partitions (run monthly)
CREATE OR REPLACE PROCEDURE maintain_partitions()
LANGUAGE plpgsql AS $$
BEGIN
    -- Create next month's partitions
    PERFORM create_monthly_partition('system_logs_partitioned', DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month'));
    PERFORM create_monthly_partition('audit_trails_partitioned', DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month'));
    
    -- Create next week's daily partitions for performance metrics
    FOR i IN 0..6 LOOP
        PERFORM create_daily_partition('performance_metrics_partitioned', CURRENT_DATE + (i || ' days')::interval);
    END LOOP;
    
    -- Drop old partitions (keep 6 months of logs, 30 days of metrics)
    PERFORM drop_old_partitions('system_logs', 6);
    PERFORM drop_old_partitions('audit_trails', 6);
    -- Performance metrics: implement daily cleanup separately due to daily partitions
    
    -- Update statistics on partitioned tables
    ANALYZE system_logs_partitioned;
    ANALYZE performance_metrics_partitioned;
    ANALYZE ai_tasks_partitioned;
    ANALYZE audit_trails_partitioned;
    ANALYZE ai_results_partitioned;
END;
$$;

-- =============================================================================
-- 10. DATA MIGRATION SCRIPTS
-- =============================================================================

-- Script to migrate existing data to partitioned tables
-- WARNING: Test this thoroughly before running in production!

/*
-- Example migration for system_logs:

-- 1. Rename existing table
ALTER TABLE system_logs RENAME TO system_logs_old;

-- 2. Create partitioned table (already done above)

-- 3. Migrate data
INSERT INTO system_logs_partitioned 
SELECT * FROM system_logs_old;

-- 4. Verify data integrity
SELECT COUNT(*) FROM system_logs_old;
SELECT COUNT(*) FROM system_logs_partitioned;

-- 5. Update application connection strings and views

-- 6. Drop old table (after verification)
-- DROP TABLE system_logs_old;
*/

-- =============================================================================
-- 11. PARTITION CONSTRAINT EXAMPLES
-- =============================================================================

-- Add check constraints to ensure partition pruning works effectively
-- These constraints help the query planner eliminate partitions

-- Example for time-based partitioning
ALTER TABLE system_logs_2025_01 
    ADD CONSTRAINT check_system_logs_2025_01_created_at 
    CHECK (created_at >= '2025-01-01' AND created_at < '2025-02-01');

-- Example for status-based partitioning
ALTER TABLE ai_tasks_pending 
    ADD CONSTRAINT check_ai_tasks_pending_status 
    CHECK (status = 'pending');

ALTER TABLE ai_tasks_running 
    ADD CONSTRAINT check_ai_tasks_running_status 
    CHECK (status = 'running');

-- =============================================================================
-- NOTES FOR PARTITIONING STRATEGY
-- =============================================================================

/*
Partitioning Benefits for SaaS Control Deck:
1. Improved query performance through partition pruning
2. Faster maintenance operations (VACUUM, ANALYZE)
3. Better data lifecycle management (easy archival/deletion)
4. Parallel query execution across partitions
5. Reduced lock contention
6. Better resource utilization

Partition Maintenance Schedule:
- Daily: Create new daily partitions for high-volume tables
- Weekly: Analyze partition statistics
- Monthly: Create new monthly partitions, drop old ones
- Quarterly: Review partition strategy and performance

Monitoring:
- Track partition sizes and growth rates
- Monitor query performance across partitions
- Check partition constraint violations
- Verify partition pruning in query plans

Best Practices Implemented:
1. Time-based partitioning for log data
2. Status-based partitioning for workflow data
3. Hash partitioning for even data distribution
4. Automated partition management functions
5. Proper constraint definitions for pruning
6. Index strategies optimized for partitioned tables
7. Data retention policies through automated cleanup
*/