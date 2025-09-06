#!/usr/bin/env python3
"""
方向探索派对 - 统一启动脚本
同时启动前端(3001)和后端(8001)服务
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def kill_process_on_port(port):
    """杀死占用指定端口的进程"""
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✓ 已终止占用端口 {port} 的进程 (PID: {pid})")
                        time.sleep(1)
                    except (ProcessLookupError, ValueError):
                        pass
            time.sleep(2)
                            
    except FileNotFoundError:
        print("⚠️ lsof 命令不可用，无法自动清理端口")
    except Exception as e:
        print(f"⚠️ 清理端口时出错: {e}")

def main():
    """主函数"""
    print("🧭 方向探索派对 - 统一启动")
    print("=" * 60)
    
    # 清理端口
    print("🔍 清理端口占用...")
    kill_process_on_port(3001)  # 前端端口
    kill_process_on_port(8001)  # 后端端口
    
    # 启动后端
    print("\n🚀 启动后端服务 (端口 8001)...")
    backend_process = subprocess.Popen([
        sys.executable, 'start_backend.py'
    ])
    
    # 等待后端启动
    time.sleep(3)
    
    # 启动前端
    print("\n🌐 启动前端服务 (端口 3001)...")
    frontend_process = subprocess.Popen([
        sys.executable, 'start_frontend.py'
    ])
    
    print("\n✅ 服务启动完成!")
    print("📍 前端地址: http://localhost:3001")
    print("📍 后端地址: http://localhost:8001")
    print("📝 后端日志: logs/backend.log")
    print("\n按 Ctrl+C 停止所有服务")
    print("=" * 60)
    
    try:
        # 等待进程
        while True:
            # 检查进程是否还在运行
            backend_running = backend_process.poll() is None
            frontend_running = frontend_process.poll() is None
            
            if not backend_running and not frontend_running:
                print("所有服务已停止")
                break
            elif not backend_running:
                print("⚠️ 后端服务已停止")
                frontend_process.terminate()
                break
            elif not frontend_running:
                print("⚠️ 前端服务已停止")
                backend_process.terminate()
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 正在停止所有服务...")
        
        # 优雅停止
        backend_process.terminate()
        frontend_process.terminate()
        
        # 等待进程结束
        try:
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("⚠️ 强制终止进程...")
            backend_process.kill()
            frontend_process.kill()
        
        print("✅ 所有服务已停止")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
