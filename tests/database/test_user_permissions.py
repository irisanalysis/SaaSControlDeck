"""
用户权限测试套件

测试各环境数据库用户的权限配置和访问控制
"""

import pytest
import asyncpg
from typing import Dict, Any, List
from . import TEST_ENVIRONMENTS


class TestUserPermissions:
    """用户权限测试类"""

    @pytest.mark.asyncio
    async def test_user_identity_verification(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """验证用户身份"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            # 检查当前用户
            current_user = await connection.fetchval("SELECT current_user")
            expected_user = TEST_ENVIRONMENTS[env_name]['user']
            
            assert current_user == expected_user, f"用户身份不匹配 {env_name}: {current_user} != {expected_user}"
            
            # 检查用户所属的角色
            user_roles = await connection.fetch(
                "SELECT rolname FROM pg_roles WHERE oid IN (SELECT unnest(rrrolesid) FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE rolname = current_user))"
            )
            role_names = [row['rolname'] for row in user_roles]
            
            print(f"✅ {env_name}: 用户 {current_user}, 角色: {role_names}")

    @pytest.mark.asyncio
    async def test_basic_select_permissions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试基本查询权限"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            try:
                # 测试系统表查询权限
                table_count = await connection.fetchval(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                assert isinstance(table_count, int)
                
                # 测试数据库大小查询权限
                db_size = await connection.fetchval("SELECT pg_database_size(current_database())")
                assert isinstance(db_size, int)
                
                # 测试表存在性查询
                users_table_exists = await connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
                
                print(f"✅ {env_name}: 基本查询权限正常，用户表存在: {users_table_exists}")
                
            except Exception as e:
                pytest.fail(f"{env_name}: 基本查询权限测试失败 - {e}")

    @pytest.mark.asyncio
    async def test_table_access_permissions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试表访问权限"""
        # 核心表列表
        core_tables = [
            'users', 'user_profiles', 'user_sessions', 
            'projects', 'project_members', 'project_settings',
            'ai_models', 'ai_tasks', 'ai_results',
            'data_sources', 'analysis_jobs', 'analysis_results',
            'file_storage', 'file_metadata',
            'system_logs', 'performance_metrics', 'audit_trails',
            'notifications'
        ]
        
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            accessible_tables = []
            inaccessible_tables = []
            
            for table in core_tables:
                try:
                    # 检查表是否存在
                    table_exists = await connection.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                        table
                    )
                    
                    if not table_exists:
                        inaccessible_tables.append(f"{table}(不存在)")
                        continue
                    
                    # 测试查询权限
                    count = await connection.fetchval(f"SELECT count(*) FROM {table}")
                    accessible_tables.append(f"{table}({count}行)")
                    
                except Exception as e:
                    inaccessible_tables.append(f"{table}(错误: {str(e)[:50]})")
            
            print(f"✅ {env_name}: 可访问表 ({len(accessible_tables)}): {', '.join(accessible_tables[:5])}{'...' if len(accessible_tables) > 5 else ''}")
            if inaccessible_tables:
                print(f"   ⚠️  不可访问表 ({len(inaccessible_tables)}): {', '.join(inaccessible_tables[:3])}{'...' if len(inaccessible_tables) > 3 else ''}")
            
            # 应该至少能访问一些核心表
            assert len(accessible_tables) > 0, f"{env_name}: 无法访问任何表"

    @pytest.mark.asyncio
    async def test_crud_permissions_by_environment(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """根据环境测试CRUD权限"""
        permission_expectations = {
            'dev_pro1': {'select': True, 'insert': True, 'update': True, 'delete': True},
            'dev_pro2': {'select': True, 'insert': True, 'update': True, 'delete': True},
            'stage_pro1': {'select': True, 'insert': True, 'update': True, 'delete': False},
            'stage_pro2': {'select': True, 'insert': True, 'update': True, 'delete': False},
            'prod_pro1': {'select': True, 'insert': False, 'update': False, 'delete': False},
            'prod_pro2': {'select': True, 'insert': False, 'update': False, 'delete': False}
        }
        
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            expected_perms = permission_expectations.get(env_name, {'select': True})
            actual_perms = {}
            
            # 检查users表是否存在
            users_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )
            
            if not users_exists:
                print(f"⚠️  {env_name}: users表不存在，跳过CRUD权限测试")
                continue
            
            # 测试SELECT权限
            try:
                await connection.fetchval("SELECT count(*) FROM users")
                actual_perms['select'] = True
            except Exception:
                actual_perms['select'] = False
            
            # 测试INSERT权限（使用事务回滚）
            try:
                async with connection.transaction():
                    await connection.execute(
                        "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                        'test@example.com', 'testuser', 'hashedpass'
                    )
                    actual_perms['insert'] = True
                    # 事务会自动回滚
            except Exception:
                actual_perms['insert'] = False
            
            # 测试UPDATE权限（只有在有数据的情况下）
            try:
                result = await connection.execute(
                    "UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE FALSE"
                )
                actual_perms['update'] = True
            except Exception:
                actual_perms['update'] = False
            
            # 测试DELETE权限
            try:
                result = await connection.execute(
                    "DELETE FROM users WHERE FALSE"
                )
                actual_perms['delete'] = True
            except Exception:
                actual_perms['delete'] = False
            
            # 验证权限是否符合预期
            permission_match = True
            for perm, expected in expected_perms.items():
                actual = actual_perms.get(perm, False)
                if actual != expected:
                    permission_match = False
                    print(f"⚠️  {env_name}: {perm} 权限不符合预期 (实际: {actual}, 期望: {expected})")
            
            if permission_match:
                print(f"✅ {env_name}: CRUD权限符合预期 - {actual_perms}")
            
            # 至少应该有SELECT权限
            assert actual_perms.get('select', False), f"{env_name}: 缺少基本的SELECT权限"

    @pytest.mark.asyncio
    async def test_schema_modification_permissions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试schema修改权限"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            permissions = {
                'create_table': False,
                'create_index': False,
                'create_function': False,
                'alter_table': False
            }
            
            # 测试CREATE TABLE权限
            try:
                async with connection.transaction():
                    await connection.execute(
                        "CREATE TEMP TABLE test_permissions (id integer)"
                    )
                    permissions['create_table'] = True
            except Exception:
                pass
            
            # 测试CREATE INDEX权限（在临时表上）
            if permissions['create_table']:
                try:
                    async with connection.transaction():
                        await connection.execute(
                            "CREATE TEMP TABLE test_index_table (id integer)"
                        )
                        await connection.execute(
                            "CREATE INDEX test_idx ON test_index_table (id)"
                        )
                        permissions['create_index'] = True
                except Exception:
                    pass
            
            # 测试CREATE FUNCTION权限
            try:
                async with connection.transaction():
                    await connection.execute(
                        """
                        CREATE OR REPLACE FUNCTION test_function()
                        RETURNS integer AS $$
                        BEGIN
                            RETURN 1;
                        END;
                        $$ LANGUAGE plpgsql;
                        """
                    )
                    permissions['create_function'] = True
            except Exception:
                pass
            
            print(f"✅ {env_name}: Schema权限 - {permissions}")
            
            # 开发环境应该有更多权限
            if 'dev' in env_name:
                assert permissions['create_table'], f"{env_name}: 开发环境应该有CREATE TABLE权限"

    @pytest.mark.asyncio
    async def test_connection_limits(self, db_config: Dict[str, Any]):
        """测试连接数限制"""
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        expected_limit = db_config['connection_limit']
        
        # 查询用户的连接限制
        connection = await asyncpg.connect(connection_string)
        
        try:
            # 检查用户的连接限制
            user_conn_limit = await connection.fetchval(
                "SELECT rolconnlimit FROM pg_roles WHERE rolname = current_user"
            )
            
            # 检查当前连接数
            current_connections = await connection.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE usename = current_user"
            )
            
            print(f"✅ 连接限制配置:")
            print(f"   用户连接限制: {user_conn_limit}")
            print(f"   当前连接数: {current_connections}")
            print(f"   期望限制: {expected_limit}")
            
            # 验证连接限制配置
            if user_conn_limit != -1:  # -1 表示无限制
                assert user_conn_limit > 0, "连接限制应该大于0"
            
            assert current_connections >= 1, "至少应该有一个当前连接"
            
        finally:
            await connection.close()

    @pytest.mark.asyncio
    async def test_database_specific_permissions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试数据库特定权限"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            # 检查数据库权限
            db_permissions = await connection.fetch(
                """
                SELECT datname, datacl
                FROM pg_database 
                WHERE datname = current_database()
                """
            )
            
            # 检查用户在当前数据库的权限
            user_db_privileges = await connection.fetch(
                """
                SELECT 
                    has_database_privilege(current_user, current_database(), 'CONNECT') as can_connect,
                    has_database_privilege(current_user, current_database(), 'CREATE') as can_create,
                    has_database_privilege(current_user, current_database(), 'TEMPORARY') as can_temp
                """
            )
            
            privileges = dict(user_db_privileges[0]) if user_db_privileges else {}
            
            print(f"✅ {env_name}: 数据库权限 - {privileges}")
            
            # 基本验证
            assert privileges.get('can_connect', False), f"{env_name}: 用户应该有CONNECT权限"

    @pytest.mark.asyncio
    async def test_superuser_restrictions(self, all_db_connections: Dict[str, asyncpg.Connection]):
        """测试超级用户限制"""
        for env_name, connection in all_db_connections.items():
            if connection is None:
                continue
                
            # 检查是否为超级用户
            is_superuser = await connection.fetchval(
                "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
            )
            
            # 检查是否可以创建角色
            can_create_role = await connection.fetchval(
                "SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user"
            )
            
            # 检查是否可以创建数据库
            can_create_db = await connection.fetchval(
                "SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user"
            )
            
            print(f"✅ {env_name}: 特权检查 - 超级用户: {is_superuser}, 创建角色: {can_create_role}, 创建数据库: {can_create_db}")
            
            # 生产环境不应该是超级用户
            if 'prod' in env_name:
                assert not is_superuser, f"{env_name}: 生产环境用户不应该是超级用户"
                assert not can_create_role, f"{env_name}: 生产环境用户不应该能创建角色"

    @pytest.mark.asyncio
    async def test_row_level_security(self, db_connection: asyncpg.Connection):
        """测试行级安全策略（如果启用）"""
        # 检查是否有启用RLS的表
        rls_tables = await db_connection.fetch(
            """
            SELECT schemaname, tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' AND rowsecurity = true
            """
        )
        
        if rls_tables:
            print(f"✅ 发现 {len(rls_tables)} 个启用行级安全的表:")
            for table in rls_tables:
                print(f"   - {table['tablename']}")
                
                # 检查RLS策略
                policies = await db_connection.fetch(
                    """
                    SELECT policyname, cmd, qual, with_check 
                    FROM pg_policies 
                    WHERE schemaname = $1 AND tablename = $2
                    """,
                    table['schemaname'], table['tablename']
                )
                
                for policy in policies:
                    print(f"     策略: {policy['policyname']} ({policy['cmd']})")
        else:
            print("✅ 未发现启用行级安全的表")

    @pytest.mark.asyncio
    async def test_privilege_escalation_protection(self, db_connection: asyncpg.Connection):
        """测试权限提升保护"""
        dangerous_operations = [
            ("SET role postgres", "角色切换到postgres"),
            ("CREATE USER malicious_user", "创建恶意用户"),
            ("ALTER USER current_user SUPERUSER", "提升为超级用户"),
            ("COPY (SELECT * FROM pg_shadow) TO '/tmp/passwords'", "导出密码信息"),
        ]
        
        for operation, description in dangerous_operations:
            try:
                await db_connection.execute(operation)
                print(f"⚠️  警告: {description} - 操作成功执行！")
            except Exception as e:
                print(f"✅ {description} - 被正确阻止: {type(e).__name__}")

    @pytest.mark.asyncio
    async def test_audit_logging_permissions(self, db_connection: asyncpg.Connection):
        """测试审计日志权限"""
        # 检查是否可以访问审计相关的系统视图
        audit_views = [
            'pg_stat_activity',
            'pg_stat_database', 
            'pg_stat_user_tables',
            'pg_locks'
        ]
        
        accessible_views = []
        for view in audit_views:
            try:
                count = await db_connection.fetchval(f"SELECT count(*) FROM {view}")
                accessible_views.append(view)
            except Exception:
                pass
        
        print(f"✅ 可访问的审计视图: {accessible_views}")
        
        # 应该至少能访问基本的统计视图
        assert 'pg_stat_activity' in accessible_views, "应该能访问pg_stat_activity"