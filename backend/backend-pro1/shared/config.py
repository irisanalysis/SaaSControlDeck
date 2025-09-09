"""
配置管理模块
使用Pydantic Settings管理应用配置
"""

from functools import lru_cache
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """应用设置类"""
    
    # 项目配置
    PROJECT_ID: str = "pro1"
    PROJECT_NAME: str = "AI Data Analysis Platform Pro1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 服务端口配置
    API_GATEWAY_PORT: int = 8000
    DATA_SERVICE_PORT: int = 8001
    AI_SERVICE_PORT: int = 8002
    
    # 数据库配置
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CELERY_DB: int = 1
    
    # AI服务配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7
    
    # Ray集群配置
    RAY_HEAD_NODE_HOST: str = "localhost"
    RAY_HEAD_NODE_PORT: int = 10001
    RAY_REDIS_PASSWORD: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # 外部API配置
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # 文件存储配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "ai-platform-pro1"
    MINIO_SECURE: bool = False
    
    # 监控配置
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY必须至少32个字符")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL必须是以下之一: {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取设置实例（缓存）"""
    return Settings()