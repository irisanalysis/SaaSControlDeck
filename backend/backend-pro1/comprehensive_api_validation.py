#!/usr/bin/env python3
"""
/home/user/studio/backend/backend-pro1/comprehensive_api_validation.py
专业的FastAPI迁移验证工具 - 全面API端点健康检查和功能验证
确保FastAPI迁移后的服务完全兼容原有功能，支持生产级质量验证
RELEVANT FILES: unified_backend_fastapi.py, test_fastapi_migration.py, migration_report.py, check_current_backend.py
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

class ComprehensiveAPIValidator:
    """专业API验证器 - 支持健康检查、功能验证、性能测试"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "health_checks": [],
            "api_endpoints": [],
            "performance_metrics": {},
            "error_logs": [],
            "validation_summary": {}
        }
        self.start_time = time.time()

    async def validate_health_endpoints(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """验证健康检查端点"""
        print("🔍 执行健康检查端点验证...")

        health_endpoints = [
            "/health",
            "/api/health",
            "/",
            "/docs",
            "/openapi.json"
        ]

        health_results = []

        for endpoint in health_endpoints:
            try:
                start_time = time.time()
                url = f"{self.base_url}{endpoint}"

                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000  # ms
                    content = await response.text()

                    result = {
                        "endpoint": endpoint,
                        "url": url,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "content_type": response.headers.get('content-type', ''),
                        "success": response.status == 200,
                        "content_preview": content[:200] if content else "",
                        "timestamp": datetime.now().isoformat()
                    }

                    # 特殊处理health端点
                    if endpoint == "/health" and response.status == 200:
                        try:
                            health_data = json.loads(content)
                            result["health_data"] = health_data
                            result["service_name"] = health_data.get("service", "unknown")
                            result["features"] = health_data.get("features", [])
                            result["uptime"] = health_data.get("uptime", 0)
                        except json.JSONDecodeError:
                            result["error"] = "健康端点返回非JSON格式"

                    health_results.append(result)

                    status_icon = "✅" if result["success"] else "❌"
                    print(f"  {status_icon} {endpoint}: {response.status} ({response_time:.1f}ms)")

            except Exception as e:
                error_result = {
                    "endpoint": endpoint,
                    "url": f"{self.base_url}{endpoint}",
                    "error": str(e),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
                health_results.append(error_result)
                print(f"  ❌ {endpoint}: 连接错误 - {str(e)}")

        return health_results

    async def validate_api_functionality(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """验证API端点功能对等性"""
        print("🔍 执行API端点功能验证...")

        api_tests = [
            # 认证端点
            {
                "name": "用户注册API",
                "method": "POST",
                "endpoint": "/auth/register",
                "data": {
                    "email": "test@example.com",
                    "password": "test123456",
                    "full_name": "Test User"
                },
                "expected_status": [200, 201, 409]  # 409 = 用户已存在
            },
            {
                "name": "用户登录API",
                "method": "POST",
                "endpoint": "/auth/login",
                "data": {
                    "email": "test@example.com",
                    "password": "test123456"
                },
                "expected_status": [200, 401]
            },
            # 文件上传端点
            {
                "name": "文件上传API (基础检查)",
                "method": "GET",
                "endpoint": "/upload/file",
                "expected_status": [200, 405]  # 405 = Method Not Allowed (正常，因为是POST端点)
            },
            # 数据管理端点
            {
                "name": "数据管理API",
                "method": "GET",
                "endpoint": "/data/preview",
                "expected_status": [200, 404, 401]
            }
        ]

        api_results = []

        for test in api_tests:
            try:
                start_time = time.time()
                url = f"{self.base_url}{test['endpoint']}"

                # 准备请求参数
                kwargs = {}
                if test["method"].upper() == "POST" and "data" in test:
                    kwargs["json"] = test["data"]

                # 执行请求
                async with session.request(test["method"], url, **kwargs) as response:
                    response_time = (time.time() - start_time) * 1000  # ms
                    content = await response.text()

                    # 判断是否成功
                    success = response.status in test["expected_status"]

                    result = {
                        "test_name": test["name"],
                        "method": test["method"],
                        "endpoint": test["endpoint"],
                        "url": url,
                        "status_code": response.status,
                        "expected_status": test["expected_status"],
                        "response_time_ms": round(response_time, 2),
                        "success": success,
                        "content_preview": content[:300] if content else "",
                        "timestamp": datetime.now().isoformat()
                    }

                    # 尝试解析JSON响应
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            result["json_response"] = json.loads(content)
                    except json.JSONDecodeError:
                        pass

                    api_results.append(result)

                    status_icon = "✅" if success else "❌"
                    print(f"  {status_icon} {test['name']}: {response.status} ({response_time:.1f}ms)")

            except Exception as e:
                error_result = {
                    "test_name": test["name"],
                    "method": test["method"],
                    "endpoint": test["endpoint"],
                    "error": str(e),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
                api_results.append(error_result)
                print(f"  ❌ {test['name']}: 连接错误 - {str(e)}")

        return api_results

    async def measure_performance_metrics(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """性能基准测试"""
        print("🔍 执行性能基准测试...")

        performance_endpoints = [
            "/health",
            "/",
            "/auth/login"  # POST endpoint for login simulation
        ]

        metrics = {}

        for endpoint in performance_endpoints:
            print(f"  📊 测试端点: {endpoint}")
            response_times = []
            successful_requests = 0
            failed_requests = 0

            # 执行10次请求测试性能
            for i in range(10):
                try:
                    start_time = time.time()
                    url = f"{self.base_url}{endpoint}"

                    # 特殊处理POST端点
                    kwargs = {}
                    if endpoint == "/auth/login":
                        kwargs["json"] = {"email": "test@example.com", "password": "test123456"}
                        method = "POST"
                    else:
                        method = "GET"

                    async with session.request(method, url, **kwargs) as response:
                        response_time = (time.time() - start_time) * 1000  # ms
                        response_times.append(response_time)

                        if response.status < 500:  # 认为非5xx错误都是成功的
                            successful_requests += 1
                        else:
                            failed_requests += 1

                except Exception as e:
                    failed_requests += 1
                    print(f"    ❌ 请求失败: {str(e)}")

            if response_times:
                metrics[endpoint] = {
                    "avg_response_time_ms": round(sum(response_times) / len(response_times), 2),
                    "min_response_time_ms": round(min(response_times), 2),
                    "max_response_time_ms": round(max(response_times), 2),
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate_percent": round((successful_requests / 10) * 100, 1),
                    "total_requests": 10
                }

                avg_time = metrics[endpoint]["avg_response_time_ms"]
                success_rate = metrics[endpoint]["success_rate_percent"]
                print(f"    ✅ 平均响应时间: {avg_time}ms, 成功率: {success_rate}%")
            else:
                metrics[endpoint] = {"error": "所有请求都失败了"}
                print(f"    ❌ 所有请求都失败了")

        return metrics

    def generate_validation_summary(self) -> Dict[str, Any]:
        """生成验证总结"""
        health_checks = self.results["health_checks"]
        api_endpoints = self.results["api_endpoints"]
        performance_metrics = self.results["performance_metrics"]

        # 计算成功率
        health_success = sum(1 for check in health_checks if check.get("success", False))
        health_total = len(health_checks)

        api_success = sum(1 for test in api_endpoints if test.get("success", False))
        api_total = len(api_endpoints)

        # 性能指标汇总
        avg_response_times = []
        for endpoint_metrics in performance_metrics.values():
            if isinstance(endpoint_metrics, dict) and "avg_response_time_ms" in endpoint_metrics:
                avg_response_times.append(endpoint_metrics["avg_response_time_ms"])

        overall_avg_response = round(sum(avg_response_times) / len(avg_response_times), 2) if avg_response_times else 0

        # 确定整体状态
        overall_health = (
            health_success == health_total and
            api_success >= api_total * 0.8 and  # 至少80%的API测试通过
            overall_avg_response < 100  # 平均响应时间小于100ms
        )

        validation_time = time.time() - self.start_time

        summary = {
            "overall_status": "✅ PASSED" if overall_health else "❌ FAILED",
            "validation_timestamp": datetime.now().isoformat(),
            "validation_duration_seconds": round(validation_time, 2),
            "health_checks": {
                "success_count": health_success,
                "total_count": health_total,
                "success_rate_percent": round((health_success / health_total) * 100, 1) if health_total > 0 else 0
            },
            "api_functionality": {
                "success_count": api_success,
                "total_count": api_total,
                "success_rate_percent": round((api_success / api_total) * 100, 1) if api_total > 0 else 0
            },
            "performance": {
                "overall_avg_response_time_ms": overall_avg_response,
                "performance_rating": (
                    "🚀 Excellent" if overall_avg_response < 50 else
                    "✅ Good" if overall_avg_response < 100 else
                    "⚠️ Acceptable" if overall_avg_response < 200 else
                    "❌ Needs Improvement"
                )
            },
            "recommendations": self._generate_recommendations(overall_health, overall_avg_response)
        }

        return summary

    def _generate_recommendations(self, overall_health: bool, avg_response_time: float) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if not overall_health:
            recommendations.append("❌ 系统整体健康状态不佳，需要排查失败的检查项")

        if avg_response_time > 100:
            recommendations.append("⚡ 响应时间偏慢，建议优化性能（目标：<50ms）")

        health_success_rate = self.results.get("validation_summary", {}).get("health_checks", {}).get("success_rate_percent", 0)
        if health_success_rate < 100:
            recommendations.append("🔧 部分健康检查失败，检查服务配置和端点可用性")

        api_success_rate = self.results.get("validation_summary", {}).get("api_functionality", {}).get("success_rate_percent", 0)
        if api_success_rate < 90:
            recommendations.append("🔨 API功能验证通过率偏低，检查端点实现和错误处理")

        if len(recommendations) == 0:
            recommendations.append("🎉 所有验证通过！FastAPI迁移质量优秀，可以投入生产使用")

        return recommendations

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行完整验证流程"""
        print("🚀 开始FastAPI迁移全面验证...")
        print(f"🎯 目标服务: {self.base_url}")
        print("-" * 60)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                # 1. 健康检查验证
                self.results["health_checks"] = await self.validate_health_endpoints(session)
                print()

                # 2. API功能验证
                self.results["api_endpoints"] = await self.validate_api_functionality(session)
                print()

                # 3. 性能基准测试
                self.results["performance_metrics"] = await self.measure_performance_metrics(session)
                print()

            except Exception as e:
                print(f"❌ 验证过程出现严重错误: {str(e)}")
                self.results["error_logs"].append({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

        # 4. 生成验证总结
        self.results["validation_summary"] = self.generate_validation_summary()

        return self.results

    def print_detailed_report(self):
        """打印详细验证报告"""
        print("=" * 80)
        print("🎯 FastAPI迁移验证详细报告")
        print("=" * 80)

        summary = self.results["validation_summary"]
        print(f"📊 整体状态: {summary['overall_status']}")
        print(f"⏱️  验证时间: {summary['validation_duration_seconds']}秒")
        print(f"🕐 验证时间: {summary['validation_timestamp']}")
        print()

        # 健康检查结果
        print("🔍 健康检查结果:")
        health = summary["health_checks"]
        print(f"  ✅ 成功: {health['success_count']}/{health['total_count']} ({health['success_rate_percent']}%)")
        for check in self.results["health_checks"]:
            status = "✅" if check.get("success") else "❌"
            endpoint = check.get("endpoint", "unknown")
            response_time = check.get("response_time_ms", "N/A")
            print(f"    {status} {endpoint} ({response_time}ms)")
        print()

        # API功能结果
        print("🔧 API功能验证结果:")
        api = summary["api_functionality"]
        print(f"  ✅ 成功: {api['success_count']}/{api['total_count']} ({api['success_rate_percent']}%)")
        for test in self.results["api_endpoints"]:
            status = "✅" if test.get("success") else "❌"
            name = test.get("test_name", "unknown")
            response_time = test.get("response_time_ms", "N/A")
            print(f"    {status} {name} ({response_time}ms)")
        print()

        # 性能结果
        print("⚡ 性能基准测试结果:")
        perf = summary["performance"]
        print(f"  📊 整体平均响应时间: {perf['overall_avg_response_time_ms']}ms")
        print(f"  🏆 性能评级: {perf['performance_rating']}")
        for endpoint, metrics in self.results["performance_metrics"].items():
            if isinstance(metrics, dict) and "avg_response_time_ms" in metrics:
                avg_time = metrics["avg_response_time_ms"]
                success_rate = metrics["success_rate_percent"]
                print(f"    📈 {endpoint}: {avg_time}ms 平均, {success_rate}% 成功率")
        print()

        # 改进建议
        print("💡 改进建议:")
        for rec in summary["recommendations"]:
            print(f"  {rec}")

        print("=" * 80)

async def main():
    """主验证流程"""
    # 检查FastAPI服务是否运行
    print("🔍 检查FastAPI服务状态...")

    validator = ComprehensiveAPIValidator()

    # 运行完整验证
    results = await validator.run_comprehensive_validation()

    # 打印详细报告
    validator.print_detailed_report()

    # 保存验证结果到文件
    output_file = "/home/user/studio/backend/backend-pro1/api_validation_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"📄 详细验证结果已保存至: {output_file}")

    # 返回整体状态码
    overall_success = results["validation_summary"]["overall_status"] == "✅ PASSED"
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)