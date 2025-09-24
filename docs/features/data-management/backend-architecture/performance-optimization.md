# 数据管理功能 - 性能优化方案

## ⚡ 性能优化概览

针对数据管理功能的核心需求：100MB文件30秒内完成分析、支持100+并发用户、API响应时间<500ms，设计多层次性能优化方案，确保系统在高负载下的稳定运行。

## 🎯 性能目标与指标

### 核心性能指标

```python
PERFORMANCE_TARGETS = {
    # 文件处理性能
    "file_upload_100mb": "< 30 seconds",
    "file_parsing_speed": "> 50MB/second",
    "chunk_processing": "< 2 seconds per 8MB chunk",

    # 质量分析性能
    "4_dimension_analysis": "< 15 seconds",
    "analysis_throughput": "> 20 concurrent analyses",
    "scoring_calculation": "< 3 seconds",

    # API响应性能
    "cached_api_response": "< 100ms",
    "uncached_api_response": "< 500ms",
    "ai_chat_response": "< 3 seconds",

    # 系统并发性能
    "concurrent_users": "> 100",
    "concurrent_uploads": "> 20",
    "concurrent_analyses": "> 50",

    # 数据库性能
    "query_response_time": "< 100ms (95th percentile)",
    "connection_pool_efficiency": "> 90%",
    "cache_hit_rate": "> 85%"
}
```

### 监控指标体系

```python
# Prometheus监控指标
MONITORING_METRICS = {
    # 吞吐量指标
    "requests_per_second": "rate(http_requests_total[5m])",
    "file_processing_rate": "rate(files_processed_total[5m])",
    "analysis_completion_rate": "rate(analyses_completed_total[5m])",

    # 延迟指标
    "api_response_time_p95": "histogram_quantile(0.95, http_request_duration_seconds)",
    "file_processing_time_p95": "histogram_quantile(0.95, file_processing_duration_seconds)",
    "ai_response_time_p95": "histogram_quantile(0.95, ai_response_duration_seconds)",

    # 资源利用率
    "cpu_usage": "100 - (avg(irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
    "memory_usage": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
    "disk_io_wait": "avg(irate(node_cpu_seconds_total{mode='iowait'}[5m])) * 100",

    # 缓存性能
    "redis_hit_rate": "redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)",
    "cache_memory_usage": "redis_memory_used_bytes / redis_memory_max_bytes"
}
```

## 🗄️ 数据库性能优化

### 连接池优化配置

```python
# PostgreSQL连接池配置
DATABASE_CONFIG = {
    "pool_size": 20,  # 基础连接数
    "max_overflow": 30,  # 最大溢出连接
    "pool_timeout": 10,  # 获取连接超时时间
    "pool_recycle": 3600,  # 连接回收时间
    "pool_pre_ping": True,  # 连接健康检查

    # 异步连接池配置
    "async_pool_size": 50,
    "async_max_overflow": 50,
    "command_timeout": 60,
    "server_settings": {
        "application_name": "data_management_service",
        "jit": "off"  # 对于短查询关闭JIT
    }
}

# 连接池监控和自适应调整
class AdaptiveConnectionPool:
    async def adjust_pool_size(self):
        current_load = await self.get_current_load()
        if current_load > 0.8:
            # 高负载时增加连接数
            await self.increase_pool_size(factor=1.2)
        elif current_load < 0.3:
            # 低负载时减少连接数
            await self.decrease_pool_size(factor=0.8)
```

### 查询优化策略

```sql
-- 质量分析查询优化
-- 1. 使用分区表提升查询性能
CREATE TABLE quality_assessments_partitioned (
    LIKE quality_assessments INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 按月分区
CREATE TABLE quality_assessments_y2024m09 PARTITION OF quality_assessments_partitioned
FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

-- 2. 优化索引策略
-- 复合索引优化
CREATE INDEX CONCURRENTLY idx_quality_user_time_score
ON quality_assessments (user_id, created_at DESC, overall_score DESC)
WHERE analysis_status = 'completed';

-- 部分索引 - 只索引有效数据
CREATE INDEX CONCURRENTLY idx_data_sources_active
ON data_sources (user_id, created_at DESC)
WHERE upload_status = 'completed' AND processing_progress = 100;

-- 3. 查询性能优化
-- 使用窗口函数替代子查询
WITH latest_assessments AS (
    SELECT
        data_source_id,
        overall_score,
        quality_grade,
        ROW_NUMBER() OVER (PARTITION BY data_source_id ORDER BY created_at DESC) as rn
    FROM quality_assessments
    WHERE analysis_status = 'completed'
)
SELECT
    ds.id,
    ds.name,
    la.overall_score,
    la.quality_grade
FROM data_sources ds
LEFT JOIN latest_assessments la ON ds.id = la.data_source_id AND la.rn = 1
WHERE ds.user_id = $1 AND ds.upload_status = 'completed';
```

