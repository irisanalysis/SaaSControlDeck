#!/usr/bin/env python3
"""
应用数据库迁移脚本
用于将数据源扩展迁移应用到开发数据库
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


async def apply_migrations():
    """应用数据库迁移"""
    settings = get_settings()

    try:
        # 连接数据库
        await Database.connect(settings.DATABASE_URL)
        logger.info("数据库连接成功")

        # 读取迁移SQL文件
        migration_file = current_dir / "scripts" / "migrations" / "001_add_data_source_extensions.sql"

        if not migration_file.exists():
            logger.error("迁移文件不存在", file_path=str(migration_file))
            return False

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        logger.info("开始应用数据库迁移", migration_file=str(migration_file))

        # 分割SQL语句并逐个执行
        sql_statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

        success_count = 0
        for i, statement in enumerate(sql_statements):
            try:
                if statement.strip():
                    await Database.execute(statement)
                    success_count += 1
                    logger.info(f"SQL语句 {i+1} 执行成功")
            except Exception as e:
                logger.error(f"SQL语句 {i+1} 执行失败", statement=statement[:100], error=str(e))
                # 继续执行其他语句，某些语句可能因为已存在而失败

        logger.info("数据库迁移完成", success_count=success_count, total_count=len(sql_statements))

        # 验证表是否创建成功
        await verify_tables()

        return True

    except Exception as e:
        logger.error("应用迁移失败", error=str(e), exc_info=True)
        return False
    finally:
        await Database.disconnect()


async def verify_tables():
    """验证表是否正确创建"""
    logger.info("验证表结构...")

    # 检查表是否存在
    tables_to_check = [
        "datasets",
        "dataset_columns",
        "upload_sessions",
        "data_quality_checks"
    ]

    for table_name in tables_to_check:
        try:
            result = await Database.fetch_val(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = $1",
                table_name
            )
            if result > 0:
                logger.info(f"表 {table_name} 存在")

                # 检查表的列
                columns = await Database.fetch_all(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                    """,
                    table_name
                )
                logger.info(f"表 {table_name} 有 {len(columns)} 列")
            else:
                logger.warning(f"表 {table_name} 不存在")
        except Exception as e:
            logger.error(f"检查表 {table_name} 失败", error=str(e))


async def main():
    """主函数"""
    logger.info("开始数据库迁移")

    success = await apply_migrations()

    if success:
        logger.info("数据库迁移成功完成")
        sys.exit(0)
    else:
        logger.error("数据库迁移失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())