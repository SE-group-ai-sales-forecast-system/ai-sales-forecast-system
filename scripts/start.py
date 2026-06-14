#!/usr/bin/env python3
"""
一键启动脚本
用法：python start.py
"""

import subprocess
import sys
import time

def main():
    print("=" * 50)
    print("  AI 电商销售预测系统")
    print("  一键启动中...")
    print("=" * 50)
    
    # 1. 安装依赖
    print("\n📦 安装依赖包...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
    
    # 2. 启动后端
    print("\n🚀 启动后端服务...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待后端启动
    time.sleep(3)
    print("   ✅ 后端已启动: http://localhost:8000")
    
    # 3. 启动前端
    print("\n🚀 启动前端服务...")
    print("   🌐 浏览器将自动打开: http://localhost:8501")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ])
    
    # 清理
    backend.terminate()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用！")
        sys.exit(0)