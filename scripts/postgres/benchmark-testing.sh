#!/bin/bash
# =============================================================================
# PostgreSQL Performance Benchmark Testing Suite
# SaaS Control Deck - Multi-Environment Testing
# =============================================================================
# Comprehensive performance testing for different workload patterns
# Optimized for AI data processing and multi-tenant architecture

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database connection settings
DB_HOST="47.79.87.199"
DB_PORT="5432"
DB_USER="jackchan"
DB_PASSWORD="secure_password_123"

# Test databases
declare -A DATABASES=(
    ["dev_pro1"]="saascontrol_dev_pro1"
    ["dev_pro2"]="saascontrol_dev_pro2"
    ["stage_pro1"]="saascontrol_stage_pro1"
    ["stage_pro2"]="saascontrol_stage_pro2"
    ["prod_pro1"]="saascontrol_prod_pro1"
    ["prod_pro2"]="saascontrol_prod_pro2"
)

# Test configuration
RESULTS_DIR="./benchmark_results_$(date +%Y%m%d_%H%M%S)"
PGBENCH_SCALE=10
PGBENCH_TIME=60
CONNECTIONS_ARRAY=(1 5 10 20 50)
AI_WORKLOAD_DURATION=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_results_dir() {
    mkdir -p "$RESULTS_DIR"
    log_info "Created results directory: $RESULTS_DIR"
}

# =============================================================================
# DATABASE CONNECTION TESTING
# =============================================================================

test_database_connection() {
    local env=$1
    local db_name=$2
    
    log_info "Testing connection to $env ($db_name)..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Connection to $env successful"
        return 0
    else
        log_error "Connection to $env failed"
        return 1
    fi
}

test_all_connections() {
    log_info "Testing all database connections..."
    local failed_count=0
    
    for env in "${!DATABASES[@]}"; do
        if ! test_database_connection "$env" "${DATABASES[$env]}"; then
            ((failed_count++))
        fi
    done
    
    if [ $failed_count -eq 0 ]; then
        log_success "All database connections successful"
        return 0
    else
        log_error "$failed_count database connection(s) failed"
        return 1
    fi
}

# =============================================================================
# PGBENCH STANDARD BENCHMARKS
# =============================================================================

initialize_pgbench() {
    local env=$1
    local db_name=$2
    
    log_info "Initializing pgbench for $env..."
    
    PGPASSWORD="$DB_PASSWORD" pgbench -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
        -i -s "$PGBENCH_SCALE" --foreign-keys > "$RESULTS_DIR/pgbench_init_$env.log" 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "pgbench initialized for $env"
    else
        log_error "Failed to initialize pgbench for $env"
        return 1
    fi
}

run_pgbench_test() {
    local env=$1
    local db_name=$2
    local connections=$3
    local test_type=$4
    
    log_info "Running pgbench test for $env (connections: $connections, type: $test_type)..."
    
    local output_file="$RESULTS_DIR/pgbench_${env}_c${connections}_${test_type}.txt"
    
    case $test_type in
        "read_only")
            local pgbench_args="-S"
            ;;
        "read_write")
            local pgbench_args=""
            ;;
        "write_only")
            local pgbench_args="-N"
            ;;
        *)
            local pgbench_args=""
            ;;
    esac
    
    PGPASSWORD="$DB_PASSWORD" pgbench -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
        -c "$connections" -j "$connections" -T "$PGBENCH_TIME" $pgbench_args \
        --progress=10 > "$output_file" 2>&1
    
    if [ $? -eq 0 ]; then
        local tps=$(grep "tps =" "$output_file" | awk '{print $3}')
        local latency=$(grep "latency average =" "$output_file" | awk '{print $4}')
        log_success "pgbench $test_type test for $env completed: $tps TPS, ${latency}ms latency"
        
        # Extract key metrics
        echo "$env,$test_type,$connections,$tps,$latency" >> "$RESULTS_DIR/pgbench_summary.csv"
    else
        log_error "pgbench $test_type test for $env failed"
        return 1
    fi
}