### 数据库分离策略

```python
# 读写分离配置
DATABASE_ROUTING = {
    "write_operations": {
        "host": "47.79.87.199",
        "port": 5432,
        "database": "saascontrol_dev_pro1",
        "pool_size": 20,
        "operations": ["INSERT", "UPDATE", "DELETE", "CREATE", "ALTER"]
    },
    "read_operations": {
        "host": "47.79.87.199",  # 可配置只读副本
        "port": 5432,
        "database": "saascontrol_dev_pro1",
        "pool_size": 30,
        "operations": ["SELECT"]
    }
}

# 智能路由决策
class DatabaseRouter:
    async def route_query(self, operation: str, query: str):
        if operation in ["SELECT"] and "FOR UPDATE" not in query:
            return self.read_pool
        else:
            return self.write_pool
```

## 🔄 缓存优化策略

### 多层缓存架构

```python
# Redis缓存层次设计
CACHE_LAYERS = {
    # L1 - 应用内存缓存 (最热数据)
    "l1_cache": {
        "type": "in_memory",
        "max_size": "500MB",
        "ttl": 300,  # 5分钟
        "use_cases": ["user_sessions", "api_rate_limits", "hot_quality_scores"]
    },

    # L2 - Redis缓存 (热数据)
    "l2_cache": {
        "type": "redis",
        "max_memory": "2GB",
        "ttl": 1800,  # 30分钟
        "use_cases": ["quality_analysis_results", "ai_chat_context", "file_metadata"]
    },

    # L3 - Redis持久化缓存 (温数据)
    "l3_cache": {
        "type": "redis_persistent",
        "ttl": 7200,  # 2小时
        "use_cases": ["user_dashboards", "historical_trends", "report_templates"]
    }
}

# 智能缓存预热
class IntelligentCacheWarming:
    async def warm_user_cache(self, user_id: str):
        """用户登录时预热相关缓存"""
        tasks = [
            self.cache_recent_data_sources(user_id),
            self.cache_latest_quality_scores(user_id),
            self.cache_user_preferences(user_id),
            self.cache_active_chat_sessions(user_id)
        ]
        await asyncio.gather(*tasks)

    async def predictive_warming(self):
        """基于使用模式预测性缓存"""
        # 分析用户行为模式，预热可能需要的数据
        popular_datasets = await self.get_trending_datasets()
        for dataset_id in popular_datasets:
            await self.cache_quality_results(dataset_id)
```

### 缓存键策略

```python
# 缓存键命名规范和分层
CACHE_KEY_PATTERNS = {
    # 用户数据缓存
    "user_data_sources": "user:{user_id}:data_sources:page:{page}",
    "user_quality_dashboard": "user:{user_id}:dashboard:quality",
    "user_preferences": "user:{user_id}:preferences",

    # 分析结果缓存
    "quality_analysis": "analysis:{analysis_id}:results",
    "analysis_progress": "analysis:{analysis_id}:progress",
    "quality_scores": "scores:{data_source_id}:latest",

    # AI相关缓存
    "ai_chat_context": "chat:{session_id}:context",
    "ai_response_cache": "ai:response:{hash}",
    "ai_insights": "insights:{analysis_id}:ai",

    # 系统级缓存
    "api_rate_limit": "ratelimit:{user_id}:{endpoint}",
    "file_upload_progress": "upload:{upload_id}:progress",
    "system_stats": "stats:system:{period}"
}

# 缓存失效策略
class CacheInvalidation:
    async def invalidate_user_data(self, user_id: str):
        """用户数据更新时的缓存失效"""
        patterns = [
            f"user:{user_id}:*",
            f"dashboard:{user_id}:*"
        ]
        await self.redis.delete_by_patterns(patterns)

    async def invalidate_analysis_chain(self, data_source_id: str):
        """数据源分析链的缓存失效"""
        patterns = [
            f"scores:{data_source_id}:*",
            f"analysis:*:results",  # 相关分析结果
            f"insights:{data_source_id}:*"
        ]
        await self.redis.delete_by_patterns(patterns)
```

