import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置 Google Gemini API
api_key = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=api_key)

# 创建模型
model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

prompt = (
    "给图中所有人穿上日本武士的服饰，背景是富士山，不要改变人脸的面貌，原图中只有人是需要换服饰并保留的，其他原图中的物品都不要保留。"
)

prompt2 = (
    "给图中人物都换成古代服装，站在金字塔旁边和埃及艳后合影，不要改变人脸的面貌和表情，但要变年轻一些（18岁），埃及艳后不要太严肃，要有亲密感，原图中只有人是需要换服饰并保留的，其他原图中的物品都不要保留。"
)

prompt3 = (
    "给图中3个人穿上明朝武将的服饰，背景是长城，不要改变人脸的面貌，原图中只有人是需要换服饰并保留的，其他原图中的物品都不要保留，头饰和帽子都要改成古代的，都要有佩剑，不要举大拇指，要威风凛凛。"
)

prompt4 = (
    "去掉图中中间的人的眼镜，其他保留不要改变"
)

# 检查图片路径是否存在，如果不存在则只使用文本提示
image_path = "/app/cat_nano_banana_20250831_132307.png"
contents = [prompt4]

if os.path.exists(image_path):
    try:
        image = Image.open(image_path)
        contents.append(image)
        print(f"✅ 已加载图片: {image_path}")
    except Exception as e:
        print(f"⚠️ 无法加载图片 {image_path}: {e}")
        print("将仅使用文本提示生成图片")
else:
    print(f"⚠️ 图片文件不存在: {image_path}")
    print("将仅使用文本提示生成图片")

# 生成内容
try:
    print("🎨 正在生成图片...")
    response = model.generate_content(contents)
    
    # 处理响应
    response_dict = response.to_dict()
    
    if "candidates" in response_dict and len(response_dict["candidates"]) > 0:
        parts = response_dict["candidates"][0]["content"]["parts"]
        
        for part in parts:
            # 如果有文本内容
            if "text" in part:
                print("生成的文本:", part["text"])
            
            # 如果有图像数据
            elif "inline_data" in part:
                # 解码base64图像数据
                image_data = base64.b64decode(part["inline_data"]["data"])
                
                # 使用PIL保存图像
                generated_image = Image.open(BytesIO(image_data))
                
                # 生成带时间戳的文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cat_nano_banana_{timestamp}.png"
                
                generated_image.save(filename)
                print(f"✅ 图像已保存: {filename}")
    else:
        print("❌ 没有生成任何内容")
        
except Exception as e:
    print(f"❌ 生成图片时出错: {e}")
    print("请检查API密钥和网络连接")




