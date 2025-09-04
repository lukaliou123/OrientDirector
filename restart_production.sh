#!/bin/bash

# OrientDirector 生产环境重启脚本

echo "🔄 重启 OrientDirector 生产环境服务"
echo "=================================="

# 停止服务
./stop_production.sh

# 等待服务完全停止
sleep 3

# 启动服务
./start_production.sh
