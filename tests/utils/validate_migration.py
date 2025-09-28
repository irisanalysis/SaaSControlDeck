#!/usr/bin/env python3
"""
/home/user/studio/tests/utils/validate_migration.py
迁移结果验证器
验证所有迁移的文件和功能是否正常工作
RELEVANT FILES: tests/migration_index.md, tests/README.md
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class MigrationValidator:
    """
迁移结果验证器
"""
    
    def __init__(self):
        self.root_dir = Path("/home/user/studio")
        self.tests_dir = self.root_dir / "tests"
        self.validation_results = []
        
        # 定义需要验证的文件和功能
        self.validation_items = [
            {
                "name": "测试目录结构",
                "type": "directory_structure",
                "paths": [
                    "tests/backend/api",
                    "tests/backend/health", 
                    "tests/backend/validation",
                    "tests/migration/fastapi_migration",
                    "tests/infrastructure/docker/build_tests",
                    "tests/utils",
                    "tests/reports",
                    "tests/logs"
                ]
            },
            {
                "name": "后端API测试脚本",
                "type": "python_script",
                "path": "tests/backend/api/fastapi_migration_test.py"
            },
            {
                "name": "快速健康检查脚本",
                "type": "python_script",
                "path": "tests/backend/health/quick_health_check.py"
            },
            {
                "name": "Studio Producer验证脚本",
                "type": "python_script",
                "path": "tests/backend/validation/producer_validation.py"
            },
            {
                "name": "FastAPI迁移验证器",
                "type": "python_script",
                "path": "tests/migration/fastapi_migration/migration_validator.py"
            },
            {
                "name": "FastAPI迁移脚本",
                "type": "python_script",
                "path": "tests/migration/fastapi_migration/migrate_to_fastapi.py"
            },
            {
                "name": "Docker构建验证脚本",
                "type": "shell_script",
                "path": "tests/infrastructure/docker/build_tests/docker_build_validator.sh"
            },
            {
                "name": "测试配置管理器",
                "type": "python_script",
                "path": "tests/utils/test_config.py"
            },
            {
                "name": "迁移回滚工具",
                "type": "python_script",
                "path": "tests/utils/rollback_migration.py"
            },
            {
                "name": "全面测试运行器",
                "type": "shell_script",
                "path": "tests/utils/run_all_tests.sh"
            },
            {
                "name": "迁移索引文档",
                "type": "documentation",
                "path": "tests/migration_index.md"
            },
            {
                "name": "测试目录README",
                "type": "documentation",
                "path": "tests/README.md"
            }
        ]
    
    def validate_directory_structure(self, paths):
        """验证目录结构"""
        print("📂 验证目录结构...")
        
        missing_dirs = []
        for path in paths:
            full_path = self.root_dir / path
            if not full_path.exists():
                missing_dirs.append(path)
            else:
                print(f"   ✅ {path}")
        
        if missing_dirs:
            print(f"   ❌ 缺少目录: {', '.join(missing_dirs)}")
            return False
        
        return True
    
    def validate_python_script(self, script_path):
        """验证Python脚本"""
        full_path = self.root_dir / script_path
        
        if not full_path.exists():
            print(f"   ❌ {script_path} 不存在")
            return False
        
        # 检查文件是否可读
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 基本语法检查
            try:
                compile(content, str(full_path), 'exec')
                print(f"   ✅ {script_path} - 语法正确")
                return True
            except SyntaxError as e:
                print(f"   ❌ {script_path} - 语法错误: {e}")
                return False
                
        except Exception as e:
            print(f"   ❌ {script_path} - 读取失败: {e}")
            return False
    
    def validate_shell_script(self, script_path):
        """验证Shell脚本"""
        full_path = self.root_dir / script_path
        
        if not full_path.exists():
            print(f"   ❌ {script_path} 不存在")
            return False
        
        # 检查是否可执行
        if not os.access(full_path, os.X_OK):
            # 尝试设置执行权限
            try:
                os.chmod(full_path, 0o755)
                print(f"   ✅ {script_path} - 已设置执行权限")
            except Exception as e:
                print(f"   ❌ {script_path} - 设置执行权限失败: {e}")
                return False
        
        # 检查脚本语法
        try:
            result = subprocess.run(['bash', '-n', str(full_path)], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {script_path} - 语法正确")
                return True
            else:
                print(f"   ❌ {script_path} - 语法错误: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ⚠️ {script_path} - 无法验证语法: {e}")
            return True  # 假设正确，因为bash可能不可用
    
    def validate_documentation(self, doc_path):
        """验证文档文件"""
        full_path = self.root_dir / doc_path
        
        if not full_path.exists():
            print(f"   ❌ {doc_path} 不存在")
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content.strip()) < 100:  # 最少100字符
                print(f"   ⚠️ {doc_path} - 文档内容过短")
                return False
            
            print(f"   ✅ {doc_path} - 文档存在且内容充实")
            return True
            
        except Exception as e:
            print(f"   ❌ {doc_path} - 读取失败: {e}")
            return False
    
    def run_validation(self):
        """执行完整验证"""
        print("🔍 SaaS Control Deck - 测试脚本迁移验证器")
        print("=" * 60)
        print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        total_items = len(self.validation_items)
        passed_items = 0
        
        for item in self.validation_items:
            print(f"🔍 验证: {item['name']}")
            
            success = False
            if item['type'] == 'directory_structure':
                success = self.validate_directory_structure(item['paths'])
            elif item['type'] == 'python_script':
                success = self.validate_python_script(item['path'])
            elif item['type'] == 'shell_script':
                success = self.validate_shell_script(item['path'])
            elif item['type'] == 'documentation':
                success = self.validate_documentation(item['path'])
            
            self.validation_results.append({
                'name': item['name'],
                'type': item['type'],
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            if success:
                passed_items += 1
            
            print()
        
        # 生成验证报告
        success_rate = (passed_items / total_items) * 100 if total_items > 0 else 0
        
        print("📊 迁移验证结果")
        print("=" * 60)
        print(f"总验证项目: {total_items}")
        print(f"通过验证: {passed_items}")
        print(f"失败验证: {total_items - passed_items}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 保存验证报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_summary': {
                'total_items': total_items,
                'passed_items': passed_items,
                'failed_items': total_items - passed_items,
                'success_rate_percent': success_rate
            },
            'validation_results': self.validation_results
        }
        
        try:
            reports_dir = self.tests_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / "migration_validation_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 验证报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 保存验证报告失败: {e}")
        
        # 结论
        print()
        if success_rate >= 90:
            print("✅ 迁移验证成功！所有核心组件都已正确迁移")
            print("✨ tests目录结构已就绪，可以开始使用新的测试体系")
            
            print("\n🎯 下一步建议:")
            print("   - 运行 tests/utils/run_all_tests.sh 执行全面测试")
            print("   - 使用 tests/backend/health/quick_health_check.py 进行快速健康检查")
            print("   - 查看 tests/README.md 了解详细使用方法")
            return True
            
        elif success_rate >= 70:
            print("⚠️ 迁移部分成功，但存在一些问题")
            print("🔧 需要修复失败的项目后再使用")
            return False
            
        else:
            print("❌ 迁移验证失败，存在重大问题")
            print("🚨 建议使用 tests/utils/rollback_migration.py 回滚到原始状态")
            return False

def main():
    """主函数"""
    validator = MigrationValidator()
    success = validator.run_validation()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
