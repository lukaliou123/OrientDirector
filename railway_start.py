#!/usr/bin/env python3
"""极简Railway启动脚本"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # 确保Python能找到backend模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 从环境变量获取端口，Railway会设置这个
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting app on port {port}")
    print(f"Python path: {sys.path[0]}")
    print(f"Working directory: {os.getcwd()}")
    
    # 直接启动
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port
    )
