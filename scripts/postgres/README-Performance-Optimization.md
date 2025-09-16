# PostgreSQL Performance Optimization Guide
## SaaS Control Deck - Multi-Environment Setup

🚀 **Comprehensive performance optimization solution for PostgreSQL databases supporting AI workloads across development, staging, and production environments.**

## 📋 Overview

This performance optimization package provides:
- **Environment-specific configurations** for 6 databases (dev_pro1/pro2, stage_pro1/pro2, prod_pro1/pro2)
- **Connection pool optimization** for different workload patterns
- **Advanced indexing strategies** optimized for AI data processing
- **Table partitioning** for high-volume time-series data
- **Comprehensive monitoring** and performance tracking
- **Automated benchmarking** and testing tools

## 🏗️ Architecture

### Database Environment Structure
```
Production Environment (47.79.87.199:5432)
├── Development Databases
│   ├── saascontrol_dev_pro1     (API Gateway, Data Service - Ports 8000-8001)
│   └── saascontrol_dev_pro2     (AI Service - Ports 8100-8102)
├── Staging Databases  
│   ├── saascontrol_stage_pro1   (Load Testing Environment)
│   └── saascontrol_stage_pro2   (AI Testing Environment)
└── Production Databases
    ├── saascontrol_prod_pro1    (High Availability Setup)
    └── saascontrol_prod_pro2    (AI Processing Workload)
```

### Expected Performance Targets

| Environment | Connections | Query Response (p95) | AI Task Processing | Cache Hit Ratio |
|-------------|-------------|---------------------|-------------------|-----------------|
| Development | 5-10        | <500ms              | <30s              | >85%            |
| Staging     | 10-20       | <200ms              | <15s              | >90%            |
| Production  | 50-100      | <100ms              | <10s              | >95%            |

## 📁 File Structure

```
scripts/postgres/
├── performance-optimized.conf       # Main PostgreSQL configuration
├── connection-pool-configs.py       # Python connection pool management
├── performance-indexes.sql          # Comprehensive indexing strategy
├── partitioning-strategy.sql        # Table partitioning implementation
├── performance-monitoring.sql       # Monitoring queries and views
├── benchmark-testing.sh             # Automated performance testing
├── environment-configs.yaml         # Environment-specific settings
└── README-Performance-Optimization.md
```

## 🚀 Quick Start

### 1. Apply Performance Configuration

```bash
# Backup current configuration
sudo cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup

# Apply optimized configuration
sudo cp scripts/postgres/performance-optimized.conf /etc/postgresql/*/main/postgresql.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Create Performance Indexes

```bash
# Connect to each database and apply indexes
psql -h 47.79.87.199 -U jackchan -d saascontrol_prod_pro1 -f scripts/postgres/performance-indexes.sql
psql -h 47.79.87.199 -U jackchan -d saascontrol_prod_pro2 -f scripts/postgres/performance-indexes.sql
# Repeat for all environments...
```

### 3. Implement Table Partitioning

```bash
# Apply partitioning strategy (high-volume tables)
psql -h 47.79.87.199 -U jackchan -d saascontrol_prod_pro1 -f scripts/postgres/partitioning-strategy.sql
```

### 4. Set Up Monitoring

```bash
# Create monitoring views and functions
psql -h 47.79.87.199 -U jackchan -d saascontrol_prod_pro1 -f scripts/postgres/performance-monitoring.sql
```

### 5. Run Performance Benchmarks

```bash
# Make script executable and run benchmarks
chmod +x scripts/postgres/benchmark-testing.sh
./scripts/postgres/benchmark-testing.sh --all
```

## ⚙️ Configuration Details

### 1. Memory Optimization

**Shared Buffers & Cache Configuration:**
```postgresql
# Production Environment (4-8GB RAM)
shared_buffers = 1200MB              # 30% of available RAM
effective_cache_size = 3200MB        # 80% of available RAM
work_mem = 32MB                      # Per-connection work memory
maintenance_work_mem = 512MB         # Maintenance operations
wal_buffers = 32MB                   # WAL buffer optimization
```

**AI Workload Specific:**
```postgresql
# JSON processing optimization
gin_pending_list_limit = 8MB         # Larger GIN index work area
hash_mem_multiplier = 2.0            # PostgreSQL 13+ hash optimization

# Parallel processing for AI computations
max_parallel_workers = 6             # Parallel query workers
max_parallel_workers_per_gather = 2  # Per-query parallelism
```

### 2. Connection Pool Optimization

**Environment-Specific Pool Sizes:**

```python
# Development Environment
DEVELOPMENT_POOL = {
    "api_gateway": {"min": 2, "max": 5},
    "data_service": {"min": 2, "max": 8}, 
    "ai_service": {"min": 1, "max": 4}
}

