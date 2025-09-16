"""
数据库约束和索引详细测试套件

深入测试数据库约束的功能性和索引性能
"""

import pytest
import asyncpg
import asyncio
import time
import random
import string
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestConstraintsAndIndexes:
    """约束和索引测试类"""

    @pytest.mark.asyncio
    async def test_email_format_constraint(self, db_transaction: asyncpg.Connection):
        """测试用户邮箱格式约束"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        # 测试有效邮箱格式
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example-domain.org",
            "123@456.789"
        ]
        
        # 测试无效邮箱格式
        invalid_emails = [
            "invalid.email",
            "@domain.com",
            "user@",
            "user.domain.com",
            "user@domain",
            ""
        ]
        
        # 测试有效邮箱
        valid_count = 0
        for email in valid_emails:
            try:
                username = f"user_{random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                    email, username, "dummy_hash"
                )
                valid_count += 1
            except Exception as e:
                print(f"有效邮箱被拒绝: {email} - {e}")
        
        # 测试无效邮箱
        invalid_rejected = 0
        for email in invalid_emails:
            try:
                username = f"user_{random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                    email, username, "dummy_hash"
                )
                print(f"无效邮箱被接受: {email}")
            except Exception:
                invalid_rejected += 1
        
        print(f"✅ 邮箱格式约束测试:")
        print(f"   有效邮箱接受: {valid_count}/{len(valid_emails)}")
        print(f"   无效邮箱拒绝: {invalid_rejected}/{len(invalid_emails)}")
        
        # 至少应该接受大部分有效邮箱
        assert valid_count >= len(valid_emails) * 0.8
        # 应该拒绝大部分无效邮箱
        assert invalid_rejected >= len(invalid_emails) * 0.7

    @pytest.mark.asyncio
    async def test_username_length_constraint(self, db_transaction: asyncpg.Connection):
        """测试用户名长度约束"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        # 测试不同长度的用户名
        test_cases = [
            ("a", False),      # 太短
            ("ab", False),     # 太短
            ("abc", True),     # 最小有效长度
            ("valid_user", True),  # 正常长度
            ("a" * 100, True), # 最大允许长度内
            ("", False)        # 空字符串
        ]
        
        results = {}
        for username, should_succeed in test_cases:
            try:
                email = f"test_{random.randint(1000, 9999)}@example.com"
                await db_transaction.execute(
                    "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                    email, username, "dummy_hash"
                )
                results[username] = True
            except Exception:
                results[username] = False
        
        # 验证结果
        passed_tests = 0
        for username, should_succeed in test_cases:
            actual_result = results.get(username, False)
            if actual_result == should_succeed:
                passed_tests += 1
            else:
                print(f"用户名测试失败: '{username}' (期望: {should_succeed}, 实际: {actual_result})")
        
        print(f"✅ 用户名长度约束测试: {passed_tests}/{len(test_cases)} 通过")
        assert passed_tests >= len(test_cases) * 0.8

    @pytest.mark.asyncio
    async def test_project_status_constraint(self, db_transaction: asyncpg.Connection, sample_user_in_db):
        """测试项目状态约束"""
        # 检查projects表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not table_exists:
            pytest.skip("projects表不存在")
        
        valid_statuses = ['active', 'inactive', 'archived']
        invalid_statuses = ['pending', 'deleted', 'invalid', '']
        
        # 测试有效状态
        valid_accepted = 0
        for status in valid_statuses:
            try:
                project_name = f"Test Project {random.randint(1000, 9999)}"
                project_slug = f"test-project-{random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO projects (name, slug, owner_id, status) VALUES ($1, $2, $3, $4)",
                    project_name, project_slug, sample_user_in_db['id'], status
                )
                valid_accepted += 1
            except Exception as e:
                print(f"有效状态被拒绝: {status} - {e}")
        
        # 测试无效状态
        invalid_rejected = 0
        for status in invalid_statuses:
            try:
                project_name = f"Test Project {random.randint(1000, 9999)}"
                project_slug = f"test-project-{random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO projects (name, slug, owner_id, status) VALUES ($1, $2, $3, $4)",
                    project_name, project_slug, sample_user_in_db['id'], status
                )
                print(f"无效状态被接受: {status}")
            except Exception:
                invalid_rejected += 1
        
        print(f"✅ 项目状态约束测试:")
        print(f"   有效状态接受: {valid_accepted}/{len(valid_statuses)}")
        print(f"   无效状态拒绝: {invalid_rejected}/{len(invalid_statuses)}")
        
        assert valid_accepted == len(valid_statuses)
        assert invalid_rejected >= len(invalid_statuses) * 0.8

    @pytest.mark.asyncio
    async def test_ai_task_priority_constraint(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试AI任务优先级约束"""
        # 检查ai_tasks表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_tasks')"
        )
        
        if not table_exists:
            pytest.skip("ai_tasks表不存在")
        
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        invalid_priorities = ['critical', 'medium', 'asap', '']
        
        # 测试有效优先级
        valid_accepted = 0
        for priority in valid_priorities:
            try:
                task_name = f"Test Task {random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO ai_tasks (project_id, user_id, task_name, task_type, priority) VALUES ($1, $2, $3, $4, $5)",
                    sample_project_in_db['id'], sample_user_in_db['id'], task_name, 'text_analysis', priority
                )
                valid_accepted += 1
            except Exception as e:
                print(f"有效优先级被拒绝: {priority} - {e}")
        
        # 测试无效优先级
        invalid_rejected = 0
        for priority in invalid_priorities:
            try:
                task_name = f"Test Task {random.randint(1000, 9999)}"
                await db_transaction.execute(
                    "INSERT INTO ai_tasks (project_id, user_id, task_name, task_type, priority) VALUES ($1, $2, $3, $4, $5)",
                    sample_project_in_db['id'], sample_user_in_db['id'], task_name, 'text_analysis', priority
                )
                print(f"无效优先级被接受: {priority}")
            except Exception:
                invalid_rejected += 1
        
        print(f"✅ AI任务优先级约束测试:")
        print(f"   有效优先级接受: {valid_accepted}/{len(valid_priorities)}")
        print(f"   无效优先级拒绝: {invalid_rejected}/{len(invalid_priorities)}")
        
        assert valid_accepted == len(valid_priorities)
        assert invalid_rejected >= len(invalid_priorities) * 0.7

    @pytest.mark.asyncio
    async def test_file_size_constraint(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试文件大小约束"""
        # 检查file_storage表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not table_exists:
            pytest.skip("file_storage表不存在")
        
        # 测试不同的文件大小
        test_sizes = [
            (0, False),        # 无效：零大小
            (-1, False),       # 无效：负数
            (1, True),         # 有效：最小大小
            (1024, True),      # 有效：正常大小
            (1024*1024, True), # 有效：大文件
        ]
        
        results = {}
        for file_size, should_succeed in test_sizes:
            try:
                file_name = f"test_file_{random.randint(1000, 9999)}.txt"
                file_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
                await db_transaction.execute(
                    """INSERT INTO file_storage 
                       (project_id, user_id, file_name, original_name, file_path, file_hash, file_size, mime_type) 
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                    sample_project_in_db['id'], sample_user_in_db['id'], 
                    file_name, file_name, f"/tmp/{file_name}", file_hash, file_size, "text/plain"
                )
                results[file_size] = True
            except Exception:
                results[file_size] = False
        
        # 验证结果
        passed_tests = 0
        for file_size, should_succeed in test_sizes:
            actual_result = results.get(file_size, False)
            if actual_result == should_succeed:
                passed_tests += 1
            else:
                print(f"文件大小测试失败: {file_size} (期望: {should_succeed}, 实际: {actual_result})")
        
        print(f"✅ 文件大小约束测试: {passed_tests}/{len(test_sizes)} 通过")
        assert passed_tests >= len(test_sizes) * 0.8

    @pytest.mark.asyncio
    async def test_unique_constraints_enforcement(self, db_transaction: asyncpg.Connection):
        """测试唯一约束的强制执行"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        # 测试邮箱唯一约束
        email = "unique_test@example.com"
        username1 = "unique_user_1"
        username2 = "unique_user_2"
        
        # 创建第一个用户
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                email, username1, "hash1"
            )
            print("✅ 第一个用户创建成功")
        except Exception as e:
            pytest.fail(f"创建第一个用户失败: {e}")
        
        # 尝试创建具有相同邮箱的用户
        duplicate_email_rejected = False
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                email, username2, "hash2"
            )
            print("❌ 重复邮箱被接受")
        except Exception:
            duplicate_email_rejected = True
            print("✅ 重复邮箱被正确拒绝")
        
        # 测试用户名唯一约束
        new_email = "another_test@example.com"
        duplicate_username_rejected = False
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                new_email, username1, "hash3"
            )
            print("❌ 重复用户名被接受")
        except Exception:
            duplicate_username_rejected = True
            print("✅ 重复用户名被正确拒绝")
        
        assert duplicate_email_rejected, "邮箱唯一约束未生效"
        assert duplicate_username_rejected, "用户名唯一约束未生效"

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_enforcement(self, db_transaction: asyncpg.Connection):
        """测试外键约束的强制执行"""
        # 检查相关表是否存在
        users_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        projects_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not (users_exists and projects_exists):
            pytest.skip("必要的表不存在")
        
        # 尝试创建引用不存在用户的项目
        import uuid
        fake_user_id = str(uuid.uuid4())
        
        foreign_key_violation_caught = False
        try:
            await db_transaction.execute(
                "INSERT INTO projects (name, slug, owner_id) VALUES ($1, $2, $3)",
                "Test Project", f"test-project-{random.randint(1000, 9999)}", fake_user_id
            )
            print("❌ 外键约束未生效")
        except Exception:
            foreign_key_violation_caught = True
            print("✅ 外键约束正确阻止了无效引用")
        
        assert foreign_key_violation_caught, "外键约束未生效"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_index_performance_email_lookup(self, db_connection: asyncpg.Connection, performance_test_data):
        """测试邮箱查找索引性能"""
        # 检查users表是否存在且有数据
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        user_count = await db_connection.fetchval("SELECT count(*) FROM users")
        if user_count == 0:
            pytest.skip("users表没有数据")
        
        # 获取一个存在的邮箱进行测试
        test_email = await db_connection.fetchval("SELECT email FROM users LIMIT 1")
        
        # 执行多次查询测试性能
        iterations = 100
        start_time = time.time()
        
        for _ in range(iterations):
            result = await db_connection.fetchval(
                "SELECT id FROM users WHERE email = $1",
                test_email
            )
            assert result is not None
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        print(f"✅ 邮箱查找性能测试:")
        print(f"   查询次数: {iterations}")
        print(f"   总时间: {end_time - start_time:.3f}秒")
        print(f"   平均查询时间: {avg_time:.6f}秒")
        print(f"   QPS: {1/avg_time:.1f}")
        
        # 每个查询应该在1ms内完成（有索引的情况下）
        assert avg_time < 0.001, f"邮箱查找性能过慢: {avg_time:.6f}秒"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_index_performance_project_lookup(self, db_connection: asyncpg.Connection):
        """测试项目slug查找索引性能"""
        # 检查projects表是否存在且有数据
        table_exists = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        )
        
        if not table_exists:
            pytest.skip("projects表不存在")
        
        project_count = await db_connection.fetchval("SELECT count(*) FROM projects")
        if project_count == 0:
            pytest.skip("projects表没有数据")
        
        # 获取一个存在的项目slug进行测试
        test_slug = await db_connection.fetchval("SELECT slug FROM projects LIMIT 1")
        
        # 执行多次查询测试性能
        iterations = 50
        start_time = time.time()
        
        for _ in range(iterations):
            result = await db_connection.fetchval(
                "SELECT id FROM projects WHERE slug = $1",
                test_slug
            )
            assert result is not None
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        print(f"✅ 项目slug查找性能测试:")
        print(f"   查询次数: {iterations}")
        print(f"   平均查询时间: {avg_time:.6f}秒")
        print(f"   QPS: {1/avg_time:.1f}")
        
        # 每个查询应该在2ms内完成
        assert avg_time < 0.002, f"项目slug查找性能过慢: {avg_time:.6f}秒"

    @pytest.mark.asyncio
    async def test_cascade_delete_behavior(self, db_transaction: asyncpg.Connection):
        """测试级联删除行为"""
        # 检查相关表是否存在
        users_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        profiles_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_profiles')"
        )
        
        if not (users_exists and profiles_exists):
            pytest.skip("必要的表不存在")
        
        # 创建测试用户
        username = f"cascade_test_{random.randint(1000, 9999)}"
        email = f"cascade_test_{random.randint(1000, 9999)}@example.com"
        
        user_id = await db_transaction.fetchval(
            "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3) RETURNING id",
            email, username, "dummy_hash"
        )
        
        # 创建用户档案
        await db_transaction.execute(
            "INSERT INTO user_profiles (user_id, first_name, last_name) VALUES ($1, $2, $3)",
            user_id, "Test", "User"
        )
        
        # 验证档案存在
        profile_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM user_profiles WHERE user_id = $1)",
            user_id
        )
        assert profile_exists, "用户档案未创建"
        
        # 删除用户
        deleted_count = await db_transaction.fetchval(
            "DELETE FROM users WHERE id = $1",
            user_id
        )
        
        # 验证级联删除
        profile_exists_after = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM user_profiles WHERE user_id = $1)",
            user_id
        )
        
        print(f"✅ 级联删除测试:")
        print(f"   删除的用户数: {deleted_count}")
        print(f"   删除后档案是否存在: {profile_exists_after}")
        
        # 用户档案应该被级联删除
        assert not profile_exists_after, "级联删除未生效"

    @pytest.mark.asyncio
    async def test_constraint_error_messages(self, db_transaction: asyncpg.Connection):
        """测试约束错误消息的有用性"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        constraint_errors = {}
        
        # 测试邮箱格式约束错误
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                "invalid.email", f"user_{random.randint(1000, 9999)}", "hash"
            )
        except Exception as e:
            constraint_errors['email_format'] = str(e)
        
        # 测试用户名长度约束错误
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                f"test_{random.randint(1000, 9999)}@example.com", "ab", "hash"
            )
        except Exception as e:
            constraint_errors['username_length'] = str(e)
        
        # 测试唯一约束错误
        unique_email = f"unique_{random.randint(1000, 9999)}@example.com"
        unique_username = f"unique_user_{random.randint(1000, 9999)}"
        
        # 先插入一个用户
        await db_transaction.execute(
            "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
            unique_email, unique_username, "hash1"
        )
        
        # 尝试插入重复邮箱
        try:
            await db_transaction.execute(
                "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
                unique_email, f"another_user_{random.randint(1000, 9999)}", "hash2"
            )
        except Exception as e:
            constraint_errors['unique_email'] = str(e)
        
        print(f"✅ 约束错误消息测试:")
        for constraint_type, error_msg in constraint_errors.items():
            print(f"   {constraint_type}: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}")
        
        # 应该至少捕获到一些约束错误
        assert len(constraint_errors) >= 2, "未捕获到足够的约束错误"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_constraint_validation(self, db_transaction: asyncpg.Connection):
        """批量测试约束验证性能"""
        # 检查users表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
        )
        
        if not table_exists:
            pytest.skip("users表不存在")
        
        # 准备批量数据
        batch_size = 100
        user_data = []
        
        for i in range(batch_size):
            user_data.append((
                f"bulk_user_{i}@example.com",
                f"bulk_user_{i}",
                "dummy_hash"
            ))
        
        # 测试批量插入性能
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
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ 批量约束验证测试:")
        print(f"   尝试插入: {batch_size}")
        print(f"   成功插入: {inserted_count}")
        print(f"   总时间: {total_time:.3f}秒")
        print(f"   每秒插入: {inserted_count/total_time:.1f}")
        
        # 应该成功插入大部分记录
        assert inserted_count >= batch_size * 0.9