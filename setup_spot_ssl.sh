#!/bin/bash

# 为spot.gitagent.io申请SSL证书并设置自动续费
# 同时删除doro.gitagent.io的SSL自动任务

echo "🔒 为spot.gitagent.io申请SSL证书并设置自动续费"
echo "================================================"

# 连接到服务器执行SSL配置
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250 << 'EOF'
    echo "🔄 服务器SSL配置开始..."
    
    # 进入项目目录
    cd /home/ec2-user/OrientDirector
    
    # 1. 检查当前SSL证书状态
    echo "📋 1. 检查当前SSL证书状态..."
    sudo certbot certificates
    
    echo ""
    echo "🔒 2. 为spot.gitagent.io申请SSL证书..."
    
    # 确保nginx配置文件存在
    if [ ! -f "nginx-doro.conf" ]; then
        echo "❌ nginx-doro.conf文件不存在"
        exit 1
    fi
    
    # 复制nginx配置到正确位置
    sudo cp nginx-doro.conf /etc/nginx/sites-available/spot.gitagent.io
    
    # 删除旧的doro配置链接
    sudo rm -f /etc/nginx/sites-enabled/doro.gitagent.io
    sudo rm -f /etc/nginx/sites-enabled/spot.gitagent.io
    
    # 创建新的配置链接
    sudo ln -sf /etc/nginx/sites-available/spot.gitagent.io /etc/nginx/sites-enabled/
    
    # 测试nginx配置
    sudo nginx -t
    if [ $? -ne 0 ]; then
        echo "❌ Nginx配置测试失败"
        exit 1
    fi
    
    # 重新加载nginx
    sudo systemctl reload nginx
    
    # 申请SSL证书
    echo "🔐 申请spot.gitagent.io的SSL证书..."
    sudo certbot --nginx -d spot.gitagent.io --non-interactive --agree-tos --email admin@gitagent.io --redirect
    
    if [ $? -eq 0 ]; then
        echo "✅ spot.gitagent.io SSL证书申请成功"
    else
        echo "❌ SSL证书申请失败"
        exit 1
    fi
    
    echo ""
    echo "🗑️  3. 删除doro.gitagent.io的SSL自动续费任务..."
    
    # 备份当前crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt
    echo "✅ 已备份当前crontab到 /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    
    # 显示当前的crontab任务
    echo "📋 当前的crontab任务："
    crontab -l | grep -n "."
    
    # 删除包含doro.gitagent.io的SSL续费任务
    crontab -l | grep -v "doro\.gitagent\.io" > /tmp/new_crontab.txt
    
    # 检查是否有变化
    if ! cmp -s <(crontab -l) /tmp/new_crontab.txt; then
        echo "🔧 发现doro.gitagent.io相关的crontab任务，正在删除..."
        crontab /tmp/new_crontab.txt
        echo "✅ 已删除doro.gitagent.io的SSL自动续费任务"
    else
        echo "ℹ️  未找到doro.gitagent.io的SSL自动续费任务"
    fi
    
    echo ""
    echo "⏰ 4. 设置spot.gitagent.io的SSL自动续费任务..."
    
    # 添加spot.gitagent.io的SSL自动续费任务
    # 检查是否已存在spot.gitagent.io的续费任务
    if ! crontab -l | grep -q "spot\.gitagent\.io"; then
        echo "📅 添加spot.gitagent.io SSL自动续费任务..."
        
        # 添加SSL证书自动续费任务（每天凌晨2点检查）
        (crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/certbot renew --quiet --post-hook \"systemctl reload nginx\" --cert-name spot.gitagent.io") | crontab -
        
        # 添加日志清理任务（每周日凌晨3点清理30天前的日志）
        (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/bin/find /var/log/letsencrypt -name \"*.log\" -mtime +30 -delete 2>/dev/null || true") | crontab -
        
        echo "✅ 已添加spot.gitagent.io SSL自动续费任务"
    else
        echo "ℹ️  spot.gitagent.io SSL自动续费任务已存在"
    fi
    
    echo ""
    echo "📋 5. 验证SSL证书配置..."
    
    # 显示所有SSL证书
    echo "当前所有SSL证书："
    sudo certbot certificates
    
    # 显示更新后的crontab任务
    echo ""
    echo "📅 当前的crontab任务："
    crontab -l | grep -n "."
    
    echo ""
    echo "🧪 6. 测试SSL证书..."
    
    # 测试SSL证书
    if curl -s -I https://spot.gitagent.io | grep -q "HTTP/2 200"; then
        echo "✅ spot.gitagent.io SSL证书工作正常"
    else
        echo "⚠️  spot.gitagent.io SSL测试可能有问题，请手动检查"
    fi
    
    # 测试证书续费（干运行）
    echo ""
    echo "🔍 测试SSL证书自动续费（干运行）..."
    sudo certbot renew --dry-run --cert-name spot.gitagent.io
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL证书自动续费测试成功"
    else
        echo "⚠️  SSL证书自动续费测试失败，请检查配置"
    fi
    
    echo ""
    echo "✅ spot.gitagent.io SSL配置完成"
    echo "=================================="
    echo "📋 配置总结："
    echo "- SSL证书已申请并配置"
    echo "- 自动续费任务已设置（每天凌晨2点检查）"
    echo "- 日志清理任务已设置（每周清理30天前的日志）"
    echo "- doro.gitagent.io的SSL任务已删除"
    echo "- nginx配置已更新并重新加载"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 SSL证书配置完成总结"
    echo "=================================="
    echo "✅ spot.gitagent.io SSL证书申请成功"
    echo "✅ SSL自动续费任务已设置"
    echo "✅ doro.gitagent.io SSL任务已删除"
    echo "✅ nginx配置已更新"
    echo ""
    echo "🔒 SSL证书信息："
    echo "- 域名: spot.gitagent.io"
    echo "- 证书类型: Let's Encrypt"
    echo "- 自动续费: 每天凌晨2点检查"
    echo "- 日志清理: 每周日凌晨3点"
    echo ""
    echo "🧪 验证SSL证书："
    echo "1. 访问 https://spot.gitagent.io"
    echo "2. 检查浏览器地址栏的锁图标"
    echo "3. 确认证书有效期和颁发机构"
    echo ""
    echo "📋 监控和维护："
    echo "- 证书状态检查: sudo certbot certificates"
    echo "- 手动续费测试: sudo certbot renew --dry-run"
    echo "- 查看续费日志: sudo tail -f /var/log/letsencrypt/letsencrypt.log"
    echo "- 查看crontab任务: crontab -l"
    echo ""
    echo "🎉 SSL证书配置和自动续费设置完成！"
else
    echo "❌ SSL证书配置失败"
    exit 1
fi
