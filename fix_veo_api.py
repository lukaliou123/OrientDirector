#!/usr/bin/env python3
"""
修复Veo 3 API图片参数格式
"""

# 读取文件
with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 要替换的代码段
old_code = '''            # 创建符合Veo 3 API要求的图片数据结构
            # API明确要求包含bytesBase64Encoded和mimeType字段
            image_input = {
                "bytesBase64Encoded": image_base64,
                "mimeType": "image/png"
            }
            
            # 调用Veo 3生成视频
            operation = client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=video_prompt,
                image=image_input,  # 使用正确的字典格式
            )'''

# 新的正确代码
new_code = '''            # 使用Google GenAI SDK的Blob对象创建图片参数
            from google.genai import types
            
            # 创建Blob对象，这是Google GenAI SDK的正确方式
            image_blob = types.Blob(
                mime_type="image/png",
                data=image_bytes  # 直接使用字节数据，不是base64
            )
            
            # 调用Veo 3生成视频
            operation = client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=video_prompt,
                image=image_blob,  # 使用Blob对象
            )'''

# 执行替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 写回文件
    with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复完成！")
else:
    print("❌ 未找到目标代码")
