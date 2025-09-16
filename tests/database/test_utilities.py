"""
数据库测试工具函数模块

提供通用的数据库测试辅助功能
"""

import asyncio
import asyncpg
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from . import TEST_ENVIRONMENTS


class DatabaseTestHelper:
    """数据库测试辅助类"""
    
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
    
    async def table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """检查表是否存在"""
        return await self.connection.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = $2
            )
            """,
            schema, table_name
        )
    
    async def column_exists(self, table_name: str, column_name: str, schema: str = 'public') -> bool:
        """检查列是否存在"""
        return await self.connection.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = $1 AND table_name = $2 AND column_name = $3
            )
            """,
            schema, table_name, column_name
        )
    
    async def get_table_row_count(self, table_name: str) -> int:
        """获取表行数"""
        return await self.connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
    
    async def get_table_columns(self, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """获取表的列信息"""
        columns = await self.connection.fetch(
            """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema, table_name
        )
        return [dict(col) for col in columns]
    
    async def get_table_constraints(self, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """获取表的约束信息"""
        constraints = await self.connection.fetch(
            """
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name as foreign_table_name,
                ccu.column_name as foreign_column_name
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_schema = $1 AND tc.table_name = $2
            ORDER BY tc.constraint_type, tc.constraint_name
            """,
            schema, table_name
        )
        return [dict(constraint) for constraint in constraints]
    
    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的索引信息"""
        indexes = await self.connection.fetch(
            """
            SELECT 
                i.relname as index_name,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary,
                array_agg(a.attname ORDER BY a.attnum) as columns
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON t.oid = a.attrelid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = $1 AND t.relkind = 'r'
            GROUP BY i.relname, ix.indisunique, ix.indisprimary
            ORDER BY i.relname
            """,
            table_name
        )
        return [dict(index) for index in indexes]
    
    async def get_database_size(self) -> Dict[str, Any]:
        """获取数据库大小信息"""
        size_info = await self.connection.fetchrow(
            """
            SELECT 
                current_database() as db_name,
                pg_database_size(current_database()) as size_bytes,
                pg_size_pretty(pg_database_size(current_database())) as size_human
            """
        )
        return dict(size_info)
    
    async def get_table_sizes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取表大小排行"""
        table_sizes = await self.connection.fetch(
            """
            SELECT 
                tablename,
                pg_total_relation_size(tablename::regclass) as size_bytes,
                pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size_human,
                pg_relation_size(tablename::regclass) as table_size_bytes,
                pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size_human
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(tablename::regclass) DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(table_size) for table_size in table_sizes]
    
    async def analyze_query_performance(self, query: str, *params) -> Dict[str, Any]:
        """分析查询性能"""
        # 获取查询计划
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        try:
            explain_result = await self.connection.fetchval(explain_query, *params)
            plan = explain_result[0] if explain_result else {}
            
            # 提取关键性能指标
            execution_time = plan.get('Execution Time', 0)
            planning_time = plan.get('Planning Time', 0)
            
            return {
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time_ms': execution_time,
                'planning_time_ms': planning_time,
                'total_time_ms': execution_time + planning_time,
                'plan': plan
            }
        except Exception as e:
            return {
                'query': query[:100] + '...' if len(query) > 100 else query,
                'error': str(e),
                'execution_time_ms': None
            }
    
    async def create_test_partition(self, base_table: str, partition_name: str, 
                                  range_start: str, range_end: str) -> bool:
        """创建测试分区"""
        try:
            await self.connection.execute(
                f"""
                CREATE TABLE {partition_name} PARTITION OF {base_table}
                FOR VALUES FROM ('{range_start}') TO ('{range_end}')
                """
            )
            return True
        except Exception as e:
            print(f"创建分区失败: {e}")
            return False
    
    async def create_test_index(self, table_name: str, columns: List[str], 
                              index_name: str = None, unique: bool = False) -> bool:
        """创建测试索引"""
        if index_name is None:
            index_name = f"test_idx_{table_name}_{'_'.join(columns)}"
        
        unique_keyword = "UNIQUE" if unique else ""
        columns_str = ", ".join(columns)
        
        try:
            await self.connection.execute(
                f"CREATE {unique_keyword} INDEX {index_name} ON {table_name} ({columns_str})"
            )
            return True
        except Exception as e:
            print(f"创建索引失败: {e}")
            return False
    
    async def drop_test_index(self, index_name: str) -> bool:
        """删除测试索引"""
        try:
            await self.connection.execute(f"DROP INDEX IF EXISTS {index_name}")
            return True
        except Exception as e:
            print(f"删除索引失败: {e}")
            return False


class DatabasePerformanceProfiler:
    """数据库性能分析器"""
    
    def __init__(self):
        self.query_stats = []
        self.connection_stats = []
    
    @asynccontextmanager
    async def profile_query(self, query_name: str, connection: asyncpg.Connection):
        """查询性能分析上下文管理器"""
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc)
        
        try:
            yield connection
        finally:
            end_time = time.time()
            end_timestamp = datetime.now(timezone.utc)
            
            self.query_stats.append({
                'query_name': query_name,
                'start_time': start_timestamp,
                'end_time': end_timestamp,
                'duration_seconds': end_time - start_time,
                'duration_ms': (end_time - start_time) * 1000
            })
    
    @asynccontextmanager
    async def profile_connection(self, connection_name: str):
        """连接性能分析上下文管理器"""
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc)
        
        try:
            yield
        finally:
            end_time = time.time()
            end_timestamp = datetime.now(timezone.utc)
            
            self.connection_stats.append({
                'connection_name': connection_name,
                'start_time': start_timestamp,
                'end_time': end_timestamp,
                'duration_seconds': end_time - start_time,
                'duration_ms': (end_time - start_time) * 1000
            })
    
    def get_query_summary(self) -> Dict[str, Any]:
        """获取查询性能摘要"""
        if not self.query_stats:
            return {'total_queries': 0}
        
        durations = [stat['duration_ms'] for stat in self.query_stats]
        
        return {
            'total_queries': len(self.query_stats),
            'total_time_ms': sum(durations),
            'avg_time_ms': sum(durations) / len(durations),
            'min_time_ms': min(durations),
            'max_time_ms': max(durations),
            'queries': self.query_stats
        }
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """获取连接性能摘要"""
        if not self.connection_stats:
            return {'total_connections': 0}
        
        durations = [stat['duration_ms'] for stat in self.connection_stats]
        
        return {
            'total_connections': len(self.connection_stats),
            'total_time_ms': sum(durations),
            'avg_time_ms': sum(durations) / len(durations),
            'min_time_ms': min(durations),
            'max_time_ms': max(durations),
            'connections': self.connection_stats
        }


