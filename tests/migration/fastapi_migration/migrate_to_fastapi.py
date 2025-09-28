#!/usr/bin/env python3
"""
/home/user/studio/tests/migration/fastapi_migration/migrate_to_fastapi.py
一键式FastAPI迁移脚本 - 从根目录迁移而来
自动停止旧服务并启动FastAPI服务
RELEVANT FILES: backend/backend-pro1/unified_backend_fastapi.py, tests/migration/fastapi_migration/backend_starter.py
"""

import subprocess
import signal
import psutil
import time
import sys
import os

def find_and_kill_process_by_port(port):
    """查找并杀死占用指定端口的进程"""
    print(f"🔍 检查端口 {port} 的占用情况...")

    killed_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 检查进程的连接
            connections = proc.connections()
            for conn in connections:
                if conn.laddr.port == port:
                    print(f"   找到占用端口的进程: PID={proc.info['pid']}, 名称={proc.info['name']}")
                    print(f"   命令行: {' '.join(proc.info['cmdline'][:3])}...")

                    # 尝试优雅地终止进程
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)  # 等待5秒
                        print(f"   ✅ 进程 {proc.info['pid']} 已优雅终止")
                        killed_processes.append(proc.info['pid'])
                    except psutil.TimeoutExpired:
                        # 如果优雅终止失败，强制杀死
                        proc.kill()
                        print(f"   ⚠️  强制终止进程 {proc.info['pid']}")
                        killed_processes.append(proc.info['pid'])
                    except Exception as e:
                        print(f"   ❌ 终止进程失败: {e}")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            continue

    if not killed_processes:
        print(f"   ℹ️  端口 {port} 当前未被占用")

    return killed_processes

def verify_port_free(port, max_retries=10):
    """验证端口是否已释放"""
    for i in range(max_retries):
        for proc in psutil.process_iter():
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == port:
                        print(f"   ⏳ 端口 {port} 仍被占用，等待... ({i+1}/{max_retries})")
                        time.sleep(1)
                        break
                else:
                    continue
                break
            except:
                continue
        else:
            print(f"   ✅ 端口 {port} 已释放")
            return True

    print(f"   ❌ 端口 {port} 在 {max_retries} 秒后仍被占用")
    return False

def start_fastapi_service():
    """启动FastAPI服务"""
    print("🚀 启动FastAPI服务...")

    # 检查FastAPI服务文件是否存在
    fastapi_path = "/home/user/studio/backend/backend-pro1/unified_backend_fastapi.py"

    if not os.path.exists(fastapi_path):
        print(f"❌ FastAPI服务文件不存在: {fastapi_path}")
        return False

    # 改变到正确的目录
    backend_dir = "/home/user/studio/backend/backend-pro1"
    original_dir = os.getcwd()

    try:
        os.chdir(backend_dir)
        print(f"   📂 切换到目录: {backend_dir}")

        # 使用uv启动FastAPI服务（优化版）
        print("   🔥 使用UV启动FastAPI统一后端服务...")
        print("   📍 服务地址: http://localhost:8000")
        print("   📆 API文档: http://localhost:8000/docs")
        print("   🔍 健康检查: http://localhost:8000/health")
        print("   👤 测试账号: test@saascontrol.dev / TestPass123")

        # 使用uv后台启动服务
        log_file_path = '/home/user/studio/tests/logs/fastapi_backend.log'
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        with open(log_file_path, 'w') as log_file:
            process = subprocess.Popen([
                "uv", "run", "uvicorn", 
                "unified_backend_fastapi:app", 
                "--reload", "--port", "8000", 
                "--host", "0.0.0.0"
            ], stdout=log_file, stderr=subprocess.STDOUT)

        print(f"   📊 FastAPI服务已启动，PID: {process.pid}")
        print(f"   📄 日志文件: {log_file_path}")

        # 等待服务启动
        print("   ⏳ 等待服务启动...")
        time.sleep(5)  # 增加等待时间确保服务完全启动

        return True

    except Exception as e:
        print(f"   ❌ 启动FastAPI服务失败: {e}")
        return False
    finally:
        os.chdir(original_dir)

def test_service_health():
    """测试服务健康状态"""
    print("🩺 测试FastAPI服务健康状态...")

    import requests

    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("   ✅ FastAPI服务健康检查通过")
            print(f"      服务名称: {health_data.get('service', 'N/A')}")
            print(f"      服务状态: {health_data.get('status', 'N/A')}")
            print(f"      功能列表: {', '.join(health_data.get('features', []))}")
            return True
        else:
            print(f"   ❌ 健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查连接失败: {e}")
        return False

def migrate_to_fastapi():
    """执行完整的FastAPI迁移"""
    print("🎯 SaaS Control Deck - FastAPI迁移执行器")
    print("=" * 60)
    print("将从 unified_backend_simple.py 迁移到 unified_backend_fastapi.py")
    print("=" * 60)

    success_steps = []

    # 第一步：停止现有服务
    print("\n📦 第一步：停止现有后端服务")
    print("-" * 40)
    killed_processes = find_and_kill_process_by_port(8000)
    if verify_port_free(8000):
        success_steps.append("停止现有服务")
        print("✅ 现有服务已成功停止")
    else:
        print("❌ 无法释放端口8000，迁移中止")
        return False

    # 第二步：启动FastAPI服务
    print("\n🚀 第二步：启动FastAPI服务")
    print("-" * 40)
    if start_fastapi_service():
        success_steps.append("启动FastAPI服务")
        print("✅ FastAPI服务启动成功")
    else:
        print("❌ FastAPI服务启动失败，迁移中止")
        return False

    # 第三步：健康检查
    print("\n🩺 第三步：验证服务健康状态")
    print("-" * 40)
    if test_service_health():
        success_steps.append("健康检查通过")
        print("✅ 服务健康检查通过")
    else:
        print("❌ 服务健康检查失败")
        return False

    # 迁移完成汇总
    print("\n🎉 FastAPI迁移完成汇总")
    print("=" * 60)
    print("✅ 迁移成功完成的步骤:")
    for i, step in enumerate(success_steps, 1):
        print(f"   {i}. {step}")

    print("\n📋 下一步操作建议:")
    print("   1. 测试前端功能: 访问 http://localhost:9000")
    print("   2. 验证API功能: python tests/backend/api/fastapi_migration_test.py")
    print("   3. 查看API文档: http://localhost:8000/docs")
    print("   4. 监控服务日志: tail -f tests/logs/fastapi_backend.log")

    print("\n🏆 FastAPI迁移成功！服务性能预期提升10-50倍")
    return True

if __name__ == "__main__":
    try:
        migrate_to_fastapi()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断迁移过程")
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
