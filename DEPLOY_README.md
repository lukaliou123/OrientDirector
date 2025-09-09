# Railway部署说明（极简版）

## 部署方式选择

### 方式1：使用Docker（推荐）
使用 `Dockerfile` + `railway.json`

### 方式2：使用Nixpacks
删除 `railway.json`，Railway会自动使用 `railway.toml`

### 方式3：使用Buildpacks
删除 `railway.json` 和 `railway.toml`，Railway会使用 `Procfile`

## 环境变量
在Railway项目设置中添加：
- `GOOGLE_MAPS_API_KEY`：你的Google Maps API密钥
- `GEMINI_API_KEY`：你的Gemini API密钥（如需要）

## 部署步骤
1. 提交代码到Git
2. 在Railway中连接GitHub仓库
3. Railway会自动部署

## 故障排除
- 如果502错误：检查Railway日志
- 如果找不到文件：确保所有文件都已提交到Git
- 如果端口错误：Railway会自动设置PORT环境变量，不要硬编码端口
