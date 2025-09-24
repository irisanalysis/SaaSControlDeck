# 数据库性能优化方案

## 🚀 性能优化策略概览

针对SaaS Control Deck数据管理平台的高性能需求，设计了全方位的数据库性能优化方案。该方案支持TB级数据分析、毫秒级查询响应和高并发数据源连接管理。

## 📊 分区策略设计

### 1. 时间分区策略

#### 质量评估数据分区 (按月分区)

```sql
-- 创建分区主表
CREATE TABLE quality_assessments_partitioned (
    LIKE quality_assessments INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 自动分区创建函数
CREATE OR REPLACE FUNCTION create_quality_assessment_partition(start_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    -- 生成分区名称: quality_assessments_y2024m09
    partition_name := 'quality_assessments_y' ||
                     EXTRACT(YEAR FROM start_date) || 'm' ||
                     LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    end_date := start_date + INTERVAL '1 month';

    -- 创建分区
    EXECUTE format(
        'CREATE TABLE %I PARTITION OF quality_assessments_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    -- 创建分区特定索引
    EXECUTE format('CREATE INDEX idx_%s_org_score ON %I(organization_id, overall_score DESC)',
                   partition_name, partition_name);
    EXECUTE format('CREATE INDEX idx_%s_user_status ON %I(user_id, status)',
                   partition_name, partition_name);

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- 创建当前和未来12个月的分区
SELECT create_quality_assessment_partition(DATE_TRUNC('month', NOW() + (n || ' months')::INTERVAL)::DATE)
FROM generate_series(-1, 12) AS n;

-- 自动分区维护任务
CREATE OR REPLACE FUNCTION maintain_quality_assessment_partitions()
RETURNS VOID AS $$
DECLARE
    next_month DATE;
    old_partition DATE;
BEGIN
    -- 创建下个月分区
    next_month := DATE_TRUNC('month', NOW() + INTERVAL '2 months')::DATE;
    PERFORM create_quality_assessment_partition(next_month);

    -- 删除12个月前的分区 (保留历史数据政策)
    old_partition := DATE_TRUNC('month', NOW() - INTERVAL '12 months')::DATE;
    EXECUTE format('DROP TABLE IF EXISTS quality_assessments_y%sm%s CASCADE',
                   EXTRACT(YEAR FROM old_partition),
                   LPAD(EXTRACT(MONTH FROM old_partition)::TEXT, 2, '0'));
END;
$$ LANGUAGE plpgsql;

-- 设置定时任务 (使用pg_cron扩展)
SELECT cron.schedule('maintain-partitions', '0 0 1 * *', 'SELECT maintain_quality_assessment_partitions();');
```

#### AI分析结果分区 (按季度分区)

```sql
-- AI分析结果按季度分区
CREATE TABLE ai_analysis_tasks_partitioned (
    LIKE ai_analysis_tasks INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建季度分区函数
CREATE OR REPLACE FUNCTION create_ai_analysis_quarter_partition(start_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
    quarter INTEGER;
BEGIN
    quarter := EXTRACT(QUARTER FROM start_date);
    partition_name := 'ai_analysis_tasks_y' ||
                     EXTRACT(YEAR FROM start_date) || 'q' || quarter;

    end_date := start_date + INTERVAL '3 months';

    EXECUTE format(
        'CREATE TABLE %I PARTITION OF ai_analysis_tasks_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    -- 创建分区索引
    EXECUTE format('CREATE INDEX idx_%s_org_model ON %I(organization_id, ai_model)',
                   partition_name, partition_name);
    EXECUTE format('CREATE INDEX idx_%s_status_priority ON %I(status, priority DESC)',
                   partition_name, partition_name);

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- 创建当前季度和未来4个季度的分区
SELECT create_ai_analysis_quarter_partition(DATE_TRUNC('quarter', NOW() + (n || ' quarters')::INTERVAL)::DATE)
FROM generate_series(-1, 4) AS n;
```

### 2. 租户分区策略

#### 多租户数据隔离分区

