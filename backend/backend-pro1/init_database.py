#!/usr/bin/env python3
"""
SaaS Control Deck - 数据库初始化脚本
自动执行数据库架构创建和基础数据设置
专为数据持久化功能升级设计
"""

import asyncio
import sys
import os
from datetime import datetime
import asyncpg

# 添加shared模块到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared.database import Database

# 数据库配置
DATABASE_URL = "postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

class DatabaseInitializer:
    def __init__(self):
        self.db = Database()

    async def connect(self):
        """连接数据库"""
        try:
            await self.db.connect(DATABASE_URL)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    async def check_tables_exist(self) -> bool:
        """检查必要的表是否存在"""
        try:
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name IN ('users', 'user_profiles', 'projects', 'datasets')
            """

            tables = await self.db.fetch_all(tables_query)
            table_names = [table['table_name'] for table in tables]

            required_tables = ['users', 'user_profiles', 'projects', 'datasets']
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                print(f"⚠️  缺少表: {', '.join(missing_tables)}")
                return False
            else:
                print(f"✅ 所有必要的表都存在: {', '.join(table_names)}")
                return True

        except Exception as e:
            print(f"❌ 检查表结构失败: {e}")
            return False

    async def create_basic_schema(self):
        """创建基础数据库架构"""
        try:
            print("🔧 创建基础数据库架构...")

            # 创建用户表
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email_verified BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login_at TIMESTAMP WITH TIME ZONE
                );
            """)

            # 创建用户配置表
            await self.db.execute("""
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
                );
            """)

            # 创建项目表
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # 创建数据集表（核心表）
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id BIGSERIAL PRIMARY KEY,
                    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    file_path VARCHAR(500),
                    file_size BIGINT,
                    file_type VARCHAR(50),
                    type VARCHAR(50) NOT NULL DEFAULT 'csv' CHECK (type IN ('csv', 'json', 'excel', 'parquet')),
                    rows_count INTEGER,
                    columns_count INTEGER,
                    status VARCHAR(50) NOT NULL DEFAULT 'uploading'
                        CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
                    metadata JSONB DEFAULT '{}',
                    file_hash VARCHAR(64),
                    original_filename VARCHAR(255),
                    mime_type VARCHAR(100),
                    encoding VARCHAR(50) DEFAULT 'utf-8',
                    delimiter VARCHAR(10),
                    has_header BOOLEAN DEFAULT true,
                    preview_data JSONB,
                    error_details TEXT,
                    processing_started_at TIMESTAMP WITH TIME ZONE,
                    processing_completed_at TIMESTAMP WITH TIME ZONE,
                    schema_info JSONB,
                    upload_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processed_at TIMESTAMP WITH TIME ZONE
                );
            """)

            print("✅ 基础表创建完成")

            # 创建索引
            print("🔧 创建数据库索引...")

            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(type);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_datasets_file_hash ON datasets(file_hash);")

            print("✅ 索引创建完成")

        except Exception as e:
            print(f"❌ 创建数据库架构失败: {e}")
            raise

    async def create_test_user(self):
        """创建测试用户"""
        try:
            print("👤 创建测试用户...")

            # 检查用户是否已存在
            existing_user = await self.db.fetch_one(
                "SELECT id FROM users WHERE email = $1",
                "test@saascontrol.dev"
            )

            if existing_user:
                print("✅ 测试用户已存在")
                return existing_user['id']

            # 创建测试用户（密码哈希已预计算）
            user_row = await self.db.fetch_one("""
                INSERT INTO users (
                    email, password_hash, email_verified, is_active, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
            "test@saascontrol.dev",
            "47e4db34d59b2bcc4b4d6b2e86ccba95f4bb8e11c1a1e8bb4e2b2b74b8e11c1a",  # TestPass123的哈希
            True,
            True,
            datetime.now()
            )

            user_id = user_row['id']

            # 创建用户配置
            await self.db.execute("""
                INSERT INTO user_profiles (
                    user_id, first_name, last_name, created_at
                ) VALUES ($1, $2, $3, $4)
            """,
            user_id,
            "测试",
            "用户",
            datetime.now()
            )

            print(f"✅ 测试用户创建成功，ID: {user_id}")
            return user_id

        except Exception as e:
            print(f"❌ 创建测试用户失败: {e}")
            raise

    async def create_default_project(self, user_id: int):
        """为用户创建默认项目"""
        try:
            print("📁 创建默认项目...")

            # 检查是否已有项目
            existing_project = await self.db.fetch_one(
                "SELECT id FROM projects WHERE user_id = $1",
                user_id
            )

            if existing_project:
                print("✅ 默认项目已存在")
                return existing_project['id']

            # 创建默认项目
            project_row = await self.db.fetch_one("""
                INSERT INTO projects (
                    user_id, name, description, status, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
            user_id,
            "默认项目",
            "系统自动创建的默认项目，用于数据源管理",
            "active",
            datetime.now()
            )

            project_id = project_row['id']
            print(f"✅ 默认项目创建成功，ID: {project_id}")
            return project_id

        except Exception as e:
            print(f"❌ 创建默认项目失败: {e}")
            raise

    async def verify_setup(self):
        """验证数据库设置"""
        try:
            print("🔍 验证数据库设置...")

            # 统计各表的记录数
            users_count = await self.db.fetch_val("SELECT COUNT(*) FROM users")
            projects_count = await self.db.fetch_val("SELECT COUNT(*) FROM projects")
            datasets_count = await self.db.fetch_val("SELECT COUNT(*) FROM datasets")

            print(f"📊 数据库统计:")
            print(f"   👥 用户数: {users_count}")
            print(f"   📁 项目数: {projects_count}")
            print(f"   📊 数据集数: {datasets_count}")

            # 验证测试用户可以登录
            test_user = await self.db.fetch_one("""
                SELECT u.id, u.email, p.first_name, p.last_name
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.email = $1
            """, "test@saascontrol.dev")

            if test_user:
                print(f"✅ 测试用户验证成功: {test_user['first_name']} {test_user['last_name']} ({test_user['email']})")
            else:
                print("❌ 测试用户验证失败")

            return True

        except Exception as e:
            print(f"❌ 验证数据库设置失败: {e}")
            return False

    async def run_initialization(self):
        """运行完整的数据库初始化过程"""
        print("🚀 开始数据库初始化")
        print("="*50)

        try:
            # 连接数据库
            if not await self.connect():
                return False

            # 检查表是否存在
            tables_exist = await self.check_tables_exist()

            if not tables_exist:
                # 创建基础架构
                await self.create_basic_schema()

            # 创建测试用户和项目
            user_id = await self.create_test_user()
            await self.create_default_project(user_id)

            # 验证设置
            await self.verify_setup()

            print("="*50)
            print("🎉 数据库初始化完成!")
            print("")
            print("💡 现在可以启动后端服务:")
            print("   cd /home/user/studio/backend/backend-pro1")
            print("   source .venv/bin/activate")
            print("   uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0")
            print("")
            print("🧪 测试数据库功能:")
            print("   ./quick_test.sh")

            return True

        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
        finally:
            await self.db.disconnect()

async def main():
    """主函数"""
    initializer = DatabaseInitializer()
    success = await initializer.run_initialization()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())