run_all_pgbench_tests() {
    log_info "Running comprehensive pgbench tests..."
    
    # Create CSV header
    echo "Environment,TestType,Connections,TPS,Latency_ms" > "$RESULTS_DIR/pgbench_summary.csv"
    
    for env in "${!DATABASES[@]}"; do
        local db_name="${DATABASES[$env]}"
        
        # Initialize pgbench for this database
        initialize_pgbench "$env" "$db_name"
        
        # Run tests with different connection counts and types
        for connections in "${CONNECTIONS_ARRAY[@]}"; do
            for test_type in "read_only" "read_write" "write_only"; do
                run_pgbench_test "$env" "$db_name" "$connections" "$test_type"
                sleep 5  # Cool down between tests
            done
        done
    done
    
    log_success "All pgbench tests completed"
}

# =============================================================================
# AI WORKLOAD SIMULATION
# =============================================================================

create_ai_workload_test_data() {
    local env=$1
    local db_name=$2
    
    log_info "Creating AI workload test data for $env..."
    
    local sql_file="$RESULTS_DIR/ai_test_data_$env.sql"
    
    cat > "$sql_file" << 'EOF'
-- Create test users if not exists
INSERT INTO users (id, email, username, password_hash, is_active, is_verified)
SELECT 
    gen_random_uuid(),
    'test_user_' || generate_series || '@benchmark.test',
    'test_user_' || generate_series,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewruNLTL0z8LG6ki', -- bcrypt hash for 'password'
    true,
    true
FROM generate_series(1, 100)
ON CONFLICT (email) DO NOTHING;

-- Create test projects
INSERT INTO projects (id, name, description, owner_id, status)
SELECT 
    gen_random_uuid(),
    'Benchmark Project ' || generate_series,
    'Test project for performance benchmarking',
    (SELECT id FROM users WHERE email LIKE 'test_user_%' ORDER BY random() LIMIT 1),
    'active'
FROM generate_series(1, 20)
ON CONFLICT DO NOTHING;

-- Create AI models for testing
INSERT INTO ai_models (id, name, version, model_type, configuration, is_active)
VALUES 
    (gen_random_uuid(), 'GPT-Test-Model', '1.0', 'language_model', '{"temperature": 0.7}', true),
    (gen_random_uuid(), 'Vision-Test-Model', '2.1', 'vision_model', '{"threshold": 0.8}', true),
    (gen_random_uuid(), 'Analysis-Test-Model', '1.5', 'analysis_model', '{"depth": 3}', true)
ON CONFLICT (name, version) DO NOTHING;
EOF

    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
        -f "$sql_file" > "$RESULTS_DIR/ai_test_data_$env.log" 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "AI workload test data created for $env"
    else
        log_error "Failed to create AI workload test data for $env"
        return 1
    fi
}

run_ai_task_simulation() {
    local env=$1
    local db_name=$2
    local concurrent_tasks=$3
    
    log_info "Running AI task simulation for $env (concurrent tasks: $concurrent_tasks)..."
    
    local sql_file="$RESULTS_DIR/ai_simulation_$env.sql"
    local output_file="$RESULTS_DIR/ai_simulation_${env}_c${concurrent_tasks}.txt"
    
    cat > "$sql_file" << 'EOF'
\set project_id `echo "SELECT id FROM projects ORDER BY random() LIMIT 1;" | psql -h 47.79.87.199 -U jackchan -d DATABASE_NAME -t -A`
\set user_id `echo "SELECT id FROM users WHERE email LIKE 'test_user_%' ORDER BY random() LIMIT 1;" | psql -h 47.79.87.199 -U jackchan -d DATABASE_NAME -t -A`
\set model_id `echo "SELECT id FROM ai_models ORDER BY random() LIMIT 1;" | psql -h 47.79.87.199 -U jackchan -d DATABASE_NAME -t -A`

WITH new_task AS (
    INSERT INTO ai_tasks (project_id, user_id, task_name, task_type, status, input_data, started_at)
    VALUES (
        :project_id::uuid,
        :user_id::uuid,
        'Benchmark Task ' || extract(epoch from now()),
        'benchmark_test',
        'running',
        '{"test": true, "data": "benchmark_input_' || extract(epoch from now()) || '"}',
        now()
    )
    RETURNING id
),
task_result AS (
    INSERT INTO ai_results (task_id, model_id, result_data, confidence_score, processing_time_ms)
    SELECT 
        id,
        :model_id::uuid,
        '{"result": "benchmark_output", "status": "success"}',
        random() * 0.3 + 0.7,  -- Random confidence between 0.7 and 1.0
        (random() * 5000 + 500)::integer  -- Random processing time 500-5500ms
    FROM new_task
    RETURNING task_id
)
UPDATE ai_tasks 
SET 
    status = 'completed',
    completed_at = now(),
    output_data = '{"benchmark": true, "completed": true}'
WHERE id IN (SELECT task_id FROM task_result);
EOF

    # Replace DATABASE_NAME placeholder
    sed -i "s/DATABASE_NAME/$db_name/g" "$sql_file"
    
    # Run the simulation
    PGPASSWORD="$DB_PASSWORD" pgbench -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
        -c "$concurrent_tasks" -j "$concurrent_tasks" -T "$AI_WORKLOAD_DURATION" -f "$sql_file" \
        --progress=30 > "$output_file" 2>&1
    
    if [ $? -eq 0 ]; then
        local tps=$(grep "tps =" "$output_file" | awk '{print $3}')
        local latency=$(grep "latency average =" "$output_file" | awk '{print $4}')
        log_success "AI simulation for $env completed: $tps TPS, ${latency}ms latency"
        
        # Record results
        echo "$env,ai_workload,$concurrent_tasks,$tps,$latency" >> "$RESULTS_DIR/ai_workload_summary.csv"
    else
        log_error "AI simulation for $env failed"
        return 1
    fi
}

