#!/usr/bin/env python3
"""
数据源API测试脚本
用于验证数据上传、预览等API功能
"""

import asyncio
import json
import sys
from pathlib import Path
from io import StringIO

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "shared"))

from shared.config import get_settings
from shared.database import Database
import structlog

logger = structlog.get_logger()


async def test_database_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")

    settings = get_settings()

    try:
        await Database.connect(settings.DATABASE_URL)
        logger.info("数据库连接成功")

        # 测试简单查询
        result = await Database.fetch_val("SELECT 1")
        assert result == 1, "数据库查询结果错误"

        logger.info("数据库连接测试通过")
        return True

    except Exception as e:
        logger.error("数据库连接测试失败", error=str(e))
        return False
    finally:
        await Database.disconnect()


async def test_data_models():
    """测试数据模型"""
    logger.info("测试数据模型...")

    try:
        # 导入模型
        from shared.models.data_source import (
            DataSource, DataSourceCreate, UploadSession, ColumnInfo,
            DataSourceType, DataSourceStatus
        )

        # 测试模型创建
        data_source_create = DataSourceCreate(
            name="测试数据集",
            type=DataSourceType.CSV,
            project_id=1
        )

        column_info = ColumnInfo(
            column_name="test_column",
            column_index=0,
            data_type="string",
            unique_count=100,
            missing_count=5
        )

        logger.info("数据模型测试通过")
        return True

    except Exception as e:
        logger.error("数据模型测试失败", error=str(e))
        return False


async def create_test_data():
    """创建测试数据"""
    logger.info("创建测试数据...")

    try:
        settings = get_settings()
        await Database.connect(settings.DATABASE_URL)

        # 确保有测试用户和项目
        user_query = """
        SELECT id FROM users WHERE email = 'admin@example.com'
        """
        user = await Database.fetch_one(user_query)

        if not user:
            logger.error("未找到测试用户")
            return False

        user_id = user['id']

        # 确保有测试项目
        project_query = """
        SELECT id FROM projects WHERE user_id = $1 LIMIT 1
        """
        project = await Database.fetch_one(project_query, user_id)

        if not project:
            # 创建测试项目
            project_insert = """
            INSERT INTO projects (user_id, name, description, status)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """
            project = await Database.fetch_one(
                project_insert, user_id, "测试项目", "用于API测试", "active"
            )

        project_id = project['id']

        logger.info("测试数据创建完成", user_id=user_id, project_id=project_id)
        return {"user_id": user_id, "project_id": project_id}

    except Exception as e:
        logger.error("创建测试数据失败", error=str(e))
        return False
    finally:
        await Database.disconnect()


def create_test_csv_file(file_path: Path):
    """创建测试CSV文件"""
    csv_content = """id,name,email,age,city,salary
1,张三,zhangsan@example.com,25,北京,8000
2,李四,lisi@example.com,30,上海,12000
3,王五,wangwu@example.com,28,广州,10000
4,赵六,zhaoliu@example.com,35,深圳,15000
5,钱七,qianqi@example.com,22,杭州,7000
6,孙八,sunba@example.com,40,成都,13000
7,周九,zhoujiu@example.com,33,武汉,11000
8,吴十,wushi@example.com,27,西安,9000
9,郑十一,,29,重庆,9500
10,王十二,wangshier@example.com,31,南京,14000"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    logger.info("测试CSV文件创建完成", file_path=str(file_path))


def create_test_json_file(file_path: Path):
    """创建测试JSON文件"""
    json_data = [
        {"id": 1, "name": "产品A", "category": "电子", "price": 999.99, "stock": 50},
        {"id": 2, "name": "产品B", "category": "服装", "price": 199.99, "stock": 100},
        {"id": 3, "name": "产品C", "category": "食品", "price": 29.99, "stock": 200},
        {"id": 4, "name": "产品D", "category": "电子", "price": 1299.99, "stock": 30},
        {"id": 5, "name": "产品E", "category": "服装", "price": 89.99, "stock": 150}
    ]

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    logger.info("测试JSON文件创建完成", file_path=str(file_path))


async def test_file_processing():
    """测试文件处理功能"""
    logger.info("测试文件处理功能...")

    try:
        # 导入文件处理函数
        from data_service.app.routers.data_preview import (
            load_dataframe_from_file, get_column_statistics, detect_data_type
        )

        # 创建测试文件
        test_dir = Path("/tmp/test_data")
        test_dir.mkdir(exist_ok=True)

        csv_file = test_dir / "test.csv"
        json_file = test_dir / "test.json"

        create_test_csv_file(csv_file)
        create_test_json_file(json_file)

        # 测试CSV文件加载
        df_csv = load_dataframe_from_file(str(csv_file), 'csv')
        logger.info("CSV文件加载成功", rows=len(df_csv), columns=len(df_csv.columns))

        # 测试JSON文件加载
        df_json = load_dataframe_from_file(str(json_file), 'json')
        logger.info("JSON文件加载成功", rows=len(df_json), columns=len(df_json.columns))

        # 测试列统计
        for i, column in enumerate(df_csv.columns):
            col_stats = get_column_statistics(df_csv[column], column, i)
            logger.info("列统计完成", column=column, data_type=col_stats.data_type)

        # 清理测试文件
        csv_file.unlink()
        json_file.unlink()
        test_dir.rmdir()

        logger.info("文件处理功能测试通过")
        return True

    except Exception as e:
        logger.error("文件处理功能测试失败", error=str(e))
        return False


async def main():
    """主测试函数"""
    logger.info("开始API功能测试")

    tests = [
        ("数据库连接测试", test_database_connection),
        ("数据模型测试", test_data_models),
        ("创建测试数据", create_test_data),
        ("文件处理功能测试", test_file_processing),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"执行测试: {test_name}")
        try:
            result = await test_func()
            if result:
                logger.info(f"✓ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"✗ {test_name} 失败")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} 异常", error=str(e))
            failed += 1

    logger.info("测试完成", passed=passed, failed=failed, total=len(tests))

    if failed == 0:
        logger.info("🎉 所有测试通过!")
        sys.exit(0)
    else:
        logger.error(f"❌ {failed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())