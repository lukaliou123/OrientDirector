#!/usr/bin/env python3
"""最简单的启动脚本 - 直接运行main.py"""
import os
import sys
import subprocess

# 获取端口
port = os.environ.get('PORT', '8000')

# 使用subprocess直接运行uvicorn命令
cmd = [
    sys.executable, "-m", "uvicorn",
    "main:app",
    "--host", "0.0.0.0",
    "--port", port,
    "--app-dir", "backend"
]

print(f"Starting with command: {' '.join(cmd)}")
subprocess.run(cmd)
