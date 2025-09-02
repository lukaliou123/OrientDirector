import time
import os
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# 配置 Google Gemini API
api_key = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=api_key)

# 创建客户端
try:
    from google import genai as google_genai
    client = google_genai.Client(api_key=api_key)
    print("✅ 客户端初始化成功")
except ImportError:
    print("❌ google.genai 包未安装")
    client = None

def generate_video_from_image(image_path, prompt):
    """基于图片生成视频"""
    try:
        print(f"🎬 正在生成视频...")
        print(f"📁 图片: {image_path}")
        print(f"📝 提示: {prompt}")
        
        # 加载图片
        image = Image.open(image_path)
        
        if client:
            # 使用 Veo 3 生成视频
            operation = client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=prompt,
                image=image,
            )
            
            # 等待视频生成完成
            print("⏳ 视频生成中，请等待...")
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                print("⏰ 仍在生成中...")
            
            # 下载并保存视频
            video = operation.response.generated_videos[0]
            client.files.download(file=video.video)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
            video.video.save(filename)
            
            print(f"✅ 视频生成成功: {filename}")
            return filename
        else:
            print("❌ 客户端未初始化，无法生成视频")
            return None
            
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return None

def main():
    """主函数"""
    print("🎥 图片转视频工具")
    print("=" * 40)
    
    # 默认图片路径
    default_image = "/app/cat_nano_banana_20250831_123113.png"
    
    # 获取图片路径
    if os.path.exists(default_image):
        image_path = default_image
        print(f"📁 使用默认图片: {image_path}")
    else:
        image_path = input("请输入图片路径: ").strip()
        if not os.path.exists(image_path):
            print("❌ 图片文件不存在")
            return
    
    # 获取提示词
    prompt = input("让图片中的人物动起来，微风吹动衣服，自然的呼吸和眨眼动作").strip()
    if not prompt:
        prompt = "让图片中的人物动起来，微风吹动衣服，自然的呼吸和眨眼动作"
    
    # 生成视频
    result = generate_video_from_image(image_path, prompt)
    
    if result:
        print(f"🎉 完成！视频文件: {result}")
    else:
        print("❌ 生成失败")

if __name__ == "__main__":
    main()
