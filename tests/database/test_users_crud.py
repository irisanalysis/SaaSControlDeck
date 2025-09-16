"""
用户模块CRUD操作测试套件

测试用户管理相关表的完整CRUD操作
"""

import pytest
import asyncpg
import json
import uuid
from typing import Dict, Any
from datetime import datetime, timezone, timedelta


class TestUsersCRUD:
    """用户CRUD操作测试类"""

    @pytest.mark.asyncio
    async def test_users_table_crud(self, db_transaction: asyncpg.Connection):
        """测试users表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # CREATE - 创建用户
        user_data = {
            'email': 'crud_test@example.com',
            'username': 'crud_test_user',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeMLq8.0cLqqRAZ3e',
            'is_active': True,
            'is_verified': False
        }
        
        user_id = await db_transaction.fetchval(
            """
            INSERT INTO users (email, username, password_hash, is_active, is_verified)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_data['email'], user_data['username'], user_data['password_hash'],
            user_data['is_active'], user_data['is_verified']
        )
        
        assert user_id is not None
        print(f"✅ 创建用户成功: {user_id}")

        # READ - 查询用户
        created_user = await db_transaction.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        assert created_user is not None
        assert created_user['email'] == user_data['email']
        assert created_user['username'] == user_data['username']
        assert created_user['is_active'] == user_data['is_active']
        assert created_user['created_at'] is not None
        assert created_user['updated_at'] is not None
        print("✅ 查询用户成功")

        # UPDATE - 更新用户
        update_data = {
            'is_verified': True,
            'email_verified_at': datetime.now(timezone.utc),
            'last_login_at': datetime.now(timezone.utc)
        }
        
        updated_rows = await db_transaction.execute(
            """
            UPDATE users 
            SET is_verified = $1, email_verified_at = $2, last_login_at = $3
            WHERE id = $4
            """,
            update_data['is_verified'], update_data['email_verified_at'], 
            update_data['last_login_at'], user_id
        )
        
        # 验证更新
        updated_user = await db_transaction.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        assert updated_user['is_verified'] == update_data['is_verified']
        assert updated_user['email_verified_at'] is not None
        assert updated_user['last_login_at'] is not None
        assert updated_user['updated_at'] > created_user['updated_at']
        print("✅ 更新用户成功")

        # DELETE - 删除用户
        deleted_rows = await db_transaction.execute(
            "DELETE FROM users WHERE id = $1",
            user_id
        )
        
        # 验证删除
        deleted_user = await db_transaction.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        assert deleted_user is None
        print("✅ 删除用户成功")

    @pytest.mark.asyncio
    async def test_user_profiles_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试user_profiles表的CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_profiles')"
        )
        
        if not table_exists:
            pytest.skip("user_profiles表不存在")

        # CREATE - 创建用户档案
        profile_data = {
            'user_id': sample_user_in_db['id'],
            'first_name': 'John',
            'last_name': 'Doe',
            'display_name': 'Johnny',
            'bio': 'Software developer with 5 years of experience',
            'phone': '+1234567890',
            'timezone': 'America/New_York',
            'language': 'en',
            'theme_preference': 'dark',
            'notification_preferences': {
                'email_notifications': True,
                'push_notifications': False,
                'marketing_emails': False,
                'security_alerts': True
            }
        }
        
        profile_id = await db_transaction.fetchval(
            """
            INSERT INTO user_profiles 
            (user_id, first_name, last_name, display_name, bio, phone, timezone, language, theme_preference, notification_preferences)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            profile_data['user_id'], profile_data['first_name'], profile_data['last_name'],
            profile_data['display_name'], profile_data['bio'], profile_data['phone'],
            profile_data['timezone'], profile_data['language'], profile_data['theme_preference'],
            json.dumps(profile_data['notification_preferences'])
        )
        
        assert profile_id is not None
        print(f"✅ 创建用户档案成功: {profile_id}")

        # READ - 查询用户档案
        created_profile = await db_transaction.fetchrow(
            "SELECT * FROM user_profiles WHERE id = $1",
            profile_id
        )
        
        assert created_profile is not None
        assert created_profile['user_id'] == profile_data['user_id']
        assert created_profile['first_name'] == profile_data['first_name']
        assert created_profile['display_name'] == profile_data['display_name']
        assert created_profile['timezone'] == profile_data['timezone']
        print("✅ 查询用户档案成功")

        # UPDATE - 更新用户档案
        update_data = {
            'display_name': 'John D.',
            'bio': 'Senior Software Developer',
            'theme_preference': 'light'
        }
        
        await db_transaction.execute(
            """
            UPDATE user_profiles 
            SET display_name = $1, bio = $2, theme_preference = $3
            WHERE id = $4
            """,
            update_data['display_name'], update_data['bio'],
            update_data['theme_preference'], profile_id
        )
        
        # 验证更新
        updated_profile = await db_transaction.fetchrow(
            "SELECT * FROM user_profiles WHERE id = $1",
            profile_id
        )
        
        assert updated_profile['display_name'] == update_data['display_name']
        assert updated_profile['bio'] == update_data['bio']
        assert updated_profile['theme_preference'] == update_data['theme_preference']
        print("✅ 更新用户档案成功")

        # DELETE - 删除用户档案
        await db_transaction.execute(
            "DELETE FROM user_profiles WHERE id = $1",
            profile_id
        )
        
        # 验证删除
        deleted_profile = await db_transaction.fetchrow(
            "SELECT * FROM user_profiles WHERE id = $1",
            profile_id
        )
        
        assert deleted_profile is None
        print("✅ 删除用户档案成功")

    @pytest.mark.asyncio
    async def test_user_sessions_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试user_sessions表的CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_sessions')"
        )
        
        if not table_exists:
            pytest.skip("user_sessions表不存在")

        # CREATE - 创建用户会话
        session_data = {
            'user_id': sample_user_in_db['id'],
            'session_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token',
            'refresh_token': 'refresh_token_12345',
            'device_id': 'device_12345',
            'device_name': 'iPhone 14 Pro',
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=24),
            'refresh_expires_at': datetime.now(timezone.utc) + timedelta(days=7),
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
            'location': {
                'country': 'US',
                'city': 'New York',
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            'is_active': True
        }
        
        session_id = await db_transaction.fetchval(
            """
            INSERT INTO user_sessions 
            (user_id, session_token, refresh_token, device_id, device_name, expires_at, 
             refresh_expires_at, ip_address, user_agent, location, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            session_data['user_id'], session_data['session_token'], session_data['refresh_token'],
            session_data['device_id'], session_data['device_name'], session_data['expires_at'],
            session_data['refresh_expires_at'], session_data['ip_address'], session_data['user_agent'],
            json.dumps(session_data['location']), session_data['is_active']
        )
        
        assert session_id is not None
        print(f"✅ 创建用户会话成功: {session_id}")

        # READ - 查询用户会话
        created_session = await db_transaction.fetchrow(
            "SELECT * FROM user_sessions WHERE id = $1",
            session_id
        )
        
        assert created_session is not None
        assert created_session['user_id'] == session_data['user_id']
        assert created_session['session_token'] == session_data['session_token']
        assert created_session['device_name'] == session_data['device_name']
        assert created_session['is_active'] == session_data['is_active']
        print("✅ 查询用户会话成功")

        # UPDATE - 更新会话（最后访问时间）
        new_last_accessed = datetime.now(timezone.utc)
        
        await db_transaction.execute(
            """
            UPDATE user_sessions 
            SET last_accessed_at = $1
            WHERE id = $2
            """,
            new_last_accessed, session_id
        )
        
        # 验证更新
        updated_session = await db_transaction.fetchrow(
            "SELECT * FROM user_sessions WHERE id = $1",
            session_id
        )
        
        assert updated_session['last_accessed_at'] is not None
        print("✅ 更新用户会话成功")

        # UPDATE - 使会话无效
        await db_transaction.execute(
            "UPDATE user_sessions SET is_active = false WHERE id = $1",
            session_id
        )
        
        # 验证状态更新
        deactivated_session = await db_transaction.fetchrow(
            "SELECT is_active FROM user_sessions WHERE id = $1",
            session_id
        )
        
        assert not deactivated_session['is_active']
        print("✅ 会话无效化成功")

        # DELETE - 删除会话
        await db_transaction.execute(
            "DELETE FROM user_sessions WHERE id = $1",
            session_id
        )
        
        # 验证删除
        deleted_session = await db_transaction.fetchrow(
            "SELECT * FROM user_sessions WHERE id = $1",
            session_id
        )
        
        assert deleted_session is None
        print("✅ 删除用户会话成功")

    @pytest.mark.asyncio
    async def test_user_relationship_integrity(self, db_transaction: asyncpg.Connection):
        """测试用户相关表之间的关系完整性"""
        # 检查所有相关表是否存在
        tables_to_check = ['users', 'user_profiles', 'user_sessions']
        existing_tables = []
        
        for table in tables_to_check:
            exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                existing_tables.append(table)
        
        if len(existing_tables) < 2:
            pytest.skip("缺少必要的表进行关系测试")

        # 创建主用户
        user_id = await db_transaction.fetchval(
            """
            INSERT INTO users (email, username, password_hash, is_active, is_verified)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            'relationship_test@example.com', 'relationship_user',
            'dummy_hash', True, False
        )
        
        profile_id = None
        session_id = None
        
        # 创建用户档案（如果表存在）
        if 'user_profiles' in existing_tables:
            profile_id = await db_transaction.fetchval(
                """
                INSERT INTO user_profiles (user_id, first_name, last_name)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_id, 'Test', 'User'
            )
            print("✅ 创建关联用户档案成功")

        # 创建用户会话（如果表存在）
        if 'user_sessions' in existing_tables:
            session_id = await db_transaction.fetchval(
                """
                INSERT INTO user_sessions 
                (user_id, session_token, expires_at)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_id, 'test_token_123',
                datetime.now(timezone.utc) + timedelta(hours=1)
            )
            print("✅ 创建关联用户会话成功")

        # 验证关系存在
        if profile_id:
            profile_exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM user_profiles WHERE user_id = $1)",
                user_id
            )
            assert profile_exists, "用户档案关系未建立"

        if session_id:
            session_exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM user_sessions WHERE user_id = $1)",
                user_id
            )
            assert session_exists, "用户会话关系未建立"

        # 测试级联删除
        delete_result = await db_transaction.execute(
            "DELETE FROM users WHERE id = $1",
            user_id
        )
        
        # 验证级联删除效果
        if profile_id:
            profile_after_delete = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM user_profiles WHERE user_id = $1)",
                user_id
            )
            assert not profile_after_delete, "用户档案未被级联删除"
            print("✅ 用户档案级联删除成功")

        if session_id:
            session_after_delete = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM user_sessions WHERE user_id = $1)",
                user_id
            )
            assert not session_after_delete, "用户会话未被级联删除"
            print("✅ 用户会话级联删除成功")

    @pytest.mark.asyncio
    async def test_user_data_validation(self, db_transaction: asyncpg.Connection):
        """测试用户数据验证和边界条件"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 测试邮箱格式验证
        invalid_emails = ['invalid', '@domain.com', 'user@', 'user.domain']
        valid_email_rejected = 0
        
        for invalid_email in invalid_emails:
            try:
                await db_transaction.execute(
                    """
                    INSERT INTO users (email, username, password_hash)
                    VALUES ($1, $2, $3)
                    """,
                    invalid_email, f'user_{invalid_email.replace("@", "_").replace(".", "_")}', 'hash'
                )
                print(f"⚠️  无效邮箱被接受: {invalid_email}")
            except Exception:
                valid_email_rejected += 1

        # 测试用户名长度验证
        username_tests = [
            ('ab', False),    # 太短
            ('abc', True),    # 最小长度
            ('a' * 100, True),  # 长用户名
        ]
        
        username_validation_passed = 0
        for username, should_pass in username_tests:
            try:
                email = f'test_{len(username)}_{username[:5]}@example.com'
                await db_transaction.execute(
                    """
                    INSERT INTO users (email, username, password_hash)
                    VALUES ($1, $2, $3)
                    """,
                    email, username, 'hash'
                )
                if should_pass:
                    username_validation_passed += 1
                else:
                    print(f"⚠️  无效用户名被接受: {username}")
            except Exception:
                if not should_pass:
                    username_validation_passed += 1

        print(f"✅ 数据验证测试:")
        print(f"   无效邮箱拒绝率: {valid_email_rejected}/{len(invalid_emails)}")
        print(f"   用户名验证通过: {username_validation_passed}/{len(username_tests)}")

    @pytest.mark.asyncio
    async def test_user_search_and_filtering(self, db_transaction: asyncpg.Connection, performance_test_data):
        """测试用户搜索和过滤功能"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 检查是否有测试数据
        user_count = await db_transaction.fetchval("SELECT count(*) FROM users")
        if user_count == 0:
            pytest.skip("没有用户数据进行搜索测试")

        # 测试邮箱搜索
        email_search_result = await db_transaction.fetch(
            "SELECT id, email FROM users WHERE email LIKE $1 LIMIT 5",
            "%@%"
        )
        
        assert len(email_search_result) > 0, "邮箱搜索未返回结果"
        print(f"✅ 邮箱搜索测试: 找到 {len(email_search_result)} 个用户")

        # 测试活跃用户过滤
        active_users = await db_transaction.fetch(
            "SELECT id, username FROM users WHERE is_active = true LIMIT 10"
        )
        
        inactive_users = await db_transaction.fetch(
            "SELECT id, username FROM users WHERE is_active = false LIMIT 10"
        )
        
        print(f"✅ 用户状态过滤:")
        print(f"   活跃用户: {len(active_users)}")
        print(f"   非活跃用户: {len(inactive_users)}")

        # 测试日期范围查询
        recent_users = await db_transaction.fetch(
            """
            SELECT id, username, created_at 
            FROM users 
            WHERE created_at > NOW() - INTERVAL '1 year'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        
        print(f"✅ 日期范围查询: 过去一年注册的用户 {len(recent_users)} 个")

        # 测试复合查询
        complex_search = await db_transaction.fetch(
            """
            SELECT id, email, username, is_active, created_at
            FROM users 
            WHERE is_active = true 
            AND email LIKE $1
            AND created_at > NOW() - INTERVAL '2 years'
            ORDER BY created_at DESC
            LIMIT 10
            """,
            "%@example.com"
        )
        
        print(f"✅ 复合查询测试: 符合条件的用户 {len(complex_search)} 个")

    @pytest.mark.asyncio
    async def test_user_batch_operations(self, db_transaction: asyncpg.Connection):
        """测试用户批量操作"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")

        # 准备批量用户数据
        batch_users = []
        for i in range(10):
            batch_users.append({
                'email': f'batch_user_{i}@example.com',
                'username': f'batch_user_{i}',
                'password_hash': 'batch_hash',
                'is_active': i % 2 == 0  # 交替活跃状态
            })

        # 批量插入用户
        inserted_ids = []
        for user_data in batch_users:
            try:
                user_id = await db_transaction.fetchval(
                    """
                    INSERT INTO users (email, username, password_hash, is_active)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    user_data['email'], user_data['username'],
                    user_data['password_hash'], user_data['is_active']
                )
                inserted_ids.append(user_id)
            except Exception as e:
                print(f"批量插入失败: {user_data['email']} - {e}")

        print(f"✅ 批量插入成功: {len(inserted_ids)}/{len(batch_users)} 个用户")

        # 批量更新操作
        if inserted_ids:
            # 批量激活所有用户
            updated_count = 0
            for user_id in inserted_ids:
                try:
                    result = await db_transaction.execute(
                        "UPDATE users SET is_active = true WHERE id = $1",
                        user_id
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"批量更新失败: {user_id} - {e}")

            print(f"✅ 批量更新成功: {updated_count} 个用户")

            # 批量删除操作
            deleted_count = 0
            for user_id in inserted_ids:
                try:
                    await db_transaction.execute(
                        "DELETE FROM users WHERE id = $1",
                        user_id
                    )
                    deleted_count += 1
                except Exception as e:
                    print(f"批量删除失败: {user_id} - {e}")

            print(f"✅ 批量删除成功: {deleted_count} 个用户")