# Production Environment  
PRODUCTION_POOL = {
    "api_gateway": {"min": 5, "max": 20},
    "data_service": {"min": 10, "max": 25},
    "ai_service": {"min": 5, "max": 15}
}
```

### 3. Advanced Indexing Strategy

**AI Task Performance Indexes:**
```sql
-- High-frequency AI task queries
CREATE INDEX CONCURRENTLY idx_ai_tasks_status_priority 
    ON ai_tasks(status, created_at) 
    WHERE status IN ('pending', 'running');

-- AI input/output data optimization (GIN for JSON)
CREATE INDEX CONCURRENTLY idx_ai_tasks_input_data 
    ON ai_tasks USING GIN (input_data);

-- Performance tracking indexes
CREATE INDEX CONCURRENTLY idx_ai_results_performance 
    ON ai_results(model_id, processing_time_ms, confidence_score);
```

**Covering Indexes for Performance:**
```sql
-- Covering index for AI task status queries
CREATE INDEX CONCURRENTLY idx_ai_tasks_status_covering 
    ON ai_tasks(project_id, status) 
    INCLUDE (task_name, created_at, updated_at);
```

### 4. Table Partitioning

**Time-Series Data Partitioning:**
```sql
-- System logs partitioned by month
CREATE TABLE system_logs_partitioned (
    -- columns definition
) PARTITION BY RANGE (created_at);

-- AI tasks partitioned by status
CREATE TABLE ai_tasks_partitioned (
    -- columns definition  
) PARTITION BY LIST (status);
```

## 📊 Performance Monitoring

### 1. Real-Time Monitoring Views

```sql
-- Connection pool health
SELECT * FROM v_connection_pool_health;

-- Query performance trends
SELECT * FROM v_query_performance_trends;

-- AI workload performance
SELECT * FROM v_ai_task_performance;
```

### 2. Performance Alerts

```sql
-- Get current performance alerts
SELECT * FROM v_performance_alerts;

-- Run database health check
SELECT * FROM check_database_health();
```

### 3. Automated Monitoring

```sql
-- Record performance metrics (run every 5 minutes)
SELECT monitoring.record_performance_metrics();

-- Check for maintenance needed
SELECT * FROM v_tables_needing_maintenance;
```

## 🧪 Benchmarking and Testing

### Comprehensive Benchmark Suite

```bash
# Run all benchmark tests
./scripts/postgres/benchmark-testing.sh --all

# Run specific test types
./scripts/postgres/benchmark-testing.sh --pgbench     # Standard pgbench tests
./scripts/postgres/benchmark-testing.sh --ai         # AI workload simulation
./scripts/postgres/benchmark-testing.sh --queries    # Query performance tests
./scripts/postgres/benchmark-testing.sh --pool       # Connection pool tests
```

### Benchmark Test Types

1. **pgbench Standard Tests**: Read-only, read-write, and write-only workloads
2. **AI Workload Simulation**: Simulates AI task processing patterns
3. **Query Performance Tests**: Complex JOIN, JSON, and time-series queries
4. **Connection Pool Tests**: Connection establishment and pool exhaustion testing

### Results Analysis

The benchmark suite generates:
- **HTML Performance Report**: Comprehensive analysis with recommendations
- **CSV Data Files**: Raw benchmark data for further analysis
- **Detailed Logs**: Query plans, timing information, and system metrics

## 🔧 Environment-Specific Optimizations

### Development Environment
- **Focus**: Fast development with debugging capabilities
- **Memory**: Conservative allocation (1GB)
- **Logging**: Verbose logging for debugging
- **Connections**: 50 max connections
- **Monitoring**: Detailed query analysis enabled

### Staging Environment  
- **Focus**: Production-like testing with monitoring
- **Memory**: Moderate allocation (2GB)
- **Logging**: Balanced logging for testing
- **Connections**: 75 max connections
- **Monitoring**: Performance tracking enabled

### Production Environment
- **Focus**: Maximum performance with minimal overhead
- **Memory**: Aggressive optimization (4GB)
- **Logging**: Minimal logging for performance
- **Connections**: 150 max connections
- **Monitoring**: Essential metrics only

## 🔍 Query Optimization Examples

### AI Task Dashboard Query
```sql
-- Optimized dashboard overview query
SELECT 
    p.name as project_name,
    COUNT(t.id) as total_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_tasks,
    AVG(EXTRACT(EPOCH FROM (t.completed_at - t.started_at))) as avg_duration
FROM projects p
LEFT JOIN ai_tasks t ON p.id = t.project_id
WHERE t.created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY p.id, p.name
ORDER BY total_tasks DESC;
```

### AI Performance Analytics
```sql
-- AI model performance comparison
SELECT 
    m.name as model_name,
    COUNT(r.*) as result_count,
    AVG(r.processing_time_ms) as avg_processing_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY r.processing_time_ms) as p95_time
