#!/usr/bin/env python3
"""
/home/user/studio/tests/utils/rollback_migration.py
测试脚本迁移回滚工具
提供一键式恢复到原始根目录结构的功能
RELEVANT FILES: tests/migration_index.md, backend/CLAUDE.md
"""

import os
import shutil
import json
import sys
from datetime import datetime
from pathlib import Path

class MigrationRollback:
    """
迁移回滚管理器
"""
    
    def __init__(self):
        self.root_dir = Path("/home/user/studio")
        self.tests_dir = self.root_dir / "tests"
        self.backup_dir = self.root_dir / ".migration_backup"
        self.rollback_log = []
        
        # 文件映射表 - 从 tests 目录回滚到根目录
        self.rollback_mapping = {
            # FastAPI迁移验证类
            "tests/backend/api/fastapi_migration_test.py": "test_fastapi_migration.py",
            "tests/backend/validation/producer_validation.py": "studio_producer_validation.py",
            "tests/migration/fastapi_migration/migrate_to_fastapi.py": "migrate_to_fastapi.py",
            "tests/migration/fastapi_migration/migration_reporter.py": "migration_report.py",
            "tests/migration/fastapi_migration/dependency_installer.py": "install_migration_deps.py",
            "tests/migration/fastapi_migration/backend_starter.py": "start_fastapi_backend.py",
            
            # 健康检查类
            "tests/backend/health/quick_health_check.py": "quick_service_check.py",
            "tests/backend/health/comprehensive_health_check.py": "run_quick_health_check.py",
            "tests/backend/health/health_check_executor.py": "execute_health_check.py",
            "tests/backend/health/direct_health_test.py": "direct_health_test.py",
            
            # 系统验证类
            "tests/backend/validation/backend_status_check.py": "check_current_backend.py",
            "tests/reports/producer_validation_report.json": "studio_producer_validation_report.json",
            
            # Docker构建验证类 - 这些是综合版，不需要回滚
            # "tests/infrastructure/docker/build_tests/docker_build_validator.sh": "", # 新建的，不回滚
            "tests/infrastructure/docker/build_tests/simple_docker_build.sh": "simple-docker-build.sh",
            "tests/infrastructure/docker/build_tests/minimal_docker_build.sh": "minimal-docker-build.sh",
            "tests/infrastructure/docker/build_tests/backend_only_build.sh": "build-backend-only.sh",
            "tests/infrastructure/deployment/dockerhub_deployment.sh": "deploy-from-dockerhub.sh",
            "tests/utils/run_all_tests.sh": "run-tests.sh",
            
            # 历史后端文件 - 保持在根目录（可选）
            "tests/migration/legacy_backend/simple_backend.py": "simple_backend.py",
            "tests/migration/legacy_backend/simple_auth.py": "simple_auth.py",
            "tests/migration/legacy_backend/auth_server.py": "auth_server.py",
        }
    
    def create_rollback_backup(self):
        """创建回滚备份"""
        print("💾 创建回滚备份...")
        
        if self.backup_dir.exists():
            # 如果已存在备份，先删除
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # 备份 tests 目录
        if self.tests_dir.exists():
            backup_tests_dir = self.backup_dir / "tests"
            shutil.copytree(self.tests_dir, backup_tests_dir)
            print(f"✅ 已备份 tests 目录到: {backup_tests_dir}")
        
        # 记录备份信息
        backup_info = {
            "backup_time": datetime.now().isoformat(),
            "backed_up_directories": ["tests"],
            "total_files": len(list(self.tests_dir.rglob("*"))) if self.tests_dir.exists() else 0
        }
        
        with open(self.backup_dir / "backup_info.json", "w", encoding="utf-8") as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 备份信息已保存到: {self.backup_dir / 'backup_info.json'}")
    
    def rollback_files(self):
        """执行文件回滚操作"""
        print("🔄 开始执行文件回滚...")
        
        rollback_count = 0
        error_count = 0
        
        for tests_path, root_path in self.rollback_mapping.items():
            source_file = self.root_dir / tests_path
            target_file = self.root_dir / root_path
            
            try:
                if source_file.exists():
                    # 如果根目录中已存在同名文件，先备份
                    if target_file.exists():
                        backup_file = self.root_dir / f"{root_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.move(str(target_file), str(backup_file))
                        self.rollback_log.append(f"💾 备份现有文件: {root_path} -> {backup_file.name}")
                    
                    # 复制文件到根目录
                    shutil.copy2(str(source_file), str(target_file))
                    rollback_count += 1
                    
                    print(f"✅ 回滚: {tests_path} -> {root_path}")
                    self.rollback_log.append(f"✅ 成功回滚: {tests_path} -> {root_path}")
                    
                else:
                    print(f"⚠️  源文件不存在: {tests_path}")
                    self.rollback_log.append(f"⚠️  跳过（源文件不存在）: {tests_path}")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"❌ 回滚失败: {tests_path} -> {root_path}, 错误: {e}"
                print(error_msg)
                self.rollback_log.append(error_msg)
        
        print(f"\n📊 回滚结果统计:")
        print(f"   成功回滚: {rollback_count} 个文件")
        print(f"   回滚失败: {error_count} 个文件")
        
        return rollback_count, error_count
    
    def remove_tests_directory(self):
        """删除 tests 目录（可选）"""
        if self.tests_dir.exists():
            print(f"\n❓ 是否要删除 tests 目录？ (y/N): ", end="")
            response = input().strip().lower()
            
            if response in ['y', 'yes', '是']:
                try:
                    shutil.rmtree(self.tests_dir)
                    print(f"✅ 已删除 tests 目录")
                    self.rollback_log.append(f"✅ 已删除 tests 目录: {self.tests_dir}")
                    return True
                except Exception as e:
                    error_msg = f"❌ 删除 tests 目录失败: {e}"
                    print(error_msg)
                    self.rollback_log.append(error_msg)
                    return False
            else:
                print("ℹ️  保留 tests 目录")
                self.rollback_log.append("ℹ️  用户选择保留 tests 目录")
                return False
        else:
            print("ℹ️  tests 目录不存在，无需删除")
            return True
    
    def save_rollback_log(self):
        """保存回滚日志"""
        rollback_report = {
            "rollback_time": datetime.now().isoformat(),
            "total_operations": len(self.rollback_log),
            "rollback_log": self.rollback_log,
            "rollback_mapping_used": self.rollback_mapping
        }
        
        log_file = self.root_dir / "migration_rollback.log"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(rollback_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 回滚日志已保存到: {log_file}")
    
    def run_full_rollback(self, create_backup=True):
        """执行完整的回滚操作"""
        print("🔄 SaaS Control Deck - 测试脚本迁移回滚工具")
        print("=" * 60)
        print(f"⏰ 回滚时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 第1步：创建备份（可选）
        if create_backup:
            self.create_rollback_backup()
            print()
        
        # 第2步：执行文件回滚
        rollback_count, error_count = self.rollback_files()
        
        # 第3步：选择性删除 tests 目录
        tests_dir_removed = self.remove_tests_directory()
        
        # 第4步：保存回滚日志
        self.save_rollback_log()
        
        # 总结
        print("\n" + "=" * 60)
        print("🎉 回滚操作完成！")
        print("=" * 60)
        
        if rollback_count > 0 and error_count == 0:
            print("✅ 所有文件都已成功回滚到根目录")
            print("✅ 项目结构已恢复到迁移前状态")
            
            if tests_dir_removed:
                print("✅ tests 目录已清理")
            else:
                print("ℹ️  tests 目录已保留（可手动删除）")
                
            print("\n✨ 下一步建议:")
            print("   - 验证现有测试脚本是否正常工作")
            print("   - 检查根目录文件是否完整")
            print("   - 考虑重新设计更简单的项目结构")
            return True
            
        else:
            if error_count > 0:
                print(f"⚠️  有 {error_count} 个文件回滚失败")
            if rollback_count == 0:
                print("ℹ️  没有找到可回滚的文件")
                
            print("\n🔧 建议措施:")
            print("   - 检查回滚日志中的错误信息")
            print("   - 手动验证文件路径和权限")
            print("   - 如有必要，手动调整文件位置")
            return False

def main():
    """主函数"""
    rollback_manager = MigrationRollback()
    
    # 检查是否存在 tests 目录
    if not rollback_manager.tests_dir.exists():
        print("⚠️  未找到 tests 目录，可能没有进行过迁移操作")
        print("ℹ️  如果你需要恢复特定文件，请手动调整脚本中的映射表")
        return 1
    
    # 确认回滚操作
    print("⚠️  警告：此操作将把 tests 目录中的文件回滚到根目录！")
    print("❓ 是否继续执行回滚操作？ (y/N): ", end="")
    response = input().strip().lower()
    
    if response not in ['y', 'yes', '是']:
        print("ℹ️  回滚操作已取消")
        return 0
    
    # 执行回滚
    success = rollback_manager.run_full_rollback()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
