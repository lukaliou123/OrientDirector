#!/usr/bin/env python3
"""
Railway部署启动脚本 - 简化版
"""

import os
import sys
import uvicorn

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 添加项目根目录到Python路径（确保能导入backend包）
    sys.path.insert(0, script_dir)
    
    # 获取端口号
    port = int(os.environ.get('PORT', 8000))
    
    print(f"🚀 Railway部署启动")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   脚本目录: {script_dir}")
    print(f"   端口: {port}")
    print(f"   Python路径: {sys.path[:3]}")
    
    # 列出关键文件检查
    print("\n📁 文件检查:")
    files_to_check = ['index.html', 'styles.css', 'app.js', 'backend/main.py', '.env']
    for file in files_to_check:
        full_path = os.path.join(script_dir, file)
        exists = os.path.exists(full_path)
        print(f"   {file}: {'✅ 存在' if exists else '❌ 不存在'} ({full_path})")
    
    print("-" * 50)
    
    try:
        # 从backend模块导入app
        from backend.main import app
        print("✅ 成功导入FastAPI应用")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        sys.exit(1)
    
    # 启动uvicorn服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
