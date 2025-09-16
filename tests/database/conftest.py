"""
pytest配置文件和数据库测试fixtures

提供数据库连接、测试数据生成和清理功能
"""

import asyncio
import pytest
import asyncpg
import os
import logging
from typing import Dict, Any, AsyncGenerator, List
from datetime import datetime, timezone
from . import TEST_ENVIRONMENTS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take several seconds)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "firebase_studio: marks tests specific to Firebase Studio environment"
    )


def pytest_collection_modifyitems(config, items):
    """自动为测试添加标记"""
    for item in items:
        # 性能测试标记
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)
        
        # 集成测试标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Firebase Studio测试标记
        if "firebase_studio" in item.nodeid:
            item.add_marker(pytest.mark.firebase_studio)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_environment() -> str:
    """获取测试环境"""
    env = os.getenv("TEST_DB_ENVIRONMENT", "dev_pro1")
    if env not in TEST_ENVIRONMENTS:
        raise ValueError(f"Invalid test environment: {env}")
    return env


@pytest.fixture(scope="session")
def db_config(test_environment: str) -> Dict[str, Any]:
    """获取数据库配置"""
    return TEST_ENVIRONMENTS[test_environment]


@pytest.fixture(scope="session")
async def db_connection(db_config: Dict[str, Any]) -> AsyncGenerator[asyncpg.Connection, None]:
    """创建数据库连接"""
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    
    logger.info(f"Connecting to database: {db_config['db_name']}")
    
    try:
        connection = await asyncpg.connect(connection_string)
        yield connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    finally:
        if connection:
            await connection.close()


@pytest.fixture(scope="session") 
async def db_pool(db_config: Dict[str, Any]) -> AsyncGenerator[asyncpg.Pool, None]:
    """创建数据库连接池"""
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    
    logger.info(f"Creating connection pool for database: {db_config['db_name']}")
    
    try:
        pool = await asyncpg.create_pool(
            connection_string,
            min_size=2,
            max_size=10,
            command_timeout=30
        )
        yield pool
    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")
        raise
    finally:
        if pool:
            await pool.close()