run_ai_workload_tests() {
    log_info "Running AI workload simulations..."
    
    # Create CSV header
    echo "Environment,TestType,Connections,TPS,Latency_ms" > "$RESULTS_DIR/ai_workload_summary.csv"
    
    for env in "${!DATABASES[@]}"; do
        local db_name="${DATABASES[$env]}"
        
        # Create test data
        create_ai_workload_test_data "$env" "$db_name"
        
        # Run AI simulations with different concurrency levels
        for connections in 1 5 10 20; do
            run_ai_task_simulation "$env" "$db_name" "$connections"
            sleep 10  # Cool down between tests
        done
    done
    
    log_success "All AI workload tests completed"
}

# =============================================================================
# QUERY PERFORMANCE TESTING
# =============================================================================

run_query_performance_test() {
    local env=$1
    local db_name=$2
    
    log_info "Running query performance tests for $env..."
    
    local sql_file="$RESULTS_DIR/query_performance_$env.sql"
    local output_file="$RESULTS_DIR/query_performance_$env.txt"
    
    cat > "$sql_file" << 'EOF'
-- Test 1: Complex JOIN query (Dashboard overview)
\timing on
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    p.name as project_name,
    COUNT(t.id) as total_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_tasks,
    AVG(EXTRACT(EPOCH FROM (t.completed_at - t.started_at))) as avg_duration,
    COUNT(r.id) as total_results,
    AVG(r.confidence_score) as avg_confidence
FROM projects p
LEFT JOIN ai_tasks t ON p.id = t.project_id
LEFT JOIN ai_results r ON t.id = r.task_id
WHERE t.created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY p.id, p.name
ORDER BY total_tasks DESC
LIMIT 20;

-- Test 2: Time-series aggregation query
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    task_type,
    COUNT(*) as task_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration
FROM ai_tasks
WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '7 days')
    AND completed_at IS NOT NULL
GROUP BY DATE_TRUNC('hour', created_at), task_type
ORDER BY hour DESC, task_count DESC;

-- Test 3: JSON query performance
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    task_name,
    input_data->>'test' as test_flag,
    output_data->'result' as result
FROM ai_tasks
WHERE input_data ? 'test'
    AND (output_data->>'status') = 'success'
    AND created_at > (CURRENT_TIMESTAMP - INTERVAL '1 day')
ORDER BY created_at DESC
LIMIT 100;

-- Test 4: Full-text search
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    id,
    task_name,
    ts_rank(to_tsvector('english', task_name), to_tsquery('english', 'benchmark')) as rank
FROM ai_tasks
WHERE to_tsvector('english', task_name) @@ to_tsquery('english', 'benchmark')
ORDER BY rank DESC
LIMIT 50;

-- Test 5: Aggregate with window functions
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    service_name,
    log_level,
    COUNT(*) as log_count,
    COUNT(*) OVER (PARTITION BY service_name) as service_total,
    PERCENT_RANK() OVER (PARTITION BY service_name ORDER BY COUNT(*)) as percentile_rank
