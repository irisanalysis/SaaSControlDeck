import subprocess
import sys

# 运行健康检查脚本
try:
    result = subprocess.run([sys.executable, "minimal_health_check.py"],
                          capture_output=True, text=True, cwd="/home/user/studio/backend/backend-pro1")

    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn Code: {result.returncode}")

except Exception as e:
    print(f"Error running script: {e}")