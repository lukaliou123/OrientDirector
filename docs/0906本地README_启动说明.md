# 🧭 方向探索派对 - 启动说明

## 📋 端口配置

- **前端服务**: `http://localhost:3001`
- **后端服务**: `http://localhost:8001`

## 🚀 启动方式

### 方式一：统一启动（推荐）
```bash
python start_all.py
```
- 自动启动前端和后端服务
- 自动处理端口占用问题
- 统一管理所有服务

### 方式二：分别启动

#### 启动后端服务
```bash
python start_backend.py
```
- 端口：8001
- 日志文件：`logs/backend.log`
- PID文件：`logs/backend.pid`

#### 启动前端服务
```bash
python start_frontend.py
```
- 端口：3001
- 自动打开浏览器

## 📝 日志管理

### 日志目录结构
```
logs/
├── backend.log     # 后端服务日志
├── backend.pid     # 后端进程ID
├── frontend.log    # 前端服务日志（如果有）
└── frontend.pid    # 前端进程ID（如果有）
```

### 日志特性
- ✅ 每次启动时自动清空历史日志
- ✅ 包含详细的时间戳
- ✅ 同时输出到控制台和文件
- ✅ 支持中文编码

## 🔧 端口占用处理

启动脚本会自动处理端口占用问题：

1. **检测端口占用**：使用 `lsof` 命令检查端口状态
2. **自动终止进程**：优雅终止占用端口的进程
3. **等待释放**：等待端口完全释放后再启动新服务
4. **错误处理**：如果无法释放端口，会显示详细错误信息

## ⚠️ 注意事项

### 系统要求
- Python 3.7+
- macOS/Linux 系统（支持 `lsof` 命令）
- 已安装必要的Python依赖

### 依赖检查
```bash
# 检查PyJWT是否安装
pip list | grep PyJWT

# 如果未安装，执行：
pip install PyJWT
```

### 文件权限
```bash
# 设置执行权限
chmod +x start_backend.py start_frontend.py start_all.py
```

## 🛑 停止服务

### 优雅停止
在运行的终端中按 `Ctrl+C`

### 强制停止
```bash
# 查找并终止后端进程
lsof -ti :8001 | xargs kill -9

# 查找并终止前端进程
lsof -ti :3001 | xargs kill -9
```

## 🔍 故障排除

### 1. 端口被占用
```bash
# 查看端口占用情况
lsof -i :8001  # 后端端口
lsof -i :3001  # 前端端口

# 手动终止进程
kill -9 <PID>
```

### 2. 依赖缺失
```bash
# 安装缺失的依赖
pip install PyJWT uvicorn fastapi
```

### 3. 权限问题
```bash
# 设置脚本执行权限
chmod +x *.py
```

### 4. 查看详细日志
```bash
# 实时查看后端日志
tail -f logs/backend.log

# 查看完整日志
cat logs/backend.log
```

## 📊 服务状态检查

### 检查后端服务
```bash
curl http://localhost:8001/api/cities
```

### 检查前端服务
在浏览器中访问：`http://localhost:3001`

## 🎯 开发模式

后端服务启动时使用了 `--reload` 参数，支持代码热重载：
- 修改Python代码后自动重启
- 无需手动重启服务
- 适合开发调试

---

## 📞 技术支持

如果遇到问题，请检查：
1. 日志文件：`logs/backend.log`
2. 端口占用：`lsof -i :8001` 和 `lsof -i :3001`
3. 进程状态：`ps aux | grep uvicorn`
4. 依赖安装：`pip list`

**祝您使用愉快！** 🎉
