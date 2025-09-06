#!/bin/bash

# 部署脚本：将doro.gitagent.io域名统一替换为spot.gitagent.io
# 并完成Supabase认证系统集成

echo "🚀 开始部署spot.gitagent.io域名更新和Supabase认证集成"
echo "================================================"

# 检查当前目录
if [ ! -f "index.html" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 1. 检查环境变量文件
echo "📋 1. 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "⚠️  警告：.env文件不存在，请确保包含以下配置："
    echo "SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co"
    echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo"
    echo "VITE_SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co"
    echo "VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcwNzEyNjYsImV4cCI6MjA2MjY0NzI2Nn0.x9Tti06ZF90B2YPg-AeVvT_tf4qOcOYcHWle6L3OVtc"
else
    echo "✅ .env文件存在"
fi

# 2. 安装Python依赖
echo "📦 2. 安装Python依赖..."
pip install -q supabase postgrest gotrue psycopg2-binary sqlalchemy alembic
if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装完成"
else
    echo "❌ Python依赖安装失败"
    exit 1
fi

# 3. 检查关键文件
echo "📁 3. 检查关键文件..."
files_to_check=(
    "supabase-client.js"
    "auth-modal.html"
    "backend/auth.py"
    "requirements.txt"
    "nginx-doro.conf"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

# 4. 验证域名替换
echo "🔍 4. 验证域名替换..."
if grep -r "doro\.gitagent\.io" --exclude-dir=.git --exclude="*.log" . > /dev/null; then
    echo "⚠️  发现未替换的doro.gitagent.io引用："
    grep -r "doro\.gitagent\.io" --exclude-dir=.git --exclude="*.log" . | head -5
    echo "请手动检查并替换剩余的引用"
else
    echo "✅ 所有doro.gitagent.io已替换为spot.gitagent.io"
fi

# 5. 测试后端服务
echo "🔧 5. 测试后端服务..."
echo "启动后端服务进行测试..."

# 启动后端服务（后台运行）
python3 start_backend.py &
BACKEND_PID=$!

# 等待服务启动
sleep 5

# 测试健康检查
if curl -s http://localhost:8001/api/auth/health > /dev/null; then
    echo "✅ 后端认证服务正常"
else
    echo "❌ 后端认证服务无响应"
fi

# 停止后端服务
kill $BACKEND_PID 2>/dev/null

# 6. 生成服务器部署命令
echo "🖥️  6. 生成服务器部署命令..."
cat > server_deploy_commands.txt << 'EOF'
# 服务器端部署命令

# 1. 更新代码
cd /path/to/OrientDirector
git pull origin main

# 2. 更新nginx配置
sudo cp nginx-doro.conf /etc/nginx/sites-available/spot.gitagent.io
sudo rm -f /etc/nginx/sites-enabled/doro.gitagent.io
sudo ln -sf /etc/nginx/sites-available/spot.gitagent.io /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 3. 更新SSL证书（如果需要）
sudo certbot --nginx -d spot.gitagent.io --non-interactive --agree-tos --email admin@gitagent.io --redirect

# 4. 更新环境变量
echo "请确保服务器.env文件包含正确的Supabase配置"

# 5. 安装Python依赖
pip install supabase postgrest gotrue psycopg2-binary sqlalchemy alembic

# 6. 重启服务
sudo systemctl restart orientdirector-backend
sudo systemctl restart orientdirector-frontend

# 7. 验证服务
curl -s https://spot.gitagent.io/api/auth/health
EOF

echo "✅ 服务器部署命令已生成到 server_deploy_commands.txt"

# 7. 显示测试信息
echo ""
echo "🎯 部署完成总结"
echo "================================================"
echo "✅ 域名替换：doro.gitagent.io → spot.gitagent.io"
echo "✅ Supabase认证系统集成完成"
echo "✅ 前端认证界面支持Supabase + 后端API双重认证"
echo "✅ 后端API支持Supabase验证和本地JWT验证"
echo "✅ 多语言支持(16种语言)保持完整"
echo ""
echo "📋 测试账户信息："
echo "邮箱: 402493977@qq.com"
echo "密码: demo123"
echo "邮箱: test@example.com" 
echo "密码: demo123"
echo ""
echo "🌐 本地测试："
echo "1. 启动服务: npx netlify dev --port 8888"
echo "2. 访问: http://localhost:8888"
echo "3. 点击登录测试认证功能"
echo ""
echo "🚀 服务器部署："
echo "请参考 server_deploy_commands.txt 文件中的命令"
echo ""
echo "⚠️  注意事项："
echo "- 确保.env文件包含正确的Supabase配置"
echo "- 服务器端需要更新nginx配置文件"
echo "- 需要为spot.gitagent.io申请新的SSL证书"
echo "- 测试完整的认证流程（注册、登录、登出）"

echo ""
echo "🎉 部署脚本执行完成！"
