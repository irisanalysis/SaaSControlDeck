#!/usr/bin/env python3
"""
/home/user/studio/tests/migration/fastapi_migration/migration_validator.py
FastAPI迁移验证器 - 从根目录迁移而来
专门用于验证FastAPI迁移的完整性和正确性
RELEVANT FILES: backend/backend-pro1/unified_backend_fastapi.py, tests/migration/fastapi_migration/migration_reporter.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime

class FastAPIMigrationValidator:
    """
FastAPI迁移验证器
"""
    
    def __init__(self):
        self.migration_results = {}
        self.backend_dir = "/home/user/studio/backend/backend-pro1"
        
    def validate_dependencies(self):
        """验证依赖安装"""
        print("🔍 验证FastAPI迁移依赖...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'pydantic',
            'python-multipart',
            'python-jose[cryptography]'
        ]
        
        try:
            os.chdir(self.backend_dir)
            
            # 检查uv环境
            result = subprocess.run(
                ['uv', 'pip', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                installed_packages = result.stdout.lower()
                missing_packages = []
                
                for package in required_packages:
                    package_name = package.split('[')[0]  # 处理fastapi[standard]格式
                    if package_name.lower() not in installed_packages:
                        missing_packages.append(package)
                
                if not missing_packages:
                    print("✅ 所有必需依赖已安装")
                    self.migration_results['dependencies'] = {
                        'status': 'success',
                        'missing': []
                    }
                    return True
                else:
                    print(f"❌ 缺少依赖: {', '.join(missing_packages)}")
                    self.migration_results['dependencies'] = {
                        'status': 'failed',
                        'missing': missing_packages
                    }
                    return False
            else:
                print("❌ 无法检查uv依赖列表")
                self.migration_results['dependencies'] = {
                    'status': 'error',
                    'error': result.stderr
                }
                return False
                
        except Exception as e:
            print(f"❌ 依赖验证失败: {e}")
            self.migration_results['dependencies'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def validate_configuration_files(self):
        """验证配置文件"""
        print("🔍 验证FastAPI配置文件...")
        
        required_files = [
            'unified_backend_fastapi.py',
            'pyproject.toml'
        ]
        
        file_status = {}
        all_exist = True
        
        for filename in required_files:
            filepath = os.path.join(self.backend_dir, filename)
            if os.path.exists(filepath):
                print(f"✅ {filename} 存在")
                file_status[filename] = True
            else:
                print(f"❌ {filename} 不存在")
                file_status[filename] = False
                all_exist = False
        
        self.migration_results['configuration_files'] = {
            'status': 'success' if all_exist else 'failed',
            'files': file_status
        }
        
        return all_exist
    
    def validate_fastapi_startup(self):
        """验证FastAPI启动"""
        print("🔍 验证FastAPI应用启动...")
        
        try:
            os.chdir(self.backend_dir)
            
            # 尝试启动FastAPI应用（但不保持运行）
            result = subprocess.run(
                ['uv', 'run', 'python', '-c', 
                 'import unified_backend_fastapi; print("FastAPI app imported successfully")'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("✅ FastAPI应用可以正常导入")
                self.migration_results['fastapi_startup'] = {
                    'status': 'success',
                    'output': result.stdout
                }
                return True
            else:
                print(f"❌ FastAPI应用导入失败")
                print(f"   错误输出: {result.stderr}")
                self.migration_results['fastapi_startup'] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'stdout': result.stdout
                }
                return False
                
        except Exception as e:
            print(f"❌ FastAPI启动验证失败: {e}")
            self.migration_results['fastapi_startup'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def generate_migration_report(self):
        """生成迁移报告"""
        print("\n" + "=" * 50)
        print("📄 FastAPI迁移验证报告")
        print("=" * 50)
        
        # 计算成功率
        checks = [
            ('依赖安装', self.migration_results.get('dependencies', {}).get('status') == 'success'),
            ('配置文件', self.migration_results.get('configuration_files', {}).get('status') == 'success'),
            ('FastAPI启动', self.migration_results.get('fastapi_startup', {}).get('status') == 'success')
        ]
        
        passed_checks = sum(1 for _, success in checks if success)
        total_checks = len(checks)
        success_rate = (passed_checks / total_checks) * 100
        
        print(f"🎯 迁移验证结果:")
        for check_name, success in checks:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   {check_name}: {status}")
        
        print(f"\n📈 迁移成功率: {success_rate:.1f}% ({passed_checks}/{total_checks})")
        
        # 生成详细报告
        detailed_report = {
            'timestamp': datetime.now().isoformat(),
            'migration_validation': {
                'success_rate_percent': success_rate,
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'overall_success': success_rate >= 80
            },
            'detailed_results': self.migration_results
        }
        
        # 保存报告
        try:
            report_path = '/home/user/studio/tests/reports/migration_validation_report.json'
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: tests/reports/migration_validation_report.json")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")
        
        return success_rate >= 80
    
    def run_full_validation(self):
        """运行完整验证流程"""
        print("🚀 开始 FastAPI 迁移完整性验证")
        print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 执行所有验证步骤
        validation_steps = [
            self.validate_dependencies,
            self.validate_configuration_files,
            self.validate_fastapi_startup
        ]
        
        for step in validation_steps:
            try:
                step()
                print()  # 空行分隔
            except Exception as e:
                print(f"❌ 执行验证步骤时出错: {e}")
                print()
        
        # 生成总结报告
        return self.generate_migration_report()

def main():
    """主函数"""
    validator = FastAPIMigrationValidator()
    success = validator.run_full_validation()
    
    if success:
        print("\n✨ FastAPI迁移验证成功！")
        print("🎯 建议下一步:")
        print("   - 运行 tests/backend/validation/producer_validation.py")
        print("   - 执行 tests/backend/api/fastapi_migration_test.py")
    else:
        print("\n⚠️ FastAPI迁移验证发现问题")
        print("🔧 建议修复措施:")
        print("   - 检查并安装缺少的依赖")
        print("   - 验证配置文件的存在和正确性")
        print("   - 检查FastAPI应用的语法和结构")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
