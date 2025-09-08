#!/usr/bin/env python3
"""
Pexels API 配置设置脚本

使用说明：
1. 访问 https://www.pexels.com/api/ 申请免费API密钥
2. 运行此脚本设置API密钥
"""

import os
import sys
from pathlib import Path

def setup_pexels_api():
    """设置Pexels API密钥"""
    
    print("="*60)
    print("Pexels API 配置设置")
    print("="*60)
    
    print("\n📋 申请Pexels API密钥的步骤：")
    print("1. 访问 https://www.pexels.com/api/")
    print("2. 点击 'Get Started' 或 'Request API Key'")
    print("3. 使用邮箱注册或登录Pexels账户")
    print("4. 填写API使用说明（可以写：用于旅游景点图片搜索）")
    print("5. 提交申请，通常会立即获得API密钥")
    
    print("\n🔑 API密钥特点：")
    print("- 免费使用")
    print("- 每小时200次请求")
    print("- 每月20,000次请求")
    print("- 支持图片和视频搜索")
    
    # 检查现有配置
    env_file = Path('.env')
    current_key = None
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('PEXELS_API_KEY='):
                    current_key = line.split('=', 1)[1].strip()
                    break
    
    if current_key and current_key != 'your_pexels_api_key_here':
        print(f"\n✅ 当前已配置API密钥: {current_key[:20]}...")
        update = input("是否要更新API密钥？(y/N): ").strip().lower()
        if update not in ['y', 'yes']:
            print("保持现有配置")
            return current_key
    
    # 获取新的API密钥
    print("\n🔧 请输入您的Pexels API密钥：")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ API密钥不能为空")
        return None
    
    # 验证API密钥格式（Pexels API密钥通常是长字符串）
    if len(api_key) < 20:
        print("⚠️  API密钥长度似乎不正确，但仍会保存")
    
    # 更新.env文件
    try:
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # 更新或添加PEXELS_API_KEY
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('PEXELS_API_KEY='):
                lines[i] = f'PEXELS_API_KEY={api_key}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'PEXELS_API_KEY={api_key}\n')
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ API密钥已保存到 {env_file}")
        return api_key
        
    except Exception as e:
        print(f"❌ 保存API密钥失败: {e}")
        return None

def test_api_key(api_key):
    """测试API密钥"""
    try:
        import requests
        
        print("\n🧪 测试API密钥...")
        
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": "landscape", "per_page": 1}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                print("✅ API密钥测试成功！")
                print(f"   找到 {data.get('total_results', 0)} 张相关图片")
                return True
            else:
                print("⚠️  API响应正常但没有找到图片")
                return False
        elif response.status_code == 401:
            print("❌ API密钥无效或未授权")
            return False
        else:
            print(f"❌ API测试失败: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  无法测试API密钥（缺少requests库）")
        print("   请手动验证API密钥是否正确")
        return True
    except Exception as e:
        print(f"❌ API测试异常: {e}")
        return False

def main():
    """主函数"""
    try:
        api_key = setup_pexels_api()
        
        if api_key:
            # 测试API密钥
            if test_api_key(api_key):
                print("\n🎉 Pexels API配置完成！")
                print("\n📝 接下来可以运行以下命令更新景点媒体：")
                print("   python update_attractions_media.py")
            else:
                print("\n❌ API密钥测试失败，请检查密钥是否正确")
        else:
            print("\n❌ API密钥配置失败")
            
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 配置过程出错: {e}")

if __name__ == "__main__":
    main()
