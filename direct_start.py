#!/usr/bin/env python3
"""直接启动脚本 - 不使用模块导入"""
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# 切换到backend目录
os.chdir(backend_dir)

# 导入并启动
import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting app on port {port} from {os.getcwd()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
