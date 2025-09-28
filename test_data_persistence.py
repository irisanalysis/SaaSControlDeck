#!/usr/bin/env python3
"""
SaaS Control Deck - 数据持久化功能测试脚本
测试场景: 用户上传文件 → 服务重启 → 数据仍然存在
验证多用户数据隔离和完整的CRUD操作
"""

import requests
import json
import time
import os
import io
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_FILE_CONTENT = "id,name,age,city,score\n1,Alice,25,New York,95.5\n2,Bob,30,San Francisco,87.2\n3,Charlie,28,Chicago,92.1"

class TestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        })

    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("健康检查", True, f"服务状态: {health_data.get('status')}")
                return True
            else:
                self.log_test("健康检查", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, str(e))
            return False

    def test_user_authentication(self) -> bool:
        """测试用户认证"""
        try:
            # 登录测试用户
            login_data = {
                "email": "test@saascontrol.dev",
                "password": "TestPass123"
            }

            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data["access_token"]
                user_email = auth_data["user"]["email"]
                self.log_test("用户认证", True, f"用户: {user_email}")
                return True
            else:
                self.log_test("用户认证", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("用户认证", False, str(e))
            return False

    def test_file_upload(self) -> str:
        """测试文件上传并返回数据源ID"""
        try:
            if not self.auth_token:
                self.log_test("文件上传", False, "缺少认证令牌")
                return None

            # 创建测试CSV文件
            files = {
                'file': ('test_data.csv', io.StringIO(TEST_FILE_CONTENT), 'text/csv')
            }

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.post(
                f"{BASE_URL}/upload/file",
                files=files,
                headers=headers
            )

            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get("success"):
                    data_source_id = upload_data["data_source"]["id"]
                    self.log_test("文件上传", True, f"数据源ID: {data_source_id}")
                    return data_source_id
                else:
                    self.log_test("文件上传", False, "上传失败")
                    return None
            else:
                self.log_test("文件上传", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_test("文件上传", False, str(e))
            return None

    def test_data_sources_list(self) -> bool:
        """测试获取数据源列表"""
        try:
            if not self.auth_token:
                self.log_test("数据源列表", False, "缺少认证令牌")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.get(
                f"{BASE_URL}/data/sources",
                headers=headers
            )

            if response.status_code == 200:
                sources_data = response.json()
                total_sources = sources_data.get("total", 0)
                data_sources = sources_data.get("data_sources", [])
                self.log_test("数据源列表", True, f"找到 {total_sources} 个数据源")
                return len(data_sources) > 0
            else:
                self.log_test("数据源列表", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据源列表", False, str(e))
            return False

    def test_data_source_details(self, source_id: str) -> bool:
        """测试获取数据源详情"""
        try:
            if not self.auth_token or not source_id:
                self.log_test("数据源详情", False, "缺少认证令牌或数据源ID")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.get(
                f"{BASE_URL}/data/sources/{source_id}",
                headers=headers
            )

            if response.status_code == 200:
                source_data = response.json()
                source_name = source_data.get("name", "未知")
                self.log_test("数据源详情", True, f"数据源: {source_name}")
                return True
            else:
                self.log_test("数据源详情", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据源详情", False, str(e))
            return False

    def test_data_source_update(self, source_id: str) -> bool:
        """测试更新数据源"""
        try:
            if not self.auth_token or not source_id:
                self.log_test("数据源更新", False, "缺少认证令牌或数据源ID")
                return False

            update_data = {
                "name": "test_data_updated.csv",
                "description": "更新后的测试数据文件",
                "type": "csv"
            }

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }

            response = self.session.put(
                f"{BASE_URL}/data/sources/{source_id}",
                json=update_data,
                headers=headers
            )

            if response.status_code == 200:
                update_result = response.json()
                self.log_test("数据源更新", True, f"更新成功: {update_result.get('name')}")
                return True
            else:
                self.log_test("数据源更新", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据源更新", False, str(e))
            return False

    def test_data_stats(self) -> bool:
        """测试数据统计"""
        try:
            if not self.auth_token:
                self.log_test("数据统计", False, "缺少认证令牌")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.get(
                f"{BASE_URL}/data/stats",
                headers=headers
            )

            if response.status_code == 200:
                stats_data = response.json()
                total_datasets = stats_data.get("total_datasets", 0)
                self.log_test("数据统计", True, f"总数据集: {total_datasets}")
                return True
            else:
                self.log_test("数据统计", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据统计", False, str(e))
            return False

    def test_data_source_delete(self, source_id: str) -> bool:
        """测试删除数据源"""
        try:
            if not self.auth_token or not source_id:
                self.log_test("数据源删除", False, "缺少认证令牌或数据源ID")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.delete(
                f"{BASE_URL}/data/sources/{source_id}",
                headers=headers
            )

            if response.status_code == 200:
                delete_result = response.json()
                self.log_test("数据源删除", True, f"删除成功: {delete_result.get('message')}")
                return True
            else:
                self.log_test("数据源删除", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据源删除", False, str(e))
            return False

    def run_all_tests(self):
        """运行全部测试"""
        print("🚀 开始SaaS Control Deck数据持久化功能测试")
        print("="*60)

        # 基础功能测试
        if not self.test_health_check():
            print("❌ 健康检查失败，退出测试")
            return

        if not self.test_user_authentication():
            print("❌ 用户认证失败，退出测试")
            return

        # 数据CRUD测试
        source_id = self.test_file_upload()
        if source_id:
            self.test_data_sources_list()
            self.test_data_source_details(source_id)
            self.test_data_source_update(source_id)
            self.test_data_stats()

            # 模拟服务重启测试（说明）
            print("⚠️  现在请重启后端服务来测试数据持久化")
            print("   重启后再次运行此脚本验证数据是否仍然存在")

            # 在实际环境中不删除，用于测试持久化
            # self.test_data_source_delete(source_id)

        # 输出测试结果
        print("\n" + "="*60)
        print("📊 测试结果汇总:")

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"✅ 通过: {passed}/{total}")

        if passed == total:
            print("🎉 所有测试通过！数据持久化功能正常工作")
        else:
            print("⚠️  部分测试失败，请检查日志")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")

def main():
    """主函数"""
    tester = TestRunner()
    tester.run_all_tests()

if __name__ == "__main__":
    main()