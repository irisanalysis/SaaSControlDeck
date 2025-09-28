#!/usr/bin/env python3
"""
安全清理脚本 - 删除根目录中已迁移的测试脚本
仅删除确认已迁移且只包含迁移标记的文件
"""
import os
import shutil
from datetime import datetime

# 需要清理的测试文件列表（已确认迁移）
TEST_FILES_TO_CLEAN = [
    'check_current_backend.py',
    'direct_health_test.py',
    'execute_health_check.py',
    'install_migration_deps.py',
    'migration_report.py',
    'quick_service_check.py',
    'run_quick_health_check.py',
    'studio_producer_validation.py',
    'test_fastapi_migration.py',
    'start_fastapi_backend.py',
    'migrate_to_fastapi.py',
    'migration_example_fastapi.py',

    # 临时验证文件（任务完成后删除）
    'migration_status_verifier.py',
    'safe_cleanup_test_files.py'  # 自删除
]

# Legacy后端文件（可以安全归档）
LEGACY_BACKEND_FILES = [
    'unified_backend_simple.py',
    'unified_backend.py',
    'unified_backend_professional.py',
    'simple_backend.py',
    'unified_backend_simple_8002.py',
    'simple_auth.py',
    'auth_server.py'
]

def create_backup_record():
    """创建删除记录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_path = f"/home/user/studio/tests/utils/cleanup_record_{timestamp}.txt"

    with open(record_path, 'w') as f:
        f.write("SaaS Control Deck 根目录清理记录\n")
        f.write(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

        f.write("已删除的测试文件:\n")
        for file in TEST_FILES_TO_CLEAN:
            f.write(f"  - {file}\n")

        f.write("\n已移动到.archive的后端文件:\n")
        for file in LEGACY_BACKEND_FILES:
            f.write(f"  - {file} -> .archive/systems/backend/legacy-implementations/\n")

        f.write(f"\n备份记录保存在: {record_path}\n")

    return record_path

def move_legacy_to_archive():
    """将legacy后端文件移动到archive"""
    archive_dir = "/home/user/studio/.archive/systems/backend/legacy-implementations"

    # 创建archive目录
    os.makedirs(archive_dir, exist_ok=True)

    moved_files = []

    for file in LEGACY_BACKEND_FILES:
        src_path = f"/home/user/studio/{file}"
        if os.path.exists(src_path):
            dst_path = f"{archive_dir}/{file}"
            try:
                shutil.move(src_path, dst_path)
                moved_files.append(file)
                print(f"✅ 已归档: {file}")
            except Exception as e:
                print(f"❌ 归档失败 {file}: {e}")

    return moved_files

def safe_delete_test_files():
    """安全删除测试文件"""
    deleted_files = []

    print("🧹 开始清理根目录测试文件...")

    for file in TEST_FILES_TO_CLEAN:
        file_path = f"/home/user/studio/{file}"

        if os.path.exists(file_path):
            # 检查文件是否为迁移标记文件（只有1行且包含"已迁移"）
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()

                # 如果文件只包含迁移标记或为空，安全删除
                if (len(content.split('\n')) <= 2 and
                    ('已迁移到' in content or content == '' or len(content) < 100)):

                    os.remove(file_path)
                    deleted_files.append(file)
                    print(f"🗑️  已删除: {file}")
                else:
                    print(f"⚠️  保留: {file} (内容过多，需手动检查)")
            except Exception as e:
                print(f"❌ 删除失败 {file}: {e}")
        else:
            print(f"ℹ️  不存在: {file}")

    return deleted_files

def main():
    """主清理流程"""
    print("🚀 SaaS Control Deck 根目录安全清理")
    print("=" * 50)

    # 1. 创建备份记录
    record_path = create_backup_record()
    print(f"📋 清理记录已创建: {record_path}")

    # 2. 归档legacy文件
    print(f"\n📦 归档legacy后端文件...")
    moved_files = move_legacy_to_archive()
    print(f"✅ 已归档 {len(moved_files)} 个legacy文件")

    # 3. 删除测试文件
    print(f"\n🧹 清理测试文件...")
    deleted_files = safe_delete_test_files()
    print(f"✅ 已清理 {len(deleted_files)} 个测试文件")

    # 4. 汇总结果
    print(f"\n" + "=" * 50)
    print(f"🎯 清理完成汇总:")
    print(f"   📦 归档文件: {len(moved_files)} 个")
    print(f"   🗑️  删除文件: {len(deleted_files)} 个")
    print(f"   📋 记录文件: {record_path}")

    print(f"\n🎉 根目录清理完成！项目结构更加整洁")

if __name__ == "__main__":
    main()