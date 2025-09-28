#!/usr/bin/env python3
"""
/home/user/studio/tests/backend/validation/producer_validation.py
Studio Producer - FastAPI迁移验证控制台 - 从根目录迁移而来
集成多种检查方法，提供全面的迁移验证结果
RELEVANT FILES: backend/backend-pro1/minimal_health_check.py, backend/backend-pro1/unified_backend_fastapi.py
"""

import socket
import urllib.request
import json
import subprocess
import sys
import os
from datetime import datetime

class StudioProducerValidator:
    """
Studio Producer验证器 - 协调所有验证活动
"""

    def __init__(self):
        self.results = {}
        self.base_url = "http://localhost:8000"

    def check_port_accessibility(self):
        """检查端叠8000可访问性"""
        print("🔍 步骤1: 检查端叠8000可达性...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()

            if result == 0:
                print("✅ 端叠8000已开放")
                self.results['port_accessible'] = True
                return True
            else:
                print("❌ 端叠8000不可达")
                self.results['port_accessible'] = False
                return False
        except Exception as e:
            print(f"❌ 端口检查失败: {e}")
            self.results['port_accessible'] = False
            return False

    def check_health_endpoint(self):
        """检查健康端点"""
        print("🔍 步骤2: 测试健康检查端点...")
        try:
            req = urllib.request.Request(f"{self.base_url}/health")
            req.add_header('User-Agent', 'Studio-Producer-Validator/1.0')

            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')

                print(f"✅ /health 响应正常 ({response.status})")

                try:
                    health_data = json.loads(content)
                    print(f"   服务: {health_data.get('service', 'Unknown')}")
                    print(f"   状态: {health_data.get('status', 'Unknown')}")
                    print(f"   端口: {health_data.get('port', 'Unknown')}")
                    print(f"   运行时间: {health_data.get('uptime', 0):.1f}秒")

                    features = health_data.get('features', [])
                    if features:
                        print(f"   功能: {', '.join(features)}")

                    self.results['health_endpoint'] = {
                        'accessible': True,
                        'data': health_data,
                        'status_code': response.status
                    }
                    return True

                except json.JSONDecodeError:
                    print(f"⚠️ 非JSON响应: {content[:100]}...")
                    self.results['health_endpoint'] = {
                        'accessible': True,
                        'data': None,
                        'status_code': response.status,
                        'content': content[:200]
                    }
                    return False

        except Exception as e:
            print(f"❌ 健康端点检查失败: {e}")
            self.results['health_endpoint'] = {
                'accessible': False,
                'error': str(e)
            }
            return False

    def check_basic_endpoints(self):
        """检查基本端点"""
        print("🔍 步骤3: 测试基本API端点...")
        endpoints = [
            ('/', 'Root Endpoint'),
            ('/docs', 'API Documentation'),
            ('/openapi.json', 'OpenAPI Schema')
        ]

        endpoint_results = {}
        success_count = 0

        for path, name in endpoints:
            try:
                req = urllib.request.Request(f"{self.base_url}{path}")
                with urllib.request.urlopen(req, timeout=5) as response:
                    status = response.status
                    if status in [200, 201]:
                        print(f"   ✅ {name}: {status}")
                        endpoint_results[path] = {'status': status, 'success': True}
                        success_count += 1
                    else:
                        print(f"   ⚠️ {name}: {status}")
                        endpoint_results[path] = {'status': status, 'success': False}
            except Exception as e:
                print(f"   ❌ {name}: {str(e)}")
                endpoint_results[path] = {'error': str(e), 'success': False}

        self.results['basic_endpoints'] = {
            'results': endpoint_results,
            'success_count': success_count,
            'total_count': len(endpoints)
        }

        return success_count >= len(endpoints) * 0.7  # 70%成功率

    def run_existing_health_check(self):
        """运行现有的健康检查脚本"""
        print("🔍 步骤4: 运行已有的健康检查脚本...")
        try:
            backend_dir = "/home/user/studio/backend/backend-pro1"
            original_dir = os.getcwd()

            os.chdir(backend_dir)

            # 运行minimal_health_check.py
            result = subprocess.run(
                [sys.executable, "minimal_health_check.py"],
                capture_output=True,
                text=True,
                timeout=15
            )

            os.chdir(original_dir)

            if result.returncode == 0:
                print("✅ 现有健康检查脚本执行成功")
                self.results['existing_health_check'] = {
                    'success': True,
                    'output': result.stdout[-500:],  # 最后500字符
                    'exit_code': result.returncode
                }
                return True
            else:
                print(f"❌ 现有健康检查脚本失败 (退出码: {result.returncode})")
                self.results['existing_health_check'] = {
                    'success': False,
                    'output': result.stderr[-500:] if result.stderr else result.stdout[-500:],
                    'exit_code': result.returncode
                }
                return False

        except Exception as e:
            print(f"❌ 运行健康检查脚本时出错: {e}")
            self.results['existing_health_check'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def generate_validation_summary(self):
        """生成验证总结"""
        print("\n" + "=" * 60)
        print("📊 Studio Producer - FastAPI迁移验证总结")
        print("=" * 60)

        # 计算总体成功率
        checks = [
            ('端口可达性', self.results.get('port_accessible', False)),
            ('健康端点', self.results.get('health_endpoint', {}).get('accessible', False)),
            ('基本端点', self.results.get('basic_endpoints', {}).get('success_count', 0) > 0),
            ('现有脚本', self.results.get('existing_health_check', {}).get('success', False))
        ]

        passed_checks = sum(1 for _, success in checks if success)
        total_checks = len(checks)
        success_rate = (passed_checks / total_checks) * 100

        print(f"🎯 验证结果概览:")
        for check_name, success in checks:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   {check_name}: {status}")

        print(f"\n📈 总体成功率: {success_rate:.1f}% ({passed_checks}/{total_checks})")

        # 判断迁移状态
        if success_rate >= 75:
            print("🎉 验证结论: ✅ FastAPI迁移成功")
            print("   - 服务正常运行")
            print("   - 主要端点可访问")
            print("   - 可以进行进一步的API功能验证")
            migration_success = True
        elif success_rate >= 50:
            print("⚠️ 验证结论: 🔧 FastAPI迁移部分成功")
            print("   - 服务基本可用")
            print("   - 需要解决部分问题")
            print("   - 建议进行修复后再做完整验证")
            migration_success = False
        else:
            print("❌ 验证结论: 🚨 FastAPI迁移存在重大问题")
            print("   - 服务可能未正常启动")
            print("   - 需要检查配置和启动流程")
            print("   - 必须解决基础问题后再验证")
            migration_success = False

        # 保存验证结果
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_summary': {
                'success_rate_percent': success_rate,
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'migration_success': migration_success
            },
            'detailed_results': self.results
        }

        try:
            report_path = '/home/user/studio/tests/reports/producer_validation_report.json'
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细验证报告已保存: tests/reports/producer_validation_report.json")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")

        return migration_success

    def run_validation(self):
        """运行完整验证流程"""
        print("🎭 Studio Producer - FastAPI迁移验证开始")
        print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 执行所有验证步骤
        steps = [
            self.check_port_accessibility,
            self.check_health_endpoint,
            self.check_basic_endpoints,
            self.run_existing_health_check
        ]

        for step in steps:
            try:
                step()
                print()  # 空行分隔
            except Exception as e:
                print(f"❌ 执行验证步骤时出错: {e}")
                print()

        # 生成总结
        return self.generate_validation_summary()

def main():
    """主函数"""
    validator = StudioProducerValidator()
    success = validator.run_validation()

    if success:
        print("\n🎯 下一步建议:")
        print("   - 运行 tests/backend/api/fastapi_migration_test.py 进行完整API验证")
        print("   - 执行 tests/migration/fastapi_migration/migration_validator.py 进行迁移对比测试")
        print("   - 协调各专家agents进行深度验证")
    else:
        print("\n🔧 下一步建议:")
        print("   - 检查FastAPI服务启动状态")
        print("   - 查看服务日志排查问题")
        print("   - 确认unified_backend_fastapi.py配置")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