```sql
-- 按组织ID进行哈希分区 (适合大规模多租户)
CREATE TABLE data_sources_partitioned (
    LIKE data_sources INCLUDING ALL
) PARTITION BY HASH (organization_id);

-- 创建8个哈希分区
CREATE TABLE data_sources_part_0 PARTITION OF data_sources_partitioned
    FOR VALUES WITH (modulus 8, remainder 0);
CREATE TABLE data_sources_part_1 PARTITION OF data_sources_partitioned
    FOR VALUES WITH (modulus 8, remainder 1);
-- ... 重复创建所有分区

-- 为每个分区创建特定索引
DO $$
DECLARE
    partition_num INTEGER;
BEGIN
    FOR partition_num IN 0..7 LOOP
        EXECUTE format('CREATE INDEX idx_data_sources_part_%s_user_type ON data_sources_part_%s(user_id, source_type)',
                       partition_num, partition_num);
        EXECUTE format('CREATE INDEX idx_data_sources_part_%s_status_updated ON data_sources_part_%s(status, updated_at)',
                       partition_num, partition_num);
    END LOOP;
END $$;
```

### 3. 数据源类型分区

```sql
-- 按数据源类型分区 (List分区)
CREATE TABLE source_schemas_partitioned (
    LIKE source_schemas INCLUDING ALL
) PARTITION BY LIST (data_source_type);

-- 文件类型数据源
CREATE TABLE source_schemas_file PARTITION OF source_schemas_partitioned
    FOR VALUES IN ('file');

-- 数据库类型数据源
CREATE TABLE source_schemas_database PARTITION OF source_schemas_partitioned
    FOR VALUES IN ('database');

-- API类型数据源
CREATE TABLE source_schemas_api PARTITION OF source_schemas_partitioned
    FOR VALUES IN ('api');

-- 云存储类型数据源
CREATE TABLE source_schemas_cloud PARTITION OF source_schemas_partitioned
    FOR VALUES IN ('cloud_storage');

-- 实时流数据源
CREATE TABLE source_schemas_stream PARTITION OF source_schemas_partitioned
    FOR VALUES IN ('stream');
```

## 🔍 高级索引策略

### 1. 复合索引设计

```sql
-- 用户工作台查询优化
CREATE INDEX idx_user_dashboard_optimized ON quality_assessments(
    user_id,
    status,
    created_at DESC,
    overall_score DESC
) WHERE status IN ('completed', 'running');

-- 组织数据概览查询优化
CREATE INDEX idx_org_data_overview ON data_sources(
    organization_id,
    is_active,
    source_type,
    updated_at DESC
) WHERE is_active = TRUE;

-- AI任务队列优化
CREATE INDEX idx_ai_task_queue_optimized ON ai_analysis_tasks(
    status,
    priority DESC,
    organization_id,
    created_at ASC
) WHERE status IN ('pending', 'running');

-- 质量趋势分析优化
CREATE INDEX idx_quality_trend_analysis ON quality_assessments(
    data_source_id,
    created_at DESC,
    overall_score,
    status
) WHERE status = 'completed' AND created_at >= NOW() - INTERVAL '6 months';
```

### 2. 部分索引策略

```sql
-- 活跃数据源索引
CREATE INDEX idx_active_data_sources ON data_sources(organization_id, updated_at DESC)
WHERE status = 'ready' AND is_active = TRUE;

-- 失败任务快速查询
CREATE INDEX idx_failed_assessments ON quality_assessments(user_id, created_at DESC, error_message)
WHERE status = 'failed';

-- 高价值评估索引
CREATE INDEX idx_high_quality_assessments ON quality_assessments(data_source_id, overall_score DESC)
WHERE overall_score >= 80 AND status = 'completed';

-- 即将到期订阅索引
CREATE INDEX idx_expiring_subscriptions ON organization_subscriptions(next_billing_date, organization_id)
WHERE subscription_status = 'active' AND next_billing_date <= NOW() + INTERVAL '7 days';
```

### 3. 表达式索引

```sql
-- JSON字段查询优化
CREATE INDEX idx_assessment_details_completeness ON quality_assessments
USING GIN ((dimension_details->'completeness'));

CREATE INDEX idx_data_source_file_size ON data_sources ((schema_metadata->>'file_size')::BIGINT)
WHERE source_type = 'file';

-- 文本搜索优化
CREATE INDEX idx_data_source_search ON data_sources
USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- 时间范围查询优化
CREATE INDEX idx_assessment_date_range ON quality_assessments (DATE_TRUNC('day', created_at))
WHERE created_at >= NOW() - INTERVAL '30 days';
```

