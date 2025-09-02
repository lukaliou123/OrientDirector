import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置 Google Gemini API
api_key = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=api_key)

# 创建客户端（注意：这里使用新的API方式）
try:
    from google import genai as google_genai
    client = google_genai.Client(api_key=api_key)
    print("✅ 使用 google.genai 客户端")
except ImportError:
    print("⚠️ google.genai 包未安装，尝试使用 google.generativeai")
    # 如果没有安装新的包，使用旧的方式
    model = genai.GenerativeModel('gemini-pro')
    client = None

def generate_video_with_new_api():
    """使用新的 google.genai API 生成视频"""
    if client is None:
        print("❌ 客户端未初始化，无法使用新API")
        return False
    
    # 视频生成提示词
    prompt = """一个古代中国武将站在长城上，身穿明朝盔甲，手持长剑，威风凛凛地望向远方。
    夕阳西下，金光洒在长城上，武将的盔甲闪闪发光。
    微风吹动他的战袍，展现出英雄气概。
    镜头从远景慢慢拉近，最后定格在武将坚毅的面容上。"""
    
    try:
        print("🎬 开始生成视频...")
        print(f"📝 提示词: {prompt}")
        
        # 启动视频生成操作
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=prompt,
        )
        
        print("⏳ 视频生成中，请耐心等待...")
        
        # 轮询操作状态直到视频准备就绪
        start_time = time.time()
        while not operation.done:
            elapsed_time = int(time.time() - start_time)
            print(f"⏰ 等待视频生成完成... ({elapsed_time}秒)")
            time.sleep(10)
            operation = client.operations.get(operation)
        
        # 下载生成的视频
        generated_video = operation.response.generated_videos[0]
        client.files.download(file=generated_video.video)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_video_{timestamp}.mp4"
        
        generated_video.video.save(filename)
        print(f"✅ 视频生成成功，已保存为: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ 视频生成失败: {e}")
        return False

def generate_video_alternative():
    """备用方案：使用其他方式生成视频描述"""
    print("🔄 尝试备用方案...")
    
    prompt = """请详细描述一个古代中国武将在长城上的视频场景：
    - 武将身穿明朝盔甲
    - 手持长剑，威风凛凛
    - 夕阳西下的长城背景
    - 镜头运动和光影效果"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        print("📝 视频场景描述:")
        print(response.text)
        
        # 保存描述到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_description_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"视频生成提示词:\n{prompt}\n\n")
            f.write(f"生成的场景描述:\n{response.text}")
        
        print(f"✅ 视频描述已保存为: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ 备用方案也失败了: {e}")
        return False

def main():
    """主函数"""
    print("🎥 视频生成测试脚本")
    print("=" * 50)
    
    # 尝试使用新的API生成视频
    success = generate_video_with_new_api()
    
    if not success:
        print("\n🔄 主要方案失败，尝试备用方案...")
        generate_video_alternative()
    
    print("\n🏁 脚本执行完成")

if __name__ == "__main__":
    main()
