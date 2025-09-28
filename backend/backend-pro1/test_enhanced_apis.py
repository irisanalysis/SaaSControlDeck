#!/usr/bin/env python3
"""
SaaS Control Deck - 数据分析API端点测试脚本
测试所有新增的数据分析和管理功能
RELEVANT FILES: unified_backend_fastapi.py, data_analysis_engine.py
"""

import asyncio
import json
import requests
import io
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

class APITestRunner:
    def __init__(self):
        self.token = None
        self.user_email = "test@saascontrol.dev"
        self.user_password = "TestPass123"
        self.uploaded_source_id = None

    def test_health_check(self):
        """测试健康检查端点"""
        print("🔍 测试健康检查...")
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 健康检查成功: {data['status']}")
            print(f"   特性: {', '.join(data['features'])}")
            return True
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False

    def test_login(self):
        """测试用户登录"""
        print("🔐 测试用户登录...")
        try:
            login_data = {
                "email": self.user_email,
                "password": self.user_password
            }
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            assert response.status_code == 200
            data = response.json()
            self.token = data["access_token"]
            print(f"✅ 登录成功: {data['user']['full_name']}")
            return True
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False

    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}

    def test_file_upload(self):
        """测试文件上传（带自动分析）"""
        print("📁 测试文件上传和自动分析...")
        try:
            # 创建一个CSV测试文件
            csv_content = """name,age,city,salary,department
张三,25,北京,8000,技术部
李四,30,上海,12000,市场部
王五,35,广州,15000,技术部
赵六,28,深圳,10000,销售部
钱七,32,杭州,13000,技术部"""

            files = {
                'file': ('test_data.csv', io.StringIO(csv_content), 'text/csv')
            }

            response = requests.post(
                f"{BASE_URL}/upload/file",
                files=files,
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            self.uploaded_source_id = data["data_source"]["id"]

            print(f"✅ 文件上传成功: {data['data_source']['name']}")
            print(f"   数据源ID: {self.uploaded_source_id}")
            print(f"   状态: {data['data_source']['status']}")
            return True
        except Exception as e:
            print(f"❌ 文件上传失败: {e}")
            return False

    def test_get_data_sources(self):
        """测试获取数据源列表"""
        print("📋 测试获取数据源列表...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 获取数据源列表成功: 找到 {data['total']} 个数据源")
            if data["data_sources"]:
                source = data["data_sources"][0]
                print(f"   示例数据源: {source['name']} ({source['type']})")
            return True
        except Exception as e:
            print(f"❌ 获取数据源列表失败: {e}")
            return False

    def test_data_preview(self):
        """测试数据预览功能"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过数据预览测试：没有可用的数据源ID")
            return False

        print("👁️ 测试数据预览...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources/{self.uploaded_source_id}/preview?limit=3",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 数据预览成功: {data['total_rows']} 行数据")
            if data["preview_data"]:
                print(f"   预览数据: {len(data['preview_data'])} 条记录")
                print(f"   示例记录: {data['preview_data'][0] if data['preview_data'] else 'N/A'}")
            return True
        except Exception as e:
            print(f"❌ 数据预览失败: {e}")
            return False

    def test_columns_analysis(self):
        """测试列分析功能"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过列分析测试：没有可用的数据源ID")
            return False

        print("📊 测试列分析...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources/{self.uploaded_source_id}/columns",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 列分析成功: {len(data['columns'])} 列")
            for col in data["columns"][:2]:  # 显示前两列
                print(f"   列: {col['column_name']} ({col['data_type']}) - 唯一值: {col['unique_count']}")
            return True
        except Exception as e:
            print(f"❌ 列分析失败: {e}")
            return False

    def test_quality_check(self):
        """测试数据质量检查"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过质量检查测试：没有可用的数据源ID")
            return False

        print("🔍 测试数据质量检查...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources/{self.uploaded_source_id}/quality",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 质量检查成功: 质量分数 {data['quality_score']}")
            print(f"   质量问题: {len(data['quality_checks'])} 个")
            for check in data["quality_checks"][:2]:  # 显示前两个问题
                print(f"   - {check['severity']}: {check['message']}")
            return True
        except Exception as e:
            print(f"❌ 质量检查失败: {e}")
            return False

    def test_stats(self):
        """测试统计信息"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过统计信息测试：没有可用的数据源ID")
            return False

        print("📈 测试统计信息...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources/{self.uploaded_source_id}/stats",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            basic_stats = data.get("basic_stats", {})
            print(f"✅ 统计信息成功: {basic_stats.get('rows_count', 0)} 行, {basic_stats.get('columns_count', 0)} 列")
            print(f"   文件类型: {basic_stats.get('file_type', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ 统计信息失败: {e}")
            return False

    def test_full_analysis(self):
        """测试完整分析功能"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过完整分析测试：没有可用的数据源ID")
            return False

        print("🤖 测试完整AI分析...")
        try:
            response = requests.post(
                f"{BASE_URL}/data/sources/{self.uploaded_source_id}/analyze",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            ai_insights = data.get("ai_insights", {})
            print(f"✅ 完整分析成功: 质量分数 {data['quality_score']}")
            print(f"   AI摘要: {ai_insights.get('summary', 'N/A')}")
            print(f"   建议数量: {len(ai_insights.get('recommendations', []))}")
            return True
        except Exception as e:
            print(f"❌ 完整分析失败: {e}")
            return False

    def test_search_and_filter(self):
        """测试搜索和过滤功能"""
        print("🔍 测试搜索和过滤...")
        try:
            response = requests.get(
                f"{BASE_URL}/data/sources/search?q=test&type=csv",
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 搜索功能成功: 找到 {data['total']} 个匹配的数据源")
            return True
        except Exception as e:
            print(f"❌ 搜索功能失败: {e}")
            return False

    def test_bulk_operations(self):
        """测试批量操作"""
        if not self.uploaded_source_id:
            print("⚠️ 跳过批量操作测试：没有可用的数据源ID")
            return False

        print("⚡ 测试批量更新操作...")
        try:
            updates = [{
                "source_id": self.uploaded_source_id,
                "description": "通过API测试更新的描述",
                "tags": ["测试", "API", "自动化"]
            }]

            response = requests.post(
                f"{BASE_URL}/data/sources/bulk/update",
                json=updates,
                headers=self.get_headers()
            )
            assert response.status_code == 200
            data = response.json()
            print(f"✅ 批量更新成功: 更新了 {data['updated_count']} 个数据源")
            return True
        except Exception as e:
            print(f"❌ 批量更新失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始API功能测试")
        print("=" * 60)

        tests = [
            ("健康检查", self.test_health_check),
            ("用户登录", self.test_login),
            ("文件上传", self.test_file_upload),
            ("数据源列表", self.test_get_data_sources),
            ("数据预览", self.test_data_preview),
            ("列分析", self.test_columns_analysis),
            ("质量检查", self.test_quality_check),
            ("统计信息", self.test_stats),
            ("完整分析", self.test_full_analysis),
            ("搜索过滤", self.test_search_and_filter),
            ("批量操作", self.test_bulk_operations),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}:")
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"   ❌ {test_name} 测试失败")
            except Exception as e:
                print(f"   ❌ {test_name} 测试异常: {e}")

        print("\n" + "=" * 60)
        print(f"📊 测试结果: {passed}/{total} 通过")

        if passed == total:
            print("🎉 所有测试通过！数据分析API功能正常工作")
        else:
            print(f"⚠️ {total - passed} 个测试失败，请检查相关功能")

        return passed == total

if __name__ == "__main__":
    tester = APITestRunner()
    tester.run_all_tests()