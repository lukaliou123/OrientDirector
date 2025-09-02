"""
🎨 预生成演示图片工具
当API配额可用时，批量生成演示所需的历史场景图片
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List

# 添加backend到路径
sys.path.append('backend')

from nano_banana_service import nano_banana_service
from historical_service import historical_service

class DemoImageGenerator:
    """演示图片批量生成器"""
    
    def __init__(self):
        self.index_path = "static/pregenerated_images/demo_scenes_index.json"
        self.output_dir = "static/pregenerated_images/"
        
        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_all_demo_images(self):
        """批量生成所有演示图片"""
        print("🎨 开始批量生成演示历史场景图片")
        print("=" * 60)
        
        # 检查API状态
        if not nano_banana_service.client_available:
            print("❌ Gemini API未配置，无法生成图片")
            print("💡 请在.env中配置GEMINI_API_KEY")
            return
        
        # 加载场景索引
        with open(self.index_path, 'r', encoding='utf-8') as f:
            scenes_index = json.load(f)
        
        demo_scenes = scenes_index.get('demo_scenes', [])
        print(f"📋 发现 {len(demo_scenes)} 个演示场景需要生成")
        print()
        
        success_count = 0
        
        for i, scene_config in enumerate(demo_scenes):
            print(f"🎯 生成 {i+1}/{len(demo_scenes)}: {scene_config['title']}")
            print(f"   政治实体: {scene_config['political_entity']}")
            print(f"   年份: {scene_config['year']}")
            print(f"   坐标: ({scene_config['lat']}, {scene_config['lng']})")
            
            try:
                # 1. 执行历史查询获取真实数据
                historical_result = await historical_service.query_historical_location(
                    scene_config['lat'], scene_config['lng'], scene_config['year']
                )
                
                if not historical_result['success']:
                    print(f"❌ 历史查询失败: {historical_result.get('error')}")
                    continue
                
                # 2. 临时关闭演示模式，强制实时生成
                original_demo_mode = nano_banana_service.demo_mode
                nano_banana_service.demo_mode = False
                
                # 3. 生成图片
                generation_result = await nano_banana_service.generate_historical_scene_image(
                    historical_result, scene_config['lat'], scene_config['lng']
                )
                
                # 4. 恢复演示模式设置
                nano_banana_service.demo_mode = original_demo_mode
                
                if generation_result['success'] and generation_result.get('images'):
                    # 5. 移动图片到预生成目录并重命名
                    generated_image_path = generation_result['images'][0].replace('/static/', 'static/')
                    target_filename = scene_config['image_filename']
                    target_path = os.path.join(self.output_dir, target_filename)
                    
                    # 复制/移动文件
                    import shutil
                    if os.path.exists(generated_image_path):
                        shutil.copy2(generated_image_path, target_path)
                        print(f"✅ 图片已保存: {target_filename}")
                        
                        # 6. 更新索引状态
                        scene_config['generated'] = True
                        scene_config['generated_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        success_count += 1
                    else:
                        print(f"❌ 生成的图片文件不存在: {generated_image_path}")
                else:
                    print(f"❌ 图片生成失败: {generation_result.get('error', '未知错误')}")
            
            except Exception as e:
                print(f"❌ 生成异常: {e}")
            
            print()
            
            # 避免API过度调用
            if i < len(demo_scenes) - 1:
                print("⏳ 等待18秒避免API限制...")
                await asyncio.sleep(18)
        
        # 更新索引文件
        scenes_index['generation_info']['generation_status'] = 'completed' if success_count == len(demo_scenes) else 'partial'
        scenes_index['generation_info']['generated_count'] = success_count
        scenes_index['generation_info']['last_generation_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(scenes_index, f, ensure_ascii=False, indent=2)
        
        print("=" * 60)
        print(f"🎉 演示图片生成完成!")
        print(f"📊 成功率: {success_count}/{len(demo_scenes)}")
        print(f"💾 图片保存在: {self.output_dir}")
    
    async def generate_single_scene(self, scene_id: str):
        """生成单个演示场景图片"""
        with open(self.index_path, 'r', encoding='utf-8') as f:
            scenes_index = json.load(f)
        
        scene_config = None
        for scene in scenes_index['demo_scenes']:
            if scene['id'] == scene_id:
                scene_config = scene
                break
        
        if not scene_config:
            print(f"❌ 未找到场景ID: {scene_id}")
            return
        
        print(f"🎨 生成单个场景: {scene_config['title']}")
        
        # 执行生成流程（类似上面的逻辑）
        # ... 简化版本，需要时可以实现
    
    def list_demo_scenes(self):
        """列出所有演示场景"""
        with open(self.index_path, 'r', encoding='utf-8') as f:
            scenes_index = json.load(f)
        
        print("📋 演示场景列表:")
        print("-" * 40)
        
        for i, scene in enumerate(scenes_index['demo_scenes']):
            status = "✅ 已生成" if scene.get('generated', False) else "🔄 待生成"
            print(f"{i+1}. {scene['title']}")
            print(f"   ID: {scene['id']}")
            print(f"   政治实体: {scene['political_entity']} ({scene['year']}年)")
            print(f"   状态: {status}")
            
            if scene.get('generated_time'):
                print(f"   生成时间: {scene['generated_time']}")
            print()


async def main():
    """主函数"""
    print("🎨 OrientDiscover 演示图片生成工具")
    print()
    
    generator = DemoImageGenerator()
    
    print("选择操作:")
    print("1. 📋 列出演示场景")
    print("2. 🎨 生成所有演示图片") 
    print("3. 🔧 检查API状态")
    
    try:
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == '1':
            generator.list_demo_scenes()
        elif choice == '2':
            confirm = input("⚠️ 这将调用真实API生成图片，是否继续? (y/n): ").strip().lower()
            if confirm == 'y':
                await generator.generate_all_demo_images()
            else:
                print("🔄 操作已取消")
        elif choice == '3':
            print(f"🔧 API状态检查:")
            print(f"   客户端可用: {nano_banana_service.client_available}")
            print(f"   演示模式: {nano_banana_service.demo_mode}")
            if nano_banana_service.demo_scenes_index:
                scene_count = len(nano_banana_service.demo_scenes_index.get('demo_scenes', []))
                print(f"   预设场景: {scene_count} 个")
        else:
            print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n👋 操作已取消")


if __name__ == "__main__":
    asyncio.run(main())
