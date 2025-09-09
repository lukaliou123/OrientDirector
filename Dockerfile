# OrientDiscover Docker Configuration
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/static/generated_images \
    && mkdir -p /app/static/pregenerated_images \
    && mkdir -p /app/static/selfies \
    && mkdir -p /app/static/profile_photo

# 设置环境变量，确保Python能找到模块
ENV PYTHONPATH=/app:/app/backend

# 暴露默认端口（Railway会通过环境变量覆盖）
EXPOSE 8000

# 注意：Railway的健康检查使用railway.json中的配置，不使用Dockerfile的HEALTHCHECK
# 如果需要本地测试，可以使用以下命令：
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# 启动命令 - 使用Python启动脚本
CMD ["python", "start_railway.py"]
