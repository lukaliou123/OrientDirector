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

# 暴露端口（Railway会动态分配端口）
EXPOSE $PORT

# 健康检查 - 使用动态端口
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# 启动命令 - 使用Railway提供的动态端口
CMD ["sh", "-c", "cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
