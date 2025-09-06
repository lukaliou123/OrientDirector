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
from pathlib import Path

PORT = 3002

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

def start_server():
    """启动前端服务器"""
    global PORT
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            with ReuseAddrTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
                print(f"🧭 方向探索派对 - 前端服务")
                print("=" * 50)
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
                return  # 成功启动，退出函数
                
        except OSError as e:
            if (e.errno == 48 or e.errno == 98) and attempt < max_retries - 1:  # Address already in use
                print(f"⚠️ 端口 {PORT} 被占用，尝试端口 {PORT + 1}...")
                PORT += 1
                time.sleep(1)
                continue
            else:
                # 最后一次尝试失败
                if e.errno == 48 or e.errno == 98:
                    print(f"❌ 错误: 所有端口都被占用 (尝试了端口 {3001} 到 {PORT})")
                    print("请手动释放端口或重启系统后重试")
                else:
                    print(f"❌ 错误: {e}")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n前端服务已停止")
            return
        except Exception as e:
            print(f"❌ 错误: 服务启动失败 - {e}")
            sys.exit(1)
    
    # 如果循环结束还没有成功启动
    print("❌ 错误: 无法找到可用端口启动服务")
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