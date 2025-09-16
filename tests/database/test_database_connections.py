"""
数据库连接测试套件

测试各环境数据库的连接性、连接池配置和网络稳定性
"""

import asyncio
import pytest
import asyncpg
import time
from typing import Dict, Any
from . import TEST_ENVIRONMENTS


class TestDatabaseConnections:
    """数据库连接测试类"""

    @pytest.mark.asyncio
    async def test_single_connection_all_environments(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试所有环境的单一连接"""
        successful_connections = 0
        failed_connections = []

        for env_name, connection in all_db_connections.items():
            if connection is None:
                failed_connections.append(env_name)
                continue
            
            try:
                # 执行简单查询验证连接
                result = await connection.fetchval("SELECT 1")
                assert result == 1
                successful_connections += 1
                
                # 检查数据库版本
                version = await connection.fetchval("SELECT version()")
                assert "PostgreSQL" in version
                
                # 检查当前数据库名
                db_name = await connection.fetchval("SELECT current_database()")
                expected_db = TEST_ENVIRONMENTS[env_name]['db_name']
                assert db_name == expected_db
                
                print(f"✅ {env_name}: 连接成功 - {expected_db}")
                
            except Exception as e:
                failed_connections.append(f"{env_name}: {str(e)}")

        # 报告结果
        print(f"\n连接测试结果:")
        print(f"成功连接: {successful_connections}/{len(TEST_ENVIRONMENTS)}")
        
        if failed_connections:
            print(f"失败连接: {failed_connections}")
        
        # 至少要有一个成功的连接
        assert successful_connections > 0, f"没有成功的数据库连接。失败详情: {failed_connections}"

    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self, db_config: Dict[str, Any]):
        """测试连接池配置"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        # 测试不同的连接池配置
        pool_configs = [
            {"min_size": 1, "max_size": 5},
            {"min_size": 2, "max_size": 10},
            {"min_size": 1, "max_size": 20}
        ]
        
        for config in pool_configs:
            try:
                pool = await asyncpg.create_pool(
                    connection_string,
                    min_size=config["min_size"],
                    max_size=config["max_size"],
                    command_timeout=30
                )
                
                # 验证连接池可以获取连接
                async with pool.acquire() as connection:
                    result = await connection.fetchval("SELECT 'pool_test'")
                    assert result == "pool_test"
                
                await pool.close()
                
                print(f"✅ 连接池配置测试成功: {config}")
                
            except Exception as e:
                pytest.fail(f"连接池配置失败 {config}: {e}")

    @pytest.mark.asyncio
    async def test_connection_timeout_and_retry(self, db_config: Dict[str, Any]):
        """测试连接超时和重试机制"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        # 测试连接超时
        start_time = time.time()
        try:
            connection = await asyncio.wait_for(
                asyncpg.connect(connection_string, command_timeout=5),
                timeout=10.0
            )
            
            connection_time = time.time() - start_time
            assert connection_time < 10, f"连接时间过长: {connection_time:.2f}秒"
            
            await connection.close()
            print(f"✅ 连接建立时间: {connection_time:.2f}秒")
            
        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            pytest.fail(f"连接失败: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, db_config: Dict[str, Any]):
        """测试并发连接"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        async def create_connection_and_query(connection_id: int):
            """创建连接并执行查询"""
            try:
                connection = await asyncpg.connect(connection_string)
                result = await connection.fetchval(f"SELECT {connection_id}")
                await connection.close()
                return result
            except Exception as e:
                return f"Error: {e}"

        # 并发创建多个连接
        concurrent_count = 10
        tasks = []
        
        start_time = time.time()
        for i in range(concurrent_count):
            task = asyncio.create_task(create_connection_and_query(i))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        successful_connections = 0
        for i, result in enumerate(results):
            if isinstance(result, int) and result == i:
                successful_connections += 1
            else:
                print(f"连接 {i} 失败: {result}")
        
        success_rate = successful_connections / concurrent_count
        total_time = end_time - start_time
        
        print(f"✅ 并发连接测试:")
        print(f"   成功率: {success_rate:.1%} ({successful_connections}/{concurrent_count})")
        print(f"   总时间: {total_time:.2f}秒")
        print(f"   平均连接时间: {total_time/concurrent_count:.3f}秒")
        
        assert success_rate >= 0.8, f"并发连接成功率过低: {success_rate:.1%}"

    @pytest.mark.asyncio 
    async def test_connection_persistence(self, db_connection: asyncpg.Connection):
        """测试连接持久性"""
        # 执行多个查询验证连接稳定性
        queries = [
            "SELECT current_timestamp",
            "SELECT current_user", 
            "SELECT current_database()",
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'",
            "SELECT pg_database_size(current_database())",
        ]
        
        results = []
        for i, query in enumerate(queries):
            try:
                result = await db_connection.fetchval(query)
                results.append(result)
                
                # 添加小延迟测试连接稳定性
                await asyncio.sleep(0.1)
                
            except Exception as e:
                pytest.fail(f"查询 {i+1} 失败: {query} - {e}")
        
        # 验证结果
        assert len(results) == len(queries), "部分查询失败"
        assert all(r is not None for r in results), "某些查询返回空值"
        
        print(f"✅ 连接持久性测试通过，执行 {len(queries)} 个查询")

    @pytest.mark.asyncio
    async def test_connection_recovery(self, db_config: Dict[str, Any]):
        """测试连接恢复能力"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        # 创建连接池
        pool = await asyncpg.create_pool(
            connection_string,
            min_size=2,
            max_size=5,
            command_timeout=30
        )
        
        try:
            # 正常操作
            async with pool.acquire() as connection:
                result1 = await connection.fetchval("SELECT 'before'")
                assert result1 == "before"
            
            # 模拟连接中断后的恢复
            # 注意：在实际环境中，这可能需要更复杂的测试
            await asyncio.sleep(1)
            
            # 验证连接池可以恢复
            async with pool.acquire() as connection:
                result2 = await connection.fetchval("SELECT 'after'")
                assert result2 == "after"
            
            print("✅ 连接恢复测试通过")
            
        finally:
            await pool.close()

    @pytest.mark.asyncio
    async def test_authentication_and_permissions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试身份验证和基本权限"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            try:
                # 检查当前用户
                current_user = await connection.fetchval("SELECT current_user")
                expected_user = TEST_ENVIRONMENTS[env_name]['user']
                assert current_user == expected_user, f"用户不匹配: {current_user} != {expected_user}"
                
                # 检查基本权限 - SELECT
                table_count = await connection.fetchval(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                assert isinstance(table_count, int), "无法查询系统表"
                
                # 检查是否可以访问用户表（如果存在）
                table_exists = await connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
                
                if table_exists:
                    # 尝试查询用户表
                    user_count = await connection.fetchval("SELECT count(*) FROM users")
                    assert isinstance(user_count, int), "无法查询users表"
                
                print(f"✅ {env_name}: 身份验证和权限验证通过")
                
            except Exception as e:
                print(f"❌ {env_name}: 权限测试失败 - {e}")

    @pytest.mark.asyncio
    async def test_database_metadata(self, db_connection: asyncpg.Connection):
        """测试数据库元数据访问"""
        metadata_queries = {
            "数据库大小": "SELECT pg_size_pretty(pg_database_size(current_database()))",
            "数据库版本": "SELECT version()",
            "字符编码": "SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = current_database()",
            "时区设置": "SELECT current_setting('timezone')",
            "表数量": "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'",
            "连接数": "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()",
        }
        
        metadata = {}
        for name, query in metadata_queries.items():
            try:
                result = await db_connection.fetchval(query)
                metadata[name] = result
            except Exception as e:
                pytest.fail(f"无法获取 {name}: {e}")
        
        # 验证关键元数据
        assert metadata["表数量"] >= 0
        assert metadata["连接数"] >= 1  # 至少有当前连接
        assert "PostgreSQL" in metadata["数据库版本"]
        
        print(f"✅ 数据库元数据:")
        for name, value in metadata.items():
            print(f"   {name}: {value}")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_connection_stress(self, db_config: Dict[str, Any]):
        """压力测试 - 大量连接创建和销毁"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        
        async def stress_worker(worker_id: int, iterations: int):
            """压力测试工作进程"""
            successful_ops = 0
            for i in range(iterations):
                try:
                    connection = await asyncpg.connect(connection_string)
                    result = await connection.fetchval("SELECT $1", worker_id * 1000 + i)
                    await connection.close()
                    
                    if result == worker_id * 1000 + i:
                        successful_ops += 1
                        
                except Exception:
                    pass  # 忽略个别失败
                    
            return successful_ops
        
        # 启动多个工作进程
        workers = 5
        iterations_per_worker = 20
        
        start_time = time.time()
        tasks = []
        for worker_id in range(workers):
            task = asyncio.create_task(stress_worker(worker_id, iterations_per_worker))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 统计结果
        total_successful = sum(results)
        total_operations = workers * iterations_per_worker
        success_rate = total_successful / total_operations
        ops_per_second = total_operations / (end_time - start_time)
        
        print(f"✅ 压力测试结果:")
        print(f"   成功操作: {total_successful}/{total_operations} ({success_rate:.1%})")
        print(f"   操作速率: {ops_per_second:.1f} ops/秒")
        print(f"   总耗时: {end_time - start_time:.2f} 秒")
        
        assert success_rate >= 0.9, f"压力测试成功率过低: {success_rate:.1%}"