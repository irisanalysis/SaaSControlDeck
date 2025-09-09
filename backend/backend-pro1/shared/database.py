"""
数据库连接管理模块
使用asyncpg进行异步PostgreSQL操作
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
import asyncpg
import structlog

logger = structlog.get_logger()


class Database:
    """数据库连接池管理类"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def connect(cls, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        """创建数据库连接池"""
        try:
            cls._pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=pool_size,
                command_timeout=60,
                server_settings={
                    'jit': 'off'  # 对于小查询禁用JIT以提高性能
                }
            )
            logger.info("数据库连接池创建成功", pool_size=pool_size)
        except Exception as e:
            logger.error("数据库连接失败", error=str(e), exc_info=True)
            raise
    
    @classmethod
    async def disconnect(cls):
        """关闭数据库连接池"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("数据库连接池已关闭")
    
    @classmethod
    async def fetch_one(cls, query: str, *args) -> Optional[Dict[str, Any]]:
        """执行查询并返回单行结果"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with cls._pool.acquire() as connection:
            try:
                row = await connection.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error("数据库查询失败", query=query, error=str(e))
                raise
    
    @classmethod
    async def fetch_all(cls, query: str, *args) -> List[Dict[str, Any]]:
        """执行查询并返回所有结果"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with cls._pool.acquire() as connection:
            try:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error("数据库查询失败", query=query, error=str(e))
                raise
    
    @classmethod
    async def fetch_val(cls, query: str, *args) -> Any:
        """执行查询并返回单个值"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with cls._pool.acquire() as connection:
            try:
                return await connection.fetchval(query, *args)
            except Exception as e:
                logger.error("数据库查询失败", query=query, error=str(e))
                raise
    
    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """执行非查询SQL语句"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with cls._pool.acquire() as connection:
            try:
                return await connection.execute(query, *args)
            except Exception as e:
                logger.error("数据库执行失败", query=query, error=str(e))
                raise
    
    @classmethod
    async def execute_many(cls, query: str, args_list: List[tuple]) -> None:
        """批量执行SQL语句"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with cls._pool.acquire() as connection:
            try:
                await connection.executemany(query, args_list)
            except Exception as e:
                logger.error("数据库批量执行失败", query=query, error=str(e))
                raise
    
    @classmethod
    async def execute_query(cls, query: str, *args) -> Union[List[Dict[str, Any]], str]:
        """通用查询执行方法"""
        if query.strip().upper().startswith(('SELECT', 'WITH')):
            return await cls.fetch_all(query, *args)
        else:
            return await cls.execute(query, *args)
    
    @classmethod
    async def transaction(cls):
        """返回事务上下文管理器"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        return cls._pool.acquire()
    
    @classmethod
    async def get_connection(cls):
        """获取数据库连接（用于事务）"""
        if not cls._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        return await cls._pool.acquire()


class DatabaseTransaction:
    """数据库事务上下文管理器"""
    
    def __init__(self, connection):
        self.connection = connection
        self.transaction = None
    
    async def __aenter__(self):
        self.transaction = self.connection.transaction()
        await self.transaction.start()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.transaction.commit()
        else:
            await self.transaction.rollback()
        await self.connection.close()