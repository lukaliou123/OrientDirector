#!/bin/bash

# 🧭 OrientDirector 本地开发环境启动脚本
# 基于成功的启动流程创建
# 创建时间: 2025年9月7日

echo "🧭 OrientDirector 本地开发环境启动"
echo "============================================================"

# 1. 检查并激活conda环境
echo "🐍 检查conda环境..."
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: conda未安装或未在PATH中"
    exit 1
fi

# 激活orient环境
echo "🔄 激活orient conda环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate orient

# 检查Python版本
PYTHON_VERSION=$(python --version)
echo "✅ Python版本: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ "Python 3.9" ]]; then
    echo "⚠️  警告: 建议使用Python 3.9，当前版本可能存在兼容性问题"
fi

# 2. 设置本地开发环境变量
echo "🔧 设置本地开发环境变量..."
export isUsedomainnameaddress=false
echo "   isUsedomainnameaddress=false"
echo "   API_BASE_URL=http://localhost:8001"

# 使用配置脚本确认设置
if [ -f "./set_environment.sh" ]; then
    ./set_environment.sh local > /dev/null 2>&1
fi

# 3. 检查并安装依赖
echo "📦 检查Python依赖..."
if [ -f "requirements.txt" ]; then
    echo "🔄 安装/更新依赖包..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # 确保email-validator已安装
    pip install pydantic[email] > /dev/null 2>&1
    echo "✅ 依赖包检查完成"
else
    echo "⚠️  警告: requirements.txt文件不存在"
fi

# 4. 创建必要的目录
echo "📁 创建日志目录..."
mkdir -p logs backend/logs
echo "✅ 目录创建完成"

# 5. 清理可能的端口占用
echo "🧹 清理端口占用..."
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
lsof -ti :3001 | xargs kill -9 2>/dev/null || true
sleep 2

# 6. 启动服务
echo "🚀 启动本地服务..."
if [ -f "start_all.py" ]; then
    echo "📍 使用统一启动脚本..."
    python start_all.py &
    STARTUP_PID=$!
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 8
    
    # 7. 验证服务状态
    echo "🔍 验证服务状态..."
    
    # 检查后端服务
    if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
        echo "✅ 后端服务正常 (http://localhost:8001)"
    else
        echo "❌ 后端服务启动失败"
        exit 1
    fi
    
    # 检查前端服务
    if curl -s http://localhost:3001/ > /dev/null 2>&1; then
        echo "✅ 前端服务正常 (http://localhost:3001)"
    else
        echo "❌ 前端服务启动失败"
        exit 1
    fi
    
    # 检查环境配置
    ENV_RESPONSE=$(curl -s http://localhost:8001/api/config/environment 2>/dev/null)
    if echo "$ENV_RESPONSE" | grep -q '"environment": "local"'; then
        echo "✅ 环境配置正确 (本地开发环境)"
    else
        echo "⚠️  警告: 环境配置可能不正确"
    fi
    
    # 检查认证服务
    if curl -s http://localhost:8001/api/auth/health > /dev/null 2>&1; then
        echo "✅ 认证服务正常"
    else
        echo "⚠️  警告: 认证服务可能异常"
    fi
    
    echo ""
    echo "🎉 本地开发环境启动成功！"
    echo "============================================================"
    echo "📍 访问地址:"
    echo "   🌐 主应用: http://localhost:3001"
    echo "   🔧 环境配置: http://localhost:3001/environment_config.html"
    echo "   📚 API文档: http://localhost:8001/docs"
    echo "   🔍 后端API: http://localhost:8001"
    echo ""
    echo "🔧 环境信息:"
    echo "   📦 Python: $PYTHON_VERSION"
    echo "   🐍 Conda环境: orient"
    echo "   🌍 环境类型: 本地开发环境"
    echo "   🔗 API_BASE_URL: http://localhost:8001"
    echo ""
    echo "💡 使用说明:"
    echo "   - 按 Ctrl+C 停止所有服务"
    echo "   - 浏览器会自动打开主应用"
    echo "   - 查看日志: tail -f logs/backend.log"
    echo ""
    echo "🛠️  调试工具:"
    echo "   - 环境状态: ./set_environment.sh status"
    echo "   - 环境切换: EnvironmentConfig.showStatus() (浏览器控制台)"
    echo "============================================================"
    
    # 自动打开浏览器
    if command -v open &> /dev/null; then
        echo "🌐 正在打开浏览器..."
        open http://localhost:3001
    fi
    
    # 等待用户停止服务
    echo "按 Ctrl+C 停止所有服务..."
    wait $STARTUP_PID
    
else
    echo "❌ 错误: start_all.py文件不存在"
    exit 1
fi

echo ""
echo "✅ 服务已停止"
