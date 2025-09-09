FROM python:3.9-slim

WORKDIR /app

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# 设置Python路径
ENV PYTHONPATH=/app

# Railway会设置PORT环境变量
EXPOSE 8000

# 使用最简单的启动脚本
CMD ["python", "simple_start.py"]
