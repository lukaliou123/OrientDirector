#!/usr/bin/env python3
"""
方向探索派对后端服务启动脚本
支持日志输出到logs目录，自动处理端口占用
"""

import subprocess
import sys
import os
import signal
import time
import logging
from datetime import datetime
from pathlib import Path

# 配置
BACKEND_PORT = 8001
BACKEND_HOST = "0.0.0.0"
LOGS_DIR = Path("logs")
BACKEND_LOG_FILE = LOGS_DIR / "backend.log"
BACKEND_PID_FILE = LOGS_DIR / "backend.pid"

def setup_logging():
    """设置日志配置"""
    # 确保logs目录存在
    LOGS_DIR.mkdir(exist_ok=True)
    
    # 清空历史日志文件
    if BACKEND_LOG_FILE.exists():
        BACKEND_LOG_FILE.unlink()
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(BACKEND_LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def kill_process_on_port(port):
    """杀死占用指定端口的进程"""
    try:
        # 查找占用端口的进程
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✓ 已终止占用端口 {port} 的进程 (PID: {pid})")
                        time.sleep(1)
                    except (ProcessLookupError, ValueError):
                        pass
            
            # 等待进程完全终止
            time.sleep(2)
            
            # 再次检查
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # 如果还有进程，强制杀死
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"✓ 强制终止进程 (PID: {pid})")
                        except (ProcessLookupError, ValueError):
                            pass
                time.sleep(1)
                            
    except FileNotFoundError:
        print("⚠️ lsof 命令不可用，无法自动清理端口")
    except Exception as e:
        print(f"⚠️ 清理端口时出错: {e}")

def save_pid(pid):
    """保存进程ID到文件"""
    try:
        with open(BACKEND_PID_FILE, 'w') as f:
            f.write(str(pid))
    except Exception as e:
        print(f"⚠️ 保存PID失败: {e}")

def start_backend():
    """启动后端服务"""
    logger = setup_logging()
    
    print("🧭 方向探索派对 - 后端服务启动")
    print("=" * 50)
    
    # 检查并清理端口
    print(f"🔍 检查端口 {BACKEND_PORT} 占用情况...")
    kill_process_on_port(BACKEND_PORT)
    
    # 切换到backend目录
    backend_dir = Path("backend")
    if not backend_dir.exists():
        logger.error("❌ backend目录不存在")
        sys.exit(1)
    
    os.chdir(backend_dir)
    
    # 检查必要文件
    required_files = ['main.py', 'auth.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        logger.error(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        sys.exit(1)

    # 启动uvicorn服务
    cmd = [
        sys.executable, '-m', 'uvicorn', 
        'main:app',
        '--host', BACKEND_HOST,
        '--port', str(BACKEND_PORT),
        '--reload',
        '--log-level', 'info'
    ]
    
    try:
        logger.info(f"🚀 启动后端服务: {' '.join(cmd)}")
        logger.info(f"📍 服务地址: http://{BACKEND_HOST}:{BACKEND_PORT}")
        logger.info(f"📝 日志文件: {BACKEND_LOG_FILE.absolute()}")
        print(f"✓ 服务地址: http://localhost:{BACKEND_PORT}")
        print(f"✓ 日志文件: {BACKEND_LOG_FILE.absolute()}")
        print("按 Ctrl+C 停止服务")
        print("-" * 50)
    
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 保存PID
        save_pid(process.pid)
        logger.info(f"📋 后端进程ID: {process.pid}")
        
        # 实时输出日志
        try:
            for line in process.stdout:
                if line.strip():
                    # 同时输出到控制台和日志文件
                    print(line.rstrip())
                    logger.info(line.rstrip())
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
        print("\n🛑 正在停止后端服务...")
        
        # 优雅关闭
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ 进程未在5秒内停止，强制终止")
            process.kill()
            process.wait()
        
        logger.info("✅ 后端服务已停止")
        print("✅ 后端服务已停止")
        
        # 清理PID文件
        if BACKEND_PID_FILE.exists():
            BACKEND_PID_FILE.unlink()
                
        return process.returncode
        
    except Exception as e:
        logger.error(f"❌ 启动后端服务失败: {e}")
        print(f"❌ 启动后端服务失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    try:
        return start_backend()
    except KeyboardInterrupt:
        print("\n👋 再见!")
        return 0

if __name__ == "__main__":
    sys.exit(main())