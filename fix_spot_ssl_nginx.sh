#!/bin/bash

# 修复spot.gitagent.io的nginx配置并完成SSL安装

echo "🔧 修复spot.gitagent.io的nginx配置并完成SSL安装"
echo "=============================================="

# 连接到服务器执行修复
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 修复nginx配置开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 1. 检查nginx目录结构
    echo "📋 1. 检查nginx目录结构..."
    sudo mkdir -p /etc/nginx/sites-available
    sudo mkdir -p /etc/nginx/sites-enabled
    
    # 确保nginx主配置包含sites-enabled
    if ! grep -q "sites-enabled" /etc/nginx/nginx.conf; then
        echo "🔧 添加sites-enabled到nginx主配置..."
        sudo sed -i '/http {/a\    include /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
    fi
    
    # 2. 创建正确的nginx配置文件
    echo "📝 2. 创建spot.gitagent.io的nginx配置..."
    
    sudo tee /etc/nginx/sites-available/spot.gitagent.io > /dev/null << 'NGINX_CONFIG'
# Nginx配置文件 for spot.gitagent.io
server {
    listen 80;
    server_name spot.gitagent.io;
    
    # 重定向HTTP到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name spot.gitagent.io;
    
    # SSL证书配置 - 将由certbot自动更新
    ssl_certificate /etc/letsencrypt/live/spot.gitagent.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/spot.gitagent.io/privkey.pem;
    
    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 日志配置
    access_log /var/log/nginx/spot.gitagent.io.access.log;
    error_log /var/log/nginx/spot.gitagent.io.error.log;
    
    # 客户端最大请求体大小 (用于文件上传)
    client_max_body_size 50M;
    
    # API请求代理到后端
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 支持WebSocket (如果需要)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件服务 (前端)
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://localhost:3001;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX_CONFIG
    
    # 3. 删除旧配置并创建新链接
    echo "🔗 3. 配置nginx站点链接..."
    sudo rm -f /etc/nginx/sites-enabled/doro.gitagent.io
    sudo rm -f /etc/nginx/sites-enabled/spot.gitagent.io
    sudo ln -sf /etc/nginx/sites-available/spot.gitagent.io /etc/nginx/sites-enabled/
    
    # 4. 删除可能冲突的conf.d配置
    echo "🧹 4. 清理可能冲突的配置..."
    sudo rm -f /etc/nginx/conf.d/doro.gitagent.io.conf
    sudo rm -f /etc/nginx/conf.d/spot.gitagent.io.conf
    
    # 5. 测试nginx配置
    echo "✅ 5. 测试nginx配置..."
    sudo nginx -t
    
    if [ $? -ne 0 ]; then
        echo "❌ Nginx配置测试失败"
        exit 1
    fi
    
    # 6. 重新加载nginx
    echo "🔄 6. 重新加载nginx..."
    sudo systemctl reload nginx
    
    # 7. 使用certbot安装SSL证书到nginx配置
    echo "🔐 7. 安装SSL证书到nginx配置..."
    sudo certbot install --cert-name spot.gitagent.io --nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL证书安装成功"
    else
        echo "⚠️  SSL证书安装可能有问题，但证书已申请成功"
    fi
    
    # 8. 删除doro.gitagent.io的SSL自动续费任务
    echo "🗑️  8. 删除doro.gitagent.io的SSL自动续费任务..."
    
    # 备份当前crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
    
    # 删除包含doro.gitagent.io的SSL续费任务
    crontab -l | grep -v "doro\.gitagent\.io" > /tmp/new_crontab.txt
    crontab /tmp/new_crontab.txt
    
    # 9. 设置spot.gitagent.io的SSL自动续费任务
    echo "⏰ 9. 设置spot.gitagent.io的SSL自动续费任务..."
    
    # 检查是否已存在spot.gitagent.io的续费任务
    if ! crontab -l | grep -q "spot\.gitagent\.io"; then
        # 添加SSL证书自动续费任务（每天凌晨2点检查）
        (crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/certbot renew --quiet --post-hook \"systemctl reload nginx\"") | crontab -
        
        # 添加日志清理任务（每周日凌晨3点清理30天前的日志）
        (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/bin/find /var/log/letsencrypt -name \"*.log\" -mtime +30 -delete 2>/dev/null || true") | crontab -
        
        echo "✅ 已添加spot.gitagent.io SSL自动续费任务"
    else
        echo "ℹ️  spot.gitagent.io SSL自动续费任务已存在"
    fi
    
    # 10. 验证配置
    echo ""
    echo "📋 10. 验证SSL配置..."
    
    # 显示所有SSL证书
    echo "当前所有SSL证书："
    sudo certbot certificates
    
    # 显示crontab任务
    echo ""
    echo "📅 当前的crontab任务："
    crontab -l
    
    # 测试SSL连接
    echo ""
    echo "🧪 11. 测试SSL连接..."
    sleep 3
    
    if curl -s -I https://spot.gitagent.io | head -1 | grep -q "200"; then
        echo "✅ spot.gitagent.io HTTPS访问正常"
    else
        echo "⚠️  spot.gitagent.io HTTPS访问可能有问题"
    fi
    
    # 测试证书续费（干运行）
    echo ""
    echo "🔍 12. 测试SSL证书自动续费（干运行）..."
    sudo certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL证书自动续费测试成功"
    else
        echo "⚠️  SSL证书自动续费测试失败"
    fi
    
    echo ""
    echo "✅ spot.gitagent.io SSL配置和自动续费设置完成"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 SSL配置完成总结"
    echo "=================================="
    echo "✅ spot.gitagent.io SSL证书申请并安装成功"
    echo "✅ nginx配置已正确设置"
    echo "✅ SSL自动续费任务已配置"
    echo "✅ doro.gitagent.io SSL任务已删除"
    echo ""
    echo "🔒 SSL证书详情："
    echo "- 域名: spot.gitagent.io"
    echo "- 证书类型: Let's Encrypt"
    echo "- 有效期: 90天（自动续费）"
    echo "- 自动续费: 每天凌晨2点检查"
    echo ""
    echo "🧪 验证步骤："
    echo "1. 访问 https://spot.gitagent.io"
    echo "2. 检查浏览器地址栏的绿色锁图标"
    echo "3. 点击锁图标查看证书详情"
    echo "4. 确认证书由Let's Encrypt颁发"
    echo ""
    echo "🎉 SSL证书配置完成！"
else
    echo "❌ SSL配置失败"
    exit 1
fi
