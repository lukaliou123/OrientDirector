#!/bin/bash

# OrientDirector 生产环境停止脚本

echo "🛑 停止 OrientDirector 生产环境服务"
echo "=================================="

# 读取PID文件并停止服务
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm -f logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f logs/frontend.pid
fi

# 强制停止相关进程
#echo "强制停止相关进程..."
#pkill -f "uvicorn.*main:app" || true
#pkill -f "python3.*start_frontend.py" || true
#pkill -f "python3.*start_backend.py" || true

echo "✅ 所有服务已停止"
