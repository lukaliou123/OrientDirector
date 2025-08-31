# 谷歌街景无法使用问题分析

## 🔍 问题描述

谷歌街景功能无法正常加载，错误日志显示：
```
127.0.0.1 - - [31/Aug/2025 20:55:56] "GET /api/config/maps HTTP/1.1" 404 -
```

## 🎯 根本原因

**API路径不一致问题**：

<xml>
<对比分析>
  <问题API>
    <路径>/api/config/maps</路径>
    <类型>相对路径</类型>
    <实际请求>http://localhost:3000/api/config/maps</实际请求>
    <结果>404错误（前端服务器上没有这个端点）</结果>
  </问题API>
  
  <正常API>
    <路径>http://localhost:8000/api/explore-real</路径>
    <类型>绝对路径</类型>
    <实际请求>http://localhost:8000/api/explore-real</实际请求>
    <结果>正常工作</结果>
  </正常API>
</对比分析>
</xml>

## 📊 详细分析

### 1. 服务架构
- **前端服务**: 运行在 http://localhost:3000 (Python SimpleHTTPServer)
- **后端API**: 运行在 http://localhost:8000 (FastAPI)
- **问题**: 前端和后端在不同端口，需要使用完整URL

### 2. 代码位置
- **前端调用**: index.html 第195行
- **后端端点**: backend/main.py 第1177行

### 3. 其他API为什么正常
app.js中的其他API调用都使用了完整路径：
```javascript
// ✅ 正确的调用方式
const apiEndpoint = 'http://localhost:8000/api/explore-real';
const response = await fetch('http://localhost:8000/api/journey/start', ...);
const response = await fetch('http://localhost:8000/api/scene-review', ...);

// ❌ 问题调用
const response = await fetch('/api/config/maps');
```

## 🛠 修复方案

### 立即修复
修改 `index.html` 第195行：

```javascript
// 原代码
const response = await fetch('/api/config/maps');

// 修改为
const response = await fetch('http://localhost:8000/api/config/maps');
```

### 完整修复建议
为了避免未来类似问题，建议创建统一的API配置：

```javascript
// 在 index.html 或 app.js 顶部添加
const API_BASE_URL = 'http://localhost:8000';

// 然后所有API调用都使用
const response = await fetch(`${API_BASE_URL}/api/config/maps`);
```

## 🚀 快速修复步骤

1. 打开 `index.html` 文件
2. 找到第195行
3. 将 `/api/config/maps` 改为 `http://localhost:8000/api/config/maps`
4. 保存文件并刷新浏览器

## 💡 额外建议

### 1. 环境配置优化
考虑使用环境变量管理API地址：
```javascript
const API_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : window.location.origin;
```

### 2. 代理配置
可以在前端服务器配置代理，将 `/api/*` 请求转发到后端：
- 修改 `start_frontend.py` 添加代理功能
- 或使用 nginx 作为反向代理

### 3. CORS检查
确保后端允许前端域名的跨域请求（当前已配置）

## ✅ 验证步骤

修复后验证：
1. 确保前后端服务都在运行
2. 在浏览器开发者工具中查看网络请求
3. 确认 `/api/config/maps` 返回200状态码
4. 检查Google Maps API Key是否正确加载
5. 测试街景功能是否正常显示

---
*分析完成时间: 2025年8月31日*
