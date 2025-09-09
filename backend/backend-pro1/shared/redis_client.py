"""
Redis客户端管理模块
用于缓存、会话管理和分布式锁
"""

import json
from typing import Any, Optional, Union
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class RedisClient:
    """Redis客户端管理类"""
    
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def connect(cls, redis_url: str):
        """创建Redis连接"""
        try:
            cls._client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await cls._client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error("Redis连接失败", error=str(e), exc_info=True)
            raise
    
    @classmethod
    async def disconnect(cls):
        """关闭Redis连接"""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Redis连接已关闭")
    
    @classmethod
    async def ping(cls) -> bool:
        """检查Redis连接状态"""
        if not cls._client:
            return False
        
        try:
            await cls._client.ping()
            return True
        except Exception:
            return False
    
    @classmethod
    async def set(
        cls, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None,
        serialize_json: bool = True
    ) -> bool:
        """设置键值"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            if serialize_json and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            
            return await cls._client.set(key, value, ex=expire)
        except Exception as e:
            logger.error("Redis设置失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def get(
        cls, 
        key: str, 
        deserialize_json: bool = True
    ) -> Optional[Any]:
        """获取键值"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            value = await cls._client.get(key)
            if value is None:
                return None
            
            if deserialize_json:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            
            return value
        except Exception as e:
            logger.error("Redis获取失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def delete(cls, *keys: str) -> int:
        """删除键"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            return await cls._client.delete(*keys)
        except Exception as e:
            logger.error("Redis删除失败", keys=keys, error=str(e))
            raise
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """检查键是否存在"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            return bool(await cls._client.exists(key))
        except Exception as e:
            logger.error("Redis检查失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def expire(cls, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            return await cls._client.expire(key, seconds)
        except Exception as e:
            logger.error("Redis过期设置失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def incr(cls, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            return await cls._client.incrby(key, amount)
        except Exception as e:
            logger.error("Redis递增失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def decr(cls, key: str, amount: int = 1) -> int:
        """递减计数器"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            return await cls._client.decrby(key, amount)
        except Exception as e:
            logger.error("Redis递减失败", key=key, error=str(e))
            raise
    
    @classmethod
    async def hset(cls, name: str, mapping: dict) -> int:
        """设置哈希表"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            # 序列化复杂对象
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v, ensure_ascii=False)
                else:
                    serialized_mapping[k] = v
            
            return await cls._client.hset(name, mapping=serialized_mapping)
        except Exception as e:
            logger.error("Redis哈希设置失败", name=name, error=str(e))
            raise
    
    @classmethod
    async def hget(cls, name: str, key: str) -> Optional[Any]:
        """获取哈希表字段"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            value = await cls._client.hget(name, key)
            if value is None:
                return None
            
            # 尝试反序列化JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error("Redis哈希获取失败", name=name, key=key, error=str(e))
            raise
    
    @classmethod
    async def hgetall(cls, name: str) -> dict:
        """获取整个哈希表"""
        if not cls._client:
            raise RuntimeError("Redis客户端未初始化")
        
        try:
            data = await cls._client.hgetall(name)
            
            # 反序列化值
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            
            return result
        except Exception as e:
            logger.error("Redis哈希全量获取失败", name=name, error=str(e))
            raise