FROM system_logs
WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '1 hour')
GROUP BY service_name, log_level
ORDER BY log_count DESC;
\timing off
EOF

    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
        -f "$sql_file" > "$output_file" 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "Query performance test completed for $env"
        
        # Extract timing information
        grep "Time:" "$output_file" | awk '{print $2}' | sed 's/ms//' > "$RESULTS_DIR/query_times_$env.txt"
    else
        log_error "Query performance test failed for $env"
        return 1
    fi
}

run_all_query_performance_tests() {
    log_info "Running query performance tests on all environments..."
    
    for env in "${!DATABASES[@]}"; do
        local db_name="${DATABASES[$env]}"
        run_query_performance_test "$env" "$db_name"
        sleep 5
    done
    
    log_success "All query performance tests completed"
}

# =============================================================================
# CONNECTION POOL TESTING
# =============================================================================

test_connection_pool_performance() {
    local env=$1
    local db_name=$2
    local max_connections=$3
    
    log_info "Testing connection pool performance for $env (max connections: $max_connections)..."
    
    local output_file="$RESULTS_DIR/connection_pool_$env.txt"
    
    # Simple connection test script
    cat > "$RESULTS_DIR/connection_test.sql" << 'EOF'
SELECT 
    COUNT(*) as connection_test,
    pg_backend_pid() as backend_pid,
    current_timestamp as test_time;
EOF

    # Test with increasing connection counts
    for ((i=1; i<=max_connections; i++)); do
        start_time=$(date +%s.%N)
        
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" \
            -f "$RESULTS_DIR/connection_test.sql" > /dev/null 2>&1
        
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        
        echo "Connection $i: ${duration}s" >> "$output_file"
        
        if [ $i -eq 1 ] || [ $((i % 10)) -eq 0 ]; then
            log_info "Connection $i/$max_connections tested (${duration}s)"
        fi
    done
    
    log_success "Connection pool test completed for $env"
}

run_connection_pool_tests() {
    log_info "Running connection pool performance tests..."
    
    for env in "${!DATABASES[@]}"; do
        local db_name="${DATABASES[$env]}"
        
        # Test with different connection limits based on environment
        local max_conn
        case $env in
            *dev*)
                max_conn=10
                ;;
            *stage*)
                max_conn=20
                ;;
            *prod*)
                max_conn=50
                ;;
            *)
                max_conn=10
                ;;
        esac
        
        test_connection_pool_performance "$env" "$db_name" "$max_conn"
    done
    
    log_success "All connection pool tests completed"
}

# =============================================================================
# SYSTEM RESOURCE MONITORING
# =============================================================================

collect_system_metrics() {
    local duration=$1
    local output_file="$RESULTS_DIR/system_metrics.txt"
    
    log_info "Collecting system metrics for ${duration}s..."
    
    {
        echo "=== System Metrics Collection Started at $(date) ==="
        echo "Duration: ${duration} seconds"
        echo
        
        # CPU and memory info
        echo "=== CPU Information ==="
        lscpu | head -20
        echo
        
        echo "=== Memory Information ==="
        free -h
        echo
        
        echo "=== Disk Usage ==="
        df -h
        echo
        
    } > "$output_file"
    
    # Collect metrics during test
    local end_time=$(($(date +%s) + duration))
    local sample_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        {
            echo "=== Sample $((++sample_count)) at $(date) ==="
            
            # CPU usage
            echo "CPU Usage:"
            top -bn1 | grep "Cpu(s)" | awk '{print "CPU: " $2 " user, " $4 " system, " $8 " idle"}'
            
            # Memory usage
            echo "Memory Usage:"
            free | grep Mem | awk '{printf "Memory: %.2f%% used (%s/%s)\n", $3*100/$2, $3, $2}'
            
            # Disk I/O
            if command -v iostat > /dev/null; then
                echo "Disk I/O:"
                iostat -x 1 1 | tail -n +4
            fi
            
            echo
        } >> "$output_file"
        
        sleep 10
    done
    
    log_success "System metrics collection completed"
}

# =============================================================================
# RESULTS ANALYSIS AND REPORTING
# =============================================================================

