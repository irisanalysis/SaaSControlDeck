"""
项目模块CRUD操作测试套件

测试项目管理相关表的完整CRUD操作
"""

import pytest
import asyncpg
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta


class TestProjectsCRUD:
    """项目CRUD操作测试类"""

    @pytest.mark.asyncio
    async def test_projects_table_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试projects表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not table_exists:
            pytest.skip("projects表不存在")

        # CREATE - 创建项目
        project_data = {
            'name': 'SaaS Control Test Project',
            'slug': 'saas-control-test-project',
            'description': 'A comprehensive test project for the SaaS Control Deck platform',
            'owner_id': sample_user_in_db['id'],
            'status': 'active',
            'visibility': 'private',
            'settings': {
                'ai_features_enabled': True,
                'data_retention_days': 90,
                'auto_backup_enabled': True,
                'collaboration_enabled': True,
                'max_file_size_mb': 100,
                'allowed_file_types': ['csv', 'json', 'xlsx']
            },
            'tags': ['test', 'saas-control', 'ai-platform']
        }
        
        project_id = await db_transaction.fetchval(
            """
            INSERT INTO projects (name, slug, description, owner_id, status, visibility, settings, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            project_data['name'], project_data['slug'], project_data['description'],
            project_data['owner_id'], project_data['status'], project_data['visibility'],
            json.dumps(project_data['settings']), project_data['tags']
        )
        
        assert project_id is not None
        print(f"✅ 创建项目成功: {project_id}")

        # READ - 查询项目
        created_project = await db_transaction.fetchrow(
            "SELECT * FROM projects WHERE id = $1",
            project_id
        )
        
        assert created_project is not None
        assert created_project['name'] == project_data['name']
        assert created_project['slug'] == project_data['slug']
        assert created_project['owner_id'] == project_data['owner_id']
        assert created_project['status'] == project_data['status']
        assert created_project['visibility'] == project_data['visibility']
        assert created_project['tags'] == project_data['tags']
        assert created_project['created_at'] is not None
        assert created_project['updated_at'] is not None
        print("✅ 查询项目成功")

        # UPDATE - 更新项目
        update_data = {
            'description': 'Updated project description with new features',
            'status': 'inactive',
            'settings': {
                'ai_features_enabled': True,
                'data_retention_days': 120,
                'auto_backup_enabled': False,
                'collaboration_enabled': True,
                'max_file_size_mb': 200,
                'allowed_file_types': ['csv', 'json', 'xlsx', 'pdf']
            },
            'tags': ['test', 'saas-control', 'ai-platform', 'updated']
        }
        
        await db_transaction.execute(
            """
            UPDATE projects 
            SET description = $1, status = $2, settings = $3, tags = $4
            WHERE id = $5
            """,
            update_data['description'], update_data['status'],
            json.dumps(update_data['settings']), update_data['tags'], project_id
        )
        
        # 验证更新
        updated_project = await db_transaction.fetchrow(
            "SELECT * FROM projects WHERE id = $1",
            project_id
        )
        
        assert updated_project['description'] == update_data['description']
        assert updated_project['status'] == update_data['status']
        assert updated_project['tags'] == update_data['tags']
        assert updated_project['updated_at'] > created_project['updated_at']
        print("✅ 更新项目成功")

        # SOFT DELETE - 归档项目
        archive_time = datetime.now(timezone.utc)
        await db_transaction.execute(
            """
            UPDATE projects 
            SET status = 'archived', archived_at = $1
            WHERE id = $2
            """,
            archive_time, project_id
        )
        
        # 验证归档
        archived_project = await db_transaction.fetchrow(
            "SELECT * FROM projects WHERE id = $1",
            project_id
        )
        
        assert archived_project['status'] == 'archived'
        assert archived_project['archived_at'] is not None
        print("✅ 项目归档成功")

        # DELETE - 物理删除项目
        await db_transaction.execute(
            "DELETE FROM projects WHERE id = $1",
            project_id
        )
        
        # 验证删除
        deleted_project = await db_transaction.fetchrow(
            "SELECT * FROM projects WHERE id = $1",
            project_id
        )
        
        assert deleted_project is None
        print("✅ 删除项目成功")

    @pytest.mark.asyncio
    async def test_project_members_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试project_members表的CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_members')"
        )
        
        if not table_exists:
            pytest.skip("project_members表不存在")

        # 创建另一个测试用户作为成员
        member_user_id = await db_transaction.fetchval(
            """
            INSERT INTO users (email, username, password_hash, is_active, is_verified)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            'project_member@example.com', 'project_member',
            'dummy_hash', True, True
        )

        # CREATE - 添加项目成员
        member_data = {
            'project_id': sample_project_in_db['id'],
            'user_id': member_user_id,
            'role': 'editor',
            'permissions': {
                'read': True,
                'write': True,
                'admin': False,
                'delete': False,
                'invite_members': False,
                'manage_settings': False
            },
            'invited_by': sample_user_in_db['id'],
            'joined_at': datetime.now(timezone.utc)
        }
        
        member_id = await db_transaction.fetchval(
            """
            INSERT INTO project_members 
            (project_id, user_id, role, permissions, invited_by, joined_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            member_data['project_id'], member_data['user_id'], member_data['role'],
            json.dumps(member_data['permissions']), member_data['invited_by'],
            member_data['joined_at']
        )
        
        assert member_id is not None
        print(f"✅ 添加项目成员成功: {member_id}")

        # READ - 查询项目成员
        created_member = await db_transaction.fetchrow(
            "SELECT * FROM project_members WHERE id = $1",
            member_id
        )
        
        assert created_member is not None
        assert created_member['project_id'] == member_data['project_id']
        assert created_member['user_id'] == member_data['user_id']
        assert created_member['role'] == member_data['role']
        assert created_member['invited_by'] == member_data['invited_by']
        print("✅ 查询项目成员成功")

        # UPDATE - 升级成员权限
        update_data = {
            'role': 'admin',
            'permissions': {
                'read': True,
                'write': True,
                'admin': True,
                'delete': True,
                'invite_members': True,
                'manage_settings': True
            },
            'last_activity_at': datetime.now(timezone.utc)
        }
        
        await db_transaction.execute(
            """
            UPDATE project_members 
            SET role = $1, permissions = $2, last_activity_at = $3
            WHERE id = $4
            """,
            update_data['role'], json.dumps(update_data['permissions']),
            update_data['last_activity_at'], member_id
        )
        
        # 验证更新
        updated_member = await db_transaction.fetchrow(
            "SELECT * FROM project_members WHERE id = $1",
            member_id
        )
        
        assert updated_member['role'] == update_data['role']
        assert updated_member['last_activity_at'] is not None
        print("✅ 更新项目成员成功")

        # READ - 查询项目的所有成员
        all_members = await db_transaction.fetch(
            """
            SELECT pm.*, u.username, u.email 
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = $1
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 项目成员查询: 找到 {len(all_members)} 个成员")

        # DELETE - 移除项目成员
        await db_transaction.execute(
            "DELETE FROM project_members WHERE id = $1",
            member_id
        )
        
        # 验证删除
        deleted_member = await db_transaction.fetchrow(
            "SELECT * FROM project_members WHERE id = $1",
            member_id
        )
        
        assert deleted_member is None
        print("✅ 移除项目成员成功")

    @pytest.mark.asyncio
    async def test_project_settings_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试project_settings表的CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_settings')"
        )
        
        if not table_exists:
            pytest.skip("project_settings表不存在")

        # CREATE - 创建项目设置
        settings_data = [
            {
                'project_id': sample_project_in_db['id'],
                'setting_category': 'ai',
                'setting_key': 'model_preference',
                'setting_value': {
                    'primary_model': 'gpt-4',
                    'fallback_model': 'gpt-3.5-turbo',
                    'temperature': 0.7,
                    'max_tokens': 4096
                },
                'is_encrypted': False,
                'updated_by': sample_user_in_db['id']
            },
            {
                'project_id': sample_project_in_db['id'],
                'setting_category': 'security',
                'setting_key': 'api_keys',
                'setting_value': {
                    'openai_api_key': '***encrypted***',
                    'last_rotated': datetime.now(timezone.utc).isoformat()
                },
                'is_encrypted': True,
                'updated_by': sample_user_in_db['id']
            },
            {
                'project_id': sample_project_in_db['id'],
                'setting_category': 'data',
                'setting_key': 'retention_policy',
                'setting_value': {
                    'default_retention_days': 90,
                    'auto_cleanup_enabled': True,
                    'backup_before_cleanup': True
                },
                'is_encrypted': False,
                'updated_by': sample_user_in_db['id']
            }
        ]
        
        setting_ids = []
        for setting in settings_data:
            setting_id = await db_transaction.fetchval(
                """
                INSERT INTO project_settings 
                (project_id, setting_category, setting_key, setting_value, is_encrypted, updated_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                setting['project_id'], setting['setting_category'], setting['setting_key'],
                json.dumps(setting['setting_value']), setting['is_encrypted'],
                setting['updated_by']
            )
            setting_ids.append(setting_id)
        
        print(f"✅ 创建项目设置成功: {len(setting_ids)} 个设置")

        # READ - 查询项目设置
        ai_setting = await db_transaction.fetchrow(
            """
            SELECT * FROM project_settings 
            WHERE project_id = $1 AND setting_category = $2 AND setting_key = $3
            """,
            sample_project_in_db['id'], 'ai', 'model_preference'
        )
        
        assert ai_setting is not None
        assert ai_setting['setting_category'] == 'ai'
        assert ai_setting['is_encrypted'] == False
        print("✅ 查询项目设置成功")

        # READ - 按类别查询设置
        security_settings = await db_transaction.fetch(
            """
            SELECT * FROM project_settings 
            WHERE project_id = $1 AND setting_category = $2
            """,
            sample_project_in_db['id'], 'security'
        )
        
        print(f"✅ 按类别查询设置: 找到 {len(security_settings)} 个安全设置")

        # UPDATE - 更新设置值
        updated_ai_settings = {
            'primary_model': 'gpt-4-turbo',
            'fallback_model': 'gpt-3.5-turbo',
            'temperature': 0.5,
            'max_tokens': 8192,
            'enable_streaming': True
        }
        
        await db_transaction.execute(
            """
            UPDATE project_settings 
            SET setting_value = $1, updated_by = $2
            WHERE project_id = $3 AND setting_category = $4 AND setting_key = $5
            """,
            json.dumps(updated_ai_settings), sample_user_in_db['id'],
            sample_project_in_db['id'], 'ai', 'model_preference'
        )
        
        # 验证更新
        updated_setting = await db_transaction.fetchrow(
            """
            SELECT * FROM project_settings 
            WHERE project_id = $1 AND setting_category = $2 AND setting_key = $3
            """,
            sample_project_in_db['id'], 'ai', 'model_preference'
        )
        
        updated_value = json.loads(updated_setting['setting_value'])
        assert updated_value['primary_model'] == 'gpt-4-turbo'
        assert updated_value['enable_streaming'] == True
        print("✅ 更新项目设置成功")

        # DELETE - 删除特定设置
        await db_transaction.execute(
            """
            DELETE FROM project_settings 
            WHERE project_id = $1 AND setting_category = $2 AND setting_key = $3
            """,
            sample_project_in_db['id'], 'data', 'retention_policy'
        )
        
        # 验证删除
        deleted_setting = await db_transaction.fetchrow(
            """
            SELECT * FROM project_settings 
            WHERE project_id = $1 AND setting_category = $2 AND setting_key = $3
            """,
            sample_project_in_db['id'], 'data', 'retention_policy'
        )
        
        assert deleted_setting is None
        print("✅ 删除项目设置成功")

    @pytest.mark.asyncio
    async def test_project_relationship_integrity(self, db_transaction: asyncpg.Connection):
        """测试项目相关表之间的关系完整性"""
        # 检查所有相关表是否存在
        tables_to_check = ['users', 'projects', 'project_members', 'project_settings']
        existing_tables = []
        
        for table in tables_to_check:
            exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                existing_tables.append(table)
        
        if 'users' not in existing_tables or 'projects' not in existing_tables:
            pytest.skip("缺少必要的表进行关系测试")

        # 创建测试用户
        user_id = await db_transaction.fetchval(
            """
            INSERT INTO users (email, username, password_hash, is_active, is_verified)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            'project_relationship_test@example.com', 'project_rel_user',
            'dummy_hash', True, False
        )

        # 创建测试项目
        project_id = await db_transaction.fetchval(
            """
            INSERT INTO projects (name, slug, owner_id, status, visibility)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            'Relationship Test Project', 'relationship-test-project',
            user_id, 'active', 'private'
        )

        member_id = None
        setting_id = None

        # 创建项目成员（如果表存在）
        if 'project_members' in existing_tables:
            # 创建另一个用户作为成员
            member_user_id = await db_transaction.fetchval(
                """
                INSERT INTO users (email, username, password_hash, is_active, is_verified)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                'project_member_rel@example.com', 'project_member_rel',
                'dummy_hash', True, True
            )
            
            member_id = await db_transaction.fetchval(
                """
                INSERT INTO project_members (project_id, user_id, role)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                project_id, member_user_id, 'member'
            )
            print("✅ 创建项目成员关系成功")

        # 创建项目设置（如果表存在）
        if 'project_settings' in existing_tables:
            setting_id = await db_transaction.fetchval(
                """
                INSERT INTO project_settings 
                (project_id, setting_category, setting_key, setting_value, updated_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                project_id, 'test', 'test_setting',
                '{"value": "test"}', user_id
            )
            print("✅ 创建项目设置关系成功")

        # 验证关系存在
        if member_id:
            member_exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM project_members WHERE project_id = $1)",
                project_id
            )
            assert member_exists, "项目成员关系未建立"

        if setting_id:
            setting_exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM project_settings WHERE project_id = $1)",
                project_id
            )
            assert setting_exists, "项目设置关系未建立"

        # 测试级联删除
        await db_transaction.execute(
            "DELETE FROM projects WHERE id = $1",
            project_id
        )

        # 验证级联删除效果
        if member_id:
            member_after_delete = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM project_members WHERE project_id = $1)",
                project_id
            )
            assert not member_after_delete, "项目成员未被级联删除"
            print("✅ 项目成员级联删除成功")

        if setting_id:
            setting_after_delete = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM project_settings WHERE project_id = $1)",
                project_id
            )
            assert not setting_after_delete, "项目设置未被级联删除"
            print("✅ 项目设置级联删除成功")

    @pytest.mark.asyncio
    async def test_project_search_and_filtering(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试项目搜索和过滤功能"""
        # 检查projects表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not table_exists:
            pytest.skip("projects表不存在")

        # 创建多个测试项目用于搜索
        test_projects = [
            {
                'name': 'AI Data Analysis Platform',
                'slug': 'ai-data-analysis',
                'status': 'active',
                'visibility': 'public',
                'tags': ['ai', 'data', 'analysis']
            },
            {
                'name': 'Marketing Dashboard',
                'slug': 'marketing-dashboard',
                'status': 'active',
                'visibility': 'private',
                'tags': ['marketing', 'dashboard', 'analytics']
            },
            {
                'name': 'Legacy System Integration',
                'slug': 'legacy-integration',
                'status': 'archived',
                'visibility': 'internal',
                'tags': ['legacy', 'integration', 'migration']
            }
        ]
        
        created_project_ids = []
        for project in test_projects:
            project_id = await db_transaction.fetchval(
                """
                INSERT INTO projects (name, slug, owner_id, status, visibility, tags)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                project['name'], project['slug'], sample_user_in_db['id'],
                project['status'], project['visibility'], project['tags']
            )
            created_project_ids.append(project_id)

        # 测试按名称搜索
        name_search_result = await db_transaction.fetch(
            "SELECT id, name FROM projects WHERE name ILIKE $1",
            "%data%"
        )
        
        print(f"✅ 名称搜索测试: 找到 {len(name_search_result)} 个匹配项目")

        # 测试按状态过滤
        active_projects = await db_transaction.fetch(
            "SELECT id, name, status FROM projects WHERE status = 'active' AND owner_id = $1",
            sample_user_in_db['id']
        )
        
        archived_projects = await db_transaction.fetch(
            "SELECT id, name, status FROM projects WHERE status = 'archived' AND owner_id = $1",
            sample_user_in_db['id']
        )
        
        print(f"✅ 状态过滤:")
        print(f"   活跃项目: {len(active_projects)}")
        print(f"   归档项目: {len(archived_projects)}")

        # 测试按可见性过滤
        public_projects = await db_transaction.fetch(
            "SELECT id, name, visibility FROM projects WHERE visibility = 'public'"
        )
        
        private_projects = await db_transaction.fetch(
            "SELECT id, name, visibility FROM projects WHERE visibility = 'private' AND owner_id = $1",
            sample_user_in_db['id']
        )
        
        print(f"✅ 可见性过滤:")
        print(f"   公开项目: {len(public_projects)}")
        print(f"   私有项目: {len(private_projects)}")

        # 测试标签搜索（如果支持数组操作）
        try:
            tag_search_result = await db_transaction.fetch(
                "SELECT id, name, tags FROM projects WHERE 'ai' = ANY(tags)"
            )
            print(f"✅ 标签搜索: 找到 {len(tag_search_result)} 个包含'ai'标签的项目")
        except Exception:
            print("⚠️  标签搜索功能不可用（可能不支持数组操作）")

        # 测试复合搜索
        complex_search = await db_transaction.fetch(
            """
            SELECT id, name, status, visibility, created_at
            FROM projects 
            WHERE owner_id = $1
            AND status = 'active'
            AND visibility IN ('public', 'private')
            AND created_at > NOW() - INTERVAL '1 year'
            ORDER BY created_at DESC
            """,
            sample_user_in_db['id']
        )
        
        print(f"✅ 复合搜索: 符合条件的项目 {len(complex_search)} 个")

    @pytest.mark.asyncio
    async def test_project_permissions_validation(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试项目权限验证"""
        # 检查project_members表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_members')"
        )
        
        if not table_exists:
            pytest.skip("project_members表不存在")

        # 测试不同角色的权限配置
        role_permissions = [
            {
                'role': 'viewer',
                'permissions': {
                    'read': True,
                    'write': False,
                    'admin': False,
                    'delete': False
                }
            },
            {
                'role': 'editor',
                'permissions': {
                    'read': True,
                    'write': True,
                    'admin': False,
                    'delete': False
                }
            },
            {
                'role': 'admin',
                'permissions': {
                    'read': True,
                    'write': True,
                    'admin': True,
                    'delete': True
                }
            }
        ]
        
        # 创建测试用户
        test_users = []
        for i, role_perm in enumerate(role_permissions):
            user_id = await db_transaction.fetchval(
                """
                INSERT INTO users (email, username, password_hash, is_active, is_verified)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                f'role_test_{i}@example.com', f'role_test_user_{i}',
                'dummy_hash', True, True
            )
            test_users.append(user_id)
        
        # 为每个用户分配不同的角色和权限
        member_ids = []
        for i, (user_id, role_perm) in enumerate(zip(test_users, role_permissions)):
            member_id = await db_transaction.fetchval(
                """
                INSERT INTO project_members 
                (project_id, user_id, role, permissions, invited_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                sample_project_in_db['id'], user_id, role_perm['role'],
                json.dumps(role_perm['permissions']), sample_user_in_db['id']
            )
            member_ids.append(member_id)
        
        print(f"✅ 创建 {len(member_ids)} 个不同权限的项目成员")

        # 验证权限查询
        for role_perm in role_permissions:
            members_with_role = await db_transaction.fetch(
                """
                SELECT pm.*, u.username 
                FROM project_members pm
                JOIN users u ON pm.user_id = u.id
                WHERE pm.project_id = $1 AND pm.role = $2
                """,
                sample_project_in_db['id'], role_perm['role']
            )
            
            print(f"   {role_perm['role']} 角色成员: {len(members_with_role)} 个")

        # 测试权限查询（查找具有特定权限的成员）
        admin_members = await db_transaction.fetch(
            """
            SELECT pm.*, u.username 
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = $1 
            AND pm.permissions->>'admin' = 'true'
            """,
            sample_project_in_db['id']
        )
        
        write_members = await db_transaction.fetch(
            """
            SELECT pm.*, u.username 
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = $1 
            AND pm.permissions->>'write' = 'true'
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 权限验证:")
        print(f"   具有管理权限的成员: {len(admin_members)}")
        print(f"   具有写入权限的成员: {len(write_members)}")

    @pytest.mark.asyncio
    async def test_project_data_validation(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试项目数据验证和约束"""
        # 检查projects表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not table_exists:
            pytest.skip("projects表不存在")

        # 测试项目slug格式验证
        invalid_slugs = ['Invalid Slug', 'invalid_slug!', 'invalid.slug', '']
        valid_slugs = ['valid-slug', 'another-valid-slug-123', 'slug123']
        
        slug_validation_results = {'invalid_rejected': 0, 'valid_accepted': 0}
        
        # 测试无效slug
        for invalid_slug in invalid_slugs:
            try:
                await db_transaction.execute(
                    """
                    INSERT INTO projects (name, slug, owner_id)
                    VALUES ($1, $2, $3)
                    """,
                    f'Test Project {invalid_slug}', invalid_slug, sample_user_in_db['id']
                )
                print(f"⚠️  无效slug被接受: {invalid_slug}")
            except Exception:
                slug_validation_results['invalid_rejected'] += 1

        # 测试有效slug
        for i, valid_slug in enumerate(valid_slugs):
            try:
                project_id = await db_transaction.fetchval(
                    """
                    INSERT INTO projects (name, slug, owner_id)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    f'Test Project {i}', valid_slug, sample_user_in_db['id']
                )
                if project_id:
                    slug_validation_results['valid_accepted'] += 1
            except Exception as e:
                print(f"⚠️  有效slug被拒绝: {valid_slug} - {e}")

        # 测试项目状态验证
        valid_statuses = ['active', 'inactive', 'archived']
        invalid_statuses = ['pending', 'deleted', 'unknown']
        
        status_validation_results = {'invalid_rejected': 0, 'valid_accepted': 0}
        
        for invalid_status in invalid_statuses:
            try:
                await db_transaction.execute(
                    """
                    INSERT INTO projects (name, slug, owner_id, status)
                    VALUES ($1, $2, $3, $4)
                    """,
                    'Status Test Project', f'status-test-{invalid_status}',
                    sample_user_in_db['id'], invalid_status
                )
                print(f"⚠️  无效状态被接受: {invalid_status}")
            except Exception:
                status_validation_results['invalid_rejected'] += 1

        for valid_status in valid_statuses:
            try:
                project_id = await db_transaction.fetchval(
                    """
                    INSERT INTO projects (name, slug, owner_id, status)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    'Status Test Project', f'status-test-{valid_status}',
                    sample_user_in_db['id'], valid_status
                )
                if project_id:
                    status_validation_results['valid_accepted'] += 1
            except Exception as e:
                print(f"⚠️  有效状态被拒绝: {valid_status} - {e}")

        print(f"✅ 数据验证测试:")
        print(f"   Slug验证 - 无效拒绝: {slug_validation_results['invalid_rejected']}/{len(invalid_slugs)}, 有效接受: {slug_validation_results['valid_accepted']}/{len(valid_slugs)}")
        print(f"   状态验证 - 无效拒绝: {status_validation_results['invalid_rejected']}/{len(invalid_statuses)}, 有效接受: {status_validation_results['valid_accepted']}/{len(valid_statuses)}")

        # 验证唯一约束
        duplicate_slug = 'duplicate-test-slug'
        
        # 创建第一个项目
        first_project_id = await db_transaction.fetchval(
            """
            INSERT INTO projects (name, slug, owner_id)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            'First Project', duplicate_slug, sample_user_in_db['id']
        )
        
        # 尝试创建具有相同slug的项目
        duplicate_rejected = False
        try:
            await db_transaction.execute(
                """
                INSERT INTO projects (name, slug, owner_id)
                VALUES ($1, $2, $3)
                """,
                'Second Project', duplicate_slug, sample_user_in_db['id']
            )
            print("❌ 重复slug被接受")
        except Exception:
            duplicate_rejected = True
            print("✅ 重复slug被正确拒绝")
        
        assert duplicate_rejected, "slug唯一约束未生效"