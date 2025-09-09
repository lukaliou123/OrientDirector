FROM python:3.11-slim

WORKDIR /app

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# Railway会设置PORT环境变量
EXPOSE 8000

# 使用Python启动脚本
CMD ["python", "railway_start.py"]