generate_performance_report() {
    local report_file="$RESULTS_DIR/performance_report.html"
    
    log_info "Generating performance report..."
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>SaaS Control Deck - PostgreSQL Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .metric { background: #e9e9e9; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .good { background: #d4edda; }
        .warning { background: #fff3cd; }
        .critical { background: #f8d7da; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SaaS Control Deck - PostgreSQL Performance Report</h1>
        <p>Generated on: $(date)</p>
        <p>Test Duration: Multiple test suites</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric">
            <strong>Databases Tested:</strong> $(echo "${!DATABASES[@]}" | wc -w)
        </div>
        <div class="metric">
            <strong>Test Types:</strong> Standard Benchmark, AI Workload Simulation, Query Performance, Connection Pool
        </div>
    </div>

    <div class="section">
        <h2>pgbench Results Summary</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Test Type</th>
                <th>Best TPS</th>
                <th>Worst Latency (ms)</th>
                <th>Optimal Connections</th>
            </tr>
EOF

    # Process pgbench results if available
    if [ -f "$RESULTS_DIR/pgbench_summary.csv" ]; then
        tail -n +2 "$RESULTS_DIR/pgbench_summary.csv" | while IFS=, read -r env test_type connections tps latency; do
            echo "<tr><td>$env</td><td>$test_type</td><td>$connections</td><td>$tps</td><td>$latency</td></tr>" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << 'EOF'
        </table>
    </div>

    <div class="section">
        <h2>AI Workload Performance</h2>
        <p>Simulation results for AI task processing patterns:</p>
        <table>
            <tr>
                <th>Environment</th>
                <th>Concurrent Tasks</th>
                <th>Tasks/Second</th>
                <th>Average Latency</th>
            </tr>
EOF

    # Process AI workload results if available
    if [ -f "$RESULTS_DIR/ai_workload_summary.csv" ]; then
        tail -n +2 "$RESULTS_DIR/ai_workload_summary.csv" | while IFS=, read -r env test_type connections tps latency; do
            echo "<tr><td>$env</td><td>$connections</td><td>$tps</td><td>$latency ms</td></tr>" >> "$report_file"
        done
    fi

    cat >> "$report_file" << 'EOF'
        </table>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <div class="metric good">
            <strong>Optimizations Applied:</strong>
            <ul>
                <li>Connection pool tuning per environment</li>
                <li>Index optimization for AI workloads</li>
                <li>Table partitioning for high-volume data</li>
                <li>Memory configuration optimization</li>
            </ul>
        </div>
        
        <div class="metric warning">
            <strong>Monitor:</strong>
            <ul>
                <li>Connection pool utilization during peak hours</li>
                <li>Query performance degradation over time</li>
                <li>Partition maintenance requirements</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>Detailed Results</h2>
        <p>Complete benchmark results and logs are available in:</p>
        <ul>
            <li>pgbench results: pgbench_*.txt</li>
            <li>AI workload results: ai_simulation_*.txt</li>
            <li>Query performance: query_performance_*.txt</li>
            <li>System metrics: system_metrics.txt</li>
        </ul>
    </div>
</body>
</html>
EOF

    log_success "Performance report generated: $report_file"
}

create_summary_csv() {
    local summary_file="$RESULTS_DIR/benchmark_summary.csv"
    
    log_info "Creating benchmark summary CSV..."
    
    {
        echo "Timestamp,Environment,TestType,Metric,Value,Unit"
        
        # Process pgbench results
        if [ -f "$RESULTS_DIR/pgbench_summary.csv" ]; then
            tail -n +2 "$RESULTS_DIR/pgbench_summary.csv" | while IFS=, read -r env test_type connections tps latency; do
                echo "$(date -Iseconds),$env,pgbench_$test_type,tps,$tps,transactions_per_second"
                echo "$(date -Iseconds),$env,pgbench_$test_type,latency,$latency,milliseconds"
                echo "$(date -Iseconds),$env,pgbench_$test_type,connections,$connections,count"
            done
        fi
        
        # Process AI workload results
        if [ -f "$RESULTS_DIR/ai_workload_summary.csv" ]; then
            tail -n +2 "$RESULTS_DIR/ai_workload_summary.csv" | while IFS=, read -r env test_type connections tps latency; do
                echo "$(date -Iseconds),$env,ai_workload,tps,$tps,tasks_per_second"
                echo "$(date -Iseconds),$env,ai_workload,latency,$latency,milliseconds"
                echo "$(date -Iseconds),$env,ai_workload,connections,$connections,count"
            done
        fi
        
    } > "$summary_file"
    
    log_success "Benchmark summary created: $summary_file"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -a, --all          Run all benchmark tests (default)"
    echo "  -c, --connections  Test database connections only"
    echo "  -p, --pgbench     Run pgbench standard tests"
    echo "  -i, --ai          Run AI workload simulation"
    echo "  -q, --queries     Run query performance tests"
    echo "  -l, --pool        Run connection pool tests"
    echo "  -m, --monitor     Collect system metrics (5min)"
    echo "  -r, --report      Generate reports only"
    echo "  -h, --help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --all          # Run complete benchmark suite"
    echo "  $0 -p -i          # Run pgbench and AI workload tests"
    echo "  $0 --connections  # Test database connectivity only"
}

main() {
    local run_all=true
    local run_connections=false
    local run_pgbench=false
    local run_ai=false
    local run_queries=false
    local run_pool=false
    local run_monitor=false
    local run_report=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                run_all=true
                shift
                ;;
            -c|--connections)
                run_all=false
                run_connections=true
                shift
                ;;
            -p|--pgbench)
                run_all=false
                run_pgbench=true
                shift
                ;;
            -i|--ai)
                run_all=false
                run_ai=true
                shift
                ;;
            -q|--queries)
                run_all=false
                run_queries=true
                shift
                ;;
            -l|--pool)
                run_all=false
                run_pool=true
                shift
                ;;
            -m|--monitor)
                run_all=false
                run_monitor=true
                shift
                ;;
            -r|--report)
                run_all=false
                run_report=true
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Create results directory
    create_results_dir
    
    log_info "Starting PostgreSQL Performance Benchmark Suite"
    log_info "Results will be saved to: $RESULTS_DIR"
    
    # Always test connections first
    if ! test_all_connections; then
        log_error "Database connectivity issues detected. Please resolve before running benchmarks."
        exit 1
    fi
    
    # Run selected test suites
    if [ "$run_all" = true ]; then
        log_info "Running complete benchmark suite..."
        collect_system_metrics 60 &
        MONITOR_PID=$!
        
        run_all_pgbench_tests
        run_ai_workload_tests
        run_all_query_performance_tests
        run_connection_pool_tests
        
        # Wait for monitoring to complete
        wait $MONITOR_PID
        
    else
        [ "$run_connections" = true ] && log_success "Database connections tested successfully"
        [ "$run_pgbench" = true ] && run_all_pgbench_tests
        [ "$run_ai" = true ] && run_ai_workload_tests
        [ "$run_queries" = true ] && run_all_query_performance_tests
        [ "$run_pool" = true ] && run_connection_pool_tests
        [ "$run_monitor" = true ] && collect_system_metrics 300
    fi
    
    # Generate reports (unless only testing connections)
    if [ "$run_connections" != true ] || [ "$run_report" = true ]; then
        generate_performance_report
        create_summary_csv
    fi
    
    log_success "Benchmark suite completed successfully!"
    log_info "Results available in: $RESULTS_DIR"
    
    # Display quick summary
    echo
    echo "=== Quick Results Summary ==="
    if [ -f "$RESULTS_DIR/pgbench_summary.csv" ]; then
        echo "Top performing configuration (TPS):"
        tail -n +2 "$RESULTS_DIR/pgbench_summary.csv" | sort -t, -k4 -nr | head -1 | \
            awk -F, '{printf "  %s (%s): %.2f TPS, %.2f ms latency\n", $1, $2, $4, $5}'
    fi
    
    if [ -f "$RESULTS_DIR/ai_workload_summary.csv" ]; then
        echo "Best AI workload performance:"
        tail -n +2 "$RESULTS_DIR/ai_workload_summary.csv" | sort -t, -k4 -nr | head -1 | \
            awk -F, '{printf "  %s: %.2f tasks/sec, %.2f ms latency\n", $1, $4, $5}'
    fi
    
    echo
    echo "View the complete report at: file://$PWD/$RESULTS_DIR/performance_report.html"
}

# Run main function with all arguments
main "$@"