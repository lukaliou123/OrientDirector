✅ OrientDirector项目标准启动流程
🚀 完整启动命令序列
# 1. 连接到服务器
ssh -i /Users/a1/work/productmindai.pem ec2-user@54.89.140.250

# 2. 进入项目目录
cd /home/ec2-user/OrientDirector

# 3. 激活Conda环境（关键步骤）
conda activate orient

# 4. 启动服务（推荐方式）
./restart_production.sh

📋 启动方式选择
方式	命令	说明
推荐	./restart_production.sh	停止现有服务并重新启动
仅启动	./start_production.sh	直接启动服务（不停止现有）
手动控制	./stop_production.sh → ./start_production.sh	分步操作
🔍 服务状态检查
# 检查进程状态
ps aux | grep -E "(uvicorn|start_frontend)"

# 查看实时日志
tail -f logs/backend.log    # 后端日志
tail -f logs/frontend.log   # 前端日志

# 测试API连接
curl https://doro.gitagent.io/api/health
📊 服务信息
后端服务: 端口8001 → https://doro.gitagent.io
前端服务: 端口3001 → 通过Nginx代理
API文档: https://doro.gitagent.io/docs
日志位置: /home/ec2-user/OrientDirector/logs/
⚠️ 重要注意事项
必须先激活Conda环境 1：conda activate orient
环境变量检查：确保.env文件包含GEMINI_API_KEY
端口配置：后端8001，前端3001
日志监控：启动后检查日志确保无错误
🛠️ 故障排除
如果服务启动失败：
# 检查环境
conda list | grep -E "(fastapi|uvicorn|google)"

# 检查端口占用
netstat -tlnp | grep -E "(8001|3001)"

# 强制停止并重启
pkill -f "uvicorn.*main:app"
pkill -f "start_frontend"
./restart_production.sh