class DatabaseDataValidator:
    """数据库数据验证器"""
    
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        self.validation_errors = []
    
    async def validate_email_format(self, table_name: str, email_column: str = 'email') -> Dict[str, Any]:
        """验证邮箱格式"""
        invalid_emails = await self.connection.fetch(
            f"""
            SELECT id, {email_column}
            FROM {table_name}
            WHERE {email_column} !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{{2,}}$'
            AND {email_column} IS NOT NULL
            LIMIT 10
            """
        )
        
        result = {
            'table': table_name,
            'column': email_column,
            'invalid_count': len(invalid_emails),
            'invalid_examples': [dict(row) for row in invalid_emails[:5]]
        }
        
        if invalid_emails:
            self.validation_errors.append(result)
        
        return result
    
    async def validate_phone_format(self, table_name: str, phone_column: str = 'phone') -> Dict[str, Any]:
        """验证电话号码格式"""
        invalid_phones = await self.connection.fetch(
            f"""
            SELECT id, {phone_column}
            FROM {table_name}
            WHERE {phone_column} !~ '^\\+?[1-9]\\d{{1,14}}$'
            AND {phone_column} IS NOT NULL
            LIMIT 10
            """
        )
        
        result = {
            'table': table_name,
            'column': phone_column,
            'invalid_count': len(invalid_phones),
            'invalid_examples': [dict(row) for row in invalid_phones[:5]]
        }
        
        if invalid_phones:
            self.validation_errors.append(result)
        
        return result
    
    async def validate_json_columns(self, table_name: str, json_columns: List[str]) -> Dict[str, Any]:
        """验证JSON列数据"""
        results = {}
        
        for column in json_columns:
            try:
                # 检查无效的JSON
                invalid_json = await self.connection.fetch(
                    f"""
                    SELECT id, {column}
                    FROM {table_name}
                    WHERE {column} IS NOT NULL
                    AND NOT ({column}::text ~ '^\\s*[[{{].*[}}\\]]\\s*$')
                    LIMIT 5
                    """
                )
                
                results[column] = {
                    'invalid_count': len(invalid_json),
                    'invalid_examples': [dict(row) for row in invalid_json]
                }
                
                if invalid_json:
                    self.validation_errors.append({
                        'table': table_name,
                        'column': column,
                        'error_type': 'invalid_json',
                        'count': len(invalid_json)
                    })
                    
            except Exception as e:
                results[column] = {'error': str(e)}
        
        return results
    
    async def validate_foreign_key_integrity(self, table_name: str, 
                                           foreign_key_column: str,
                                           referenced_table: str,
                                           referenced_column: str = 'id') -> Dict[str, Any]:
        """验证外键完整性"""
        orphaned_records = await self.connection.fetch(
            f"""
            SELECT t.id, t.{foreign_key_column}
            FROM {table_name} t
            LEFT JOIN {referenced_table} r ON t.{foreign_key_column} = r.{referenced_column}
            WHERE t.{foreign_key_column} IS NOT NULL
            AND r.{referenced_column} IS NULL
            LIMIT 10
            """
        )
        
        result = {
            'table': table_name,
            'foreign_key_column': foreign_key_column,
            'referenced_table': referenced_table,
            'orphaned_count': len(orphaned_records),
            'orphaned_examples': [dict(row) for row in orphaned_records[:5]]
        }
        
        if orphaned_records:
            self.validation_errors.append(result)
        
        return result
    
    async def validate_unique_constraints(self, table_name: str, unique_columns: List[str]) -> Dict[str, Any]:
        """验证唯一性约束"""
        results = {}
        
        for column in unique_columns:
            duplicates = await self.connection.fetch(
                f"""
                SELECT {column}, COUNT(*) as duplicate_count
                FROM {table_name}
                WHERE {column} IS NOT NULL
                GROUP BY {column}
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT 10
                """
            )
            
            results[column] = {
                'duplicate_groups': len(duplicates),
                'duplicate_examples': [dict(row) for row in duplicates[:5]]
            }
            
            if duplicates:
                self.validation_errors.append({
                    'table': table_name,
                    'column': column,
                    'error_type': 'duplicate_values',
                    'count': len(duplicates)
                })
        
        return results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        return {
            'total_errors': len(self.validation_errors),
            'error_types': list(set(error.get('error_type', 'unknown') for error in self.validation_errors)),
            'errors': self.validation_errors
        }


class DatabaseConnectionManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.connections = {}
        self.pools = {}
    
    async def get_connection(self, env_name: str) -> Optional[asyncpg.Connection]:
        """获取指定环境的连接"""
        if env_name not in TEST_ENVIRONMENTS:
            raise ValueError(f"未知环境: {env_name}")
        
        if env_name in self.connections and not self.connections[env_name].is_closed():
            return self.connections[env_name]
        
        config = TEST_ENVIRONMENTS[env_name]
        connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
        
        try:
            connection = await asyncpg.connect(connection_string)
            self.connections[env_name] = connection
            return connection
        except Exception as e:
            print(f"连接 {env_name} 失败: {e}")
            return None
    
    async def get_pool(self, env_name: str, min_size: int = 2, max_size: int = 10) -> Optional[asyncpg.Pool]:
        """获取指定环境的连接池"""
        if env_name not in TEST_ENVIRONMENTS:
            raise ValueError(f"未知环境: {env_name}")
        
        if env_name in self.pools and not self.pools[env_name].is_closing():
            return self.pools[env_name]
        
        config = TEST_ENVIRONMENTS[env_name]
        connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
        
        try:
            pool = await asyncpg.create_pool(
                connection_string,
                min_size=min_size,
                max_size=max_size,
                command_timeout=30
            )
            self.pools[env_name] = pool
            return pool
        except Exception as e:
            print(f"创建连接池 {env_name} 失败: {e}")
            return None
    
    async def close_all_connections(self):
        """关闭所有连接"""
        # 关闭单个连接
        for env_name, connection in self.connections.items():
            if connection and not connection.is_closed():
                await connection.close()
        
        # 关闭连接池
        for env_name, pool in self.pools.items():
            if pool and not pool.is_closing():
                await pool.close()
        
        self.connections.clear()
        self.pools.clear()


def calculate_table_hash(rows: List[Dict]) -> str:
    """计算表数据的哈希值"""
    if not rows:
        return hashlib.md5(b'').hexdigest()
    
    # 将行数据转换为确定性的字符串
    sorted_data = []
    for row in rows:
        # 按键排序确保一致性
        sorted_row = dict(sorted(row.items()))
        # 处理特殊类型
        for key, value in sorted_row.items():
            if isinstance(value, datetime):
                sorted_row[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                sorted_row[key] = json.dumps(value, sort_keys=True)
        
        sorted_data.append(json.dumps(sorted_row, sort_keys=True))
    
    # 计算整体哈希
    combined_data = ''.join(sorted(sorted_data))
    return hashlib.md5(combined_data.encode()).hexdigest()


def format_query_result(result: Union[List, Dict, Any]) -> str:
    """格式化查询结果用于显示"""
    if isinstance(result, list):
        if len(result) == 0:
            return "[]"
        elif len(result) <= 3:
            return json.dumps(result, indent=2, default=str)
        else:
            return f"[{len(result)} items] " + json.dumps(result[:2], default=str) + " ..."
    elif isinstance(result, dict):
        return json.dumps(result, indent=2, default=str)
    else:
        return str(result)


async def wait_for_database_ready(connection: asyncpg.Connection, timeout: int = 30) -> bool:
    """等待数据库准备就绪"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            await connection.fetchval("SELECT 1")
            return True
        except Exception:
            await asyncio.sleep(0.5)
    
    return False


async def execute_with_retry(connection: asyncpg.Connection, query: str, 
                           *params, max_retries: int = 3, retry_delay: float = 1.0):
    """带重试的查询执行"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            if query.strip().upper().startswith(('SELECT', 'WITH')):
                return await connection.fetch(query, *params)
            else:
                return await connection.execute(query, *params)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                raise last_exception


def get_database_helper(connection: asyncpg.Connection) -> DatabaseTestHelper:
    """获取数据库测试助手实例"""
    return DatabaseTestHelper(connection)


def get_performance_profiler() -> DatabasePerformanceProfiler:
    """获取性能分析器实例"""
    return DatabasePerformanceProfiler()


def get_data_validator(connection: asyncpg.Connection) -> DatabaseDataValidator:
    """获取数据验证器实例"""
    return DatabaseDataValidator(connection)


def get_connection_manager() -> DatabaseConnectionManager:
    """获取连接管理器实例"""
    return DatabaseConnectionManager()