#!/usr/bin/env python3
"""
临时迁移状态验证器 - 仅用于根目录清理前的安全检查
验证所有重要测试脚本都已迁移到tests目录
"""
import os
import subprocess

# 定义根目录中需要验证的测试文件映射关系
FILE_MIGRATION_MAP = {
    # 健康检查类
    'quick_service_check.py': 'tests/backend/health/quick_health_check.py',
    'run_quick_health_check.py': 'tests/backend/health/comprehensive_health_check.py',
    'execute_health_check.py': 'tests/backend/health/health_check_executor.py',
    'direct_health_test.py': 'tests/backend/health/direct_health_test.py',

    # 迁移验证类
    'test_fastapi_migration.py': 'tests/backend/api/fastapi_migration_test.py',
    'studio_producer_validation.py': 'tests/backend/validation/producer_validation.py',
    'check_current_backend.py': 'tests/backend/validation/backend_status_check.py',

    # 迁移工具类
    'migrate_to_fastapi.py': 'tests/migration/fastapi_migration/migrate_to_fastapi.py',
    'migration_report.py': 'tests/migration/fastapi_migration/migration_reporter.py',
    'install_migration_deps.py': 'tests/migration/fastapi_migration/dependency_installer.py',
    'start_fastapi_backend.py': 'tests/migration/fastapi_migration/backend_starter.py',
}

def verify_migration_status():
    """验证迁移状态"""
    print("🔍 开始验证迁移状态...")

    verified_files = []
    missing_files = []

    for root_file, target_path in FILE_MIGRATION_MAP.items():
        root_path = f"/home/user/studio/{root_file}"
        target_full_path = f"/home/user/studio/{target_path}"

        # 检查根文件是否存在
        root_exists = os.path.exists(root_path)

        # 检查目标文件是否存在
        target_exists = os.path.exists(target_full_path)

        print(f"📁 {root_file}:")
        print(f"   根目录存在: {'✅' if root_exists else '❌'}")
        print(f"   目标目录存在: {'✅' if target_exists else '❌'}")

        if root_exists and target_exists:
            # 比较文件大小
            try:
                root_size = os.path.getsize(root_path)
                target_size = os.path.getsize(target_full_path)

                if abs(root_size - target_size) < 100:  # 允许小的差异（路径修改等）
                    print(f"   ✅ 迁移完成（大小相近: {root_size} vs {target_size}）")
                    verified_files.append(root_file)
                else:
                    print(f"   ⚠️  文件大小差异较大: {root_size} vs {target_size}")
                    missing_files.append(root_file)
            except Exception as e:
                print(f"   ❌ 大小检查失败: {e}")
                missing_files.append(root_file)
        elif root_exists and not target_exists:
            print(f"   ❌ 未迁移")
            missing_files.append(root_file)
        elif not root_exists and target_exists:
            print(f"   ✅ 已迁移（根文件已删除）")
            verified_files.append(root_file)
        else:
            print(f"   ❌ 两边都不存在")
            missing_files.append(root_file)

        print()

    print("📊 验证结果汇总:")
    print(f"   ✅ 已验证迁移: {len(verified_files)} 个文件")
    print(f"   ❌ 需要处理: {len(missing_files)} 个文件")

    if missing_files:
        print(f"\n⚠️ 需要手动处理的文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print(f"\n🎉 所有文件迁移验证成功！可以安全删除根目录文件")
        return True

def list_remaining_test_files():
    """列出根目录中剩余的测试相关文件"""
    print("\n🔍 扫描根目录剩余测试文件...")

    test_patterns = [
        'test_', '_test', 'check_', 'execute_', 'run_', 'quick_',
        'migration_', 'install_', 'studio_', 'direct_'
    ]

    remaining_files = []

    for file in os.listdir('/home/user/studio'):
        if file.endswith('.py'):
            for pattern in test_patterns:
                if pattern in file:
                    remaining_files.append(file)
                    break

    print(f"📋 发现 {len(remaining_files)} 个疑似测试文件:")
    for file in remaining_files:
        print(f"   - {file}")

    return remaining_files

if __name__ == "__main__":
    print("🚀 SaaS Control Deck 迁移状态验证器")
    print("=" * 50)

    # 验证迁移状态
    migration_ok = verify_migration_status()

    # 列出剩余文件
    remaining = list_remaining_test_files()

    print("\n" + "=" * 50)
    if migration_ok and len(remaining) <= len(FILE_MIGRATION_MAP):
        print("🎯 结论: 可以安全执行根目录清理")
    else:
        print("⚠️ 结论: 需要进一步检查后再执行清理")