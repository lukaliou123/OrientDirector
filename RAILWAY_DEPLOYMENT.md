# 🚄 Railway 部署指南

## 🎯 部署概述
本项目已经配置为单服务部署，FastAPI后端同时服务前端和API。

## 📋 部署前准备

### 1. 确保文件结构正确
```
OrientDiscover/
├── backend/main.py          # 后端API服务器
├── index.html               # 前端页面
├── styles.css               # 样式文件
├── app.js                   # 前端JavaScript
├── requirements.txt         # Python依赖
├── Procfile                 # Railway启动配置
├── runtime.txt              # Python版本
├── railway.json             # Railway优化配置
└── static/                  # 静态文件目录
    ├── generated_images/
    ├── selfies/
    └── profile_photo/
```

### 2. 环境变量配置
在Railway中设置以下环境变量：

**必需的API密钥：**
```bash
GOOGLE_MAPS_API_KEY=你的谷歌地图API密钥
GEMINI_API_KEY=你的Gemini API密钥
```

**应用配置：**
```bash
AI_PROVIDER=gemini
USE_LANGCHAIN=true
DEMO_MODE=false
```

## 🚀 Railway部署步骤

### 方法1: CLI部署（推荐）
```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录Railway
railway login

# 3. 初始化项目
railway init

# 4. 设置环境变量
railway variables set GOOGLE_MAPS_API_KEY=你的密钥
railway variables set GEMINI_API_KEY=你的密钥
railway variables set AI_PROVIDER=gemini
railway variables set USE_LANGCHAIN=true
railway variables set DEMO_MODE=false

# 5. 部署
railway up
```

### 方法2: GitHub连接部署
1. 将代码推送到GitHub
2. 在Railway.app中选择"Deploy from GitHub"
3. 连接仓库并设置环境变量
4. Railway会自动检测并部署

## 🔧 部署配置说明

### Procfile
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```
- 单worker配置适合Railway免费层
- `$PORT` 环境变量由Railway自动设置

### 修改的main.py路由
```python
@app.get("/")
async def root():
    return FileResponse('../index.html')

@app.get("/styles.css")
async def get_css():
    return FileResponse('../styles.css')

@app.get("/app.js") 
async def get_js():
    return FileResponse('../app.js')
```

## ✅ 部署验证

部署完成后，访问以下URL验证：

- **主页**: `https://你的railway域名/`
- **API健康检查**: `https://你的railway域名/api/health`
- **API文档**: `https://你的railway域名/docs`

### 预期响应：
- 主页：显示完整的OrientDiscover应用界面
- Health check：`{"message": "方向探索派对API服务正在运行", "status": "healthy"}`

## 🚨 常见问题

### Q: 部署失败，找不到模块
A: 确保requirements.txt包含所有依赖，特别是：
```
langchain-google-genai>=0.1.0
google-genai>=1.32.0
```

### Q: 静态文件404错误
A: 检查文件路径，确保static目录存在且包含.gitkeep文件

### Q: Gemini API调用失败
A: 检查GEMINI_API_KEY是否正确设置，确认API配额充足

### Q: 前端无法加载
A: 检查main.py中的FileResponse路径是否正确（`../index.html`）

## 💡 优化建议

### 1. 监控设置
在Railway Dashboard中启用：
- CPU/Memory监控
- 日志监控
- 错误告警

### 2. 自定义域名
```bash
railway domain add 你的域名.com
```

### 3. 环境分离
为开发和生产创建不同的Railway项目

## 🎭 演示模式配置

如果API配额有限，可以启用演示模式：
```bash
railway variables set DEMO_MODE=true
```

这将使用预生成的图片而不是实时API调用。

## 📞 技术支持

如果遇到问题：
1. 检查Railway部署日志
2. 确认环境变量设置
3. 验证API密钥有效性
4. 检查网络连接和防火墙设置
