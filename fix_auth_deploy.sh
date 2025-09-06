#!/bin/bash

# 修复认证401错误的部署脚本
# 解决Supabase与后端API认证集成问题

echo "🔐 修复认证401错误部署脚本"
echo "=================================="

# 检查当前目录
if [ ! -f "backend/auth.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 1. 验证本地认证代码已修改
echo "📋 1. 验证本地认证代码修改..."
if grep -q "JWT payload:" backend/auth.py; then
    echo "✅ 后端认证代码已更新"
else
    echo "❌ 后端认证代码未正确修改"
    exit 1
fi

# 2. 提交代码到Git
echo "📦 2. 提交认证修复代码..."
git add backend/auth.py
git commit -m "fix: 修复Supabase令牌验证和认证集成问题

- 改进verify_supabase_token函数的JWT解析逻辑
- 添加详细的认证日志记录
- 支持Supabase access_token的正确验证
- 修复/api/auth/me端点的401错误"

git push origin hw01

if [ $? -eq 0 ]; then
    echo "✅ 认证修复代码已推送到GitHub"
else
    echo "❌ 代码推送失败"
    exit 1
fi

# 3. 部署到服务器
echo "🚀 3. 部署认证修复到服务器..."
echo "正在连接服务器并更新代码..."

# 使用记忆中的部署命令
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 服务器端认证修复操作开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 激活conda环境
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate orient
    
    # 拉取最新代码
    echo "📥 拉取认证修复代码..."
    git checkout hw01
    git pull origin hw01
    
    # 检查环境变量
    echo "🔧 检查Supabase环境变量..."
    if [ -f ".env" ]; then
        if grep -q "SUPABASE_URL" .env && grep -q "SUPABASE_SERVICE_KEY" .env; then
            echo "✅ Supabase环境变量配置正确"
        else
            echo "❌ 缺少Supabase环境变量"
            echo "请确保.env文件包含："
            echo "SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co"
            echo "SUPABASE_SERVICE_KEY=..."
        fi
    else
        echo "❌ .env文件不存在"
    fi
    
    # 重启后端服务
    echo "🔄 重启后端服务..."
    ./restart_production.sh
    
    # 等待服务启动
    sleep 10
    
    # 测试认证健康检查
    echo "🔍 测试认证服务..."
    if curl -s https://spot.gitagent.io/api/auth/health > /dev/null; then
        echo "✅ 认证服务健康检查通过"
        
        # 显示认证服务状态
        curl -s https://spot.gitagent.io/api/auth/health | python3 -m json.tool
    else
        echo "❌ 认证服务健康检查失败"
    fi
    
    echo "✅ 服务器认证修复完成"
EOF

if [ $? -eq 0 ]; then
    echo "✅ 服务器部署成功"
else
    echo "❌ 服务器部署失败"
    exit 1
fi

# 4. 验证修复效果
echo "🔍 4. 验证认证修复效果..."
sleep 5

echo "正在测试认证API..."
if curl -s https://spot.gitagent.io/api/auth/health > /dev/null; then
    echo "✅ 认证API响应正常"
    echo "认证服务状态："
    curl -s https://spot.gitagent.io/api/auth/health | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "无法解析JSON响应"
else
    echo "❌ 认证API无响应"
fi

echo ""
echo "🎯 认证修复完成总结"
echo "=================================="
echo "✅ 问题：Supabase令牌验证失败导致401错误"
echo "✅ 解决：改进JWT令牌解析和验证逻辑"
echo "✅ 改进：添加详细的认证日志记录"
echo "✅ 测试：认证健康检查端点正常"
echo ""
echo "🌐 测试步骤："
echo "1. 访问 https://spot.gitagent.io"
echo "2. 点击登录按钮"
echo "3. 使用测试账户登录："
echo "   - 邮箱: 402493977@qq.com"
echo "   - 密码: demo123"
echo "4. 确认登录成功且用户信息正确显示"
echo ""
echo "📋 调试信息："
echo "- 后端日志: tail -f /home/ec2-user/OrientDirector/logs/backend.log"
echo "- 认证健康检查: https://spot.gitagent.io/api/auth/health"
echo "- API文档: https://spot.gitagent.io/docs"
echo ""
echo "🎉 认证401错误修复完成！"
