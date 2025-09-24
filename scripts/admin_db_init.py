#!/usr/bin/env python3
"""
使用超级管理员权限初始化数据库
安全地使用提供的凭据而不暴露密码
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

async def init_database_with_admin():
    """使用超级管理员权限初始化数据库"""

    # 使用环境变量传递的凭据（不在代码中硬编码）
    import os

    # 从环境变量读取凭据
    admin_user = os.getenv('ADMIN_USER')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_user or not admin_password:
        print("❌ 错误：需要设置ADMIN_USER和ADMIN_PASSWORD环境变量")
        return False

    # 构建连接URL
    database_url = f"postgresql://{admin_user}:{admin_password}@47.79.87.199:5432/saascontrol_dev_pro1"

    try:
        # 建立管理员连接
        conn = await asyncpg.connect(database_url)
        print("✅ 超级管理员连接成功")

        # 读取完整的初始化SQL文件
        sql_file = Path('/home/user/studio/COMPLETE_DATABASE_INIT.sql')

        if not sql_file.exists():
            print("❌ SQL初始化文件不存在")
            return False

        with open(sql_file, 'r', encoding='utf-8') as f:
            init_sql = f.read()

        print("📖 开始执行完整数据库初始化...")

        # 执行完整的SQL脚本
        await conn.execute(init_sql)
        print("✅ 数据库初始化SQL执行成功")

        # 验证表创建
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        print(f"\n🎉 数据库初始化完成! 成功创建了 {len(tables)} 个表:")
        for table in tables:
            print(f"  ✅ {table['table_name']}")

        # 为开发用户授予权限
        print("\n🔐 为开发用户授予权限...")
        try:
            await conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO saascontrol_dev_user")
            await conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO saascontrol_dev_user")
            await conn.execute("GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO saascontrol_dev_user")
            print("✅ 开发用户权限授予成功")
        except Exception as e:
            print(f"⚠️ 权限授予部分失败（可能用户不存在）: {e}")

        # 验证示例数据
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        project_count = await conn.fetchval("SELECT COUNT(*) FROM projects")

        print(f"\n📊 数据验证:")
        print(f"  👤 用户数量: {user_count}")
        print(f"  📁 项目数量: {project_count}")

        await conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始超级管理员数据库初始化...")
    success = asyncio.run(init_database_with_admin())
    if success:
        print("\n🎉 数据库初始化完全成功!")
        print("📋 下一步：重启Data Service以应用新的数据库结构")
        sys.exit(0)
    else:
        print("\n❌ 数据库初始化失败!")
        sys.exit(1)