### 4. GIN和GiST索引

```sql
-- JSONB字段全文索引
CREATE INDEX idx_quality_dimension_details ON quality_assessments
USING GIN (dimension_details);

CREATE INDEX idx_ai_analysis_results ON ai_analysis_tasks
USING GIN (analysis_results);

CREATE INDEX idx_connection_config_search ON connection_configs
USING GIN (connection_config);

-- 数组字段索引
CREATE INDEX idx_quality_rules_tags ON quality_rules
USING GIN (tags);

CREATE INDEX idx_subscription_plan_features ON subscription_plans
USING GIN (allowed_source_types);

-- 地理空间索引 (如果有地理位置数据)
CREATE INDEX idx_org_location ON organizations
USING GIST (location_point) WHERE location_point IS NOT NULL;
```

## ⚡ 查询优化策略

### 1. 查询重写和优化

```sql
-- 创建物化视图优化重复查询
CREATE MATERIALIZED VIEW mv_organization_stats AS
SELECT
    o.id as organization_id,
    o.name as organization_name,
    o.subscription_tier,
    COUNT(DISTINCT ds.id) as total_data_sources,
    COUNT(DISTINCT qa.id) as total_assessments,
    ROUND(AVG(qa.overall_score), 2) as avg_quality_score,
    COUNT(DISTINCT om.user_id) as total_users,
    SUM(COALESCE((ds.schema_metadata->>'data_size_bytes')::BIGINT, 0)) as total_data_bytes,
    MAX(qa.created_at) as last_assessment_date,
    COUNT(DISTINCT qa.id) FILTER (WHERE qa.created_at >= NOW() - INTERVAL '30 days') as recent_assessments
FROM organizations o
LEFT JOIN data_sources ds ON o.id = ds.organization_id AND ds.is_active = TRUE
LEFT JOIN quality_assessments qa ON ds.id = qa.data_source_id AND qa.status = 'completed'
LEFT JOIN organization_members om ON o.id = om.organization_id
GROUP BY o.id, o.name, o.subscription_tier;

-- 创建唯一索引
CREATE UNIQUE INDEX idx_mv_org_stats_id ON mv_organization_stats(organization_id);

-- 定时刷新物化视图
SELECT cron.schedule('refresh-org-stats', '*/15 * * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_organization_stats;');
```

### 2. 分析型查询优化

```sql
-- 质量趋势分析物化视图
CREATE MATERIALIZED VIEW mv_quality_trends AS
SELECT
    ds.organization_id,
    ds.id as data_source_id,
    ds.name as data_source_name,
    ds.source_type,
    DATE_TRUNC('week', qa.created_at) as week_start,
    AVG(qa.overall_score) as avg_overall_score,
    AVG(qa.completeness_score) as avg_completeness_score,
    AVG(qa.consistency_score) as avg_consistency_score,
    AVG(qa.accuracy_score) as avg_accuracy_score,
    AVG(qa.timeliness_score) as avg_timeliness_score,
    COUNT(*) as assessment_count,
    MIN(qa.overall_score) as min_score,
    MAX(qa.overall_score) as max_score,
    STDDEV_POP(qa.overall_score) as score_stddev
FROM data_sources ds
JOIN quality_assessments qa ON ds.id = qa.data_source_id
WHERE qa.status = 'completed'
  AND qa.created_at >= NOW() - INTERVAL '24 weeks'
GROUP BY ds.organization_id, ds.id, ds.name, ds.source_type, DATE_TRUNC('week', qa.created_at)
ORDER BY week_start DESC;

CREATE INDEX idx_mv_quality_trends_lookup ON mv_quality_trends(organization_id, data_source_id, week_start DESC);
```

### 3. 实时查询优化

