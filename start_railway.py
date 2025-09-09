#!/usr/bin/env python3
"""
Railway部署专用启动脚本
解决路径和端口配置问题
"""

import os
import sys
import uvicorn

def main():
    # 确保工作目录正确
    if not os.path.exists('backend/main.py'):
        # 如果在子目录中启动，切换到项目根目录
        while not os.path.exists('backend/main.py') and os.getcwd() != '/':
            os.chdir('..')
        
        if not os.path.exists('backend/main.py'):
            print("❌ 错误: 找不到backend/main.py文件")
            sys.exit(1)
    
    # 切换到backend目录
    os.chdir('backend')
    
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
