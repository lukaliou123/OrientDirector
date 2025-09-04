#!/bin/bash

# 环境配置脚本
# 用于设置 isUsedomainnameaddress 环境变量

show_help() {
    echo "🔧 环境配置脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  local       设置为本地环境 (http://localhost:8001)"
    echo "  production  设置为生产环境 (https://doro.gitagent.io)"
    echo "  status      显示当前环境配置"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 local       # 切换到本地环境"
    echo "  $0 production  # 切换到生产环境"
    echo "  $0 status      # 查看当前配置"
}

set_local_environment() {
    export isUsedomainnameaddress=false
    echo "✅ 已设置为本地环境"
    echo "   isUsedomainnameaddress=false"
    echo "   API_BASE_URL=http://localhost:8001"
    echo ""
    echo "💡 要使配置永久生效，请将以下内容添加到 ~/.bashrc 或 ~/.zshrc:"
    echo "   export isUsedomainnameaddress=false"
}

set_production_environment() {
    export isUsedomainnameaddress=true
    echo "✅ 已设置为生产环境"
    echo "   isUsedomainnameaddress=true"
    echo "   API_BASE_URL=https://doro.gitagent.io"
    echo ""
    echo "💡 要使配置永久生效，请将以下内容添加到 ~/.bashrc 或 ~/.zshrc:"
    echo "   export isUsedomainnameaddress=true"
}

show_status() {
    echo "🔧 当前环境配置:"
    echo "   isUsedomainnameaddress=${isUsedomainnameaddress:-未设置}"
    
    if [ "${isUsedomainnameaddress}" = "true" ]; then
        echo "   环境类型: 生产环境"
        echo "   API_BASE_URL: https://doro.gitagent.io"
    elif [ "${isUsedomainnameaddress}" = "false" ]; then
        echo "   环境类型: 本地环境"
        echo "   API_BASE_URL: http://localhost:8001"
    else
        echo "   环境类型: 未配置 (默认本地环境)"
        echo "   API_BASE_URL: http://localhost:8001"
    fi
}

# 主逻辑
case "$1" in
    "local")
        set_local_environment
        ;;
    "production")
        set_production_environment
        ;;
    "status")
        show_status
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        echo "❌ 请指定操作类型"
        echo "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
    *)
        echo "❌ 未知选项: $1"
        echo "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
esac
