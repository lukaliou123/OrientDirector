#!/bin/bash

# 服务器部署脚本 - spot.gitagent.io
# 用于在服务器上部署更新后的代码

echo "🚀 开始部署 spot.gitagent.io 服务器更新"
echo "================================================"

# 检查是否在服务器环境
if [ ! -d "/home/ec2-user" ]; then
    echo "⚠️  警告：此脚本应在服务器环境中运行"
    echo "本地测试模式，跳过某些服务器特定操作"
    LOCAL_MODE=true
else
    LOCAL_MODE=false
fi

# 1. 停止现有服务
echo "🛑 1. 停止现有服务..."
if [ "$LOCAL_MODE" = false ]; then
    sudo systemctl stop orientdirector-backend 2>/dev/null || echo "后端服务未运行"
    sudo systemctl stop orientdirector-frontend 2>/dev/null || echo "前端服务未运行"
else
    # 本地模式：查找并停止相关进程
    pkill -f "start_backend.py" 2>/dev/null || echo "本地后端进程未运行"
    pkill -f "start_frontend.py" 2>/dev/null || echo "本地前端进程未运行"
    pkill -f "netlify dev" 2>/dev/null || echo "Netlify dev进程未运行"
fi

# 2. 备份当前配置
echo "💾 2. 备份当前配置..."
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ .env文件已备份"
else
    echo "⚠️  .env文件不存在，跳过备份"
fi

# 3. 更新代码
echo "📥 3. 更新代码..."
git fetch origin
git checkout main
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ 代码更新成功"
else
    echo "❌ 代码更新失败"
    exit 1
fi

# 4. 安装/更新依赖
echo "📦 4. 安装/更新依赖..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装成功"
else
    echo "❌ Python依赖安装失败"
    exit 1
fi

# 5. 更新nginx配置
echo "🌐 5. 更新nginx配置..."
if [ "$LOCAL_MODE" = false ]; then
    # 服务器模式
    sudo cp nginx-doro.conf /etc/nginx/sites-available/spot.gitagent.io
    
    # 删除旧的doro配置
    sudo rm -f /etc/nginx/sites-enabled/doro.gitagent.io
    
    # 启用新的spot配置
    sudo ln -sf /etc/nginx/sites-available/spot.gitagent.io /etc/nginx/sites-enabled/
    
    # 测试nginx配置
    sudo nginx -t
    if [ $? -eq 0 ]; then
        echo "✅ Nginx配置测试通过"
        sudo systemctl reload nginx
        echo "✅ Nginx配置已重载"
    else
        echo "❌ Nginx配置测试失败"
        exit 1
    fi
else
    echo "⚠️  本地模式，跳过nginx配置更新"
fi

# 6. 更新SSL证书（如果需要）
echo "🔒 6. 检查SSL证书..."
if [ "$LOCAL_MODE" = false ]; then
    if command -v certbot >/dev/null 2>&1; then
        echo "正在为 spot.gitagent.io 申请SSL证书..."
        sudo certbot --nginx -d spot.gitagent.io --non-interactive --agree-tos --email admin@gitagent.io --redirect
        if [ $? -eq 0 ]; then
            echo "✅ SSL证书配置成功"
        else
            echo "⚠️  SSL证书配置失败，请手动检查"
        fi
    else
        echo "⚠️  certbot未安装，跳过SSL证书配置"
    fi
else
    echo "⚠️  本地模式，跳过SSL证书配置"
fi

# 7. 检查环境变量
echo "🔧 7. 检查环境变量..."
if [ -f ".env" ]; then
    if grep -q "SUPABASE_URL" .env && grep -q "SUPABASE_SERVICE_KEY" .env; then
        echo "✅ Supabase配置存在"
    else
        echo "⚠️  警告：.env文件缺少Supabase配置"
        echo "请确保包含以下配置："
        echo "SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co"
        echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo"
        echo "VITE_SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co"
        echo "VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcwNzEyNjYsImV4cCI6MjA2MjY0NzI2Nn0.x9Tti06ZF90B2YPg-AeVvT_tf4qOcOYcHWle6L3OVtc"
    fi
else
    echo "❌ .env文件不存在，请创建并配置"
    exit 1
fi

# 8. 清理旧的日志文件
echo "🧹 8. 清理旧日志..."
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    echo "✅ 清理了7天前的日志文件"
fi

# 9. 启动服务
echo "▶️  9. 启动服务..."
if [ "$LOCAL_MODE" = false ]; then
    # 服务器模式
    sudo systemctl start orientdirector-backend
    sudo systemctl start orientdirector-frontend
    
    # 启用开机自启
    sudo systemctl enable orientdirector-backend
    sudo systemctl enable orientdirector-frontend
    
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet orientdirector-backend; then
        echo "✅ 后端服务启动成功"
    else
        echo "❌ 后端服务启动失败"
        sudo systemctl status orientdirector-backend
    fi
    
    if systemctl is-active --quiet orientdirector-frontend; then
        echo "✅ 前端服务启动成功"
    else
        echo "❌ 前端服务启动失败"
        sudo systemctl status orientdirector-frontend
    fi
else
    # 本地模式
    echo "本地模式：请手动启动服务"
    echo "后端: python3 start_backend.py &"
    echo "前端: npx netlify dev --port 8888"
fi

# 10. 验证服务
echo "🔍 10. 验证服务..."
sleep 3

if [ "$LOCAL_MODE" = false ]; then
    # 检查HTTPS服务
    if curl -s https://spot.gitagent.io/api/auth/health > /dev/null; then
        echo "✅ HTTPS API服务正常"
    else
        echo "⚠️  HTTPS API服务无响应"
    fi
    
    if curl -s https://spot.gitagent.io > /dev/null; then
        echo "✅ HTTPS前端服务正常"
    else
        echo "⚠️  HTTPS前端服务无响应"
    fi
else
    # 检查本地服务
    if curl -s http://localhost:8001/api/auth/health > /dev/null; then
        echo "✅ 本地API服务正常"
    else
        echo "⚠️  本地API服务无响应"
    fi
fi

# 11. 显示服务信息
echo ""
echo "🎯 部署完成总结"
echo "================================================"
echo "✅ 代码已更新到最新版本"
echo "✅ 域名已从 doro.gitagent.io 更新为 spot.gitagent.io"
echo "✅ Supabase认证系统已集成"
echo "✅ 测试账号已清理"
echo ""

if [ "$LOCAL_MODE" = false ]; then
    echo "🌐 服务地址："
    echo "- 主站: https://spot.gitagent.io"
    echo "- API: https://spot.gitagent.io/api"
    echo "- API文档: https://spot.gitagent.io/docs"
    echo ""
    echo "📊 服务状态："
    echo "- 后端服务: $(systemctl is-active orientdirector-backend)"
    echo "- 前端服务: $(systemctl is-active orientdirector-frontend)"
    echo "- Nginx: $(systemctl is-active nginx)"
else
    echo "🏠 本地服务："
    echo "- 主站: http://localhost:8888"
    echo "- API: http://localhost:8001/api"
    echo ""
    echo "启动命令："
    echo "- 后端: python3 start_backend.py &"
    echo "- 前端: npx netlify dev --port 8888"
fi

echo ""
echo "📋 重要提醒："
echo "- 所有测试账号已删除，现在使用Supabase数据库进行用户管理"
echo "- 用户可以通过注册页面创建新账号"
echo "- 认证系统支持Supabase + 后端API双重机制"
echo "- 多语言支持(16种语言)保持完整"

echo ""
echo "🎉 部署完成！"