## 🔄 异步处理优化

### Celery任务队列优化

```python
# Celery性能配置
CELERY_CONFIG = {
    # 并发配置
    "worker_concurrency": 8,  # 每个Worker的并发数
    "worker_prefetch_multiplier": 2,  # 预取任务数
    "task_acks_late": True,  # 任务完成后确认
    "worker_disable_rate_limits": False,

    # 任务路由优化
    "task_routes": {
        "quality_analysis.analyze_data_quality": {
            "queue": "cpu_intensive",
            "routing_key": "cpu.quality_analysis"
        },
        "ai_chat.generate_response": {
            "queue": "io_intensive",
            "routing_key": "io.ai_response"
        },
        "file_processing.process_large_file": {
            "queue": "memory_intensive",
            "routing_key": "memory.file_process"
        }
    },

    # 结果缓存配置
    "result_backend": "redis://localhost:6379/1",
    "result_expires": 3600,  # 结果保存1小时
    "task_ignore_result": False,

    # 监控配置
    "worker_send_task_events": True,
    "task_send_sent_event": True
}

# 动态任务优先级调整
class TaskPriorityManager:
    def get_task_priority(self, task_type: str, user_priority: str) -> int:
        """动态计算任务优先级"""
        base_priority = {
            "user_interaction": 10,  # 用户交互任务最高优先级
            "quality_analysis": 7,   # 质量分析中等优先级
            "report_generation": 5,   # 报告生成较低优先级
            "data_cleanup": 1        # 清理任务最低优先级
        }

        user_boost = {
            "premium": 3,
            "standard": 1,
            "free": 0
        }

        return base_priority.get(task_type, 5) + user_boost.get(user_priority, 0)
```

### 文件处理并行化

```python
# 大文件并行处理策略
class ParallelFileProcessor:
    def __init__(self):
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        self.max_workers = 4  # 每个文件最大并行度

    async def process_large_file(self, file_path: str) -> dict:
        """并行处理大文件"""
        # 1. 文件分块
        chunks = await self.split_file_into_chunks(file_path)

        # 2. 创建处理任务
        semaphore = asyncio.Semaphore(self.max_workers)
        tasks = []

        for chunk_info in chunks:
            task = self.process_chunk_with_semaphore(
                semaphore, chunk_info
            )
            tasks.append(task)

        # 3. 并行执行
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 合并结果
        return await self.merge_chunk_results(chunk_results)

    async def process_chunk_with_semaphore(self, semaphore, chunk_info):
        """使用信号量控制并发"""
        async with semaphore:
            return await self.process_single_chunk(chunk_info)

# 质量分析并行化
class ParallelQualityAnalyzer:
    async def analyze_4_dimensions_parallel(self, data_frame):
        """4维度质量分析并行化"""
        # 创建并行分析任务
        analysis_tasks = [
            self.analyze_completeness(data_frame),
            self.analyze_consistency(data_frame),
            self.analyze_accuracy(data_frame),
            self.analyze_timeliness(data_frame)
        ]

        # 并行执行分析
        start_time = time.time()
        results = await asyncio.gather(*analysis_tasks)
        analysis_duration = time.time() - start_time

        # 合并结果并计算综合评分
        comprehensive_score = self.calculate_comprehensive_score(results)

        return {
            "completeness": results[0],
            "consistency": results[1],
            "accuracy": results[2],
            "timeliness": results[3],
            "overall": comprehensive_score,
            "analysis_duration": analysis_duration
        }
```

## 🖥️ API性能优化

### 响应时间优化

