# 🚄 Railway 部署修复指南

## 🚨 ERR_CONNECTION_REFUSED 问题解决方案

### 问题根源分析
您遇到的 `ERR_CONNECTION_REFUSED` 错误主要由以下原因导致：

1. **硬编码localhost URL** - 最主要原因 🎯
2. **端口配置不一致** 
3. **静态资源路径问题**
4. **环境变量配置缺失**

---

## ✅ 已修复的问题

### 1. 前端API调用硬编码修复
**修复前:**
```javascript
fetch('http://localhost:8000/api/explore-real')
fetch('http://localhost:8000/api/generate-historical-scene')
// ... 9个硬编码URL
```

**修复后:**
```javascript  
fetch('/api/explore-real')  // 相对URL，自动适配域名
fetch('/api/generate-historical-scene')
// ... 所有URL改为相对路径
```

### 2. 后端静态资源URL修复
**修复前:**
```python
# nano_banana_service.py
image_url = f"http://localhost:8000/static/generated_images/{filename}"

# main.py  
avatar_url = "http://localhost:8000/static/profile_photo/profile.jpg"
```

**修复后:**
```python
# 使用相对路径，适配云环境
image_url = f"/static/generated_images/{filename}"
avatar_url = "/static/profile_photo/profile.jpg" 
```

### 3. Docker端口配置修复
**修复前:**
```dockerfile
EXPOSE 8000
CMD [...uvicorn main:app --host 0.0.0.0 --port 8000"]
```

**修复后:**
```dockerfile
EXPOSE $PORT  # Railway动态端口
CMD [...uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

---

## 🚀 Railway部署步骤（已优化）

### 步骤1: 环境变量配置
在Railway Dashboard中设置：
```bash
# API密钥（必需）
GOOGLE_MAPS_API_KEY=你的谷歌地图API密钥
GEMINI_API_KEY=你的Gemini_API密钥

# 应用配置
AI_PROVIDER=gemini
USE_LANGCHAIN=true
DEMO_MODE=false  # 或true（如果API配额有限）

# Railway会自动设置以下变量，无需手动配置：
# PORT=动态端口号
# RAILWAY_ENVIRONMENT=production
```

### 步骤2: 部署方式选择

**方式A: CLI部署（推荐）**
```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录并初始化
railway login
railway init

# 3. 部署（会自动使用修复后的配置）
railway up
```

**方式B: GitHub自动部署**
1. 推送代码到GitHub仓库
2. 在Railway.app中连接GitHub仓库  
3. Railway会自动检测并部署

### 步骤3: 验证部署
部署完成后访问：
- **主页**: `https://你的railway域名/`
- **API健康检查**: `https://你的railway域名/api/health`
- **API文档**: `https://你的railway域名/docs`

---

## 🛠️ 部署最佳实践

### 1. 监控和日志
```bash
# 实时查看日志
railway logs --follow

# 查看服务状态
railway status
```

### 2. 环境分离
为不同环境创建不同的Railway项目：
- `orientdiscover-dev` (开发环境)
- `orientdiscover-prod` (生产环境)

### 3. 自定义域名
```bash
railway domain add yourdomain.com
```

### 4. 资源优化
- 启用Railway Pro获得更好的性能
- 设置合理的健康检查间隔
- 配置自动扩缩容

---

## 🚨 常见问题解决

### Q: 仍然出现Connection Refused
**A:** 检查以下项目：
1. 确认所有localhost URL已修复
2. 验证环境变量正确设置
3. 检查Railway服务状态
4. 查看部署日志是否有错误

### Q: 静态文件404错误  
**A:** 确保static目录结构正确：
```
static/
├── generated_images/
├── pregenerated_images/  
├── selfies/
└── profile_photo/
```

### Q: API调用超时
**A:** Railway免费层有限制，考虑：
- 启用DEMO_MODE减少API调用
- 升级到Railway Pro
- 优化API调用频率

### Q: Gemini API失效
**A:** 检查：
- GEMINI_API_KEY是否正确
- API配额是否充足
- 网络连接是否正常

---

## 📊 性能优化建议

### 1. 减少冷启动时间
```python
# 在main.py中预加载服务
@app.on_event("startup") 
async def startup_event():
    # 预热服务
    logger.info("🚀 服务预热完成")
```

### 2. 启用缓存
```python  
# 使用Redis缓存（可选）
import redis
cache = redis.Redis(host=os.getenv('REDIS_URL'))
```

### 3. 图片优化
- 使用WebP格式
- 设置合理的压缩质量
- 实现图片懒加载

---

## 🎭 演示模式配置

如果API配额有限，启用演示模式：
```bash
railway variables set DEMO_MODE=true
```

演示模式特性：
- 使用预生成图片
- 减少API调用
- 保持完整功能体验

---

## 📞 故障排查

### 检查清单
- [ ] 所有localhost URL已改为相对路径
- [ ] 环境变量正确设置  
- [ ] Railway服务状态正常
- [ ] 部署日志无错误
- [ ] 网络连接正常
- [ ] API密钥有效

### 调试命令
```bash
# 查看环境变量
railway variables

# 查看实时日志  
railway logs --tail 100

# 重新部署
railway up --detach
```

---

## 🎉 修复效果

经过以上修复，您的应用应该能够：
- ✅ 在Railway上稳定运行
- ✅ 正确处理API调用
- ✅ 正常显示静态资源
- ✅ 支持动态端口分配
- ✅ 适配云环境部署

现在重新部署到Railway，ERR_CONNECTION_REFUSED错误应该彻底解决！🚀
