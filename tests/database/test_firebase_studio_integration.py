"""
Firebase Studio集成测试套件

测试Firebase Studio环境与外部PostgreSQL数据库的集成
"""

import pytest
import asyncpg
import asyncio
import os
import time
from typing import Dict, Any, List
from datetime import datetime, timezone
import subprocess
import json


class TestFirebaseStudioIntegration:
    """Firebase Studio集成测试类"""

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_external_database_connectivity(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试Firebase Studio环境连接外部PostgreSQL数据库"""
        print("🔄 测试Firebase Studio环境数据库连接")
        
        # 检查环境变量
        is_firebase_studio = os.getenv('FIREBASE_STUDIO_ENV', 'false').lower() == 'true'
        workspace_id = os.getenv('WORKSPACE_ID', 'unknown')
        
        print(f"   Firebase Studio环境: {is_firebase_studio}")
        print(f"   工作空间ID: {workspace_id}")
        
        successful_connections = 0
        connection_details = []
        
        for env_name, connection in all_db_connections.items():
            if connection is None:
                connection_details.append({
                    'env': env_name,
                    'status': 'failed',
                    'error': 'Connection is None'
                })
                continue
            
            try:
                # 测试基本连接
                start_time = time.time()
                result = await connection.fetchval("SELECT 'Firebase Studio Connection Test'")
                end_time = time.time()
                
                # 获取连接信息
                connection_info = await connection.fetchrow(
                    """
                    SELECT 
                        current_database() as db_name,
                        current_user as user_name,
                        inet_server_addr() as server_ip,
                        inet_server_port() as server_port,
                        version() as pg_version
                    """
                )
                
                connection_details.append({
                    'env': env_name,
                    'status': 'success',
                    'response_time_ms': (end_time - start_time) * 1000,
                    'db_name': connection_info['db_name'],
                    'user': connection_info['user_name'],
                    'server_ip': str(connection_info['server_ip']) if connection_info['server_ip'] else 'localhost',
                    'server_port': connection_info['server_port'],
                    'pg_version': connection_info['pg_version'][:50] + '...' if len(connection_info['pg_version']) > 50 else connection_info['pg_version']
                })
                
                successful_connections += 1
                
            except Exception as e:
                connection_details.append({
                    'env': env_name,
                    'status': 'failed',
                    'error': str(e)[:100]
                })
        
        print(f"✅ 外部数据库连接测试结果:")
        print(f"   成功连接: {successful_connections}/{len(all_db_connections)}")
        
        for detail in connection_details:
            if detail['status'] == 'success':
                print(f"   ✅ {detail['env']}: {detail['response_time_ms']:.2f}ms")
                print(f"      数据库: {detail['db_name']} ({detail['server_ip']}:{detail['server_port']})")
            else:
                print(f"   ❌ {detail['env']}: {detail['error']}")
        
        # 断言：至少应该有一个成功的连接
        assert successful_connections > 0, f"Firebase Studio环境无法连接任何外部数据库"

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_environment_variables_access(self):
        """测试Firebase Studio环境变量访问"""
        print("🔄 测试环境变量访问")
        
        # Firebase Studio特定的环境变量
        firebase_env_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_STUDIO_ENV',
            'WORKSPACE_ID',
            'PROJECT_ROOT'
        ]
        
        # 数据库相关的环境变量
        database_env_vars = [
            'TEST_DB_ENVIRONMENT',
            'DB_HOST',
            'DB_PORT'
        ]
        
        env_status = {}
        
        print("   Firebase Studio环境变量:")
        for var in firebase_env_vars:
            value = os.getenv(var)
            env_status[var] = value is not None
            if value:
                # 对于敏感信息，只显示前几个字符
                display_value = value if len(value) <= 20 else value[:10] + '...'
                print(f"   ✅ {var}: {display_value}")
            else:
                print(f"   ⚠️  {var}: 未设置")
        
        print("   数据库环境变量:")
        for var in database_env_vars:
            value = os.getenv(var)
            env_status[var] = value is not None
            if value:
                print(f"   ✅ {var}: {value}")
            else:
                print(f"   ⚠️  {var}: 未设置")
        
        # 检查关键环境变量
        critical_vars = ['TEST_DB_ENVIRONMENT']
        missing_critical = [var for var in critical_vars if not env_status.get(var, False)]
        
        if missing_critical:
            print(f"   ⚠️  缺少关键环境变量: {missing_critical}")
        
        return env_status

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_network_latency_to_database(self, db_connection: asyncpg.Connection):
        """测试Firebase Studio到外部数据库的网络延迟"""
        print("🔄 测试网络延迟")
        
        # 执行多次网络往返测试
        latency_tests = []
        
        for i in range(10):
            start_time = time.time()
            result = await db_connection.fetchval("SELECT $1", f"latency_test_{i}")
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latency_tests.append(latency_ms)
            
            assert result == f"latency_test_{i}", f"网络通信数据不一致: {result}"
        
        # 计算延迟统计
        avg_latency = sum(latency_tests) / len(latency_tests)
        min_latency = min(latency_tests)
        max_latency = max(latency_tests)
        
        print(f"✅ 网络延迟测试结果:")
        print(f"   平均延迟: {avg_latency:.2f}ms")
        print(f"   最小延迟: {min_latency:.2f}ms")
        print(f"   最大延迟: {max_latency:.2f}ms")
        print(f"   延迟抖动: {max_latency - min_latency:.2f}ms")
        
        # 性能断言 - Firebase Studio到云数据库的延迟应该合理
        assert avg_latency < 500, f"网络延迟过高: {avg_latency:.2f}ms"
        assert max_latency < 1000, f"最大延迟过高: {max_latency:.2f}ms"
        
        return {
            'avg_latency_ms': avg_latency,
            'min_latency_ms': min_latency,
            'max_latency_ms': max_latency
        }

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_development_server_integration(self):
        """测试开发服务器集成"""
        print("🔄 测试开发服务器集成")
        
        # 检查开发服务器相关的进程
        try:
            # 检查端口9000是否被占用（Firebase Studio预览端口）
            import socket
            
            def check_port(host, port):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    return result == 0
            
            port_9000_open = check_port('localhost', 9000)
            
            print(f"   端口9000状态: {'开启' if port_9000_open else '关闭'}")
            
            # 如果端口开启，尝试进行HTTP请求
            if port_9000_open:
                import aiohttp
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://localhost:9000', timeout=5) as response:
                            status = response.status
                            print(f"   HTTP响应状态: {status}")
                            
                            if status == 200:
                                content_type = response.headers.get('content-type', '')
                                print(f"   内容类型: {content_type}")
                                return {'dev_server_running': True, 'status': status}
                            
                except Exception as e:
                    print(f"   HTTP请求失败: {str(e)[:50]}")
            
            return {'dev_server_running': port_9000_open}
            
        except Exception as e:
            print(f"   开发服务器检测失败: {e}")
            return {'dev_server_running': False, 'error': str(e)}

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_file_system_access(self):
        """测试文件系统访问权限"""
        print("🔄 测试文件系统访问")
        
        # 测试项目根目录访问
        project_root = os.getenv('PROJECT_ROOT', '/home/user/studio')
        
        access_results = {}
        
        # 测试目录访问
        test_directories = [
            project_root,
            os.path.join(project_root, 'frontend'),
            os.path.join(project_root, 'backend'),
            os.path.join(project_root, 'tests'),
            '/tmp'
        ]
        
        for directory in test_directories:
            try:
                accessible = os.path.exists(directory) and os.access(directory, os.R_OK)
                if accessible:
                    # 尝试列出目录内容
                    contents = os.listdir(directory)
                    access_results[directory] = {
                        'accessible': True,
                        'item_count': len(contents),
                        'items': contents[:5]  # 前5个项目
                    }
                else:
                    access_results[directory] = {'accessible': False}
                    
            except Exception as e:
                access_results[directory] = {
                    'accessible': False,
                    'error': str(e)
                }
        
        print("   目录访问测试:")
        for directory, result in access_results.items():
            if result.get('accessible', False):
                print(f"   ✅ {directory}: {result.get('item_count', 0)} 个项目")
            else:
                error_msg = result.get('error', '无权限')
                print(f"   ❌ {directory}: {error_msg}")
        
        # 测试临时文件创建
        temp_file_test = False
        try:
            temp_file_path = '/tmp/firebase_studio_test.txt'
            with open(temp_file_path, 'w') as f:
                f.write('Firebase Studio integration test')
            
            # 验证文件存在
            if os.path.exists(temp_file_path):
                temp_file_test = True
                os.remove(temp_file_path)  # 清理
                
        except Exception as e:
            print(f"   临时文件创建失败: {e}")
        
        print(f"   临时文件创建: {'成功' if temp_file_test else '失败'}")
        
        return {
            'directory_access': access_results,
            'temp_file_creation': temp_file_test
        }

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_concurrent_database_operations_from_studio(self, db_pool: asyncpg.Pool):
        """测试从Firebase Studio环境进行并发数据库操作"""
        print("🔄 测试Firebase Studio并发数据库操作")
        
        # 检查表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        async def firebase_studio_db_worker(worker_id: int):
            """模拟Firebase Studio环境的数据库工作负载"""
            operations = []
            
            try:
                async with db_pool.acquire() as connection:
                    # 1. 查询操作
                    start_time = time.time()
                    count = await connection.fetchval("SELECT COUNT(*) FROM users")
                    query_time = time.time() - start_time
                    operations.append({'type': 'count_query', 'time': query_time, 'success': True})
                    
                    # 2. 事务操作
                    start_time = time.time()
                    async with connection.transaction():
                        user_id = await connection.fetchval(
                            """
                            INSERT INTO users (email, username, password_hash, is_active)
                            VALUES ($1, $2, $3, $4)
                            RETURNING id
                            """,
                            f'firebase_studio_{worker_id}@example.com',
                            f'firebase_studio_user_{worker_id}',
                            'firebase_hash', True
                        )
                        
                        if user_id:
                            await connection.execute(
                                "UPDATE users SET is_active = false WHERE id = $1",
                                user_id
                            )
                    
                    transaction_time = time.time() - start_time
                    operations.append({'type': 'transaction', 'time': transaction_time, 'success': True})
                    
                    # 3. 复杂查询操作
                    start_time = time.time()
                    results = await connection.fetch(
                        """
                        SELECT is_active, COUNT(*) as count 
                        FROM users 
                        WHERE email LIKE $1
                        GROUP BY is_active
                        """,
                        '%firebase_studio%'
                    )
                    complex_query_time = time.time() - start_time
                    operations.append({'type': 'complex_query', 'time': complex_query_time, 'success': True})
                    
                return {
                    'worker_id': worker_id,
                    'operations': operations,
                    'total_success': True
                }
                
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'operations': operations,
                    'total_success': False,
                    'error': str(e)
                }

        # 启动多个并发工作进程
        worker_count = 6
        start_time = time.time()
        
        tasks = []
        for worker_id in range(worker_count):
            task = asyncio.create_task(firebase_studio_db_worker(worker_id))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        successful_workers = sum(1 for r in results if r.get('total_success', False))
        
        operation_stats = {
            'count_query': [],
            'transaction': [],
            'complex_query': []
        }
        
        for result in results:
            if result.get('total_success', False):
                for op in result.get('operations', []):
                    if op['success'] and op['type'] in operation_stats:
                        operation_stats[op['type']].append(op['time'])
        
        print(f"✅ Firebase Studio并发数据库操作结果:")
        print(f"   工作进程: {successful_workers}/{worker_count}")
        print(f"   总耗时: {total_time:.3f}秒")
        
        for op_type, times in operation_stats.items():
            if times:
                avg_time = sum(times) / len(times)
                print(f"   {op_type} 平均时间: {avg_time:.4f}秒 ({len(times)} 次操作)")
        
        # 清理测试数据
        async with db_pool.acquire() as connection:
            await connection.execute("DELETE FROM users WHERE email LIKE 'firebase_studio_%'")
        
        # 断言
        assert successful_workers >= worker_count * 0.8, \
            f"Firebase Studio并发操作成功率过低: {successful_workers}/{worker_count}"

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_external_api_access(self):
        """测试外部API访问能力"""
        print("🔄 测试外部API访问")
        
        # 测试对外网的访问
        api_tests = [
            {
                'name': 'Google DNS',
                'url': 'https://dns.google/resolve?name=example.com&type=A',
                'timeout': 10
            },
            {
                'name': 'HTTPBin Echo',
                'url': 'https://httpbin.org/json',
                'timeout': 10
            }
        ]
        
        api_results = []
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                for test in api_tests:
                    try:
                        start_time = time.time()
                        async with session.get(test['url'], timeout=test['timeout']) as response:
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            api_results.append({
                                'name': test['name'],
                                'success': True,
                                'status': response.status,
                                'response_time': response_time
                            })
                            
                    except Exception as e:
                        api_results.append({
                            'name': test['name'],
                            'success': False,
                            'error': str(e)[:100]
                        })
            
            print("   外部API访问测试:")
            successful_apis = 0
            for result in api_results:
                if result['success']:
                    successful_apis += 1
                    print(f"   ✅ {result['name']}: {result['status']} ({result['response_time']:.3f}s)")
                else:
                    print(f"   ❌ {result['name']}: {result['error']}")
            
            return {
                'successful_apis': successful_apis,
                'total_apis': len(api_tests),
                'results': api_results
            }
            
        except ImportError:
            print("   ⚠️  aiohttp不可用，跳过外部API测试")
            return {'successful_apis': 0, 'total_apis': 0, 'error': 'aiohttp_unavailable'}

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_memory_and_resource_usage(self):
        """测试内存和资源使用情况"""
        print("🔄 测试资源使用情况")
        
        try:
            import psutil
            
            # 获取当前进程信息
            process = psutil.Process()
            
            # 内存使用
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # CPU使用（需要短暂等待来计算）
            cpu_percent = process.cpu_percent(interval=1)
            
            # 文件描述符
            try:
                num_fds = process.num_fds() if hasattr(process, 'num_fds') else 'N/A'
            except:
                num_fds = 'N/A'
            
            # 线程数
            num_threads = process.num_threads()
            
            print(f"   资源使用情况:")
            print(f"   内存使用: {memory_info.rss / 1024 / 1024:.2f} MB ({memory_percent:.1f}%)")
            print(f"   CPU使用: {cpu_percent:.1f}%")
            print(f"   线程数: {num_threads}")
            print(f"   文件描述符: {num_fds}")
            
            # 系统资源
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)
            
            print(f"   系统资源:")
            print(f"   系统内存: {system_memory.percent:.1f}% 已使用")
            print(f"   系统CPU: {system_cpu:.1f}%")
            
            return {
                'process_memory_mb': memory_info.rss / 1024 / 1024,
                'process_memory_percent': memory_percent,
                'process_cpu_percent': cpu_percent,
                'process_threads': num_threads,
                'system_memory_percent': system_memory.percent,
                'system_cpu_percent': system_cpu
            }
            
        except ImportError:
            print("   ⚠️  psutil不可用，无法获取资源信息")
            return {'error': 'psutil_unavailable'}
        except Exception as e:
            print(f"   ⚠️  资源监控失败: {e}")
            return {'error': str(e)}

    @pytest.mark.firebase_studio
    @pytest.mark.asyncio
    async def test_database_connection_persistence(self, db_pool: asyncpg.Pool):
        """测试数据库连接持久性（Firebase Studio环境特有的网络条件）"""
        print("🔄 测试数据库连接持久性")
        
        # 模拟长时间运行的应用场景
        persistence_tests = []
        
        for i in range(5):
            try:
                async with db_pool.acquire() as connection:
                    # 执行查询
                    start_time = time.time()
                    result = await connection.fetchval("SELECT CURRENT_TIMESTAMP")
                    query_time = time.time() - start_time
                    
                    # 等待一段时间模拟连接空闲
                    await asyncio.sleep(2)
                    
                    # 再次查询验证连接仍然有效
                    start_time = time.time()
                    result2 = await connection.fetchval("SELECT 'connection_alive'")
                    query_time2 = time.time() - start_time
                    
                    persistence_tests.append({
                        'round': i + 1,
                        'success': True,
                        'first_query_time': query_time,
                        'second_query_time': query_time2,
                        'timestamp': result
                    })
                    
            except Exception as e:
                persistence_tests.append({
                    'round': i + 1,
                    'success': False,
                    'error': str(e)
                })
        
        # 分析结果
        successful_rounds = sum(1 for t in persistence_tests if t.get('success', False))
        
        print(f"✅ 连接持久性测试结果:")
        print(f"   成功轮次: {successful_rounds}/5")
        
        total_query_time = 0
        query_count = 0
        
        for test in persistence_tests:
            if test.get('success', False):
                round_num = test['round']
                q1_time = test['first_query_time'] * 1000  # 转换为毫秒
                q2_time = test['second_query_time'] * 1000
                
                print(f"   轮次{round_num}: 查询1={q1_time:.2f}ms, 查询2={q2_time:.2f}ms")
                
                total_query_time += q1_time + q2_time
                query_count += 2
            else:
                print(f"   轮次{test['round']}: 失败 - {test.get('error', 'Unknown')[:50]}")
        
        if query_count > 0:
            avg_query_time = total_query_time / query_count
            print(f"   平均查询时间: {avg_query_time:.2f}ms")
        
        # 断言：连接应该保持稳定
        assert successful_rounds >= 4, \
            f"连接持久性不足: 仅 {successful_rounds}/5 轮成功"

    @pytest.mark.firebase_studio
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_stack_integration(self, db_connection: asyncpg.Connection):
        """测试完整技术栈集成（Firebase Studio + 外部PostgreSQL + 应用逻辑）"""
        print("🔄 测试完整技术栈集成")
        
        # 模拟完整的应用工作流
        integration_results = {}
        
        # 1. 数据库操作测试
        try:
            # 检查表是否存在
            tables_exist = await db_connection.fetchval(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('users', 'projects')
                """
            )
            
            integration_results['database_schema'] = {
                'tables_found': tables_exist,
                'success': tables_exist > 0
            }
            
            if tables_exist > 0:
                # 执行CRUD操作
                # CREATE
                user_id = await db_connection.fetchval(
                    """
                    INSERT INTO users (email, username, password_hash, is_active)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    'integration_test@firebase.studio', 'integration_user', 'test_hash', True
                )
                
                # READ
                user_data = await db_connection.fetchrow(
                    "SELECT * FROM users WHERE id = $1", user_id
                )
                
                # UPDATE
                await db_connection.execute(
                    "UPDATE users SET is_active = false WHERE id = $1", user_id
                )
                
                # 验证更新
                updated_status = await db_connection.fetchval(
                    "SELECT is_active FROM users WHERE id = $1", user_id
                )
                
                integration_results['crud_operations'] = {
                    'create_success': user_id is not None,
                    'read_success': user_data is not None,
                    'update_success': updated_status == False,
                    'success': all([user_id is not None, user_data is not None, updated_status == False])
                }
                
                # 清理
                await db_connection.execute("DELETE FROM users WHERE id = $1", user_id)
            
        except Exception as e:
            integration_results['database_operations'] = {
                'success': False,
                'error': str(e)
            }
        
        # 2. 并发操作测试
        try:
            concurrent_start = time.time()
            
            async def concurrent_query(query_id):
                return await db_connection.fetchval("SELECT $1", f"concurrent_test_{query_id}")
            
            # 执行并发查询
            tasks = [asyncio.create_task(concurrent_query(i)) for i in range(5)]
            concurrent_results = await asyncio.gather(*tasks)
            
            concurrent_end = time.time()
            concurrent_time = concurrent_end - concurrent_start
            
            integration_results['concurrency'] = {
                'success': len(concurrent_results) == 5,
                'execution_time': concurrent_time,
                'all_results_correct': all(f"concurrent_test_{i}" in str(concurrent_results[i]) for i in range(5))
            }
            
        except Exception as e:
            integration_results['concurrency'] = {
                'success': False,
                'error': str(e)
            }
        
        # 3. 性能基准测试
        try:
            performance_queries = [
                "SELECT 1",
                "SELECT COUNT(*) FROM information_schema.tables",
                "SELECT CURRENT_TIMESTAMP",
                "SELECT version()",
                "SELECT pg_database_size(current_database())"
            ]
            
            query_times = []
            for query in performance_queries:
                start_time = time.time()
                await db_connection.fetchval(query)
                end_time = time.time()
                query_times.append((end_time - start_time) * 1000)  # ms
            
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            
            integration_results['performance'] = {
                'success': avg_query_time < 100,  # 平均查询时间应小于100ms
                'avg_query_time_ms': avg_query_time,
                'max_query_time_ms': max_query_time,
                'total_queries': len(performance_queries)
            }
            
        except Exception as e:
            integration_results['performance'] = {
                'success': False,
                'error': str(e)
            }
        
        # 汇总结果
        total_tests = len(integration_results)
        successful_tests = sum(1 for result in integration_results.values() 
                             if isinstance(result, dict) and result.get('success', False))
        
        print(f"✅ 完整技术栈集成测试结果:")
        print(f"   成功测试: {successful_tests}/{total_tests}")
        
        for test_name, result in integration_results.items():
            if isinstance(result, dict):
                if result.get('success', False):
                    print(f"   ✅ {test_name}: 通过")
                else:
                    error_msg = result.get('error', '未知错误')
                    print(f"   ❌ {test_name}: 失败 - {error_msg[:50]}")
        
        # 最终断言
        success_rate = successful_tests / total_tests
        assert success_rate >= 0.8, \
            f"完整技术栈集成成功率过低: {success_rate:.1%}"
        
        return integration_results