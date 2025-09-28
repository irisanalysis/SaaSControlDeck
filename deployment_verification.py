#!/usr/bin/env python3
"""
SaaS Control Deck - 部署验证脚本
验证整个系统的部署状态和核心功能
确保数据持久化升级成功完成
"""

import asyncio
import sys
import subprocess
import time
import requests
import os
from datetime import datetime

class DeploymentVerifier:
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:8000"

    def log_result(self, component: str, status: bool, message: str = ""):
        """记录验证结果"""
        icon = "✅" if status else "❌"
        print(f"{icon} {component}: {message}")
        self.results.append({
            "component": component,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def check_backend_process(self) -> bool:
        """检查后端进程是否运行"""
        try:
            # 检查8000端口是否被占用
            result = subprocess.run(
                ["lsof", "-i", ":8000"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and "uvicorn" in result.stdout:
                self.log_result("后端进程", True, "Uvicorn服务正在运行")
                return True
            else:
                self.log_result("后端进程", False, "端口8000未被Uvicorn占用")
                return False

        except Exception as e:
            self.log_result("后端进程", False, f"检查失败: {e}")
            return False

    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        try:
            # 尝试连接数据库
            import asyncpg

            async def test_connection():
                try:
                    conn = await asyncpg.connect(
                        "postgresql://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"
                    )
                    await conn.execute("SELECT 1")
                    await conn.close()
                    return True
                except Exception as e:
                    print(f"数据库连接错误: {e}")
                    return False

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_connection())
            loop.close()

            if result:
                self.log_result("数据库连接", True, "PostgreSQL连接正常")
                return True
            else:
                self.log_result("数据库连接", False, "无法连接到PostgreSQL")
                return False

        except ImportError:
            self.log_result("数据库连接", False, "缺少asyncpg依赖")
            return False
        except Exception as e:
            self.log_result("数据库连接", False, f"检查失败: {e}")
            return False

    def check_api_health(self) -> bool:
        """检查API健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)

            if response.status_code == 200:
                health_data = response.json()
                features = health_data.get("features", [])

                if "authentication" in features and "data-management" in features:
                    self.log_result("API健康检查", True, f"服务状态: {health_data.get('status')}")
                    return True
                else:
                    self.log_result("API健康检查", False, "缺少关键功能")
                    return False
            else:
                self.log_result("API健康检查", False, f"HTTP {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.log_result("API健康检查", False, f"请求失败: {e}")
            return False

    def check_authentication(self) -> str:
        """检查用户认证功能"""
        try:
            login_data = {
                "email": "test@saascontrol.dev",
                "password": "TestPass123"
            }

            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                auth_data = response.json()
                if "access_token" in auth_data:
                    self.log_result("用户认证", True, f"用户: {auth_data['user']['email']}")
                    return auth_data["access_token"]
                else:
                    self.log_result("用户认证", False, "响应中缺少访问令牌")
                    return None
            else:
                self.log_result("用户认证", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_result("用户认证", False, f"认证失败: {e}")
            return None

    def check_data_persistence(self, auth_token: str) -> bool:
        """检查数据持久化功能"""
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}

            # 获取数据源列表
            response = requests.get(
                f"{self.base_url}/data/sources",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                sources_data = response.json()
                total_sources = sources_data.get("total", 0)
                self.log_result("数据持久化", True, f"数据源数量: {total_sources}")
                return True
            else:
                self.log_result("数据持久化", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("数据持久化", False, f"检查失败: {e}")
            return False

    def check_file_upload(self, auth_token: str) -> bool:
        """检查文件上传功能"""
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}

            # 创建测试文件
            test_content = "id,name,value\n1,test,100\n2,demo,200"
            files = {
                'file': ('test_verification.csv', test_content, 'text/csv')
            }

            response = requests.post(
                f"{self.base_url}/upload/file",
                files=files,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get("success"):
                    self.log_result("文件上传", True, f"文件ID: {upload_data['data_source']['id']}")
                    return True
                else:
                    self.log_result("文件上传", False, "上传响应显示失败")
                    return False
            else:
                self.log_result("文件上传", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("文件上传", False, f"上传失败: {e}")
            return False

    def check_frontend_files(self) -> bool:
        """检查前端文件结构"""
        try:
            frontend_path = "/home/user/studio/frontend"
            required_files = [
                "src/app/data-management/page.tsx",
                "src/lib/api/data-sources.ts",
                "package.json"
            ]

            missing_files = []
            for file_path in required_files:
                full_path = os.path.join(frontend_path, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)

            if not missing_files:
                self.log_result("前端文件", True, "所有关键文件存在")
                return True
            else:
                self.log_result("前端文件", False, f"缺少文件: {', '.join(missing_files)}")
                return False

        except Exception as e:
            self.log_result("前端文件", False, f"检查失败: {e}")
            return False

    def check_backend_files(self) -> bool:
        """检查后端文件结构"""
        try:
            backend_path = "/home/user/studio/backend/backend-pro1"
            required_files = [
                "unified_backend_fastapi.py",
                "shared/database.py",
                "init_database.py"
            ]

            missing_files = []
            for file_path in required_files:
                full_path = os.path.join(backend_path, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)

            if not missing_files:
                self.log_result("后端文件", True, "所有关键文件存在")
                return True
            else:
                self.log_result("后端文件", False, f"缺少文件: {', '.join(missing_files)}")
                return False

        except Exception as e:
            self.log_result("后端文件", False, f"检查失败: {e}")
            return False

    def run_verification(self):
        """运行完整的部署验证"""
        print("🔍 SaaS Control Deck 部署验证")
        print("="*50)

        # 文件结构检查
        self.check_frontend_files()
        self.check_backend_files()

        # 服务状态检查
        backend_running = self.check_backend_process()
        if not backend_running:
            print("\n⚠️  后端服务未运行，跳过API测试")
            print("启动后端服务命令:")
            print("cd /home/user/studio/backend/backend-pro1")
            print("source .venv/bin/activate")
            print("uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0")
        else:
            # API功能检查
            self.check_database_connection()
            self.check_api_health()

            # 认证和数据功能检查
            auth_token = self.check_authentication()
            if auth_token:
                self.check_data_persistence(auth_token)
                self.check_file_upload(auth_token)

        # 统计结果
        print("\n" + "="*50)
        print("📊 验证结果汇总:")

        passed_count = sum(1 for result in self.results if result["status"])
        total_count = len(self.results)

        print(f"✅ 通过: {passed_count}/{total_count}")

        # 显示失败的项目
        failed_results = [result for result in self.results if not result["status"]]
        if failed_results:
            print("\n❌ 失败项目:")
            for result in failed_results:
                print(f"   • {result['component']}: {result['message']}")

        # 总体状态
        if passed_count == total_count:
            print("\n🎉 所有验证通过！数据持久化升级成功完成")
            print("\n📋 下一步操作:")
            print("1. 测试前端数据管理页面: http://localhost:9000/data-management")
            print("2. 运行完整功能测试: ./quick_test.sh")
            print("3. 验证服务重启后数据保持")
        else:
            print(f"\n⚠️  {len(failed_results)} 个组件验证失败")
            print("请检查失败项目并修复后重新验证")

        return passed_count == total_count

def main():
    """主函数"""
    verifier = DeploymentVerifier()
    success = verifier.run_verification()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()