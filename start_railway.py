#!/usr/bin/env python3
"""
Railway部署专用启动脚本
解决路径和端口配置问题
"""

import os
import sys
import uvicorn

def main():
    print(f"🔍 启动检查 - 当前目录: {os.getcwd()}")
    print(f"🔍 目录内容: {os.listdir('.')}")
    
    # 确保工作目录正确
    if not os.path.exists('backend/main.py'):
        print("⚠️ backend/main.py不在当前目录，尝试查找...")
        
        # 检查是否在Docker的WORKDIR(/app)中
        if os.getcwd() == '/app' and os.path.exists('./backend/main.py'):
            print("✅ 在Docker工作目录/app中找到backend/main.py")
        else:
            # 尝试在上级目录查找
            found = False
            for _ in range(3):  # 最多向上查找3级目录
                parent_dir = os.path.dirname(os.getcwd())
                if parent_dir == os.getcwd():  # 到达根目录
                    break
                os.chdir(parent_dir)
                print(f"🔍 检查目录: {os.getcwd()}")
                if os.path.exists('backend/main.py'):
                    print(f"✅ 在 {os.getcwd()} 中找到backend/main.py")
                    found = True
                    break
            
            if not found:
                print("❌ 错误: 找不到backend/main.py文件")
                print(f"   最终目录: {os.getcwd()}")
                print(f"   目录内容: {os.listdir('.')}")
                sys.exit(1)
    
    # 切换到backend目录
    backend_path = os.path.join(os.getcwd(), 'backend')
    print(f"🔄 切换到backend目录: {backend_path}")
    os.chdir(backend_path)
    
    # 获取端口号
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Railway部署启动")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   端口: {port}")
    print(f"   主机: 0.0.0.0")
    print("-" * 50)
    
    # 启动uvicorn服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
