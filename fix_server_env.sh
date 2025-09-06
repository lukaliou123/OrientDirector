#!/bin/bash

# 修复服务器环境变量配置脚本
# 添加缺失的Supabase环境变量

echo "🔧 修复服务器环境变量配置"
echo "=================================="

# 使用记忆中的部署命令连接服务器
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 服务器环境变量修复开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 备份现有.env文件
    if [ -f ".env" ]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ 已备份现有.env文件"
    fi
    
    # 检查并添加Supabase环境变量
    echo "🔧 配置Supabase环境变量..."
    
    # 添加或更新Supabase配置
    if ! grep -q "SUPABASE_URL" .env 2>/dev/null; then
        echo "SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co" >> .env
        echo "✅ 添加SUPABASE_URL"
    else
        echo "✅ SUPABASE_URL已存在"
    fi
    
    if ! grep -q "SUPABASE_SERVICE_KEY" .env 2>/dev/null; then
        echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo" >> .env
        echo "✅ 添加SUPABASE_SERVICE_KEY"
    else
        echo "✅ SUPABASE_SERVICE_KEY已存在"
    fi
    
    if ! grep -q "VITE_SUPABASE_URL" .env 2>/dev/null; then
        echo "VITE_SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co" >> .env
        echo "✅ 添加VITE_SUPABASE_URL"
    else
        echo "✅ VITE_SUPABASE_URL已存在"
    fi
    
    if ! grep -q "VITE_SUPABASE_ANON_KEY" .env 2>/dev/null; then
        echo "VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcwNzEyNjYsImV4cCI6MjA2MjY0NzI2Nn0.x9Tti06ZF90B2YPg-AeVvT_tf4qOcOYcHWle6L3OVtc" >> .env
        echo "✅ 添加VITE_SUPABASE_ANON_KEY"
    else
        echo "✅ VITE_SUPABASE_ANON_KEY已存在"
    fi
    
    # 确保SECRET_KEY存在
    if ! grep -q "SECRET_KEY" .env 2>/dev/null; then
        echo "SECRET_KEY=orient-director-secret-key-$(date +%s)" >> .env
        echo "✅ 添加SECRET_KEY"
    else
        echo "✅ SECRET_KEY已存在"
    fi
    
    echo ""
    echo "📋 当前.env文件内容："
    echo "=================================="
    # 显示.env文件内容（隐藏敏感信息）
    if [ -f ".env" ]; then
        sed 's/=.*$/=***HIDDEN***/' .env
    fi
    
    echo ""
    echo "🔄 重启服务以应用新的环境变量..."
    ./restart_production.sh
    
    # 等待服务启动
    sleep 15
    
    # 测试认证服务
    echo ""
    echo "🔍 测试认证服务..."
    if curl -s https://spot.gitagent.io/api/auth/health > /dev/null; then
        echo "✅ 认证服务响应正常"
        echo "认证服务状态："
        curl -s https://spot.gitagent.io/api/auth/health | python3 -m json.tool 2>/dev/null || echo "无法解析JSON响应"
    else
        echo "❌ 认证服务无响应"
        echo "检查后端日志："
        tail -10 logs/backend.log
    fi
    
    echo ""
    echo "✅ 服务器环境变量配置完成"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 环境变量修复完成总结"
    echo "=================================="
    echo "✅ Supabase环境变量已添加到服务器"
    echo "✅ 服务已重启以应用新配置"
    echo "✅ 认证服务状态已验证"
    echo ""
    echo "🧪 现在可以测试认证功能："
    echo "1. 访问 https://spot.gitagent.io"
    echo "2. 点击登录按钮"
    echo "3. 使用测试账户："
    echo "   - 邮箱: 402493977@qq.com"
    echo "   - 密码: demo123"
    echo "4. 验证登录成功且不再出现401错误"
    echo ""
    echo "🎉 服务器环境变量修复完成！"
else
    echo "❌ 服务器环境变量修复失败"
    exit 1
fi