```sql
-- 用户仪表板实时数据视图
CREATE VIEW v_user_dashboard_realtime AS
SELECT
    u.id as user_id,
    COUNT(DISTINCT ds.id) as my_data_sources,
    COUNT(DISTINCT qa.id) as my_assessments,
    COUNT(DISTINCT qa.id) FILTER (WHERE qa.status = 'running') as running_assessments,
    COUNT(DISTINCT qa.id) FILTER (WHERE qa.created_at >= NOW() - INTERVAL '24 hours') as recent_assessments,
    ROUND(AVG(qa.overall_score) FILTER (WHERE qa.status = 'completed'), 2) as avg_quality_score,
    MAX(qa.created_at) as last_assessment_time,
    COUNT(DISTINCT aat.id) FILTER (WHERE aat.status = 'pending') as pending_ai_tasks
FROM users u
LEFT JOIN data_sources ds ON u.id = ds.user_id AND ds.is_active = TRUE
LEFT JOIN quality_assessments qa ON ds.id = qa.data_source_id
LEFT JOIN ai_analysis_tasks aat ON ds.id = aat.data_source_id
GROUP BY u.id;
```

## 🗄️ 缓存架构设计

### 1. Redis缓存策略

```python
# 缓存配置和策略
CACHE_CONFIG = {
    # 用户会话缓存 (短期)
    'user_sessions': {
        'ttl': 1800,  # 30分钟
        'key_pattern': 'session:{user_id}',
        'compress': False
    },

    # 组织统计缓存 (中期)
    'org_stats': {
        'ttl': 900,   # 15分钟
        'key_pattern': 'org_stats:{org_id}',
        'compress': True
    },

    # 质量评估结果缓存 (长期)
    'quality_results': {
        'ttl': 3600,  # 1小时
        'key_pattern': 'quality:{assessment_id}',
        'compress': True
    },

    # AI分析结果缓存 (长期)
    'ai_results': {
        'ttl': 7200,  # 2小时
        'key_pattern': 'ai_result:{task_id}',
        'compress': True
    },

    # 数据源元数据缓存 (长期)
    'source_metadata': {
        'ttl': 1800,  # 30分钟
        'key_pattern': 'source_meta:{source_id}',
        'compress': True
    }
}

# 缓存预热策略
def cache_warmup_strategy():
    return {
        'user_login': [
            'load_user_dashboard_data',
            'load_recent_data_sources',
            'load_subscription_info'
        ],
        'org_switch': [
            'load_org_stats',
            'load_org_data_sources',
            'load_org_members'
        ],
        'data_source_view': [
            'load_source_metadata',
            'load_recent_assessments',
            'load_quality_history'
        ]
    }
```

### 2. 应用级缓存

```sql
-- 创建缓存表
CREATE TABLE application_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    cache_type VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 缓存索引
CREATE INDEX idx_app_cache_type_expires ON application_cache(cache_type, expires_at);
CREATE INDEX idx_app_cache_expires ON application_cache(expires_at);

-- 缓存清理函数
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM application_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 定时清理过期缓存
SELECT cron.schedule('cleanup-cache', '0 */2 * * *', 'SELECT cleanup_expired_cache();');
```

## 📊 连接池和负载均衡

### 1. 数据库连接池配置

```yaml
# 生产环境连接池配置
database_pools:
  primary_db:
    host: "47.79.87.199"
    port: 5432
    database: "saascontrol_prod_pro1"

    # 连接池大小
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true

    # 读写分离
    read_replicas:
      - host: "47.79.87.200"
        weight: 100
      - host: "47.79.87.201"
        weight: 100

    # 连接参数优化
    connect_args:
      connect_timeout: 10
      command_timeout: 300
      server_settings:
        statement_timeout: "300s"
        idle_in_transaction_session_timeout: "60s"

  secondary_db:
    host: "47.79.87.199"
    port: 5432
    database: "saascontrol_prod_pro2"

    pool_size: 15
    max_overflow: 20
    pool_timeout: 30
    pool_recycle: 3600

    # AI分析专用优化
    connect_args:
      server_settings:
        work_mem: "256MB"
        maintenance_work_mem: "1GB"
        effective_cache_size: "4GB"
```

### 2. 读写分离策略

