#!/bin/bash

# 直接复制修改后的文件到服务器并重启服务

echo "📁 复制修改文件到服务器并重启服务"
echo "=================================="

# 1. 复制修改后的文件到服务器
echo "📤 复制文件到服务器..."

# 复制backend/auth.py
scp -i /Users/a1/work/productmindai.pem backend/auth.py ec2-user@54.89.140.250:/home/ec2-user/OrientDirector/backend/auth.py

if [ $? -eq 0 ]; then
    echo "✅ backend/auth.py 复制成功"
else
    echo "❌ backend/auth.py 复制失败"
    exit 1
fi

# 复制start_production.sh
scp -i /Users/a1/work/productmindai.pem start_production.sh ec2-user@54.89.140.250:/home/ec2-user/OrientDirector/start_production.sh

if [ $? -eq 0 ]; then
    echo "✅ start_production.sh 复制成功"
else
    echo "❌ start_production.sh 复制失败"
    exit 1
fi

# 复制stop_production.sh
scp -i /Users/a1/work/productmindai.pem stop_production.sh ec2-user@54.89.140.250:/home/ec2-user/OrientDirector/stop_production.sh

if [ $? -eq 0 ]; then
    echo "✅ stop_production.sh 复制成功"
else
    echo "❌ stop_production.sh 复制失败"
    exit 1
fi

# 2. 在服务器上执行操作
echo "🔧 在服务器上执行重启操作..."

ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 服务器端操作开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 给脚本添加执行权限
    chmod +x start_production.sh stop_production.sh restart_production.sh
    
    # 修复环境变量名称问题
    echo "🔧 修复环境变量名称..."
    
    # 检查并修复SUPABASE_SERVICE_KEY环境变量
    if grep -q "SUPABASE_SERVICE_ROLE_KEY" .env; then
        # 将SUPABASE_SERVICE_ROLE_KEY重命名为SUPABASE_SERVICE_KEY
        sed -i 's/SUPABASE_SERVICE_ROLE_KEY=/SUPABASE_SERVICE_KEY=/' .env
        echo "✅ 已将SUPABASE_SERVICE_ROLE_KEY重命名为SUPABASE_SERVICE_KEY"
    fi
    
    # 确保所有必要的Supabase环境变量都存在
    if ! grep -q "^SUPABASE_SERVICE_KEY=" .env; then
        echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo" >> .env
        echo "✅ 添加SUPABASE_SERVICE_KEY环境变量"
    fi
    
    echo "📋 检查关键环境变量..."
    echo "SUPABASE_URL: $(grep SUPABASE_URL .env | head -1 | cut -d'=' -f1)"
    echo "SUPABASE_SERVICE_KEY: $(grep SUPABASE_SERVICE_KEY .env | head -1 | cut -d'=' -f1)"
    
    # 激活conda环境
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate orient
    
    # 重启服务
    echo "🔄 重启服务..."
    ./restart_production.sh
    
    # 等待服务启动
    sleep 15
    
    # 测试认证服务
    echo ""
    echo "🔍 测试认证服务..."
    if curl -s https://spot.gitagent.io/api/auth/health > /dev/null; then
        echo "✅ 认证服务响应正常"
        echo "认证服务状态："
        curl -s https://spot.gitagent.io/api/auth/health | python3 -m json.tool 2>/dev/null || echo "响应获取成功但JSON解析失败"
    else
        echo "❌ 认证服务无响应"
        echo "检查后端日志："
        tail -15 logs/backend.log
    fi
    
    echo ""
    echo "✅ 服务器文件更新和重启完成"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 文件部署和服务重启完成"
    echo "=================================="
    echo "✅ 已复制修改后的文件到服务器"
    echo "✅ 已修复环境变量名称问题"
    echo "✅ 服务已重启"
    echo ""
    echo "🧪 现在可以测试认证功能："
    echo "1. 访问 https://spot.gitagent.io"
    echo "2. 点击登录按钮"
    echo "3. 使用测试账户："
    echo "   - 邮箱: 402493977@qq.com"
    echo "   - 密码: demo123"
    echo "4. 验证登录成功且不再出现401错误"
    echo ""
    echo "📋 调试信息："
    echo "- 认证健康检查: https://spot.gitagent.io/api/auth/health"
    echo "- API文档: https://spot.gitagent.io/docs"
    echo "- 主站: https://spot.gitagent.io"
    echo ""
    echo "🎉 部署完成！"
else
    echo "❌ 服务器操作失败"
    exit 1
fi
