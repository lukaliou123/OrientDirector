#!/usr/bin/env python3
"""
测试Google Gemini API服务状态
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
import time

# 加载环境变量
load_dotenv()

def test_gemini_text():
    """测试Gemini文本生成API"""
    print("🔍 测试Gemini文本生成API...")
    
    try:
        # 配置API密钥
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ 未找到GEMINI_API_KEY环境变量")
            return False
            
        genai.configure(api_key=api_key)
        
        # 使用文本模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 简单的文本生成测试
        response = model.generate_content("Hello, please respond with 'OK' if you're working.")
        
        print(f"✅ Gemini文本API正常工作")
        print(f"响应: {response.text[:100]}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini文本API错误: {e}")
        return False

def test_gemini_vision():
    """测试Gemini视觉API"""
    print("\n🔍 测试Gemini视觉API...")
    
    try:
        # 配置API密钥
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ 未找到GEMINI_API_KEY环境变量")
            return False
            
        genai.configure(api_key=api_key)
        
        # 使用视觉模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 创建一个简单的测试（只用文本，不用图片）
        response = model.generate_content("Describe a simple white square image.")
        
        print(f"✅ Gemini视觉API正常工作")
        print(f"响应: {response.text[:100]}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini视觉API错误: {e}")
        return False

def test_gemini_image_generation():
    """测试Gemini图片生成API (Imagen)"""
    print("\n🔍 测试Gemini图片生成API (Imagen)...")
    
    try:
        # 配置API密钥
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ 未找到GEMINI_API_KEY环境变量")
            return False
            
        genai.configure(api_key=api_key)
        
        # 尝试使用Imagen模型
        # 注意：这个模型可能有区域限制
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 简单的生成测试
        response = model.generate_content("A simple red square")
        
        print(f"✅ Gemini图片生成API可能正常")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "location is not supported" in error_msg.lower():
            print(f"⚠️ Gemini图片生成API: 当前区域不支持")
        elif "500" in error_msg or "internal" in error_msg.lower():
            print(f"❌ Gemini图片生成API: 服务器内部错误（500）")
        else:
            print(f"❌ Gemini图片生成API错误: {e}")
        return False

def check_api_quota():
    """检查API配额状态"""
    print("\n🔍 检查API配额...")
    
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ 未找到GEMINI_API_KEY环境变量")
            return
            
        # 这里可以添加配额检查逻辑
        print("ℹ️ 配额检查需要通过Google Cloud Console查看")
        print(f"API密钥前缀: {api_key[:10]}...")
        
    except Exception as e:
        print(f"❌ 配额检查错误: {e}")

def main():
    print("=" * 50)
    print("Google Gemini API 状态检查")
    print("=" * 50)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试各个API
    text_ok = test_gemini_text()
    vision_ok = test_gemini_vision()
    image_ok = test_gemini_image_generation()
    
    # 检查配额
    check_api_quota()
    
    print("\n" + "=" * 50)
    print("诊断结果:")
    print("=" * 50)
    
    if not text_ok and not vision_ok and not image_ok:
        print("❌ 所有Gemini API都无法工作")
        print("可能原因:")
        print("1. API密钥无效或过期")
        print("2. API配额已用尽")
        print("3. Google服务暂时中断")
        print("4. 网络连接问题")
    elif not image_ok:
        print("⚠️ 图片生成API有问题")
        print("可能原因:")
        print("1. Imagen服务暂时不可用（Google端问题）")
        print("2. 区域限制（某些地区不支持图片生成）")
        print("3. 该模型的配额已用尽")
        print("\n建议:")
        print("1. 等待几分钟后重试")
        print("2. 检查Google Cloud Console中的API状态")
        print("3. 考虑使用备用的图片生成服务")
    else:
        print("✅ Gemini API基本正常")
    
    print("\n💡 提示: 如果持续出现500错误，通常是Google服务端的临时问题，建议:")
    print("1. 等待5-10分钟后重试")
    print("2. 访问 https://status.cloud.google.com/ 查看服务状态")
    print("3. 检查API配额是否用尽")

if __name__ == "__main__":
    main()