@pytest.fixture(scope="function")
async def db_transaction(db_pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """提供事务性数据库连接（自动回滚）"""
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            yield connection
            # 事务会在fixture结束时自动回滚


@pytest.fixture(scope="session")
async def all_db_connections() -> AsyncGenerator[Dict[str, asyncpg.Connection], None]:
    """创建所有环境的数据库连接"""
    connections = {}
    
    try:
        for env_name, config in TEST_ENVIRONMENTS.items():
            connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
            
            try:
                connection = await asyncpg.connect(connection_string)
                connections[env_name] = connection
                logger.info(f"Connected to {env_name}: {config['db_name']}")
            except Exception as e:
                logger.warning(f"Failed to connect to {env_name}: {e}")
                connections[env_name] = None
        
        yield connections
    
    finally:
        for env_name, connection in connections.items():
            if connection:
                await connection.close()
                logger.info(f"Closed connection to {env_name}")


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """生成测试用户数据"""
    return {
        "email": "test@saascontrol.com",
        "username": f"testuser_{datetime.now().microsecond}",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeMLq8.0cLqqRAZ3e",  # hashed "testpassword"
        "is_active": True,
        "is_verified": False
    }


@pytest.fixture
def sample_project_data(sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成测试项目数据"""
    return {
        "name": f"Test Project {datetime.now().microsecond}",
        "slug": f"test-project-{datetime.now().microsecond}",
        "description": "A test project for validation",
        "status": "active",
        "visibility": "private",
        "settings": {
            "ai_features_enabled": True,
            "data_retention_days": 90
        },
        "tags": ["test", "validation"]
    }


@pytest.fixture
def sample_ai_task_data() -> Dict[str, Any]:
    """生成测试AI任务数据"""
    return {
        "task_name": f"Test AI Task {datetime.now().microsecond}",
        "task_type": "text_analysis",
        "priority": "normal",
        "status": "pending",
        "input_data": {"text": "Sample text for analysis"},
        "progress_percentage": 0,
        "retry_count": 0,
        "max_retries": 3
    }


@pytest.fixture
def sample_file_data() -> Dict[str, Any]:
    """生成测试文件数据"""
    return {
        "file_name": f"test_file_{datetime.now().microsecond}.txt",
        "original_name": "test_file.txt",
        "file_path": "/test/path/file.txt",
        "file_hash": "abcd1234efgh5678",
        "file_size": 1024,
        "mime_type": "text/plain",
        "storage_type": "local",
        "upload_status": "completed"
    }


@pytest.fixture
async def cleanup_test_data(db_transaction: asyncpg.Connection):
    """测试后清理数据"""
    # 在测试运行前不做任何操作
    yield
    
    # 由于使用了事务性连接，数据会自动回滚
    # 如果需要特殊清理，可以在这里添加


@pytest.fixture
async def sample_user_in_db(db_transaction: asyncpg.Connection, sample_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """在数据库中创建测试用户"""
    query = """
    INSERT INTO users (email, username, password_hash, is_active, is_verified)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id, email, username, is_active, is_verified, created_at
    """
    
    result = await db_transaction.fetchrow(
        query,
        sample_user_data["email"],
        sample_user_data["username"], 
        sample_user_data["password_hash"],
        sample_user_data["is_active"],
        sample_user_data["is_verified"]
    )
    
    return dict(result)


@pytest.fixture
async def sample_project_in_db(
    db_transaction: asyncpg.Connection, 
    sample_user_in_db: Dict[str, Any],
    sample_project_data: Dict[str, Any]
) -> Dict[str, Any]:
    """在数据库中创建测试项目"""
    import json
    
    query = """
    INSERT INTO projects (name, slug, description, owner_id, status, visibility, settings, tags)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING id, name, slug, owner_id, status, visibility, created_at
    """
    
    result = await db_transaction.fetchrow(
        query,
        sample_project_data["name"],
        sample_project_data["slug"],
        sample_project_data["description"],
        sample_user_in_db["id"],
        sample_project_data["status"],
        sample_project_data["visibility"],
        json.dumps(sample_project_data["settings"]),
        sample_project_data["tags"]
    )
    
    return dict(result)


@pytest.fixture
async def performance_test_data(db_transaction: asyncpg.Connection) -> Dict[str, Any]:
    """生成性能测试数据"""
    # 创建批量用户数据
    users = []
    base_time = datetime.now(timezone.utc)
    
    user_batch = []
    for i in range(100):
        user_data = (
            f"perf_user_{i}@example.com",
            f"perf_user_{i}",
            "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeMLq8.0cLqqRAZ3e",
            True,
            False
        )
        user_batch.append(user_data)
    
    # 批量插入用户
    query = """
    INSERT INTO users (email, username, password_hash, is_active, is_verified)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id
    """
    
    user_ids = []
    for user_data in user_batch:
        result = await db_transaction.fetchval(query, *user_data)
        user_ids.append(result)
    
    return {
        "user_ids": user_ids,
        "user_count": len(user_ids),
        "created_at": base_time
    }


class DatabaseTestUtils:
    """数据库测试工具类"""
    
    @staticmethod
    async def table_exists(connection: asyncpg.Connection, table_name: str) -> bool:
        """检查表是否存在"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        )
        """
        return await connection.fetchval(query, table_name)
    
    @staticmethod
    async def get_table_row_count(connection: asyncpg.Connection, table_name: str) -> int:
        """获取表行数"""
        query = f"SELECT COUNT(*) FROM {table_name}"
        return await connection.fetchval(query)
    
    @staticmethod
    async def get_column_info(connection: asyncpg.Connection, table_name: str) -> List[Dict]:
        """获取表列信息"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = $1 AND table_schema = 'public'
        ORDER BY ordinal_position
        """
        rows = await connection.fetch(query, table_name)
        return [dict(row) for row in rows]
    
    @staticmethod
    async def get_indexes(connection: asyncpg.Connection, table_name: str) -> List[Dict]:
        """获取表索引信息"""
        query = """
        SELECT 
            i.relname as index_name,
            ix.indisunique as is_unique,
            array_agg(a.attname ORDER BY a.attnum) as columns
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON t.oid = a.attrelid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = $1
        GROUP BY i.relname, ix.indisunique
        """
        rows = await connection.fetch(query, table_name)
        return [dict(row) for row in rows]


@pytest.fixture
def db_utils() -> DatabaseTestUtils:
    """数据库测试工具"""
    return DatabaseTestUtils()