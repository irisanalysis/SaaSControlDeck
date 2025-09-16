"""
数据库查询性能测试套件

测试各种查询的性能表现和索引效果
"""

import pytest
import asyncpg
import asyncio
import time
import statistics
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta


class TestQueryPerformance:
    """查询性能测试类"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_record_lookup_performance(self, db_connection: asyncpg.Connection, performance_test_data):
        """测试单记录查找性能"""
        # 检查users表是否存在
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        user_count = await db_connection.fetchval("SELECT count(*) FROM users")
        if user_count == 0:
            pytest.skip("users表没有数据")

        # 获取一个存在的用户邮箱
        test_email = await db_connection.fetchval("SELECT email FROM users LIMIT 1")
        test_user_id = await db_connection.fetchval("SELECT id FROM users LIMIT 1")
        
        # 测试不同类型的单记录查找
        performance_tests = [
            {
                'name': 'Primary Key Lookup',
                'query': 'SELECT * FROM users WHERE id = $1',
                'param': test_user_id,
                'expected_time_ms': 1.0  # 主键查找应该非常快
            },
            {
                'name': 'Unique Email Lookup',
                'query': 'SELECT * FROM users WHERE email = $1',
                'param': test_email,
                'expected_time_ms': 2.0  # 唯一索引查找
            },
            {
                'name': 'Count Query',
                'query': 'SELECT count(*) FROM users WHERE is_active = $1',
                'param': True,
                'expected_time_ms': 10.0  # 计数查询
            }
        ]
        
        results = []
        for test in performance_tests:
            times = []
            
            # 执行多次测试获取平均值
            for _ in range(50):
                start_time = time.time()
                result = await db_connection.fetchval(test['query'], test['param'])
                end_time = time.time()
                
                times.append((end_time - start_time) * 1000)  # 转换为毫秒
                assert result is not None, f"查询 {test['name']} 返回空结果"
            
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            
            results.append({
                'name': test['name'],
                'avg_time_ms': avg_time,
                'median_time_ms': median_time,
                'p95_time_ms': p95_time,
                'expected_time_ms': test['expected_time_ms']
            })
            
            print(f"✅ {test['name']}:")
            print(f"   平均时间: {avg_time:.2f}ms")
            print(f"   中位数: {median_time:.2f}ms")
            print(f"   P95: {p95_time:.2f}ms")
            
            # 性能断言
            assert avg_time < test['expected_time_ms'] * 2, \
                f"{test['name']} 平均性能不达标: {avg_time:.2f}ms > {test['expected_time_ms'] * 2}ms"
        
        return results

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_complex_join_performance(self, db_connection: asyncpg.Connection):
        """测试复杂连接查询性能"""
        # 检查相关表是否存在
        tables_needed = ['users', 'projects']
        existing_tables = []
        
        for table in tables_needed:
            exists = await db_connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                existing_tables.append(table)
        
        if len(existing_tables) < len(tables_needed):
            pytest.skip(f"缺少必要的表: {set(tables_needed) - set(existing_tables)}")

        # 检查是否有足够的数据
        user_count = await db_connection.fetchval("SELECT count(*) FROM users")
        project_count = await db_connection.fetchval("SELECT count(*) FROM projects")
        
        if user_count == 0 or project_count == 0:
            pytest.skip("没有足够的测试数据")

        # 复杂连接查询测试
        join_queries = [
            {
                'name': 'Simple Inner Join',
                'query': """
                    SELECT u.username, p.name as project_name
                    FROM users u
                    INNER JOIN projects p ON u.id = p.owner_id
                    LIMIT 100
                """,
                'expected_time_ms': 20.0
            },
            {
                'name': 'Left Join with Aggregation',
                'query': """
                    SELECT u.username, COUNT(p.id) as project_count
                    FROM users u
                    LEFT JOIN projects p ON u.id = p.owner_id
                    GROUP BY u.id, u.username
                    LIMIT 50
                """,
                'expected_time_ms': 50.0
            },
            {
                'name': 'Complex Where Clause',
                'query': """
                    SELECT u.*, p.name as project_name
                    FROM users u
                    INNER JOIN projects p ON u.id = p.owner_id
                    WHERE u.is_active = true 
                    AND p.status = 'active'
                    AND u.created_at > $1
                    ORDER BY u.created_at DESC
                    LIMIT 20
                """,
                'params': [datetime.now(timezone.utc) - timedelta(days=365)],
                'expected_time_ms': 30.0
            }
        ]
        
        for query_test in join_queries:
            times = []
            params = query_test.get('params', [])
            
            # 执行多次测试
            for _ in range(10):
                start_time = time.time()
                
                if params:
                    results = await db_connection.fetch(query_test['query'], *params)
                else:
                    results = await db_connection.fetch(query_test['query'])
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
                
                # 验证结果
                assert isinstance(results, list), f"查询 {query_test['name']} 返回格式错误"
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"✅ {query_test['name']}:")
            print(f"   平均时间: {avg_time:.2f}ms")
            print(f"   最快: {min_time:.2f}ms")
            print(f"   最慢: {max_time:.2f}ms")
            print(f"   结果数量: {len(results)}")
            
            # 性能断言
            assert avg_time < query_test['expected_time_ms'] * 3, \
                f"{query_test['name']} 性能不达标: {avg_time:.2f}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_pagination_performance(self, db_connection: asyncpg.Connection):
        """测试分页查询性能"""
        # 检查users表是否存在
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        user_count = await db_connection.fetchval("SELECT count(*) FROM users")
        if user_count < 10:
            pytest.skip("用户数据不足，无法进行分页测试")

        # 测试不同的分页策略
        page_size = 10
        pagination_tests = [
            {
                'name': 'OFFSET/LIMIT Pagination',
                'query_template': 'SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2',
                'get_params': lambda page: [page_size, page * page_size]
            },
            {
                'name': 'Cursor-based Pagination (ID)',
                'query_template': 'SELECT * FROM users WHERE id < $1 ORDER BY id DESC LIMIT $2',
                'get_params': lambda cursor_id: [cursor_id, page_size],
                'needs_cursor': True
            },
            {
                'name': 'Cursor-based Pagination (Timestamp)',
                'query_template': 'SELECT * FROM users WHERE created_at < $1 ORDER BY created_at DESC LIMIT $2',
                'get_params': lambda cursor_time: [cursor_time, page_size],
                'needs_cursor': True
            }
        ]
        
        for test in pagination_tests:
            times = []
            
            if test.get('needs_cursor'):
                # 获取游标值
                if 'ID' in test['name']:
                    cursor = await db_connection.fetchval(
                        "SELECT id FROM users ORDER BY id DESC LIMIT 1 OFFSET 5"
                    )
                else:  # Timestamp cursor
                    cursor = await db_connection.fetchval(
                        "SELECT created_at FROM users ORDER BY created_at DESC LIMIT 1 OFFSET 5"
                    )
                
                if cursor is None:
                    print(f"⚠️  跳过 {test['name']} - 无足够数据")
                    continue
                
                # 执行游标分页查询
                for _ in range(5):
                    start_time = time.time()
                    params = test['get_params'](cursor)
                    results = await db_connection.fetch(test['query_template'], *params)
                    end_time = time.time()
                    times.append((end_time - start_time) * 1000)
                    
                    if results:
                        # 更新游标
                        if 'ID' in test['name']:
                            cursor = results[-1]['id']
                        else:
                            cursor = results[-1]['created_at']
                    else:
                        break
            else:
                # OFFSET/LIMIT 分页
                for page in range(5):
                    start_time = time.time()
                    params = test['get_params'](page)
                    results = await db_connection.fetch(test['query_template'], *params)
                    end_time = time.time()
                    times.append((end_time - start_time) * 1000)
                    
                    if len(results) < page_size:
                        break
            
            if times:
                avg_time = statistics.mean(times)
                print(f"✅ {test['name']}:")
                print(f"   平均时间: {avg_time:.2f}ms")
                print(f"   查询次数: {len(times)}")
                
                # 游标分页应该比OFFSET分页性能更好
                if 'Cursor-based' in test['name']:
                    assert avg_time < 50, f"游标分页性能不达标: {avg_time:.2f}ms"
                else:
                    assert avg_time < 100, f"OFFSET分页性能不达标: {avg_time:.2f}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_aggregation_performance(self, db_connection: asyncpg.Connection):
        """测试聚合查询性能"""
        # 检查相关表是否存在
        tables_to_check = ['users', 'projects', 'ai_tasks']
        existing_tables = []
        
        for table in tables_to_check:
            exists = await db_connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                existing_tables.append(table)
        
        if 'users' not in existing_tables:
            pytest.skip("users表不存在")

        # 基础聚合查询测试
        basic_aggregations = [
            {
                'name': 'Simple Count',
                'query': 'SELECT COUNT(*) FROM users',
                'expected_time_ms': 10.0
            },
            {
                'name': 'Count with Condition',
                'query': 'SELECT COUNT(*) FROM users WHERE is_active = true',
                'expected_time_ms': 15.0
            },
            {
                'name': 'Group By Count',
                'query': 'SELECT is_active, COUNT(*) FROM users GROUP BY is_active',
                'expected_time_ms': 20.0
            }
        ]
        
        # 如果projects表存在，添加更复杂的聚合查询
        if 'projects' in existing_tables:
            basic_aggregations.extend([
                {
                    'name': 'Join Aggregation',
                    'query': """
                        SELECT u.is_active, COUNT(p.id) as project_count
                        FROM users u
                        LEFT JOIN projects p ON u.id = p.owner_id
                        GROUP BY u.is_active
                    """,
                    'expected_time_ms': 50.0
                },
                {
                    'name': 'Complex Aggregation',
                    'query': """
                        SELECT 
                            p.status,
                            COUNT(*) as project_count,
                            COUNT(DISTINCT p.owner_id) as unique_owners
                        FROM projects p
                        GROUP BY p.status
                        HAVING COUNT(*) > 0
                    """,
                    'expected_time_ms': 30.0
                }
            ])
        
        for agg_test in basic_aggregations:
            times = []
            
            # 执行多次测试
            for _ in range(20):
                start_time = time.time()
                result = await db_connection.fetch(agg_test['query'])
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
                
                # 验证结果
                assert len(result) > 0, f"聚合查询 {agg_test['name']} 返回空结果"
            
            avg_time = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            print(f"✅ {agg_test['name']}:")
            print(f"   平均时间: {avg_time:.2f}ms")
            print(f"   标准差: {std_dev:.2f}ms")
            print(f"   结果行数: {len(result)}")
            
            # 性能断言
            assert avg_time < agg_test['expected_time_ms'] * 2, \
                f"{agg_test['name']} 性能不达标: {avg_time:.2f}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_full_text_search_performance(self, db_connection: asyncpg.Connection):
        """测试全文搜索性能"""
        # 检查是否有文本搜索的表
        searchable_tables = []
        
        # 检查users表的文本字段
        users_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        if users_exists:
            searchable_tables.append('users')
        
        # 检查projects表的文本字段
        projects_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        if projects_exists:
            searchable_tables.append('projects')
        
        if not searchable_tables:
            pytest.skip("没有可搜索的表")

        # 文本搜索测试
        search_tests = []
        
        if 'users' in searchable_tables:
            user_count = await db_connection.fetchval("SELECT count(*) FROM users")
            if user_count > 0:
                search_tests.append({
                    'name': 'User Email Search',
                    'query': "SELECT * FROM users WHERE email ILIKE $1 LIMIT 10",
                    'param': '%@%',
                    'expected_time_ms': 20.0
                })
                search_tests.append({
                    'name': 'User Username Search',
                    'query': "SELECT * FROM users WHERE username ILIKE $1 LIMIT 10",
                    'param': '%user%',
                    'expected_time_ms': 25.0
                })
        
        if 'projects' in searchable_tables:
            project_count = await db_connection.fetchval("SELECT count(*) FROM projects")
            if project_count > 0:
                search_tests.append({
                    'name': 'Project Name Search',
                    'query': "SELECT * FROM projects WHERE name ILIKE $1 LIMIT 10",
                    'param': '%project%',
                    'expected_time_ms': 30.0
                })
                search_tests.append({
                    'name': 'Project Description Search',
                    'query': "SELECT * FROM projects WHERE description ILIKE $1 LIMIT 10",
                    'param': '%test%',
                    'expected_time_ms': 40.0
                })
        
        for search_test in search_tests:
            times = []
            
            # 执行多次搜索测试
            for _ in range(10):
                start_time = time.time()
                results = await db_connection.fetch(search_test['query'], search_test['param'])
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            print(f"✅ {search_test['name']}:")
            print(f"   平均时间: {avg_time:.2f}ms")
            print(f"   最长时间: {max_time:.2f}ms")
            print(f"   结果数量: {len(results)}")
            
            # 全文搜索性能断言（相对宽松）
            assert avg_time < search_test['expected_time_ms'] * 3, \
                f"{search_test['name']} 搜索性能不达标: {avg_time:.2f}ms"

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, db_transaction: asyncpg.Connection):
        """测试批量操作性能"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 准备批量数据
        batch_sizes = [10, 50, 100, 500]
        
        for batch_size in batch_sizes:
            # 生成批量用户数据
            user_data = []
            for i in range(batch_size):
                user_data.append((
                    f'bulk_perf_{batch_size}_{i}@example.com',
                    f'bulk_perf_user_{batch_size}_{i}',
                    'bulk_hash'
                ))
            
            # 测试单个INSERT性能
            start_time = time.time()
            inserted_count = 0
            
            for email, username, password_hash in user_data:
                try:
                    await db_transaction.execute(
                        "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                        email, username, password_hash
                    )
                    inserted_count += 1
                except Exception:
                    pass  # 忽略约束违反
            
            single_insert_time = time.time() - start_time
            
            # 测试批量SELECT性能
            start_time = time.time()
            bulk_select_results = await db_transaction.fetch(
                "SELECT * FROM users WHERE email LIKE $1",
                f'bulk_perf_{batch_size}_%'
            )
            bulk_select_time = time.time() - start_time
            
            # 测试批量UPDATE性能
            start_time = time.time()
            update_result = await db_transaction.execute(
                "UPDATE users SET is_active = false WHERE email LIKE $1",
                f'bulk_perf_{batch_size}_%'
            )
            bulk_update_time = time.time() - start_time
            
            # 测试批量DELETE性能
            start_time = time.time()
            delete_result = await db_transaction.execute(
                "DELETE FROM users WHERE email LIKE $1",
                f'bulk_perf_{batch_size}_%'
            )
            bulk_delete_time = time.time() - start_time
            
            print(f"✅ 批量操作性能 (批次大小: {batch_size}):")
            print(f"   INSERT: {single_insert_time:.3f}秒 ({inserted_count} 条记录, {inserted_count/single_insert_time:.1f} records/sec)")
            print(f"   SELECT: {bulk_select_time:.3f}秒 ({len(bulk_select_results)} 条记录)")
            print(f"   UPDATE: {bulk_update_time:.3f}秒")
            print(f"   DELETE: {bulk_delete_time:.3f}秒")
            
            # 性能断言
            if batch_size <= 100:
                assert single_insert_time < 1.0, f"小批量INSERT性能不达标: {single_insert_time:.3f}s"
                assert bulk_select_time < 0.1, f"批量SELECT性能不达标: {bulk_select_time:.3f}s"
            else:
                assert single_insert_time < 5.0, f"大批量INSERT性能不达标: {single_insert_time:.3f}s"
                assert bulk_select_time < 0.5, f"大批量SELECT性能不达标: {bulk_select_time:.3f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_index_effectiveness(self, db_connection: asyncpg.Connection):
        """测试索引效果"""
        # 检查users表是否存在
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        user_count = await db_connection.fetchval("SELECT count(*) FROM users")
        if user_count < 10:
            pytest.skip("用户数据不足")

        # 测试有索引的查询 vs 可能没有索引的查询
        index_tests = [
            {
                'name': 'Indexed Email Query',
                'query': 'SELECT * FROM users WHERE email = $1',
                'get_param': lambda: db_connection.fetchval("SELECT email FROM users LIMIT 1"),
                'indexed': True,
                'expected_time_ms': 2.0
            },
            {
                'name': 'Indexed Username Query',
                'query': 'SELECT * FROM users WHERE username = $1',
                'get_param': lambda: db_connection.fetchval("SELECT username FROM users LIMIT 1"),
                'indexed': True,
                'expected_time_ms': 2.0
            },
            {
                'name': 'Non-indexed Field Query',
                'query': 'SELECT * FROM users WHERE password_hash = $1',
                'get_param': lambda: db_connection.fetchval("SELECT password_hash FROM users LIMIT 1"),
                'indexed': False,
                'expected_time_ms': 20.0
            }
        ]
        
        for test in index_tests:
            param = await test['get_param']()
            if param is None:
                continue
                
            times = []
            
            # 执行多次查询
            for _ in range(30):
                start_time = time.time()
                result = await db_connection.fetchrow(test['query'], param)
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
                
                assert result is not None, f"查询 {test['name']} 应该返回结果"
            
            avg_time = statistics.mean(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            
            print(f"✅ {test['name']} ({'有索引' if test['indexed'] else '无索引'}):")
            print(f"   平均时间: {avg_time:.2f}ms")
            print(f"   P95时间: {p95_time:.2f}ms")
            
            # 索引效果验证
            if test['indexed']:
                assert avg_time < test['expected_time_ms'], \
                    f"索引查询性能不达标: {avg_time:.2f}ms > {test['expected_time_ms']}ms"
            else:
                # 非索引查询可能较慢，但不应该过慢
                assert avg_time < test['expected_time_ms'] * 2, \
                    f"非索引查询过慢: {avg_time:.2f}ms > {test['expected_time_ms'] * 2}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_explain_analyze_queries(self, db_connection: asyncpg.Connection):
        """使用EXPLAIN ANALYZE分析查询执行计划"""
        # 检查users表是否存在
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 需要分析的查询
        queries_to_analyze = [
            {
                'name': 'Simple Select',
                'query': 'SELECT * FROM users WHERE is_active = true LIMIT 10'
            },
            {
                'name': 'Count Query',
                'query': 'SELECT COUNT(*) FROM users WHERE is_active = true'
            },
            {
                'name': 'Order By Query',
                'query': 'SELECT * FROM users ORDER BY created_at DESC LIMIT 20'
            }
        ]
        
        # 如果projects表存在，添加JOIN查询分析
        projects_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if projects_exists:
            queries_to_analyze.append({
                'name': 'Join Query',
                'query': '''
                    SELECT u.username, COUNT(p.id) as project_count
                    FROM users u
                    LEFT JOIN projects p ON u.id = p.owner_id
                    GROUP BY u.id, u.username
                    LIMIT 10
                '''
            })
        
        for query_info in queries_to_analyze:
            try:
                # 执行EXPLAIN ANALYZE
                explain_result = await db_connection.fetch(
                    f"EXPLAIN ANALYZE {query_info['query']}"
                )
                
                # 解析执行计划
                plan_text = '\n'.join([row[0] for row in explain_result])
                
                # 提取关键指标
                execution_time = None
                planning_time = None
                
                for line in plan_text.split('\n'):
                    if 'Execution Time:' in line:
                        execution_time = float(line.split(':')[1].strip().split(' ')[0])
                    elif 'Planning Time:' in line:
                        planning_time = float(line.split(':')[1].strip().split(' ')[0])
                
                print(f"✅ {query_info['name']} 执行计划分析:")
                if planning_time:
                    print(f"   规划时间: {planning_time:.3f}ms")
                if execution_time:
                    print(f"   执行时间: {execution_time:.3f}ms")
                
                # 检查是否使用了索引扫描
                if 'Index Scan' in plan_text:
                    print("   ✅ 使用了索引扫描")
                elif 'Seq Scan' in plan_text:
                    print("   ⚠️  使用了顺序扫描")
                
                # 检查是否有昂贵的操作
                if 'Sort' in plan_text:
                    print("   📊 包含排序操作")
                if 'Hash Join' in plan_text:
                    print("   🔗 使用哈希连接")
                if 'Nested Loop' in plan_text:
                    print("   🔄 使用嵌套循环连接")
                
                # 性能警告
                if execution_time and execution_time > 100:
                    print(f"   ⚠️  查询执行时间较长: {execution_time:.3f}ms")
                
                print(f"   详细执行计划:\n{plan_text[:500]}{'...' if len(plan_text) > 500 else ''}")
                
            except Exception as e:
                print(f"⚠️  无法分析 {query_info['name']}: {e}")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_statistics(self, db_connection: asyncpg.Connection):
        """收集数据库统计信息"""
        # 获取数据库大小
        try:
            db_size = await db_connection.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            print(f"✅ 数据库大小: {db_size}")
        except Exception as e:
            print(f"⚠️  无法获取数据库大小: {e}")
        
        # 获取表大小统计
        try:
            table_sizes = await db_connection.fetch(
                """
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
                    pg_total_relation_size(tablename::regclass) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(tablename::regclass) DESC
                LIMIT 10
                """
            )
            
            print("✅ 表大小统计:")
            for table_info in table_sizes:
                print(f"   {table_info['tablename']}: {table_info['size']}")
                
        except Exception as e:
            print(f"⚠️  无法获取表大小: {e}")
        
        # 获取索引使用统计
        try:
            index_stats = await db_connection.fetch(
                """
                SELECT 
                    tablename,
                    indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
                LIMIT 10
                """
            )
            
            if index_stats:
                print("✅ 索引使用统计:")
                for idx_info in index_stats:
                    print(f"   {idx_info['tablename']}.{idx_info['indexname']}: {idx_info['scans']} 次扫描")
            else:
                print("⚠️  没有索引使用统计数据")
                
        except Exception as e:
            print(f"⚠️  无法获取索引统计: {e}")
        
        # 获取表统计信息
        try:
            table_stats = await db_connection.fetch(
                """
                SELECT 
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                WHERE n_live_tup > 0
                ORDER BY n_live_tup DESC
                LIMIT 10
                """
            )
            
            if table_stats:
                print("✅ 表活动统计:")
                for stat in table_stats:
                    print(f"   {stat['tablename']}: {stat['live_tuples']} 活跃行, {stat['inserts']} 插入")
            else:
                print("⚠️  没有表活动统计数据")
                
        except Exception as e:
            print(f"⚠️  无法获取表统计: {e}")