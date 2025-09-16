"""
数据库并发操作测试套件

测试多用户并发访问、事务隔离和锁机制
"""

import pytest
import asyncpg
import asyncio
import time
import random
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestConcurrentOperations:
    """并发操作测试类"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, db_config: Dict[str, Any]):
        """测试并发连接处理"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        async def create_connection_and_query(connection_id: int):
            """创建连接并执行查询"""
            try:
                connection = await asyncpg.connect(connection_string)
                
                # 执行简单查询
                result = await connection.fetchval("SELECT $1 as connection_id", connection_id)
                
                # 模拟一些工作负载
                await asyncio.sleep(0.1)
                
                # 执行另一个查询
                timestamp = await connection.fetchval("SELECT CURRENT_TIMESTAMP")
                
                await connection.close()
                return {
                    'connection_id': connection_id,
                    'result': result,
                    'timestamp': timestamp,
                    'success': True
                }
            except Exception as e:
                return {
                    'connection_id': connection_id,
                    'error': str(e),
                    'success': False
                }

        # 测试不同并发级别
        concurrency_levels = [5, 10, 20]
        
        for concurrent_count in concurrency_levels:
            print(f"🔄 测试并发连接数: {concurrent_count}")
            
            start_time = time.time()
            
            # 创建并发任务
            tasks = []
            for i in range(concurrent_count):
                task = asyncio.create_task(create_connection_and_query(i))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            successful_connections = 0
            failed_connections = 0
            errors = []
            
            for result in results:
                if isinstance(result, dict):
                    if result.get('success', False):
                        successful_connections += 1
                    else:
                        failed_connections += 1
                        errors.append(result.get('error', 'Unknown error'))
                else:
                    failed_connections += 1
                    errors.append(str(result))
            
            success_rate = successful_connections / concurrent_count
            avg_time_per_connection = total_time / concurrent_count
            
            print(f"✅ 并发连接测试结果 ({concurrent_count} 连接):")
            print(f"   成功连接: {successful_connections}")
            print(f"   失败连接: {failed_connections}")
            print(f"   成功率: {success_rate:.1%}")
            print(f"   总耗时: {total_time:.3f}秒")
            print(f"   平均连接时间: {avg_time_per_connection:.3f}秒")
            
            if errors:
                unique_errors = list(set(errors[:5]))  # 显示前5种不同错误
                print(f"   错误样例: {unique_errors}")
            
            # 并发性能断言
            assert success_rate >= 0.8, f"并发连接成功率过低: {success_rate:.1%}"
            assert avg_time_per_connection < 1.0, f"平均连接时间过长: {avg_time_per_connection:.3f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_reads(self, db_pool: asyncpg.Pool):
        """测试并发读操作"""
        # 检查users表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        async def concurrent_read_worker(worker_id: int, iterations: int):
            """并发读工作进程"""
            successful_reads = 0
            read_times = []
            
            try:
                async with db_pool.acquire() as connection:
                    for i in range(iterations):
                        start_time = time.time()
                        
                        # 执行不同类型的读查询
                        query_type = i % 4
                        if query_type == 0:
                            result = await connection.fetchval("SELECT COUNT(*) FROM users")
                        elif query_type == 1:
                            result = await connection.fetch("SELECT * FROM users LIMIT 5")
                        elif query_type == 2:
                            result = await connection.fetchval("SELECT MAX(created_at) FROM users")
                        else:
                            result = await connection.fetch("SELECT is_active, COUNT(*) FROM users GROUP BY is_active")
                        
                        end_time = time.time()
                        read_times.append(end_time - start_time)
                        
                        if result is not None:
                            successful_reads += 1
                        
                        # 模拟处理时间
                        await asyncio.sleep(0.01)
                
                return {
                    'worker_id': worker_id,
                    'successful_reads': successful_reads,
                    'total_iterations': iterations,
                    'avg_read_time': sum(read_times) / len(read_times) if read_times else 0,
                    'max_read_time': max(read_times) if read_times else 0
                }
                
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'error': str(e),
                    'successful_reads': successful_reads
                }

        # 启动多个并发读工作进程
        worker_count = 8
        iterations_per_worker = 20
        
        print(f"🔄 启动 {worker_count} 个并发读工作进程，每个执行 {iterations_per_worker} 次读操作")
        
        start_time = time.time()
        
        tasks = []
        for worker_id in range(worker_count):
            task = asyncio.create_task(concurrent_read_worker(worker_id, iterations_per_worker))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        total_successful_reads = sum(r.get('successful_reads', 0) for r in results)
        total_expected_reads = worker_count * iterations_per_worker
        success_rate = total_successful_reads / total_expected_reads
        
        avg_read_times = [r.get('avg_read_time', 0) for r in results if 'avg_read_time' in r]
        overall_avg_read_time = sum(avg_read_times) / len(avg_read_times) if avg_read_times else 0
        
        throughput = total_successful_reads / total_time
        
        print(f"✅ 并发读操作测试结果:")
        print(f"   总读操作: {total_successful_reads}/{total_expected_reads}")
        print(f"   成功率: {success_rate:.1%}")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   平均读操作时间: {overall_avg_read_time:.6f}秒")
        print(f"   吞吐量: {throughput:.1f} 读/秒")
        
        # 性能断言
        assert success_rate >= 0.95, f"并发读成功率过低: {success_rate:.1%}"
        assert throughput > 50, f"读操作吞吐量过低: {throughput:.1f} 读/秒"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_writes(self, db_pool: asyncpg.Pool):
        """测试并发写操作"""
        # 检查users表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        async def concurrent_write_worker(worker_id: int, iterations: int):
            """并发写工作进程"""
            successful_writes = 0
            write_times = []
            created_records = []
            
            try:
                async with db_pool.acquire() as connection:
                    async with connection.transaction():
                        for i in range(iterations):
                            start_time = time.time()
                            
                            try:
                                # 创建唯一的用户
                                email = f"concurrent_write_{worker_id}_{i}@example.com"
                                username = f"concurrent_user_{worker_id}_{i}"
                                
                                user_id = await connection.fetchval(
                                    """
                                    INSERT INTO users (email, username, password_hash, is_active)
                                    VALUES ($1, $2, $3, $4)
                                    RETURNING id
                                    """,
                                    email, username, 'concurrent_hash', True
                                )
                                
                                if user_id:
                                    created_records.append(user_id)
                                    successful_writes += 1
                                
                                end_time = time.time()
                                write_times.append(end_time - start_time)
                                
                            except Exception as write_error:
                                # 记录写入错误但继续
                                end_time = time.time()
                                write_times.append(end_time - start_time)
                                print(f"Worker {worker_id} 写入错误: {write_error}")
                            
                            # 模拟处理时间
                            await asyncio.sleep(0.01)
                
                return {
                    'worker_id': worker_id,
                    'successful_writes': successful_writes,
                    'total_iterations': iterations,
                    'created_records': len(created_records),
                    'avg_write_time': sum(write_times) / len(write_times) if write_times else 0,
                    'max_write_time': max(write_times) if write_times else 0
                }
                
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'error': str(e),
                    'successful_writes': successful_writes
                }

        # 启动多个并发写工作进程
        worker_count = 4  # 减少写并发以避免锁竞争
        iterations_per_worker = 10
        
        print(f"🔄 启动 {worker_count} 个并发写工作进程，每个执行 {iterations_per_worker} 次写操作")
        
        start_time = time.time()
        
        tasks = []
        for worker_id in range(worker_count):
            task = asyncio.create_task(concurrent_write_worker(worker_id, iterations_per_worker))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        total_successful_writes = sum(r.get('successful_writes', 0) for r in results)
        total_expected_writes = worker_count * iterations_per_worker
        success_rate = total_successful_writes / total_expected_writes
        
        avg_write_times = [r.get('avg_write_time', 0) for r in results if 'avg_write_time' in r]
        overall_avg_write_time = sum(avg_write_times) / len(avg_write_times) if avg_write_times else 0
        
        throughput = total_successful_writes / total_time
        
        print(f"✅ 并发写操作测试结果:")
        print(f"   总写操作: {total_successful_writes}/{total_expected_writes}")
        print(f"   成功率: {success_rate:.1%}")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   平均写操作时间: {overall_avg_write_time:.6f}秒")
        print(f"   吞吐量: {throughput:.1f} 写/秒")
        
        # 显示错误信息
        errors = [r.get('error') for r in results if 'error' in r]
        if errors:
            print(f"   遇到错误: {len(errors)} 个工作进程")
        
        # 性能断言（写操作容许较低的成功率）
        assert success_rate >= 0.7, f"并发写成功率过低: {success_rate:.1%}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_pool: asyncpg.Pool):
        """测试事务隔离级别"""
        # 检查users表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        async def transaction_worker_a():
            """事务A - 更新用户状态"""
            async with db_pool.acquire() as connection:
                async with connection.transaction():
                    # 创建测试用户
                    user_id = await connection.fetchval(
                        """
                        INSERT INTO users (email, username, password_hash, is_active)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id
                        """,
                        'isolation_test_a@example.com', 'isolation_user_a', 'hash', True
                    )
                    
                    # 模拟长时间处理
                    await asyncio.sleep(0.5)
                    
                    # 更新用户状态
                    await connection.execute(
                        "UPDATE users SET is_active = false WHERE id = $1",
                        user_id
                    )
                    
                    # 再次睡眠模拟更多处理
                    await asyncio.sleep(0.3)
                    
                    return user_id

        async def transaction_worker_b():
            """事务B - 读取用户状态"""
            async with db_pool.acquire() as connection:
                # 等待事务A开始
                await asyncio.sleep(0.1)
                
                # 尝试读取数据（应该在事务A提交前后看到不同结果）
                before_results = []
                after_results = []
                
                # 事务A执行期间的读取
                for _ in range(3):
                    count_active = await connection.fetchval(
                        "SELECT COUNT(*) FROM users WHERE email LIKE 'isolation_test_%' AND is_active = true"
                    )
                    before_results.append(count_active)
                    await asyncio.sleep(0.2)
                
                # 等待事务A完成
                await asyncio.sleep(1.0)
                
                # 事务A完成后的读取
                count_active_after = await connection.fetchval(
                    "SELECT COUNT(*) FROM users WHERE email LIKE 'isolation_test_%' AND is_active = true"
                )
                after_results.append(count_active_after)
                
                return {
                    'before_commit': before_results,
                    'after_commit': after_results
                }

        # 启动两个并发事务
        print("🔄 测试事务隔离级别")
        
        start_time = time.time()
        
        task_a = asyncio.create_task(transaction_worker_a())
        task_b = asyncio.create_task(transaction_worker_b())
        
        results = await asyncio.gather(task_a, task_b)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        user_id_a = results[0]
        read_results = results[1]
        
        print(f"✅ 事务隔离测试结果:")
        print(f"   执行时间: {total_time:.3f}秒")
        print(f"   事务A创建用户ID: {user_id_a}")
        print(f"   事务B提交前读取: {read_results['before_commit']}")
        print(f"   事务B提交后读取: {read_results['after_commit']}")
        
        # 清理测试数据
        async with db_pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM users WHERE email LIKE 'isolation_test_%'"
            )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_deadlock_detection(self, db_pool: asyncpg.Pool):
        """测试死锁检测和处理"""
        # 检查users表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 首先创建两个测试用户
        async with db_pool.acquire() as connection:
            user1_id = await connection.fetchval(
                """
                INSERT INTO users (email, username, password_hash, is_active)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                'deadlock_test_1@example.com', 'deadlock_user_1', 'hash', True
            )
            
            user2_id = await connection.fetchval(
                """
                INSERT INTO users (email, username, password_hash, is_active)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                'deadlock_test_2@example.com', 'deadlock_user_2', 'hash', True
            )

        async def deadlock_worker_1():
            """可能导致死锁的事务1"""
            try:
                async with db_pool.acquire() as connection:
                    async with connection.transaction():
                        # 首先锁定用户1
                        await connection.execute(
                            "UPDATE users SET is_active = false WHERE id = $1",
                            user1_id
                        )
                        
                        # 等待一段时间，让事务2也开始
                        await asyncio.sleep(0.5)
                        
                        # 尝试锁定用户2（可能导致死锁）
                        await connection.execute(
                            "UPDATE users SET is_active = false WHERE id = $1",
                            user2_id
                        )
                        
                        return {'success': True, 'transaction': 1}
                        
            except Exception as e:
                error_msg = str(e)
                is_deadlock = 'deadlock detected' in error_msg.lower()
                return {
                    'success': False,
                    'transaction': 1,
                    'error': error_msg,
                    'is_deadlock': is_deadlock
                }

        async def deadlock_worker_2():
            """可能导致死锁的事务2"""
            try:
                # 稍微延迟启动，但不要太长
                await asyncio.sleep(0.1)
                
                async with db_pool.acquire() as connection:
                    async with connection.transaction():
                        # 首先锁定用户2
                        await connection.execute(
                            "UPDATE users SET is_active = true WHERE id = $1",
                            user2_id
                        )
                        
                        # 等待一段时间，确保事务1也在进行
                        await asyncio.sleep(0.5)
                        
                        # 尝试锁定用户1（可能导致死锁）
                        await connection.execute(
                            "UPDATE users SET is_active = true WHERE id = $1",
                            user1_id
                        )
                        
                        return {'success': True, 'transaction': 2}
                        
            except Exception as e:
                error_msg = str(e)
                is_deadlock = 'deadlock detected' in error_msg.lower()
                return {
                    'success': False,
                    'transaction': 2,
                    'error': error_msg,
                    'is_deadlock': is_deadlock
                }

        print("🔄 测试死锁检测和处理")
        
        start_time = time.time()
        
        # 启动可能导致死锁的两个事务
        task1 = asyncio.create_task(deadlock_worker_1())
        task2 = asyncio.create_task(deadlock_worker_2())
        
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ 死锁检测测试结果:")
        print(f"   执行时间: {total_time:.3f}秒")
        
        deadlock_detected = False
        successful_transactions = 0
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                if result.get('success', False):
                    successful_transactions += 1
                    print(f"   事务{result['transaction']}: 成功完成")
                else:
                    if result.get('is_deadlock', False):
                        deadlock_detected = True
                        print(f"   事务{result['transaction']}: 检测到死锁")
                    else:
                        print(f"   事务{result['transaction']}: 其他错误 - {result.get('error', 'Unknown')[:100]}")
            else:
                print(f"   事务{i+1}: 异常 - {str(result)[:100]}")
        
        print(f"   成功事务: {successful_transactions}/2")
        print(f"   死锁检测: {'是' if deadlock_detected else '否'}")
        
        # 清理测试数据
        async with db_pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM users WHERE email LIKE 'deadlock_test_%'"
            )
        
        # 断言：应该至少有一个事务成功，或者检测到死锁
        assert successful_transactions > 0 or deadlock_detected, \
            "应该有成功的事务或者检测到死锁"

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_running_transactions(self, db_pool: asyncpg.Pool):
        """测试长时间运行的事务"""
        # 检查users表是否存在
        async with db_pool.acquire() as connection:
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
        
        if not table_exists:
            pytest.skip("users表不存在")

        async def long_running_transaction(transaction_id: int, duration: float):
            """长时间运行的事务"""
            try:
                async with db_pool.acquire() as connection:
                    async with connection.transaction():
                        # 创建用户
                        user_id = await connection.fetchval(
                            """
                            INSERT INTO users (email, username, password_hash, is_active)
                            VALUES ($1, $2, $3, $4)
                            RETURNING id
                            """,
                            f'long_tx_{transaction_id}@example.com',
                            f'long_tx_user_{transaction_id}',
                            'long_hash', True
                        )
                        
                        # 模拟长时间处理
                        await asyncio.sleep(duration)
                        
                        # 更新用户
                        await connection.execute(
                            "UPDATE users SET is_active = false WHERE id = $1",
                            user_id
                        )
                        
                        # 再次处理
                        await asyncio.sleep(duration / 2)
                        
                        return {
                            'transaction_id': transaction_id,
                            'success': True,
                            'user_id': user_id,
                            'duration': duration
                        }
                        
            except Exception as e:
                return {
                    'transaction_id': transaction_id,
                    'success': False,
                    'error': str(e),
                    'duration': duration
                }

        async def concurrent_short_operations():
            """并发的短操作"""
            operations_completed = 0
            
            for i in range(20):
                try:
                    async with db_pool.acquire() as connection:
                        # 快速查询操作
                        count = await connection.fetchval("SELECT COUNT(*) FROM users")
                        if isinstance(count, int):
                            operations_completed += 1
                        
                        await asyncio.sleep(0.05)  # 50ms间隔
                        
                except Exception as e:
                    print(f"短操作 {i} 失败: {e}")
            
            return operations_completed

        print("🔄 测试长时间运行事务的影响")
        
        # 启动长事务和短操作
        start_time = time.time()
        
        # 启动2个长事务
        long_tx_tasks = [
            asyncio.create_task(long_running_transaction(1, 2.0)),
            asyncio.create_task(long_running_transaction(2, 1.5))
        ]
        
        # 启动短操作
        short_ops_task = asyncio.create_task(concurrent_short_operations())
        
        # 等待所有任务完成
        all_tasks = long_tx_tasks + [short_ops_task]
        results = await asyncio.gather(*all_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        long_tx_results = results[:-1]
        short_ops_completed = results[-1]
        
        successful_long_tx = sum(1 for r in long_tx_results if r.get('success', False))
        
        print(f"✅ 长事务测试结果:")
        print(f"   总执行时间: {total_time:.3f}秒")
        print(f"   长事务成功: {successful_long_tx}/{len(long_tx_results)}")
        print(f"   短操作完成: {short_ops_completed}/20")
        
        for result in long_tx_results:
            if result.get('success', False):
                print(f"   长事务{result['transaction_id']}: 成功 ({result['duration']}s)")
            else:
                print(f"   长事务{result['transaction_id']}: 失败 - {result.get('error', 'Unknown')[:50]}")
        
        # 清理测试数据
        async with db_pool.acquire() as connection:
            await connection.execute("DELETE FROM users WHERE email LIKE 'long_tx_%'")
        
        # 断言：长事务不应该显著影响短操作
        short_ops_success_rate = short_ops_completed / 20
        assert short_ops_success_rate >= 0.8, \
            f"长事务严重影响了短操作: 成功率仅 {short_ops_success_rate:.1%}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_connection_pool_stress(self, db_config: Dict[str, Any]):
        """测试连接池压力"""
        # 创建小的连接池进行压力测试
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        pool = await asyncpg.create_pool(
            connection_string,
            min_size=2,
            max_size=5,  # 小连接池
            command_timeout=30
        )
        
        async def pool_worker(worker_id: int, operations: int):
            """连接池工作进程"""
            successful_operations = 0
            wait_times = []
            
            for i in range(operations):
                start_wait = time.time()
                
                try:
                    async with pool.acquire() as connection:
                        end_wait = time.time()
                        wait_times.append(end_wait - start_wait)
                        
                        # 执行一些数据库操作
                        await connection.fetchval("SELECT $1", f"worker_{worker_id}_op_{i}")
                        
                        # 模拟处理时间
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        
                        successful_operations += 1
                        
                except Exception as e:
                    print(f"Worker {worker_id} 操作 {i} 失败: {e}")
            
            return {
                'worker_id': worker_id,
                'successful_operations': successful_operations,
                'total_operations': operations,
                'avg_wait_time': sum(wait_times) / len(wait_times) if wait_times else 0,
                'max_wait_time': max(wait_times) if wait_times else 0
            }
        
        try:
            print("🔄 测试连接池压力 (最大5个连接)")
            
            # 启动10个工作进程竞争5个连接
            worker_count = 10
            operations_per_worker = 8
            
            start_time = time.time()
            
            tasks = []
            for worker_id in range(worker_count):
                task = asyncio.create_task(pool_worker(worker_id, operations_per_worker))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            total_successful = sum(r['successful_operations'] for r in results)
            total_expected = worker_count * operations_per_worker
            success_rate = total_successful / total_expected
            
            avg_wait_times = [r['avg_wait_time'] for r in results if r['avg_wait_time'] > 0]
            overall_avg_wait = sum(avg_wait_times) / len(avg_wait_times) if avg_wait_times else 0
            
            max_wait_time = max((r['max_wait_time'] for r in results), default=0)
            
            print(f"✅ 连接池压力测试结果:")
            print(f"   工作进程: {worker_count}")
            print(f"   连接池大小: 2-5")
            print(f"   总操作: {total_successful}/{total_expected}")
            print(f"   成功率: {success_rate:.1%}")
            print(f"   总耗时: {total_time:.3f}秒")
            print(f"   平均等待时间: {overall_avg_wait:.3f}秒")
            print(f"   最长等待时间: {max_wait_time:.3f}秒")
            
            # 性能断言
            assert success_rate >= 0.9, f"连接池压力测试成功率过低: {success_rate:.1%}"
            assert overall_avg_wait < 1.0, f"连接池等待时间过长: {overall_avg_wait:.3f}s"
            
        finally:
            await pool.close()

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_query_timeout_handling(self, db_pool: asyncpg.Pool):
        """测试查询超时处理"""
        print("🔄 测试查询超时处理")
        
        async def timeout_test_query(timeout_seconds: float):
            """执行可能超时的查询"""
            try:
                async with db_pool.acquire() as connection:
                    # 设置查询超时
                    start_time = time.time()
                    
                    result = await asyncio.wait_for(
                        connection.fetchval("SELECT pg_sleep($1), 'completed'", timeout_seconds),
                        timeout=timeout_seconds + 0.5
                    )
                    
                    end_time = time.time()
                    actual_time = end_time - start_time
                    
                    return {
                        'success': True,
                        'expected_time': timeout_seconds,
                        'actual_time': actual_time,
                        'result': result
                    }
                    
            except asyncio.TimeoutError:
                end_time = time.time()
                actual_time = end_time - start_time
                return {
                    'success': False,
                    'timeout': True,
                    'expected_time': timeout_seconds,
                    'actual_time': actual_time
                }
            except Exception as e:
                return {
                    'success': False,
                    'timeout': False,
                    'error': str(e),
                    'expected_time': timeout_seconds
                }

        # 测试不同的超时场景
        timeout_tests = [
            0.1,  # 100ms - 应该成功
            0.5,  # 500ms - 应该成功
            1.0,  # 1s - 应该成功但较慢
            # 2.0   # 2s - 可能超时（取决于服务器性能）
        ]
        
        results = []
        for timeout in timeout_tests:
            print(f"   测试 {timeout}秒 超时...")
            result = await timeout_test_query(timeout)
            results.append(result)
            
            if result['success']:
                print(f"   ✅ {timeout}秒查询成功，实际耗时: {result['actual_time']:.3f}秒")
            elif result.get('timeout', False):
                print(f"   ⏱️  {timeout}秒查询超时，实际耗时: {result['actual_time']:.3f}秒")
            else:
                print(f"   ❌ {timeout}秒查询失败: {result.get('error', 'Unknown')}")
        
        # 验证超时机制工作正常
        successful_queries = sum(1 for r in results if r['success'])
        print(f"✅ 查询超时测试完成: {successful_queries}/{len(results)} 个查询成功")
        
        # 至少短时间的查询应该成功
        short_queries = [r for r in results if r['expected_time'] <= 0.5]
        short_successful = sum(1 for r in short_queries if r['success'])
        
        if short_queries:
            assert short_successful > 0, "短时间查询应该至少有一个成功"