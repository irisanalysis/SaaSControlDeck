#!/usr/bin/env python3
"""
数据库权限检查和表创建脚本
检查表的所有者并尝试创建扩展
"""

import asyncio
import sys
import os

# 添加shared模块到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.database import Database

DATABASE_URL = "postgresql://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

async def check_table_permissions():
    """检查表权限和所有者"""
    db = Database()

    try:
        await db.connect(DATABASE_URL)
        print("✅ 数据库连接成功")

        # 检查表的所有者
        owner_query = """
            SELECT schemaname, tablename, tableowner
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('datasets', 'users', 'projects')
            ORDER BY tablename
        """

        tables = await db.fetch_all(owner_query)

        print("📊 表所有者信息:")
        for table in tables:
            print(f"   📋 {table['tablename']}: 所有者 = {table['tableowner']}")

        # 检查当前用户权限
        user_query = "SELECT current_user"
        current_user = await db.fetch_val(user_query)
        print(f"🔑 当前数据库用户: {current_user}")

        # 检查表是否存在以及列信息
        columns_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'datasets'
            ORDER BY ordinal_position
        """

        columns = await db.fetch_all(columns_query)
        print(f"📄 datasets表当前列信息 ({len(columns)} 列):")
        for col in columns:
            print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_table_permissions())