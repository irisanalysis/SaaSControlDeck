#!/usr/bin/env python3
"""
/home/user/studio/tests/backend/health/quick_health_check.py
简单的FastAPI服务状态检查 - 从根目录迁移而来
快速检查后端服务健康状态
RELEVANT FILES: backend/backend-pro1/minimal_health_check.py, tests/backend/validation/producer_validation.py
"""

import socket
import urllib.request
import json

def quick_check():
    """快速检查服务状态"""
    print("🔍 快速检查FastAPI服务状态...")

    # 检查端口
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()

        if result == 0:
            print("✅ 端叠8000开放")

            # 检查健康端点
            try:
                req = urllib.request.Request("http://localhost:8000/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    content = response.read().decode('utf-8')
                    print(f"✅ /health响应: {response.status}")

                    # 尝试解析健康数据
                    try:
                        health_data = json.loads(content)
                        print(f"   服务: {health_data.get('service', '未知')}")
                        print(f"   状态: {health_data.get('status', '未知')}")

                        print("🎉 FastAPI服务运行正常！")
                        return True
                    except:
                        print("⚠️ 响应不是JSON格式")
                        return False

            except Exception as e:
                print(f"❌ 健康端点访问失败: {e}")
                return False

        else:
            print("❌ 端叠8000未开放，服务可能未启动")
            print("💡 启动命令:")
            print("   cd /home/user/studio/backend/backend-pro1")
            print("   uv shell")
            print("   uv run uvicorn unified_backend_fastapi:app --reload --port 8000")
            return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    quick_check()
