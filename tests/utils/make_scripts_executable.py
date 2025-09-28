#!/usr/bin/env python3
"""
快速脚本：设置所有shell脚本的可执行权限
"""

import os
import stat
from pathlib import Path

def make_executable():
    root_dir = Path("/home/user/studio")
    tests_dir = root_dir / "tests"
    
    # 查找所有.sh文件
    shell_scripts = list(tests_dir.rglob("*.sh"))
    
    print(f"找到 {len(shell_scripts)} 个shell脚本")
    
    for script in shell_scripts:
        try:
            # 设置可执行权限
            script.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print(f"✅ 已设置可执行权限: {script.relative_to(root_dir)}")
        except Exception as e:
            print(f"❌ 设置权限失败 {script}: {e}")

if __name__ == "__main__":
    make_executable()
