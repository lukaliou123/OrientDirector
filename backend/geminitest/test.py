import json
import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置 Google Gemini API
genai.configure(api_key="AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0")
model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

def generate_image(prompt, filename=None):
    """使用 AI 生成图像"""
    try:
        print(f"🎨 正在生成图像: {prompt}")
        response = model.generate_content([prompt])
        response = response.to_dict()
        
        # 提取图像数据
        bytes_data = response["candidates"][0]["content"]["parts"][-1]["inline_data"]["data"]
        generated_img = base64.b64decode(bytes_data)
        
        # 如果没有指定文件名，使用时间戳生成
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
        
        # 保存图像到本地
        with open(filename, 'wb') as out:
            out.write(generated_img)
        
        print(f"✅ 图像已保存到本地: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ 图像生成失败: {e}")
        return None

def upload_to_imgbb(image_path, imgbb_api_key):
    """上传图像到 ImgBB"""
    try:
        print(f"📤 正在上传图像到 ImgBB: {image_path}")
        
        # 读取图像文件并转换为 Base64
        with open(image_path, 'rb') as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        if not image_b64:
            raise ValueError("图像文件为空")
        
        # 构建上传请求
        upload_url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": imgbb_api_key,
            "image": image_b64,
            "name": os.path.basename(image_path)
        }
        
        # 发送上传请求
        resp = requests.post(upload_url, data=payload, timeout=60)
        resp.raise_for_status()
        
        resp_json = resp.json()
        
        if "data" not in resp_json:
            raise Exception(f"ImgBB 上传失败: {resp_json}")
        
        uploaded_url = resp_json["data"]["url"]
        print(f"✅ 图像上传成功: {uploaded_url}")
        return uploaded_url
        
    except Exception as e:
        print(f"❌ 图像上传失败: {e}")
        return None

def download_image(url, filename=None):
    """从 URL 下载图像到本地"""
    try:
        print(f"📥 正在下载图像: {url}")
        
        # 如果没有指定文件名，从 URL 中提取或使用时间戳
        if not filename:
            if url.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                filename = url.split('/')[-1]
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"downloaded_image_{timestamp}.png"
        
        # 下载图像
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 保存到本地
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 图像下载成功: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ 图像下载失败: {e}")
        return None

def main():
    """主函数"""
    # 图像生成提示词
    prompt = "Create nano-sized banana in a lab setting."
    
    # 生成图像
    generated_filename = generate_image(prompt)
    if not generated_filename:
        print("❌ 程序终止：图像生成失败")
        return
    
    # 获取 ImgBB API 密钥
    imgbb_api_key = os.getenv("IMGBB_API_KEY")
    if not imgbb_api_key:
        print("⚠️  IMGBB_API_KEY 环境变量未设置，跳过上传步骤")
        print(f"📁 生成的图像已保存在本地: {generated_filename}")
        return
    
    # 上传到 ImgBB
    uploaded_url = upload_to_imgbb(generated_filename, imgbb_api_key)
    if not uploaded_url:
        print("❌ 上传失败，但本地图像已保存")
        return
    
    # 下载上传后的图像（可选，用于验证）
    print("\n🔄 正在下载上传后的图像进行验证...")
    downloaded_filename = download_image(uploaded_url, f"verified_{generated_filename}")
    
    if downloaded_filename:
        print(f"\n🎉 所有操作完成！")
        print(f"📁 原始生成图像: {generated_filename}")
        print(f"🌐 在线图像链接: {uploaded_url}")
        print(f"📁 验证下载图像: {downloaded_filename}")
    else:
        print(f"\n✅ 主要操作完成！")
        print(f"📁 生成的图像: {generated_filename}")
        print(f"🌐 在线图像链接: {uploaded_url}")

if __name__ == "__main__":
    main()