#!/usr/bin/env python3
"""
/home/user/studio/tests/utils/test_config.py
测试配置管理器
为所有测试脚本提供统一的配置和环境管理
RELEVANT FILES: backend/CLAUDE.md, tests/migration_index.md
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class TestConfig:
    """
测试配置管理器
"""
    
    def __init__(self):
        self.root_dir = Path("/home/user/studio")
        self.tests_dir = self.root_dir / "tests"
        self.backend_dir = self.root_dir / "backend" / "backend-pro1"
        
        # 默认配置
        self.config = {
            # 服务地址配置
            "services": {
                "backend_pro1": {
                    "base_url": "http://localhost:8000",
                    "health_endpoint": "/health",
                    "docs_endpoint": "/docs",
                    "openapi_endpoint": "/openapi.json"
                },
                "backend_pro2": {
                    "base_url": "http://localhost:8100",
                    "health_endpoint": "/health"
                },
                "frontend": {
                    "base_url": "http://localhost:9000",
                    "health_endpoint": "/api/ready"
                }
            },
            
            # 测试环境配置
            "test_environment": {
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "wait_between_retries": 1,
                "log_level": "INFO"
            },
            
            # 数据库配置
            "database": {
                "dev_connection_string": "postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1",
                "test_connection_string": "postgresql+asyncpg://saascontrol_test_user:test_pass_2024@47.79.87.199:5432/saascontrol_test_pro1"
            },
            
            # 测试用户配置
            "test_users": {
                "default": {
                    "email": "test@saascontrol.dev",
                    "password": "TestPass123"
                },
                "admin": {
                    "email": "admin@saascontrol.dev",
                    "password": "AdminPass123"
                }
            },
            
            # 目录路径配置
            "paths": {
                "root_dir": str(self.root_dir),
                "tests_dir": str(self.tests_dir),
                "backend_dir": str(self.backend_dir),
                "reports_dir": str(self.tests_dir / "reports"),
                "logs_dir": str(self.tests_dir / "logs"),
                "temp_dir": str(self.tests_dir / "temp")
            },
            
            # Docker配置
            "docker": {
                "registry": "saascontrol",
                "backend_image": "saascontrol-backend",
                "test_container_prefix": "saascontrol-test"
            }
        }
        
        # 加载用户自定义配置（如果存在）
        self.load_user_config()
    
    def load_user_config(self):
        """加载用户自定义配置"""
        config_file = self.tests_dir / "test_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 递归合并配置
                    self._merge_config(self.config, user_config)
                    print(f"✅ 已加载用户配置: {config_file}")
            except Exception as e:
                print(f"⚠️ 加载用户配置失败: {e}")
    
    def _merge_config(self, base: Dict, override: Dict):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
获取配置值，支持点分隔的路径
        例如: get('services.backend_pro1.base_url')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
设置配置值
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_service_url(self, service_name: str, endpoint: str = "") -> str:
        """获取服务URL"""
        base_url = self.get(f"services.{service_name}.base_url")
        if not base_url:
            raise ValueError(f"未找到服务 {service_name} 的配置")
        
        return f"{base_url.rstrip('/')}{endpoint}"
    
    def get_health_url(self, service_name: str) -> str:
        """获取服务健康检查URL"""
        health_endpoint = self.get(f"services.{service_name}.health_endpoint", "/health")
        return self.get_service_url(service_name, health_endpoint)
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        for dir_key in ['reports_dir', 'logs_dir', 'temp_dir']:
            dir_path = Path(self.get(f"paths.{dir_key}"))
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_test_user(self, user_type: str = "default") -> Dict[str, str]:
        """获取测试用户信息"""
        return self.get(f"test_users.{user_type}", {})
    
    def save_config(self):
        """保存当前配置到文件"""
        config_file = self.tests_dir / "test_config.json"
        self.ensure_directories()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 配置已保存到: {config_file}")
    
    def create_test_report(self, test_name: str, results: Dict[str, Any]) -> str:
        """创建测试报告"""
        self.ensure_directories()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(self.get('paths.reports_dir')) / f"{test_name}_{timestamp}.json"
        
        report_data = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "environment": "test",
            "results": results,
            "config_snapshot": self.config
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    def get_log_file(self, test_name: str) -> str:
        """获取日志文件路径"""
        self.ensure_directories()
        
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = Path(self.get('paths.logs_dir')) / f"{test_name}_{timestamp}.log"
        
        return str(log_file)

# 全局配置实例
_config_instance = None

def get_config() -> TestConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TestConfig()
    return _config_instance

# 便捷函数
def get_service_url(service_name: str, endpoint: str = "") -> str:
    """便捷函数：获取服务URL"""
    return get_config().get_service_url(service_name, endpoint)

def get_health_url(service_name: str) -> str:
    """便捷函数：获取健康检查URL"""
    return get_config().get_health_url(service_name)

def get_test_user(user_type: str = "default") -> Dict[str, str]:
    """便捷函数：获取测试用户"""
    return get_config().get_test_user(user_type)

def create_test_report(test_name: str, results: Dict[str, Any]) -> str:
    """便捷函数：创建测试报告"""
    return get_config().create_test_report(test_name, results)

if __name__ == "__main__":
    # 测试配置管理器
    config = TestConfig()
    
    print("🔧 SaaS Control Deck - 测试配置管理器")
    print("=" * 50)
    
    # 显示主要配置
    print("📍 主要服务地址:")
    for service in config.get("services", {}):
        url = config.get_service_url(service)
        health_url = config.get_health_url(service)
        print(f"   {service}: {url} (health: {health_url})")
    
    print("\n📂 目录配置:")
    for path_key, path_value in config.get("paths", {}).items():
        print(f"   {path_key}: {path_value}")
    
    print("\n👤 测试用户:")
    for user_type in config.get("test_users", {}):
        user = config.get_test_user(user_type)
        print(f"   {user_type}: {user.get('email', 'N/A')}")
    
    # 确保目录存在
    config.ensure_directories()
    print("\n✅ 所有必要目录已创建")
    
    # 保存配置文件
    config.save_config()
    print("✅ 配置管理器初始化完成")
