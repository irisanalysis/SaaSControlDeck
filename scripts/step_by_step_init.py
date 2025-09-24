#!/usr/bin/env python3
"""
逐步执行数据库初始化，提供详细的错误信息
"""

import asyncio
import asyncpg
import sys
import os

async def init_database_step_by_step():
    """逐步初始化数据库"""

    # 从环境变量读取凭据
    admin_user = os.getenv('ADMIN_USER')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_user or not admin_password:
        print("❌ 错误：需要设置ADMIN_USER和ADMIN_PASSWORD环境变量")
        return False

    database_url = f"postgresql://{admin_user}:{admin_password}@47.79.87.199:5432/saascontrol_dev_pro1"

    try:
        conn = await asyncpg.connect(database_url)
        print("✅ 超级管理员连接成功")

        # 第一步：创建扩展
        print("\n📦 第一步：创建PostgreSQL扩展...")
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
            print("✅ 扩展创建成功")
        except Exception as e:
            print(f"⚠️ 扩展创建失败（可能已存在）: {e}")

        # 第二步：创建基础表
        print("\n🏗️ 第二步：创建基础表结构...")

        # users表
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

        # user_profiles表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                avatar_url VARCHAR(500),
                timezone VARCHAR(50) DEFAULT 'UTC',
                language VARCHAR(10) DEFAULT 'en',
                preferences JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ user_profiles表创建成功")

        # projects表
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

        # datasets表（基础结构）
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
        print("✅ datasets表基础结构创建成功")

        # 第三步：扩展datasets表
        print("\n🔧 第三步：扩展datasets表字段...")
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
            print(f"⚠️ datasets表扩展失败: {e}")

        # 第四步：创建数据管理相关表
        print("\n📊 第四步：创建数据管理相关表...")

        # dataset_columns表
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

        # upload_sessions表
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

        # data_quality_checks表
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

        # 第五步：创建索引
        print("\n⚡ 第五步：创建性能索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status)",
            "CREATE INDEX IF NOT EXISTS idx_upload_sessions_user_id ON upload_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_upload_sessions_status ON upload_sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_dataset_columns_dataset_id ON dataset_columns(dataset_id)",
            "CREATE INDEX IF NOT EXISTS idx_data_quality_checks_dataset_id ON data_quality_checks(dataset_id)"
        ]

        for index_sql in indexes:
            await conn.execute(index_sql)
        print(f"✅ {len(indexes)}个索引创建成功")

        # 第六步：创建触发器函数
        print("\n🔧 第六步：创建触发器函数...")
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)

        # 应用触发器
        triggers = [
            "CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
            "CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
            "CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
            "CREATE TRIGGER update_upload_sessions_updated_at BEFORE UPDATE ON upload_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
        ]

        for trigger_sql in triggers:
            try:
                await conn.execute(trigger_sql)
            except Exception as e:
                print(f"⚠️ 触发器可能已存在: {e}")

        print("✅ 触发器创建成功")

        # 第七步：插入示例数据
        print("\n📝 第七步：插入示例数据...")
        await conn.execute("""
            INSERT INTO users (email, password_hash, email_verified, is_active)
            VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdeXhR8Qn/C9U/G', true, true)
            ON CONFLICT (email) DO NOTHING
        """)

        # 获取用户ID并创建项目
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = 'admin@example.com'")
        if user_id:
            await conn.execute("""
                INSERT INTO user_profiles (user_id, first_name, last_name)
                VALUES ($1, 'Admin', 'User')
                ON CONFLICT DO NOTHING
            """, user_id)

            await conn.execute("""
                INSERT INTO projects (user_id, name, description, status)
                VALUES ($1, 'Demo Project', '示例项目用于测试数据管理功能', 'active')
                ON CONFLICT DO NOTHING
            """, user_id)

        print("✅ 示例数据插入成功")

        # 第八步：权限设置
        print("\n🔐 第八步：为开发用户设置权限...")
        try:
            await conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO saascontrol_dev_user")
            await conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO saascontrol_dev_user")
            await conn.execute("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO saascontrol_dev_user")
            print("✅ 开发用户权限授予成功")
        except Exception as e:
            print(f"⚠️ 权限授予失败: {e}")

        # 验证最终结果
        print("\n🎯 验证数据库初始化结果...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        project_count = await conn.fetchval("SELECT COUNT(*) FROM projects")

        print(f"\n🎉 数据库初始化完成!")
        print(f"✅ 成功创建 {len(tables)} 个表:")
        for table in tables:
            print(f"   📋 {table['table_name']}")

        print(f"\n📊 数据验证:")
        print(f"   👤 用户数量: {user_count}")
        print(f"   📁 项目数量: {project_count}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始逐步数据库初始化...")
    success = asyncio.run(init_database_step_by_step())
    if success:
        print("\n🎉 数据库初始化完全成功!")
        print("📋 下一步：重启Data Service测试数据管理功能")
        sys.exit(0)
    else:
        print("\n❌ 数据库初始化失败!")
        sys.exit(1)