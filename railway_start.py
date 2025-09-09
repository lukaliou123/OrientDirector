#!/usr/bin/env python3
"""极简Railway启动脚本"""
import os
import uvicorn

if __name__ == "__main__":
    # 从环境变量获取端口，Railway会设置这个
    port = int(os.environ.get('PORT', 8000))
    
    # 直接启动
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port
    )