```python
# API响应缓存中间件
class APIResponseCacheMiddleware:
    def __init__(self):
        self.cache = Redis()
        self.cache_duration = {
            "GET": 300,    # GET请求缓存5分钟
            "POST": 0,     # POST请求不缓存
            "static": 3600  # 静态数据缓存1小时
        }

    async def __call__(self, request: Request, call_next):
        # 检查是否可以缓存
        if self.is_cacheable(request):
            cache_key = self.generate_cache_key(request)
            cached_response = await self.cache.get(cache_key)

            if cached_response:
                return self.deserialize_response(cached_response)

        # 执行请求
        response = await call_next(request)

        # 缓存响应
        if self.should_cache_response(request, response):
            await self.cache_response(request, response)

        return response

# 数据预聚合
class DataPreAggregation:
    async def precompute_dashboard_data(self, user_id: str):
        """预计算仪表板数据"""
        # 计算用户的聚合统计数据
        stats = await self.calculate_user_stats(user_id)

        # 缓存预聚合结果
        cache_key = f"dashboard:{user_id}:precomputed"
        await self.redis.setex(
            cache_key,
            1800,  # 30分钟缓存
            json.dumps(stats)
        )

        return stats

    async def get_dashboard_data_fast(self, user_id: str):
        """快速获取仪表板数据"""
        cache_key = f"dashboard:{user_id}:precomputed"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # 缓存未命中，异步计算并返回基础数据
        asyncio.create_task(self.precompute_dashboard_data(user_id))
        return await self.get_basic_dashboard_data(user_id)
```

### 压缩和优化

```python
# API响应压缩
class CompressionMiddleware:
    def __init__(self):
        self.min_size = 1024  # 1KB以上才压缩
        self.compression_level = 6  # 中等压缩级别

    async def compress_response(self, response_data: bytes):
        """智能响应压缩"""
        if len(response_data) < self.min_size:
            return response_data

        # 根据内容类型选择压缩算法
        if self.is_json_content(response_data):
            return await self.compress_with_gzip(response_data)
        elif self.is_binary_content(response_data):
            return await self.compress_with_lz4(response_data)

        return response_data

# 请求批处理
class BatchRequestProcessor:
    async def batch_quality_scores(self, data_source_ids: List[str]):
        """批量获取质量评分"""
        # 将多个单独请求合并为一个数据库查询
        scores = await self.db.fetch_multiple_quality_scores(data_source_ids)

        # 并行缓存结果
        cache_tasks = []
        for data_source_id, score in scores.items():
            cache_key = f"scores:{data_source_id}:latest"
            task = self.redis.setex(cache_key, 1800, json.dumps(score))
            cache_tasks.append(task)

        await asyncio.gather(*cache_tasks)
        return scores
```

## 🔧 系统级优化

### 内存优化

```python
# 内存池管理
class MemoryPoolManager:
    def __init__(self):
        self.pools = {
            "small": {"size": 1024, "count": 1000},      # 1KB * 1000
            "medium": {"size": 8192, "count": 500},      # 8KB * 500
            "large": {"size": 65536, "count": 100},      # 64KB * 100
            "xlarge": {"size": 1048576, "count": 20}     # 1MB * 20
        }
        self.available_buffers = {}
        self.used_buffers = {}

    async def get_buffer(self, size: int):
        """获取合适大小的内存缓冲区"""
        pool_type = self.get_pool_type(size)

        if pool_type in self.available_buffers and self.available_buffers[pool_type]:
            return self.available_buffers[pool_type].pop()

        # 创建新缓冲区
        return bytearray(self.pools[pool_type]["size"])

    async def return_buffer(self, buffer, pool_type: str):
        """归还内存缓冲区"""
        # 清理缓冲区
        buffer[:] = b'\x00' * len(buffer)

        # 归还到可用池
        if pool_type not in self.available_buffers:
            self.available_buffers[pool_type] = []

        self.available_buffers[pool_type].append(buffer)

# 垃圾回收优化
import gc
import psutil

class GCOptimizer:
    def __init__(self):
        self.memory_threshold = 0.8  # 内存使用率阈值
        self.gc_interval = 60  # GC检查间隔(秒)

    async def monitor_memory_and_gc(self):
        """监控内存使用并智能触发GC"""
        while True:
            memory_percent = psutil.virtual_memory().percent / 100

            if memory_percent > self.memory_threshold:
                # 强制垃圾回收
                collected = gc.collect()
                logger.info(f"Forced GC collected {collected} objects, memory: {memory_percent:.2%}")

                # 如果内存仍然很高，降低缓存大小
                if memory_percent > 0.9:
                    await self.reduce_cache_size()

            await asyncio.sleep(self.gc_interval)
```

### CPU优化

