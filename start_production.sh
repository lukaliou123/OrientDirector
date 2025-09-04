#!/bin/bash

# OrientDirector 生产环境启动脚本
# 用于在AWS服务器上后台启动前端和后端服务

echo "🚀 启动 OrientDirector 生产环境服务"
echo "=================================="

# 设置工作目录
cd /home/ec2-user/OrientDirector

# 检查Python版本
python3 --version

# 安装依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 停止可能正在运行的服务
echo "🛑 停止现有服务..."
pkill -f "uvicorn.*main:app" || true
pkill -f "python3.*start_frontend.py" || true
pkill -f "python3.*start_backend.py" || true

# 等待端口释放
sleep 3

# 启动后端服务（后台运行）
echo "🔧 启动后端服务 (端口 8001)..."
cd backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务PID: $BACKEND_PID"
cd ..

# 等待后端启动
sleep 5

# 启动前端服务（后台运行）
echo "🌐 启动前端服务 (端口 3001)..."
nohup python3 start_frontend.py > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务PID: $FRONTEND_PID"

# 保存PID到文件
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo "✅ 服务启动完成！"
echo "后端服务: http://localhost:8001"
echo "前端服务: http://localhost:3001"
echo "API文档: http://localhost:8001/docs"
echo ""
echo "查看日志:"
echo "  后端: tail -f logs/backend.log"
echo "  前端: tail -f logs/frontend.log"
echo ""
echo "停止服务: ./stop_production.sh"
