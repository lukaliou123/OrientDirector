#!/usr/bin/env python3
"""
方向探索派对前端服务启动脚本
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import sys
import subprocess
import signal
import os
from pathlib import Path

PORT = 3001

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，添加CORS支持"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

class ReuseAddrTCPServer(socketserver.TCPServer):
    """支持端口重用的TCP服务器"""
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=False)
        self.socket.setsockopt(socketserver.socket.SOL_SOCKET, socketserver.socket.SO_REUSEADDR, 1)
        if bind_and_activate:
            self.server_bind()
            self.server_activate()

def kill_process_on_port(port):
    """杀死占用指定端口的进程"""
    try:
        # 查找占用端口的进程
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
            
            # 等待进程完全终止
            time.sleep(2)
                            
    except FileNotFoundError:
        print("⚠️ lsof 命令不可用，无法自动清理端口")
    except Exception as e:
        print(f"⚠️ 清理端口时出错: {e}")

def start_server():
    """启动前端服务器"""
    print("🧭 方向探索派对 - 前端服务")
    print("=" * 50)
    
    # 检查并清理端口3001
    print(f"🔍 检查端口 {PORT} 占用情况...")
    kill_process_on_port(PORT)
    
    try:
        with ReuseAddrTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✓ 服务地址: http://localhost:{PORT}")
            print(f"✓ 在浏览器中打开应用...")
            print("按 Ctrl+C 停止服务")
            print("-" * 50)
            
            # 延迟打开浏览器
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{PORT}')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
                
    except OSError as e:
        if e.errno == 48 or e.errno == 98:  # Address already in use
            print(f"❌ 错误: 端口 {PORT} 仍被占用")
            print("请手动释放端口或重启系统后重试")
        else:
            print(f"❌ 错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✅ 前端服务已停止")
        return
    except Exception as e:
        print(f"❌ 错误: 服务启动失败 - {e}")
        sys.exit(1)

def main():
    """主函数"""
    # 检查必要文件是否存在
    required_files = ['index.html', 'styles.css', 'app.js']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ 错误: 缺少必要文件: {', '.join(missing_files)}")
        sys.exit(1)
    
    start_server()

if __name__ == "__main__":
    main()