```python
class DatabaseRouter:
    """数据库读写分离路由器"""

    def __init__(self):
        self.write_db = "primary"
        self.read_dbs = ["primary", "replica1", "replica2"]
        self.read_weights = [30, 35, 35]  # 主库承担30%读取

    def route_query(self, query_type, table_name=None):
        if query_type in ['INSERT', 'UPDATE', 'DELETE']:
            return self.write_db

        if query_type == 'SELECT':
            # 实时数据查询路由到主库
            if table_name in ['user_sessions', 'ai_analysis_tasks']:
                return self.write_db

            # 分析查询路由到读库
            return random.choices(self.read_dbs, weights=self.read_weights)[0]

        return self.write_db

# 查询路由示例
router = DatabaseRouter()

# 实时查询 -> 主库
db = router.route_query('SELECT', 'user_sessions')

# 分析查询 -> 读库
db = router.route_query('SELECT', 'quality_assessments')
```

## 🔧 数据库参数优化

### 1. PostgreSQL性能参数

```sql
-- 内存相关参数
ALTER SYSTEM SET shared_buffers = '4GB';           -- 共享缓冲区
ALTER SYSTEM SET effective_cache_size = '12GB';     -- 有效缓存大小
ALTER SYSTEM SET work_mem = '256MB';                -- 单个查询工作内存
ALTER SYSTEM SET maintenance_work_mem = '1GB';      -- 维护操作内存

-- 并发和连接参数
ALTER SYSTEM SET max_connections = 200;             -- 最大连接数
ALTER SYSTEM SET max_worker_processes = 16;         -- 最大工作进程
ALTER SYSTEM SET max_parallel_workers = 12;         -- 最大并行工作者
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- WAL和检查点参数
ALTER SYSTEM SET wal_buffers = '64MB';              -- WAL缓冲区
ALTER SYSTEM SET checkpoint_completion_target = 0.9; -- 检查点完成目标
ALTER SYSTEM SET max_wal_size = '4GB';              -- 最大WAL大小
ALTER SYSTEM SET min_wal_size = '1GB';              -- 最小WAL大小

-- 查询优化参数
ALTER SYSTEM SET random_page_cost = 1.1;            -- 随机页面成本
ALTER SYSTEM SET seq_page_cost = 1.0;               -- 顺序页面成本
ALTER SYSTEM SET cpu_tuple_cost = 0.01;             -- CPU元组成本
ALTER SYSTEM SET cpu_index_tuple_cost = 0.005;      -- CPU索引元组成本

-- 自动清理参数
ALTER SYSTEM SET autovacuum_max_workers = 6;        -- 自动清理最大工作者
ALTER SYSTEM SET autovacuum_naptime = '30s';        -- 自动清理间隔
ALTER SYSTEM SET autovacuum_vacuum_threshold = 500; -- 清理阈值
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;

-- 统计收集参数
ALTER SYSTEM SET track_counts = on;                 -- 启用统计收集
ALTER SYSTEM SET track_functions = 'all';           -- 跟踪函数
ALTER SYSTEM SET track_activity_query_size = 4096;  -- 查询大小跟踪

-- 重载配置
SELECT pg_reload_conf();
```

### 2. 分析和监控

```sql
-- 性能监控查询
CREATE VIEW v_database_performance AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    ROUND(n_dead_tup::NUMERIC / GREATEST(n_live_tup + n_dead_tup, 1) * 100, 2) as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY dead_tuple_percent DESC;

-- 慢查询监控
CREATE VIEW v_slow_queries AS
SELECT
    query,
    calls,
    total_time,
    ROUND(mean_time::NUMERIC, 2) as avg_time_ms,
    ROUND((100 * total_time / sum(total_time) OVER())::NUMERIC, 2) as percent_total,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) as hit_percent
FROM pg_stat_statements
WHERE calls > 100  -- 排除偶发查询
ORDER BY total_time DESC
LIMIT 20;

-- 索引使用率监控
CREATE VIEW v_index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    CASE
        WHEN idx_tup_read = 0 THEN 0
        ELSE ROUND(idx_tup_fetch::NUMERIC / idx_tup_read * 100, 2)
    END as fetch_ratio,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
```

这个性能优化方案为数据管理平台提供了全方位的性能保障，确保系统能够处理大规模数据和高并发访问需求。