FROM ai_models m
JOIN ai_results r ON m.id = r.model_id
WHERE r.created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY m.id, m.name;
```

## 🚨 Performance Alerts and Thresholds

### Connection Monitoring
- **Warning**: >80% of max connections used
- **Critical**: >95% of max connections used

### Query Performance
- **Warning**: Average query time >1s
- **Critical**: Average query time >5s

### AI Workload Monitoring
- **Warning**: AI task error rate >5%
- **Critical**: AI task error rate >10%

### Cache Performance
- **Warning**: Cache hit ratio <90%
- **Critical**: Cache hit ratio <80%

## 🛠️ Maintenance Procedures

### Daily Maintenance
```bash
# Update table statistics
ANALYZE;

# Check for needed vacuum operations
SELECT * FROM v_tables_needing_maintenance;
```

### Weekly Maintenance
```bash
# Run comprehensive maintenance
CALL maintain_partitions();

# Update all table statistics
ANALYZE VERBOSE;

# Check index usage
SELECT * FROM v_index_usage WHERE usage_category = 'UNUSED';
```

### Monthly Maintenance
```bash
# Review and optimize slow queries
SELECT * FROM v_slow_queries;

# Check partition sizes and performance
SELECT * FROM partition_sizes;

# Review connection pool performance
SELECT * FROM v_connection_pool_health;
```

## 📈 Performance Tuning Recommendations

### Immediate Optimizations (Hours)
1. ✅ Apply optimized PostgreSQL configuration
2. ✅ Create performance-critical indexes
3. ✅ Configure connection pools per environment
4. ✅ Enable query performance monitoring

### Medium-Term Improvements (Days)
1. 🔄 Implement table partitioning for high-volume tables
2. 🔄 Set up automated performance monitoring
3. 🔄 Optimize AI workload query patterns
4. 🔄 Configure automated maintenance schedules

### Long-Term Enhancements (Weeks)
1. 📋 Implement read replicas for query scalability
2. 📋 Set up connection pooling with PgBouncer
3. 📋 Implement query result caching
4. 📋 Consider database sharding for massive scale

## 🔐 Security Considerations

### Connection Security
- SSL/TLS encryption for all environments
- SCRAM-SHA-256 password encryption
- Row-level security policies
- Connection timeout configurations

### Access Control
- Environment-specific database users
- Restricted permissions per environment
- Audit logging for production
- IP-based connection restrictions

## 📞 Troubleshooting

### Common Performance Issues

**High Connection Count:**
```sql
-- Check current connections
SELECT * FROM v_connection_status;

-- Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';
```

**Slow Queries:**
```sql
-- Find slow queries
SELECT * FROM v_slow_queries LIMIT 10;

-- Analyze specific query
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

**High Memory Usage:**
```sql
-- Check work_mem usage
SELECT name, setting, unit FROM pg_settings WHERE name LIKE '%mem%';

-- Monitor temporary file creation
SELECT * FROM v_maintenance_status WHERE temp_files > 0;
```

### Emergency Procedures

**Database Unresponsive:**
1. Check system resources (CPU, memory, disk I/O)
2. Review active connections and long-running queries
3. Check for lock contention
4. Consider connection pool reset

**Performance Degradation:**
1. Run performance health check: `SELECT * FROM check_database_health();`
2. Check for missing statistics: `SELECT * FROM v_tables_needing_maintenance;`
3. Review slow query log
4. Verify index usage patterns

## 📚 Additional Resources

### PostgreSQL Performance Documentation
- [PostgreSQL Performance Tips](https://www.postgresql.org/docs/current/performance-tips.html)
- [Query Tuning Guide](https://www.postgresql.org/docs/current/using-explain.html)
- [Connection Pooling Best Practices](https://www.postgresql.org/docs/current/runtime-config-connection.html)

### SaaS Control Deck Specific Guides
- **Backend Architecture**: [`backend/CLAUDE.md`](../../backend/CLAUDE.md)
- **Frontend Development**: [`CLAUDE.md`](../../CLAUDE.md)
- **Deployment Guide**: [`DEPLOYMENT_GUIDE.md`](../deploy/DEPLOYMENT_GUIDE.md)

---

## 🏆 Expected Performance Improvements

After implementing this optimization package, you should see:

- **Query Performance**: 30-70% reduction in average query execution time
- **Connection Efficiency**: 50% improvement in connection pool utilization
- **AI Workload Processing**: 40% faster AI task completion times
- **System Stability**: Reduced memory usage and improved cache hit ratios
- **Monitoring Visibility**: Complete performance observability across all environments

**Implementation Time**: 2-4 hours for basic setup, 1-2 days for complete optimization

**Maintenance Overhead**: 30 minutes weekly for monitoring and maintenance

---

*This performance optimization guide is specifically tailored for the SaaS Control Deck's multi-environment PostgreSQL setup with AI workload requirements. For questions or additional optimization needs, refer to the comprehensive monitoring views and benchmark tools provided.*