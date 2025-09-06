# 🚀 服务器部署指令 - spot.gitagent.io

## 📋 部署概述

本文档提供了将 OrientDirector 项目从 `doro.gitagent.io` 迁移到 `spot.gitagent.io` 的完整服务器部署指令。

## 🔧 服务器信息

- **服务器IP**: 54.89.140.250
- **新域名**: spot.gitagent.io
- **操作系统**: Amazon Linux 2
- **用户**: ec2-user

## 📦 部署步骤

### 1. 连接到服务器

```bash
ssh ec2-user@54.89.140.250
cd /path/to/OrientDirector  # 替换为实际项目路径
```

### 2. 执行自动部署脚本

```bash
# 下载并执行部署脚本
./server_deploy.sh
```

### 3. 手动部署步骤（如果自动脚本失败）

#### 3.1 停止现有服务
```bash
sudo systemctl stop orientdirector-backend
sudo systemctl stop orientdirector-frontend
```

#### 3.2 更新代码
```bash
git fetch origin
git checkout main
git pull origin main
```

#### 3.3 安装依赖
```bash
pip install -r requirements.txt
```

#### 3.4 更新nginx配置
```bash
# 复制新的nginx配置
sudo cp nginx-doro.conf /etc/nginx/sites-available/spot.gitagent.io

# 删除旧配置
sudo rm -f /etc/nginx/sites-enabled/doro.gitagent.io

# 启用新配置
sudo ln -sf /etc/nginx/sites-available/spot.gitagent.io /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载nginx
sudo systemctl reload nginx
```

#### 3.5 更新SSL证书
```bash
# 为新域名申请SSL证书
sudo certbot --nginx -d spot.gitagent.io --non-interactive --agree-tos --email admin@gitagent.io --redirect
```

#### 3.6 配置环境变量
确保 `.env` 文件包含以下配置：

```bash
# Supabase配置 (后端如果需要直接访问)
SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo

# 前端Supabase配置 (公开密钥)
VITE_SUPABASE_URL=https://uobwbhvwrciaxloqdizc.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcwNzEyNjYsImV4cCI6MjA2MjY0NzI2Nn0.x9Tti06ZF90B2YPg-AeVvT_tf4qOcOYcHWle6L3OVtc

# 环境变量控制
isUsedomainnameaddress=true
```

#### 3.7 启动服务
```bash
# 启动后端服务
sudo systemctl start orientdirector-backend
sudo systemctl enable orientdirector-backend

# 启动前端服务
sudo systemctl start orientdirector-frontend
sudo systemctl enable orientdirector-frontend
```

#### 3.8 验证部署
```bash
# 检查服务状态
sudo systemctl status orientdirector-backend
sudo systemctl status orientdirector-frontend

# 测试API
curl -s https://spot.gitagent.io/api/auth/health

# 测试前端
curl -s https://spot.gitagent.io
```

## 🔍 验证清单

- [ ] 代码已更新到最新版本
- [ ] nginx配置已更新为 spot.gitagent.io
- [ ] SSL证书已为新域名配置
- [ ] 环境变量包含Supabase配置
- [ ] 后端服务正常运行
- [ ] 前端服务正常运行
- [ ] API健康检查通过
- [ ] 网站可正常访问
- [ ] 用户注册/登录功能正常
- [ ] 多语言功能正常

## 🎯 重要变更

### ✅ 已完成的更新

1. **域名迁移**: `doro.gitagent.io` → `spot.gitagent.io`
2. **认证系统**: 集成Supabase认证 + 后端API双重机制
3. **测试账号**: 已删除所有测试账号，现使用Supabase数据库
4. **多语言**: 保持16种语言完整支持
5. **安全性**: 更新SSL证书和安全配置

### 🔧 技术栈更新

- **前端认证**: Supabase JavaScript客户端
- **后端认证**: Supabase Python客户端 + FastAPI
- **数据库**: Supabase PostgreSQL
- **部署**: 自动化部署脚本

## 🚨 故障排除

### 常见问题

#### 1. nginx配置错误
```bash
# 检查nginx配置
sudo nginx -t

# 查看nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

#### 2. SSL证书问题
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期证书
sudo certbot renew
```

#### 3. 服务启动失败
```bash
# 查看服务日志
sudo journalctl -u orientdirector-backend -f
sudo journalctl -u orientdirector-frontend -f
```

#### 4. API连接问题
```bash
# 检查后端服务
curl -s http://localhost:8001/api/auth/health

# 检查环境变量
grep SUPABASE .env
```

## 📞 联系信息

如果部署过程中遇到问题，请检查：

1. **日志文件**: `/path/to/OrientDirector/logs/`
2. **系统日志**: `sudo journalctl -f`
3. **nginx日志**: `/var/log/nginx/`

## 🎉 部署完成

部署完成后，访问以下地址验证：

- **主站**: https://spot.gitagent.io
- **API文档**: https://spot.gitagent.io/docs
- **健康检查**: https://spot.gitagent.io/api/auth/health

---

**部署日期**: 2025年1月9日  
**版本**: v2.0 - Supabase集成版  
**维护**: Claude Sonnet 4 AI Assistant
