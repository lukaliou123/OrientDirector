#!/usr/bin/env python3
"""
简单测试Doro视频生成功能
使用最小化的参数测试
"""

import requests
import base64
import time
import io
from PIL import Image

# API配置
API_BASE_URL = "https://doro.gitagent.io"

def create_dummy_image():
    """创建一个简单的测试图片"""
    # 创建一个简单的100x100的白色图片
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_video_generation():
    """测试视频生成功能"""
    
    print("🎬 开始测试Doro视频生成功能...")
    print(f"API地址: {API_BASE_URL}")
    
    # 创建测试用的图片
    user_photo = create_dummy_image()
    
    # 准备FormData
    files = {
        'user_photo': ('user.png', user_photo, 'image/png')
    }
    
    data = {
        'attraction_name': '鸟巢（国家体育场）',
        'location': '北京市朝阳区',
        'doro_id': 'doro1',  # 使用预设的doro1
        'attraction_type': 'landmark',
        'doro_style': 'default',
        'time_of_day': 'afternoon',
        'weather': 'sunny',
        'season': 'autumn',
        'mood': 'happy'
    }
    
    # 发送请求
    url = f"{API_BASE_URL}/api/doro/generate-video"
    
    print(f"📡 发送请求到: {url}")
    print(f"📦 请求参数:")
    for key, value in data.items():
        print(f"  - {key}: {value}")
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            files=files,
            data=data,
            timeout=900  # 15分钟超时
        )
        
        print(f"\n📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("✅ 视频生成成功！")
                print(f"📝 消息: {result.get('message', '')}")
                
                if result.get("video_url"):
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
                        print(f"🔗 视频URL: {result['video_url'][:100]}...")
                
                if result.get("filename"):
                    print(f"📁 文件名: {result['filename']}")
                    
                if result.get("duration"):
                    print(f"⏱️ 生成时长: {result['duration']}秒")
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
                
        else:
            print(f"❌ 请求失败")
            try:
                error_detail = response.json()
                print(f"错误详情: {error_detail}")
            except:
                print(f"错误响应: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("⏱️ 请求超时（超过15分钟）")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请检查网络或API服务")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def test_simple_image_generation():
    """测试简单的图片生成"""
    
    print("\n🖼️ 先测试Doro合影图片生成...")
    
    # 创建测试用的图片
    user_photo = create_dummy_image()
    
    files = {
        'user_photo': ('user.png', user_photo, 'image/png')
    }
    
    data = {
        'attraction_name': '故宫博物院',
        'location': '北京市东城区',
        'doro_id': 'doro2',  # 使用预设的doro2
        'attraction_type': 'cultural',
        'doro_style': 'default'
    }
    
    url = f"{API_BASE_URL}/api/doro/generate"
    
    print(f"📡 发送请求到: {url}")
    
    try:
        response = requests.post(
            url,
            files=files,
            data=data,
            timeout=120  # 2分钟超时
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("✅ 图片生成成功！")
                print(f"📝 消息: {result.get('message', '')}")
                
                if result.get("image_url"):
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
                
                if result.get("filename"):
                    print(f"📁 文件名: {result['filename']}")
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"错误详情: {error_detail}")
            except:
                print(f"错误响应: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Doro视频生成功能测试（简化版）")
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
