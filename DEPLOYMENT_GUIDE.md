# 🚀 OrientDiscover 部署指南

## 📋 部署前准备

### 1. 环境变量配置
确保以下API密钥已配置：
```bash
GOOGLE_MAPS_API_KEY=你的谷歌地图API密钥
GEMINI_API_KEY=你的Gemini API密钥
OPENAI_API_KEY=你的OpenAI API密钥（可选）
AI_PROVIDER=gemini
USE_LANGCHAIN=true
DEMO_MODE=false
```

## 🏆 推荐部署平台

### 方案1: Railway (⭐ 最推荐)
```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录并初始化
railway login
railway init

# 3. 设置环境变量
railway variables set GOOGLE_MAPS_API_KEY=你的密钥
railway variables set GEMINI_API_KEY=你的密钥
railway variables set AI_PROVIDER=gemini

# 4. 部署
railway up
```

**优势：**
- 🚀 5分钟快速部署
- 💰 免费额度充足
- 📁 支持文件存储
- 🔧 自动构建

### 方案2: Render
```bash
# 1. 连接GitHub仓库到Render
# 2. 选择Web Service
# 3. 构建命令: pip install -r requirements.txt
# 4. 启动命令: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**优势：**
- 🏢 企业级稳定性
- 🔒 自动SSL
- 💾 持久化存储

### 方案3: Docker + 云服务器
```bash
# 1. 构建镜像
docker build -t orientdiscover .

# 2. 运行容器
docker run -d -p 8000:8000 \
  -e GOOGLE_MAPS_API_KEY=你的密钥 \
  -e GEMINI_API_KEY=你的密钥 \
  orientdiscover
```

## 🔧 部署后验证

访问以下URL验证部署：
- 主页: `https://你的域名/`
- API文档: `https://你的域名/docs`
- 健康检查: `https://你的域名/api/health`

## ⚠️ 注意事项

1. **API限额管理**: 设置合理的使用限制
2. **文件存储**: 定期清理生成的图片
3. **环境变量安全**: 不要在代码中硬编码密钥
4. **监控**: 设置基本的性能监控

## 🎯 比赛展示优化

- 准备演示数据和预生成图片
- 设置错误处理和优雅降级
- 添加使用说明和帮助提示
- 测试各种网络条件下的性能

## 💡 常见问题

**Q: 图片生成失败怎么办？**
A: 确保GEMINI_API_KEY有效，并检查API配额

**Q: 静态文件无法访问？**
A: 检查static目录权限和路径配置

**Q: 部署后功能异常？**
A: 查看应用日志，通常是环境变量配置问题
