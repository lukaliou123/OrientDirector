#!/usr/bin/env python3
"""
测试Doro视频生成功能
使用现有的Doro图片资源测试视频生成API
"""

import requests
import json
import base64
import time
from pathlib import Path

# API配置
API_BASE_URL = "https://spot.gitagent.io"
# API_BASE_URL = "http://localhost:8001"  # 本地测试

def test_video_generation():
    """测试视频生成功能"""
    
    print("🎬 开始测试Doro视频生成功能...")
    print(f"API地址: {API_BASE_URL}")
    
    # 准备测试数据
    test_data = {
        "attraction_info": {
            "name": "天安门广场",
            "address": "北京市东城区",
            "description": "中国的象征性建筑，世界最大的城市广场"
        },
        "user_photo": None,  # 可选，不提供则使用默认
        "doro_photo": "doro1",  # 使用预设的doro1图片
        "style_photo": None  # 可选，不提供则使用默认风格
    }
    
    # 发送请求
    url = f"{API_BASE_URL}/api/doro/generate-video"
    
    print(f"📡 发送请求到: {url}")
    print(f"📦 请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            json=test_data,
            timeout=900  # 15分钟超时
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 视频生成成功！")
            print(f"📄 响应数据:")
            
            # 打印响应信息（不包括base64数据）
            if "video_url" in result:
                # 如果有视频数据，保存到文件
                if result["video_url"].startswith("data:video/mp4;base64,"):
                    video_base64 = result["video_url"].replace("data:video/mp4;base64,", "")
                    video_data = base64.b64decode(video_base64)
                    
                    # 保存视频文件
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    video_filename = f"test_doro_video_{timestamp}.mp4"
                    
                    with open(video_filename, "wb") as f:
                        f.write(video_data)
                    
                    print(f"💾 视频已保存到: {video_filename}")
                    print(f"📏 文件大小: {len(video_data) / 1024 / 1024:.2f} MB")
                else:
                    print(f"🔗 视频URL: {result['video_url']}")
            
            if "filename" in result:
                print(f"📁 文件名: {result['filename']}")
                
            if "duration" in result:
                print(f"⏱️ 生成时长: {result['duration']}秒")
                
        else:
            print(f"❌ 请求失败")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️ 请求超时（超过15分钟）")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请检查网络或API服务")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def test_simple_image_generation():
    """先测试简单的图片生成"""
    
    print("\n🖼️ 先测试Doro合影图片生成...")
    
    test_data = {
        "attraction_info": {
            "name": "故宫博物院",
            "address": "北京市东城区",
            "description": "中国明清两代的皇家宫殿"
        },
        "user_photo": None,
        "doro_photo": "doro2",
        "style_photo": None
    }
    
    url = f"{API_BASE_URL}/api/doro/generate"
    
    print(f"📡 发送请求到: {url}")
    
    try:
        response = requests.post(
            url,
            json=test_data,
            timeout=120  # 2分钟超时
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 图片生成成功！")
            
            if "image_url" in result:
                if result["image_url"].startswith("data:image"):
                    # 提取并保存图片
                    image_base64 = result["image_url"].split(",")[1]
                    image_data = base64.b64decode(image_base64)
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    image_filename = f"test_doro_image_{timestamp}.png"
                    
                    with open(image_filename, "wb") as f:
                        f.write(image_data)
                    
                    print(f"💾 图片已保存到: {image_filename}")
                    print(f"📏 文件大小: {len(image_data) / 1024:.2f} KB")
            
            if "filename" in result:
                print(f"📁 文件名: {result['filename']}")
                
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Doro视频生成功能测试")
    print("=" * 50)
    
    # 先测试图片生成
    test_simple_image_generation()
    
    print("\n" + "=" * 50)
    
    # 再测试视频生成
    user_input = input("\n是否继续测试视频生成？(y/n): ")
    if user_input.lower() == 'y':
        test_video_generation()
    else:
        print("跳过视频生成测试")
    
    print("\n测试完成！")