```python
# CPU亲和性设置
import os

class CPUOptimizer:
    def __init__(self):
        self.cpu_count = os.cpu_count()
        self.process_affinity = self.setup_cpu_affinity()

    def setup_cpu_affinity(self):
        """设置进程CPU亲和性"""
        # 为不同类型的任务分配不同的CPU核心
        return {
            "api_workers": list(range(0, self.cpu_count // 2)),
            "celery_workers": list(range(self.cpu_count // 2, self.cpu_count)),
            "io_workers": [0, 1],  # IO密集型任务使用少量核心
            "cpu_workers": list(range(2, self.cpu_count))  # CPU密集型任务使用多核心
        }

    def set_worker_affinity(self, worker_type: str):
        """为Worker进程设置CPU亲和性"""
        if worker_type in self.process_affinity:
            os.sched_setaffinity(0, self.process_affinity[worker_type])

# 异步IO优化
class AsyncIOOptimizer:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=20)

    async def run_cpu_bound_task(self, func, *args):
        """在线程池中运行CPU密集型任务"""
        return await self.loop.run_in_executor(self.executor, func, *args)

    async def run_io_bound_task(self, coro):
        """优化IO密集型任务"""
        return await asyncio.wait_for(coro, timeout=30)
```

## 📊 性能监控和告警

### 实时性能监控

```python
# 性能指标收集器
class PerformanceCollector:
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            "api_response_time": 500,  # ms
            "cpu_usage": 80,           # %
            "memory_usage": 85,        # %
            "cache_hit_rate": 80,      # %
            "queue_length": 100        # 任务数
        }

    async def collect_metrics(self):
        """收集系统性能指标"""
        metrics = {
            "timestamp": time.time(),
            "api_response_time": await self.get_avg_response_time(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "cache_hit_rate": await self.get_cache_hit_rate(),
            "active_connections": await self.get_active_connections(),
            "queue_length": await self.get_queue_length()
        }

        # 检查阈值并发送告警
        await self.check_thresholds(metrics)

        return metrics

    async def check_thresholds(self, metrics):
        """检查性能阈值并发送告警"""
        for metric_name, value in metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]

                if metric_name == "cache_hit_rate" and value < threshold:
                    await self.send_alert(f"Cache hit rate too low: {value}%")
                elif metric_name != "cache_hit_rate" and value > threshold:
                    await self.send_alert(f"{metric_name} too high: {value}")

# 自适应性能调整
class AdaptivePerformanceTuner:
    async def auto_tune_based_on_load(self):
        """基于负载自动调整性能参数"""
        current_load = await self.get_current_system_load()

        if current_load > 0.8:
            # 高负载时的优化策略
            await self.increase_worker_count()
            await self.reduce_cache_ttl()
            await self.enable_aggressive_gc()
        elif current_load < 0.3:
            # 低负载时的节能策略
            await self.reduce_worker_count()
            await self.increase_cache_ttl()
            await self.reduce_gc_frequency()
```

## 🎯 性能测试和基准

### 压力测试配置

```python
# 性能基准测试
class PerformanceBenchmark:
    async def benchmark_file_upload(self):
        """文件上传性能基准测试"""
        test_files = [
            {"size": "10MB", "path": "test_10mb.csv"},
            {"size": "50MB", "path": "test_50mb.csv"},
            {"size": "100MB", "path": "test_100mb.csv"}
        ]

        results = {}
        for test_file in test_files:
            start_time = time.time()
            await self.upload_and_process_file(test_file["path"])
            duration = time.time() - start_time

            results[test_file["size"]] = {
                "duration": duration,
                "throughput": test_file["size_bytes"] / duration / 1024 / 1024  # MB/s
            }

        return results

    async def benchmark_concurrent_analyses(self, concurrent_count: int = 20):
        """并发质量分析性能测试"""
        tasks = []
        for i in range(concurrent_count):
            task = self.run_quality_analysis(f"test_dataset_{i}")
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        successful_analyses = len([r for r in results if not isinstance(r, Exception)])

        return {
            "concurrent_count": concurrent_count,
            "successful_analyses": successful_analyses,
            "total_duration": total_duration,
            "avg_duration_per_analysis": total_duration / successful_analyses,
            "analyses_per_second": successful_analyses / total_duration
        }
```

这个性能优化方案为数据管理功能提供了全面的性能保障，确保系统在高负载下能够稳定运行并满足所有性能指标要求。