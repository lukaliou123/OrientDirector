#!/usr/bin/env python3
"""
Railway部署启动脚本 - 简化版
"""

import os
import sys
import uvicorn

def main():
    # 添加backend目录到Python路径
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_path)
    
    # 获取端口号
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Railway部署启动")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   Backend路径: {backend_path}")
    print(f"   端口: {port}")
    print(f"   Python路径: {sys.path[:2]}")
    print("-" * 50)
    
    # 从backend模块导入app
    from backend.main import app
    
    # 启动uvicorn服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
