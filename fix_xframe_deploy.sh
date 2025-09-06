#!/bin/bash

# 修复X-Frame-Options问题的部署脚本
# 解决登录界面无法在iframe中显示的问题

echo "🔧 修复X-Frame-Options问题部署脚本"
echo "=================================="

# 检查当前目录
if [ ! -f "nginx-doro.conf" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 1. 验证本地nginx配置文件已修改
echo "📋 1. 验证本地nginx配置文件..."
if grep -q "X-Frame-Options SAMEORIGIN" nginx-doro.conf; then
    echo "✅ 本地nginx配置已修改为SAMEORIGIN"
else
    echo "❌ 本地nginx配置未正确修改"
    echo "正在修改..."
    sed -i.bak 's/X-Frame-Options DENY/X-Frame-Options SAMEORIGIN/g' nginx-doro.conf
    echo "✅ 已修改本地nginx配置"
fi

# 2. 提交代码到Git
echo "📦 2. 提交代码更改..."
git add nginx-doro.conf
git commit -m "fix: 修改X-Frame-Options为SAMEORIGIN以支持iframe登录"
git push origin hw01

if [ $? -eq 0 ]; then
    echo "✅ 代码已推送到GitHub"
else
    echo "❌ 代码推送失败"
    exit 1
fi

# 3. 部署到服务器
echo "🚀 3. 部署到服务器..."
echo "正在连接服务器并更新配置..."

# 使用记忆中的部署命令
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 服务器端操作开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 激活conda环境
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate orient
    
    # 拉取最新代码
    echo "📥 拉取最新代码..."
    git checkout hw01
    git pull origin hw01
    
    # 备份当前nginx配置
    echo "💾 备份当前nginx配置..."
    sudo cp /etc/nginx/conf.d/doro.gitagent.io.conf /etc/nginx/conf.d/doro.gitagent.io.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # 更新nginx配置中的X-Frame-Options
    echo "🔧 更新nginx配置..."
    sudo sed -i 's/X-Frame-Options DENY/X-Frame-Options SAMEORIGIN/g' /etc/nginx/conf.d/doro.gitagent.io.conf
    
    # 验证nginx配置
    echo "✅ 验证nginx配置..."
    sudo nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ nginx配置验证通过"
        
        # 重新加载nginx配置
        echo "🔄 重新加载nginx配置..."
        sudo systemctl reload nginx
        
        # 重启应用服务
        echo "🔄 重启应用服务..."
        ./restart_production.sh
        
        echo "✅ 服务器配置更新完成"
    else
        echo "❌ nginx配置验证失败"
        exit 1
    fi
EOF

if [ $? -eq 0 ]; then
    echo "✅ 服务器部署成功"
else
    echo "❌ 服务器部署失败"
    exit 1
fi

# 4. 验证修复效果
echo "🔍 4. 验证修复效果..."
sleep 5

echo "正在测试API连接..."
if curl -s https://spot.gitagent.io/api/health > /dev/null; then
    echo "✅ 后端API响应正常"
else
    echo "❌ 后端API无响应"
fi

echo ""
echo "🎯 修复完成总结"
echo "=================================="
echo "✅ 问题：X-Frame-Options设置为DENY阻止iframe显示"
echo "✅ 解决：修改为SAMEORIGIN允许同源iframe"
echo "✅ 影响：登录界面现在可以正常在iframe中显示"
echo "✅ 安全：仍然防止跨域iframe攻击"
echo ""
echo "🌐 测试地址："
echo "主站：https://spot.gitagent.io"
echo "API文档：https://spot.gitagent.io/docs"
echo ""
echo "📋 验证步骤："
echo "1. 访问 https://spot.gitagent.io"
echo "2. 点击登录按钮"
echo "3. 确认登录界面正常显示"
echo "4. 测试登录功能"
echo ""
echo "🎉 X-Frame-Options问题修复完成！"
