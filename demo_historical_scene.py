"""
🎨 OrientDiscover 历史场景生成演示
展示历史查询 + AI场景描述的完整功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict

class HistoricalSceneDemo:
    """历史场景生成演示器"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        
        # 精彩的演示案例
        self.demo_cases = [
            {
                'title': '🏯 德川幕府的江户城下町',
                'description': '1600年德川家康建立江户幕府时期的东京街景',
                'lat': 35.7148,
                'lng': 139.7967,
                'year': 1600,
                'highlight': '日本从战国走向和平统一的历史转折点'
            },
            {
                'title': '🏛️ 盛世大唐的长安都城',
                'description': '800年唐朝鼎盛时期的国际化都市',
                'lat': 39.9042,
                'lng': 116.4074,
                'year': 800,
                'highlight': '中华文明最开放自信的黄金时代'
            },
            {
                'title': '⛪ 查理大帝时代的教皇国',
                'description': '800年基督教欧洲精神中心的罗马',
                'lat': 41.9028,
                'lng': 12.4964,
                'year': 800,
                'highlight': '东西方文明交汇的神圣之地'
            }
        ]
    
    async def run_scene_generation_demo(self):
        """运行历史场景生成演示"""
        print("🎨 OrientDiscover 历史场景生成演示")
        print("=" * 60)
        print("基于Historical-basemaps + AI的时空可视化体验")
        print()
        
        # 等待服务启动
        await self.wait_for_service()
        
        # 显示生成能力
        await self.show_generation_capabilities()
        
        # 执行场景生成演示
        await self.demo_scene_generation()
        
        print("\n" + "=" * 60)
        print("🎉 历史场景生成演示完成！")
        print("✨ OrientDiscover现已支持AI历史场景可视化！")
    
    async def wait_for_service(self):
        """等待后端服务启动"""
        print("⏳ 等待后端服务启动...")
        
        for i in range(15):  # 最多等待15秒
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_base}/api/health") as response:
                        if response.status == 200:
                            print("✅ 后端服务已就绪")
                            return
            except:
                pass
            
            await asyncio.sleep(1)
            if i % 3 == 0:
                print(f"   等待中... {i+1}/15秒")
        
        print("⚠️ 服务未完全启动，但继续演示...")
    
    async def show_generation_capabilities(self):
        """显示图像生成能力"""
        print("\n🔧 历史场景生成能力检查")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/historical/generation-capabilities") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success'):
                            capabilities = data.get('capabilities', {})
                            
                            print(f"🎯 API状态: {'已配置' if data.get('api_configured') else '演示模式'}")
                            print(f"🤖 当前模型: {capabilities.get('current_model', 'N/A')}")
                            print(f"🚀 目标模型: {capabilities.get('target_model', 'N/A')}")
                            
                            supported = capabilities.get('supported_features', [])
                            print(f"✅ 支持功能: {', '.join(supported)}")
                            
                            planned = capabilities.get('planned_features', [])
                            print(f"📋 计划功能: {', '.join(planned)}")
                        else:
                            print(f"❌ 能力检查失败: {data.get('error')}")
                    else:
                        print(f"❌ API调用失败: HTTP {response.status}")
        
        except Exception as e:
            print(f"❌ 能力检查异常: {e}")
    
    async def demo_scene_generation(self):
        """演示历史场景生成"""
        print("\n🎨 历史场景生成演示")
        print("-" * 30)
        
        success_count = 0
        
        for i, case in enumerate(self.demo_cases):
            print(f"\n📍 演示 {i+1}: {case['title']}")
            print(f"🎯 {case['description']}")
            print(f"💡 {case['highlight']}")
            print(f"📊 坐标: ({case['lat']}, {case['lng']}) | 年份: {case['year']}")
            
            # 执行历史场景生成
            result = await self.generate_scene_api(case)
            
            if result:
                self.display_scene_result(result, case)
                success_count += 1
            
            print("-" * 50)
            await asyncio.sleep(1)  # 稍作停顿，便于观看
        
        print(f"\n📊 演示总结: {success_count}/{len(self.demo_cases)} 成功")
    
    async def generate_scene_api(self, case: Dict) -> Dict:
        """调用历史场景生成API"""
        try:
            request_data = {
                'latitude': case['lat'],
                'longitude': case['lng'],
                'year': case['year']
            }
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/api/generate-historical-scene",
                    json=request_data
                ) as response:
                    
                    api_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        result['api_response_time'] = api_time
                        return result
                    else:
                        print(f"❌ API调用失败: HTTP {response.status}")
                        error_text = await response.text()
                        print(f"   错误详情: {error_text}")
                        return None
        
        except Exception as e:
            print(f"❌ API调用异常: {e}")
            return None
    
    def display_scene_result(self, result: Dict, case: Dict):
        """展示场景生成结果"""
        if result.get('success'):
            historical_info = result.get('historical_info', {})
            scene_info = result.get('generated_scene', {})
            
            print(f"✅ 场景生成成功! (API耗时: {result.get('api_response_time', 0):.3f}秒)")
            print()
            
            # 🏛️ 历史查询结果
            print(f"📚 Historical-basemaps查询结果:")
            print(f"   🏛️ 政治实体: {historical_info.get('political_entity', 'N/A')}")
            print(f"   👑 统治者: {historical_info.get('ruler_or_power', 'N/A')}")
            print(f"   🌍 文化圈: {historical_info.get('cultural_region', 'N/A')}")
            print(f"   📊 边界精度: {self.get_precision_text(historical_info.get('border_precision', 0))}")
            
            # 🎨 AI场景生成结果
            print(f"\n🎨 AI场景生成结果:")
            print(f"   🤖 生成模型: {scene_info.get('generation_model', 'N/A')}")
            print(f"   ⚡ 生成耗时: {scene_info.get('generation_time', 0):.3f}秒")
            
            if scene_info.get('demo_mode'):
                print(f"   🎭 运行模式: 演示模式")
                if scene_info.get('note'):
                    print(f"   💡 说明: {scene_info['note']}")
            
            # 📝 场景描述
            scene_description = scene_info.get('scene_description', '')
            if scene_description:
                print(f"\n📝 AI生成的历史场景描述:")
                # 格式化显示描述，保持原有的分段
                lines = scene_description.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                    else:
                        print()
            
        else:
            print(f"❌ 场景生成失败: {result.get('error', '未知错误')}")
    
    def get_precision_text(self, precision: int) -> str:
        """边界精度文本"""
        precision_map = {
            1: '大致边界',
            2: '中等精度', 
            3: '高精度'
        }
        return precision_map.get(precision, f'未知精度')


async def main():
    """主演示函数"""
    print("🌍 OrientDiscover 历史场景生成功能演示")
    print("🎯 展示Historical-basemaps + AI的完整时空可视化")
    print()
    
    demo = HistoricalSceneDemo()
    
    # 运行完整演示
    await demo.run_scene_generation_demo()


if __name__ == "__main__":
    print("🚀 启动历史场景生成演示...")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⭐ 感谢观看OrientDiscover历史场景生成演示!")
        print(f"🎨 我们成功实现了Historical-basemaps + AI的时空可视化!")

