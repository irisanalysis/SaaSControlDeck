#!/usr/bin/env python3
"""
直接SQL执行脚本
尝试绕过权限问题直接创建必要的表结构
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# 数据库连接信息
DATABASE_URL = "postgresql://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

async def test_and_create_tables():
    """测试连接并尝试创建表"""
    try:
        # 建立连接
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ 数据库连接成功")

        # 测试当前用户权限
        try:
            result = await conn.fetchval("SELECT current_user, current_database()")
            print(f"当前用户: {result}")

            # 检查表创建权限
            await conn.execute("CREATE TABLE IF NOT EXISTS test_permissions (id SERIAL PRIMARY KEY)")
            print("✅ 具有表创建权限")

            # 删除测试表
            await conn.execute("DROP TABLE IF EXISTS test_permissions")

        except Exception as e:
            print(f"❌ 权限测试失败: {e}")
            return False

        # 尝试创建基础表结构
        print("开始创建基础表结构...")

        # 首先创建扩展
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
            print("✅ 扩展创建成功")
        except Exception as e:
            print(f"⚠️ 扩展创建失败（可能已存在）: {e}")

        # 创建基础表 - users
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("✅ users表创建成功")

        # 创建projects表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
                settings JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ projects表创建成功")

        # 创建datasets表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id BIGSERIAL PRIMARY KEY,
                project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                file_path VARCHAR(500),
                file_size BIGINT,
                file_type VARCHAR(50),
                schema_info JSONB,
                upload_status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                processed_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("✅ datasets表创建成功")

        # 创建数据源扩展字段
        try:
            await conn.execute("""
                ALTER TABLE datasets
                ADD COLUMN IF NOT EXISTS type VARCHAR(50) NOT NULL DEFAULT 'csv' CHECK (type IN ('csv', 'json', 'excel', 'parquet')),
                ADD COLUMN IF NOT EXISTS rows_count INTEGER,
                ADD COLUMN IF NOT EXISTS columns_count INTEGER,
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'uploading'
                    CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
                ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64),
                ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
                ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
                ADD COLUMN IF NOT EXISTS encoding VARCHAR(50) DEFAULT 'utf-8',
                ADD COLUMN IF NOT EXISTS delimiter VARCHAR(10),
                ADD COLUMN IF NOT EXISTS has_header BOOLEAN DEFAULT true,
                ADD COLUMN IF NOT EXISTS preview_data JSONB,
                ADD COLUMN IF NOT EXISTS error_details TEXT,
                ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITH TIME ZONE
            """)
            print("✅ datasets表扩展字段添加成功")
        except Exception as e:
            print(f"⚠️ datasets表扩展字段添加失败: {e}")

        # 创建upload_sessions表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_size BIGINT NOT NULL,
                uploaded_size BIGINT DEFAULT 0,
                chunk_size INTEGER DEFAULT 1048576,
                total_chunks INTEGER NOT NULL,
                uploaded_chunks INTEGER DEFAULT 0,
                status VARCHAR(50) NOT NULL DEFAULT 'uploading'
                    CHECK (status IN ('uploading', 'processing', 'completed', 'failed', 'cancelled')),
                dataset_id BIGINT REFERENCES datasets(id) ON DELETE SET NULL,
                temp_file_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '24 hours'
            )
        """)
        print("✅ upload_sessions表创建成功")

        # 创建dataset_columns表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dataset_columns (
                id BIGSERIAL PRIMARY KEY,
                dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
                column_name VARCHAR(255) NOT NULL,
                column_index INTEGER NOT NULL,
                data_type VARCHAR(50) NOT NULL,
                is_nullable BOOLEAN DEFAULT true,
                unique_count INTEGER DEFAULT 0,
                missing_count INTEGER DEFAULT 0,
                min_value TEXT,
                max_value TEXT,
                avg_value NUMERIC,
                std_value NUMERIC,
                sample_values TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ dataset_columns表创建成功")

        # 创建data_quality_checks表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_checks (
                id BIGSERIAL PRIMARY KEY,
                dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
                check_type VARCHAR(100) NOT NULL,
                column_name VARCHAR(255),
                severity VARCHAR(20) NOT NULL DEFAULT 'info'
                    CHECK (severity IN ('info', 'warning', 'error', 'critical')),
                message TEXT NOT NULL,
                details JSONB DEFAULT '{}',
                affected_rows INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ data_quality_checks表创建成功")

        # 创建索引
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_upload_sessions_user_id ON upload_sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_upload_sessions_status ON upload_sessions(status)")
        print("✅ 索引创建成功")

        # 插入示例数据
        await conn.execute("""
            INSERT INTO users (email, password_hash, email_verified, is_active)
            VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdeXhR8Qn/C9U/G', true, true)
            ON CONFLICT (email) DO NOTHING
        """)

        # 插入示例项目
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = 'admin@example.com'")
        if user_id:
            await conn.execute("""
                INSERT INTO projects (user_id, name, description, status)
                VALUES ($1, 'Demo Project', '示例项目用于测试', 'active')
                ON CONFLICT DO NOTHING
            """, user_id)
            print("✅ 示例数据插入成功")

        # 验证表创建
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        print(f"\n✅ 数据库初始化完成! 创建了 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table['table_name']}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始数据库初始化...")
    success = asyncio.run(test_and_create_tables())
    if success:
        print("\n✅ 数据库初始化成功!")
        sys.exit(0)
    else:
        print("\n❌ 数据库初始化失败!")
        sys.exit(1)