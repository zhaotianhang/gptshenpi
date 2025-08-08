#!/usr/bin/env python3
"""
财务审批系统启动脚本
"""

import os
import sys
import subprocess
import threading
import time

def run_backend():
    """运行后端服务"""
    print("启动后端服务...")
    os.system("python app.py")

def run_frontend():
    """运行前端服务"""
    print("启动前端服务...")
    os.chdir("frontend/my-vite-app")
    os.system("npm run dev")

def main():
    print("财务审批系统启动中...")
    
    # 检查依赖
    print("检查Python依赖...")
    os.system("pip install -r requirements.txt")
    
    print("检查前端依赖...")
    os.chdir("frontend/my-vite-app")
    os.system("npm install")
    os.chdir("../..")
    
    # 启动服务
    backend_thread = threading.Thread(target=run_backend)
    frontend_thread = threading.Thread(target=run_frontend)
    
    backend_thread.daemon = True
    frontend_thread.daemon = True
    
    backend_thread.start()
    time.sleep(2)  # 等待后端启动
    frontend_thread.start()
    
    print("服务启动完成!")
    print("后端服务: http://localhost:3000")
    print("前端服务: http://localhost:5173")
    print("管理后台: http://localhost:3000/admin")
    print("\n按 Ctrl+C 停止服务")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        sys.exit(0)

if __name__ == "__main__":
    main()
