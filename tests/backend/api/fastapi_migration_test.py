#!/usr/bin/env python3
"""
/home/user/studio/tests/backend/api/fastapi_migration_test.py
测试FastAPI迁移的脚本 - 从根目录迁移而来
验证所有API端点是否正常工作
RELEVANT FILES: backend/backend-pro1/unified_backend_fastapi.py, tests/backend/health/quick_health_check.py
"""

import requests
import json
import sys
from datetime import datetime

def test_api_endpoint(method, url, data=None, headers=None, expected_status=200):
    """测试API端点"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return False

        if response.status_code == expected_status:
            print(f"✅ {method} {url} - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ {method} {url} - 期望状态码: {expected_status}, 实际: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}...")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {url} - 连接错误: {e}")
        return False

def test_fastapi_migration():
    """测试FastAPI迁移的完整功能"""

    print("🧪 SaaS Control Deck - FastAPI迁移功能测试")
    print("=" * 50)

    base_url = "http://localhost:8000"
    test_results = []
    access_token = None

    # 测试用例列表
    test_cases = [
        # 健康检查
        {
            "name": "健康检查",
            "method": "GET",
            "url": f"{base_url}/health",
            "expected_status": 200
        },
    ]

    # 执行基础测试
    print("\n📋 第一阶段：基础服务测试")
    print("-" * 30)

    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        result = test_api_endpoint(
            test_case["method"],
            test_case["url"],
            test_case.get("data"),
            test_case.get("headers"),
            test_case["expected_status"]
        )
        test_results.append(result)

    # 认证功能测试
    print("\n🔐 第二阶段：认证功能测试")
    print("-" * 30)

    # 测试登录
    login_data = {
        "email": "test@saascontrol.dev",
        "password": "TestPass123"
    }

    print("测试: 用户登录")
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ POST /auth/login - 状态码: 200")
            login_response = response.json()
            access_token = login_response.get("access_token")
            print(f"   获取访问令牌: {access_token[:20]}...")
            test_results.append(True)
        else:
            print(f"❌ POST /auth/login - 状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ POST /auth/login - 连接错误: {e}")
        test_results.append(False)

    # 使用令牌测试获取用户信息
    if access_token:
        print("测试: 获取当前用户信息")
        headers = {"Authorization": f"Bearer {access_token}"}
        result = test_api_endpoint("GET", f"{base_url}/auth/me", headers=headers)
        test_results.append(result)

        # 测试数据源列表
        print("测试: 获取数据源列表")
        result = test_api_endpoint("GET", f"{base_url}/data/sources", headers=headers)
        test_results.append(result)

    # 测试结果汇总
    print("\n📊 测试结果汇总")
    print("=" * 50)

    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests

    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")

    if failed_tests == 0:
        print("🎉 所有测试通过！FastAPI服务运行正常")
        return True
    else:
        print(f"⚠️  有 {failed_tests} 个测试失败，请检查服务状态")
        return False

def check_service_status():
    """检查服务状态"""
    print("🔍 检查FastAPI服务状态...")

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ FastAPI服务运行正常")
            print(f"   服务名称: {health_data.get('service', 'N/A')}")
            print(f"   服务状态: {health_data.get('status', 'N/A')}")
            print(f"   服务端口: {health_data.get('port', 'N/A')}")
            print(f"   时间戳: {health_data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"❌ FastAPI服务健康检查失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到FastAPI服务: {e}")
        print("   请确保FastAPI服务已启动在端口8000")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_service_status()
    else:
        # 首先检查服务状态
        if check_service_status():
            print()
            test_fastapi_migration()
        else:
            print("\n💡 启动FastAPI服务命令:")
            print("   cd /home/user/studio/backend/backend-pro1")
            print("   uv shell")
            print("   uv run uvicorn unified_backend_fastapi:app --reload --port 8000")
