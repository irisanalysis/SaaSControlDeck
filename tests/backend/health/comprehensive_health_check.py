#!/usr/bin/env python3
"""
/home/user/studio/tests/backend/health/comprehensive_health_check.py
Studio Producer - FastAPI服务健康检查协调脚本 - 从根目录迁移而来
执行快速健康检查并分析结果，为进一步验证提供基础数据
RELEVANT FILES: backend/backend-pro1/quick_health_check.py, tests/backend/health/quick_health_check.py
"""

import subprocess
import sys
import os
import json
import urllib.request
from datetime import datetime

def check_service_running():
    """检查FastAPI服务是否已经在运行"""
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                return True
    except:
        pass
    return False

def main():
    """
Studio Producer协调健康检查流程
"""
    print("🎭 Studio Producer - FastAPI迁移验证开始")
    print("🔍 步骤1: 快速健康检查验证服务状态")
    print("=" * 60)

    # 检查服务是否运行
    print("🔍 检查FastAPI服务运行状态...")
    if check_service_running():
        print("✅ FastAPI服务正在运行，开始健康检查")
    else:
        print("⚠️  FastAPI服务未运行")
        print("💡 请先启动服务：")
        print("   1. cd /home/user/studio/backend/backend-pro1")
        print("   2. uv shell")
        print("   3. uv run uvicorn unified_backend_fastapi:app --reload --port 8000")
        print()
        print("🚀 或使用迁移启动脚本：")
        print("   python tests/migration/fastapi_migration/migrate_to_fastapi.py")
        return False

    # 切换到backend-pro1目录
    backend_dir = "/home/user/studio/backend/backend-pro1"
    os.chdir(backend_dir)

    print(f"📂 工作目录: {backend_dir}")
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 执行快速健康检查
        print("🚀 执行快速健康检查...")
        result = subprocess.run(
            [sys.executable, "quick_health_check.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 显示输出结果
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️ 警告信息:")
            print(result.stderr)
        
        # 分析检查结果
        if result.returncode == 0:
            print("✅ 快速健康检查完成 - 服务状态正常")
            
            # 读取生成的报告文件
            try:
                with open("quick_health_report.json", "r", encoding="utf-8") as f:
                    report = json.load(f)
                
                print("\n📊 Studio Producer分析结果:")
                print(f"   🎯 整体健康状态: {'✅ 正常' if report['overall_health'] else '❌ 异常'}")
                print(f"   📈 成功率: {report['success_rate_percent']:.1f}%")
                print(f"   ⚡ 平均响应时间: {report['avg_response_time_ms']:.1f}ms")
                print(f"   🚨 关键失败: {report['critical_failures']}")
                
                # 基于结果决定下一步行动
                if report['overall_health'] and report['success_rate_percent'] >= 80:
                    print("\n🎉 验证结论: FastAPI服务运行正常，可以进行完整API验证")
                    
                    # 保存综合报告到tests/reports目录
                    report_dir = "/home/user/studio/tests/reports"
                    os.makedirs(report_dir, exist_ok=True)
                    
                    comprehensive_report = {
                        "timestamp": datetime.now().isoformat(),
                        "health_check_type": "comprehensive",
                        "service_status": "healthy",
                        "detailed_health_data": report,
                        "next_recommended_actions": [
                            "tests/backend/api/fastapi_migration_test.py",
                            "tests/backend/validation/producer_validation.py",
                            "tests/migration/fastapi_migration/migration_validator.py"
                        ]
                    }
                    
                    report_file = os.path.join(report_dir, "comprehensive_health_report.json")
                    with open(report_file, "w", encoding="utf-8") as f:
                        json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
                    
                    print(f"📄 综合报告已保存: {report_file}")
                    return True
                else:
                    print("\n⚠️ 验证结论: 服务存在问题，需要先解决基础问题")
                    return False
                    
            except FileNotFoundError:
                print("⚠️ 无法找到健康检查报告文件")
                return result.returncode == 0
            except Exception as e:
                print(f"⚠️ 解析健康检查报告时出错: {e}")
                return result.returncode == 0
        else:
            print(f"❌ 快速健康检查失败 (退出码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 健康检查超时 (30秒)")
        return False
    except Exception as e:
        print(f"❌ 执行健康检查时发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 下一步: 可以执行完整的API验证测试")
        print("   - tests/backend/api/fastapi_migration_test.py (迁移测试)")
        print("   - tests/backend/validation/producer_validation.py (专业验证)")
        print("   - tests/migration/fastapi_migration/migration_validator.py (迁移验证)")
    else:
        print("\n🔧 下一步: 需要启动FastAPI服务")
        print("   - 使用 tests/migration/fastapi_migration/migrate_to_fastapi.py")
        print("   - 或手动启动: uv run uvicorn unified_backend_fastapi:app --reload --port 8000")

    sys.exit(0 if success else 1)
