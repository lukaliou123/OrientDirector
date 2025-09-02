
import json
import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

# 加载环境变量
load_dotenv()

# 配置 Google Gemini API
api_key = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=api_key)

# 创建客户端（使用正确的方式）
model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

prompt = (
    "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
)

# 使用正确的方式生成内容
response = model.generate_content([prompt])

# 处理响应
try:
    # 将响应转换为字典格式
    response_dict = response.to_dict()
    
    # 提取图像数据
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
                image = Image.open(BytesIO(image_data))
                
                # 生成带时间戳的文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_nano_banana_{timestamp}.png"
                
                image.save(filename)
                print(f"✅ 图像已保存: {filename}")
                
except Exception as e:
    print(f"❌ 处理响应时出错: {e}")
    print("响应内容:", response)







