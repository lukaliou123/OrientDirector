#!/usr/bin/env python3
"""
简单的后端启动脚本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 修改导入路径
import main

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main.app, host="0.0.0.0", port=8000)