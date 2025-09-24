#!/usr/bin/env python3
"""
应用基础数据库表结构脚本
先创建基础表，再应用扩展迁移
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "shared"))

from shared.config import get_settings
from shared.database import Database
import structlog

logger = structlog.get_logger()


async def apply_base_schema():
    """应用基础数据库表结构"""
    settings = get_settings()

    try:
        # 连接数据库
        await Database.connect(settings.DATABASE_URL)
        logger.info("数据库连接成功")

        # 读取基础初始化SQL文件
        init_file = current_dir / "scripts" / "init-db.sql"

        if not init_file.exists():
            logger.error("初始化文件不存在", file_path=str(init_file))
            return False

        with open(init_file, 'r', encoding='utf-8') as f:
            init_sql = f.read()

        logger.info("开始应用基础数据库表结构", init_file=str(init_file))

        # 执行完整的SQL
        try:
            await Database.execute(init_sql)
            logger.info("基础数据库表结构创建成功")
        except Exception as e:
            logger.error("基础表结构创建失败", error=str(e))
            return False

        # 验证基础表是否创建成功
        await verify_base_tables()

        return True

    except Exception as e:
        logger.error("应用基础表结构失败", error=str(e), exc_info=True)
        return False
    finally:
        await Database.disconnect()


async def verify_base_tables():
    """验证基础表是否正确创建"""
    logger.info("验证基础表结构...")

    # 检查基础表是否存在
    base_tables = [
        "users",
        "user_profiles",
        "projects",
        "datasets",
        "analysis_tasks"
    ]

    for table_name in base_tables:
        try:
            result = await Database.fetch_val(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = $1",
                table_name
            )
            if result > 0:
                logger.info(f"基础表 {table_name} 存在")
            else:
                logger.warning(f"基础表 {table_name} 不存在")
        except Exception as e:
            logger.error(f"检查基础表 {table_name} 失败", error=str(e))


async def main():
    """主函数"""
    logger.info("开始应用基础数据库表结构")

    success = await apply_base_schema()

    if success:
        logger.info("基础数据库表结构应用成功")
        sys.exit(0)
    else:
        logger.error("基础数据库表结构应用失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())