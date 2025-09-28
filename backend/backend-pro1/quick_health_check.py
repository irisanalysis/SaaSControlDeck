#!/usr/bin/env python3
"""
/home/user/studio/backend/backend-pro1/quick_health_check.py
快速健康检查脚本 - 验证FastAPI服务基础功能
使用标准库，无需额外依赖，快速验证服务状态
RELEVANT FILES: unified_backend_fastapi.py, comprehensive_api_validation.py, migration_report.py, test_fastapi_migration.py
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import sys

def check_endpoint(url: str, method: str = "GET", data: dict = None, timeout: int = 10) -> dict:
    """检查单个端点"""
    try:
        start_time = time.time()

        # 准备请求
        if data and method == "POST":
            post_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=post_data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)

        # 执行请求
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_time = (time.time() - start_time) * 1000  # ms
            content = response.read().decode('utf-8')

            return {
                "success": True,
                "status_code": response.status,
                "response_time_ms": round(response_time, 2),
                "content": content,
                "headers": dict(response.headers)
            }

    except urllib.error.HTTPError as e:
        response_time = (time.time() - start_time) * 1000
        try:
            content = e.read().decode('utf-8')
        except:
            content = str(e)

        return {
            "success": False,
            "status_code": e.code,
            "response_time_ms": round(response_time, 2),
            "content": content,
            "error": str(e)
        }
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status_code": 0,
            "response_time_ms": round(response_time, 2),
            "error": str(e)
        }

def main():
    """主健康检查流程"""
    base_url = "http://localhost:8000"

    print("🚀 FastAPI服务快速健康检查")
    print(f"🎯 目标服务: {base_url}")
    print("=" * 60)

    # 健康检查端点列表
    health_checks = [
        {
            "name": "基础健康检查",
            "url": f"{base_url}/health",
            "method": "GET",
            "critical": True
        },
        {
            "name": "根路径访问",
            "url": f"{base_url}/",
            "method": "GET",
            "critical": True
        },
        {
            "name": "API文档访问",
            "url": f"{base_url}/docs",
            "method": "GET",
            "critical": False
        },
        {
            "name": "OpenAPI规范",
            "url": f"{base_url}/openapi.json",
            "method": "GET",
            "critical": False
        }
    ]

    # API功能基础检查
    api_checks = [
        {
            "name": "用户注册API (结构检查)",
            "url": f"{base_url}/auth/register",
            "method": "POST",
            "data": {"email": "test@example.com", "password": "test123", "full_name": "Test User"},
            "critical": True
        },
        {
            "name": "用户登录API (结构检查)",
            "url": f"{base_url}/auth/login",
            "method": "POST",
            "data": {"email": "test@example.com", "password": "test123"},
            "critical": True
        }
    ]

    all_checks = health_checks + api_checks
    results = []
    critical_failures = 0

    # 执行所有检查
    for check in all_checks:
        print(f"🔍 检查: {check['name']}")

        result = check_endpoint(
            url=check["url"],
            method=check["method"],
            data=check.get("data"),
            timeout=10
        )

        result["name"] = check["name"]
        result["critical"] = check["critical"]
        result["timestamp"] = datetime.now().isoformat()
        results.append(result)

        # 显示结果
        if result["success"] or result["status_code"] in [200, 201, 400, 401, 409, 422]:
            status_icon = "✅"
            status_desc = f"{result['status_code']} ({result['response_time_ms']:.1f}ms)"
        else:
            status_icon = "❌"
            status_desc = f"错误: {result.get('error', 'Unknown error')}"
            if check["critical"]:
                critical_failures += 1

        print(f"  {status_icon} {status_desc}")

        # 解析健康检查响应
        if check["name"] == "基础健康检查" and result["success"]:
            try:
                health_data = json.loads(result["content"])
                print(f"    🏥 服务: {health_data.get('service', 'Unknown')}")
                print(f"    🔌 端口: {health_data.get('port', 'Unknown')}")
                print(f"    ⏱️  运行时间: {health_data.get('uptime', 0):.1f}秒")
                features = health_data.get('features', [])
                print(f"    🎯 功能: {', '.join(features) if features else 'None'}")
            except:
                pass

        print()

    # 生成总结报告
    print("=" * 60)
    print("📊 健康检查总结")
    print("=" * 60)

    successful_checks = sum(1 for r in results if r["success"] or r["status_code"] in [200, 201, 400, 401, 409, 422])
    total_checks = len(results)
    success_rate = (successful_checks / total_checks) * 100 if total_checks > 0 else 0

    avg_response_time = sum(r["response_time_ms"] for r in results if r["response_time_ms"] > 0) / len([r for r in results if r["response_time_ms"] > 0])

    print(f"✅ 成功检查: {successful_checks}/{total_checks} ({success_rate:.1f}%)")
    print(f"⚡ 平均响应时间: {avg_response_time:.1f}ms")
    print(f"🚨 关键失败: {critical_failures}")

    # 整体状态判断
    overall_health = critical_failures == 0 and success_rate >= 80

    if overall_health:
        print(f"🎉 整体状态: ✅ 健康 - FastAPI服务运行正常")
        performance_rating = (
            "🚀 优秀" if avg_response_time < 50 else
            "✅ 良好" if avg_response_time < 100 else
            "⚠️ 可接受" if avg_response_time < 200 else
            "❌ 需优化"
        )
        print(f"⚡ 性能评级: {performance_rating}")
    else:
        print(f"❌ 整体状态: 🚨 异常 - 发现关键问题，需要排查")

    print()
    print("💡 快速建议:")
    if critical_failures > 0:
        print("  🔧 请检查FastAPI服务是否正常启动")
        print("  🔍 查看服务日志排查错误原因")
    elif avg_response_time > 100:
        print("  ⚡ 考虑优化响应性能，目标<50ms")
    else:
        print("  🎯 所有基础检查通过，可以执行完整API验证")

    # 保存简化报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_health": overall_health,
        "success_rate_percent": success_rate,
        "avg_response_time_ms": avg_response_time,
        "critical_failures": critical_failures,
        "checks": results
    }

    with open("/home/user/studio/backend/backend-pro1/quick_health_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("📄 详细结果已保存至: quick_health_report.json")

    return 0 if overall_health else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)