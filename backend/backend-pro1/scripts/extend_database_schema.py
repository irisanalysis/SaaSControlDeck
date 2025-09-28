#!/usr/bin/env python3
"""
SaaS Control Deck - 数据库架构扩展脚本
扩展现有的datasets表并创建新的关联表，支持完整的数据分析功能
RELEVANT FILES: init_database.py, unified_backend_fastapi.py, shared/database.py
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加shared模块到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import Database

# 数据库配置
DATABASE_URL = "postgresql://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

class DatabaseSchemaExtender:
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

    async def extend_datasets_table(self):
        """扩展datasets表，添加新的分析字段"""
        try:
            print("🔧 扩展datasets表架构...")

            # 检查是否已经扩展过
            check_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'datasets'
                AND column_name IN ('description', 'tags', 'last_accessed', 'access_count', 'quality_score', 'ai_insights')
            """
            existing_columns = await self.db.fetch_all(check_query)
            existing_column_names = [col['column_name'] for col in existing_columns]

            # 添加新字段（如果不存在）
            extensions = [
                ("description", "ALTER TABLE datasets ADD COLUMN description TEXT"),
                ("tags", "ALTER TABLE datasets ADD COLUMN tags JSONB DEFAULT '[]'"),
                ("last_accessed", "ALTER TABLE datasets ADD COLUMN last_accessed TIMESTAMP DEFAULT NOW()"),
                ("access_count", "ALTER TABLE datasets ADD COLUMN access_count INTEGER DEFAULT 0"),
                ("quality_score", "ALTER TABLE datasets ADD COLUMN quality_score FLOAT DEFAULT 0.0"),
                ("ai_insights", "ALTER TABLE datasets ADD COLUMN ai_insights JSONB DEFAULT '{}'")
            ]

            for column_name, alter_sql in extensions:
                if column_name not in existing_column_names:
                    await self.db.execute(alter_sql)
                    print(f"   ✅ 添加字段: {column_name}")
                else:
                    print(f"   ⚠️  字段已存在: {column_name}")

            print("✅ datasets表扩展完成")

        except Exception as e:
            print(f"❌ 扩展datasets表失败: {e}")
            raise

    async def create_dataset_columns_table(self):
        """创建列信息详表"""
        try:
            print("🔧 创建dataset_columns表...")

            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_columns (
                    id BIGSERIAL PRIMARY KEY,
                    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
                    column_name VARCHAR(255) NOT NULL,
                    column_index INTEGER NOT NULL,
                    data_type VARCHAR(50) NOT NULL,
                    is_nullable BOOLEAN DEFAULT false,
                    unique_count INTEGER DEFAULT 0,
                    null_count INTEGER DEFAULT 0,
                    min_value TEXT,
                    max_value TEXT,
                    avg_value FLOAT,
                    std_value FLOAT,
                    sample_values JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(dataset_id, column_name)
                );
            """)

            # 创建索引
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_dataset_columns_dataset_id ON dataset_columns(dataset_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_dataset_columns_data_type ON dataset_columns(data_type);")

            print("✅ dataset_columns表创建完成")

        except Exception as e:
            print(f"❌ 创建dataset_columns表失败: {e}")
            raise

    async def create_data_quality_checks_table(self):
        """创建数据质量检查表"""
        try:
            print("🔧 创建data_quality_checks表...")

            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_checks (
                    id BIGSERIAL PRIMARY KEY,
                    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
                    check_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
                    message TEXT NOT NULL,
                    details JSONB DEFAULT '{}',
                    affected_rows INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # 创建索引
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_data_quality_checks_dataset_id ON data_quality_checks(dataset_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_data_quality_checks_severity ON data_quality_checks(severity);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_data_quality_checks_check_type ON data_quality_checks(check_type);")

            print("✅ data_quality_checks表创建完成")

        except Exception as e:
            print(f"❌ 创建data_quality_checks表失败: {e}")
            raise

    async def create_dataset_analysis_cache_table(self):
        """创建数据分析缓存表"""
        try:
            print("🔧 创建dataset_analysis_cache表...")

            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_analysis_cache (
                    id BIGSERIAL PRIMARY KEY,
                    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
                    analysis_type VARCHAR(50) NOT NULL,
                    analysis_params JSONB DEFAULT '{}',
                    analysis_result JSONB NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(dataset_id, analysis_type, analysis_params)
                );
            """)

            # 创建索引
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_cache_dataset_id ON dataset_analysis_cache(dataset_id);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_cache_type ON dataset_analysis_cache(analysis_type);")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires ON dataset_analysis_cache(expires_at);")

            print("✅ dataset_analysis_cache表创建完成")

        except Exception as e:
            print(f"❌ 创建dataset_analysis_cache表失败: {e}")
            raise

    async def verify_extended_schema(self):
        """验证扩展的数据库架构"""
        try:
            print("🔍 验证扩展的数据库架构...")

            # 检查所有新表和字段是否存在
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name IN ('datasets', 'dataset_columns', 'data_quality_checks', 'dataset_analysis_cache')
                ORDER BY table_name
            """

            tables = await self.db.fetch_all(tables_query)
            table_names = [table['table_name'] for table in tables]

            print(f"📊 数据库表统计:")
            for table_name in table_names:
                count = await self.db.fetch_val(f"SELECT COUNT(*) FROM {table_name}")
                print(f"   📋 {table_name}: {count} 记录")

            # 验证datasets表的扩展字段
            datasets_columns_query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'datasets'
                AND column_name IN ('description', 'tags', 'last_accessed', 'access_count', 'quality_score', 'ai_insights')
                ORDER BY column_name
            """

            datasets_columns = await self.db.fetch_all(datasets_columns_query)

            print(f"📊 datasets表扩展字段:")
            for col in datasets_columns:
                print(f"   📄 {col['column_name']}: {col['data_type']}")

            return len(table_names) >= 4 and len(datasets_columns) >= 6

        except Exception as e:
            print(f"❌ 验证数据库架构失败: {e}")
            return False

    async def run_schema_extension(self):
        """运行完整的数据库架构扩展过程"""
        print("🚀 开始数据库架构扩展")
        print("="*60)

        try:
            # 连接数据库
            if not await self.connect():
                return False

            # 扩展datasets表
            await self.extend_datasets_table()

            # 创建新的关联表
            await self.create_dataset_columns_table()
            await self.create_data_quality_checks_table()
            await self.create_dataset_analysis_cache_table()

            # 验证扩展结果
            success = await self.verify_extended_schema()

            if success:
                print("="*60)
                print("🎉 数据库架构扩展完成!")
                print("")
                print("✅ 新增功能:")
                print("   📊 数据集详细描述和标签")
                print("   📈 列级别统计分析")
                print("   🔍 数据质量检查")
                print("   💾 分析结果缓存")
                print("")
                print("💡 下一步:")
                print("   启动扩展的后端服务测试新API端点")
                print("")
            else:
                print("❌ 数据库架构扩展验证失败")

            return success

        except Exception as e:
            print(f"❌ 数据库架构扩展失败: {e}")
            return False
        finally:
            await self.db.disconnect()

async def main():
    """主函数"""
    extender = DatabaseSchemaExtender()
    success = await extender.run_schema_extension()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())