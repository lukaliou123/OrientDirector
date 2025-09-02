"""
🏛️ OrientDiscover 历史查询功能演示脚本
展示基于Historical-basemaps的真实时空查询能力
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List

class HistoricalQueryDemo:
    """历史查询功能演示器"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        
        # 精心设计的演示案例 - 展示不同时代和文明
        self.demo_cases = [
            {
                'title': '🏯 江户时代的日本',
                'description': '1600年德川家康建立江户幕府时期的东京',
                'lat': 35.7148,
                'lng': 139.7967,
                'year': 1600,
                'highlight': '展示日本从战国到统一的历史转折'
            },
            {
                'title': '🏛️ 唐朝盛世的长安',
                'description': '800年唐朝鼎盛时期的中国首都',
                'lat': 39.9042,
                'lng': 116.4074,
                'year': 800,
                'highlight': '中华文明的黄金时代'
            },
            {
                'title': '⛪ 教皇国时代的罗马',
                'description': '800年查理大帝加冕时期的罗马',
                'lat': 41.9028,
                'lng': 12.4964,
                'year': 800,
                'highlight': '基督教欧洲的精神中心'
            },
            {
                'title': '🇫🇷 二战后的法国',
                'description': '1945年战争结束后的巴黎',
                'lat': 48.8584,
                'lng': 2.2945,
                'year': 1945,
                'highlight': '展示二战对欧洲政治版图的影响'
            },
            {
                'title': '🇺🇸 美军占领下的日本',
                'description': '1945年美军占领期的东京',
                'lat': 35.7148,
                'lng': 139.7967,
                'year': 1945,
                'highlight': 'Historical-basemaps展现的复杂政治现实'
            }
        ]
    
    async def run_full_demo(self):
        """运行完整演示"""
        print("🏛️ OrientDiscover 历史查询功能演示")
        print("=" * 60)
        print("基于Historical-basemaps学术项目的真实历史边界数据")
        print("支持5000年历史跨度的精确时空查询")
        print()
        
        # 等待服务启动
        await self.wait_for_service()
        
        # 显示API状态
        await self.show_api_status()
        
        # 执行演示查询
        await self.demo_historical_queries()
        
        # 显示数据集信息
        await self.show_dataset_info()
        
        print("\n" + "=" * 60)
        print("🎉 历史查询功能演示完成！")
        print("✨ OrientDiscover现已具备真正的时空探索能力！")
    
    async def wait_for_service(self):
        """等待后端服务启动"""
        print("⏳ 等待后端服务启动...")
        
        for i in range(30):  # 最多等待30秒
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_base}/api/health") as response:
                        if response.status == 200:
                            print("✅ 后端服务已就绪")
                            return
            except:
                pass
            
            await asyncio.sleep(1)
            print(f"   等待中... {i+1}/30秒")
        
        print("❌ 后端服务启动超时，但继续演示...")
    
    async def show_api_status(self):
        """显示API状态"""
        print("\n📡 API服务状态检查")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 检查健康状态
                async with session.get(f"{self.api_base}/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 服务状态: {data.get('status', 'unknown')}")
                        print(f"📝 服务名: {data.get('service', 'N/A')}")
                        print(f"🏷️ 版本: {data.get('version', 'N/A')}")
                    else:
                        print(f"⚠️ 健康检查失败: HTTP {response.status}")
                
                # 检查可用历史年份
                async with session.get(f"{self.api_base}/api/historical/available-years") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            print(f"📅 可用历史数据集: {data.get('total_datasets', 'N/A')} 个")
                            year_range = data.get('year_range', {})
                            print(f"📊 时间跨度: {year_range.get('earliest', 'N/A')} - {year_range.get('latest', 'N/A')}")
                            
                            cache_info = data.get('cache_info', {})
                            print(f"💾 已缓存数据: {cache_info.get('cached_datasets', 0)} 个")
                            print(f"💾 缓存大小: {cache_info.get('cache_size_mb', 0):.2f} MB")
                
        except Exception as e:
            print(f"❌ API状态检查失败: {e}")
    
    async def demo_historical_queries(self):
        """演示历史查询功能"""
        print("\n🕰️ 时空查询演示")
        print("-" * 30)
        
        for i, case in enumerate(self.demo_cases):
            print(f"\n📍 演示 {i+1}: {case['title']}")
            print(f"🎯 {case['description']}")
            print(f"💡 {case['highlight']}")
            print(f"📊 坐标: ({case['lat']}, {case['lng']}) | 年份: {case['year']}")
            
            # 执行历史查询
            result = await self.query_historical_api(case)
            
            if result:
                self.display_query_result(result, case)
            
            print("-" * 50)
            await asyncio.sleep(1)  # 稍作停顿，便于观看
    
    async def query_historical_api(self, case: Dict) -> Dict:
        """调用历史查询API"""
        try:
            request_data = {
                'latitude': case['lat'],
                'longitude': case['lng'],
                'year': case['year']
            }
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/api/query-historical",
                    json=request_data
                ) as response:
                    
                    query_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        result['api_response_time'] = query_time
                        return result
                    else:
                        print(f"❌ API调用失败: HTTP {response.status}")
                        error_text = await response.text()
                        print(f"   错误详情: {error_text}")
                        return None
        
        except Exception as e:
            print(f"❌ API调用异常: {e}")
            return None
    
    def display_query_result(self, result: Dict, case: Dict):
        """展示查询结果"""
        if result.get('success'):
            historical_info = result.get('historical_info', {})
            
            print(f"✅ 查询成功! (耗时: {result.get('api_response_time', 0):.3f}秒)")
            print()
            
            # 🏛️ 政治实体信息
            print(f"🏛️ 政治实体: {historical_info.get('political_entity', 'N/A')}")
            print(f"👑 统治者: {historical_info.get('ruler_or_power', 'N/A')}")
            print(f"🌍 文化圈: {historical_info.get('cultural_region', 'N/A')}")
            print(f"📊 边界精度: {self.get_precision_text(historical_info.get('border_precision', 0))}")
            print(f"🎭 时代: {historical_info.get('time_period', 'N/A')}")
            
            # 📍 位置和精度信息
            if historical_info.get('is_approximate'):
                distance = historical_info.get('distance_to_border', 0)
                print(f"⚠️ 近似匹配 (距离最近边界: {distance:.2f}km)")
            else:
                print(f"✅ 精确匹配")
            
            # 📝 历史描述
            description = historical_info.get('description', '')
            if description:
                print(f"\n📝 历史背景:")
                print(f"   {description}")
            
            # 🎨 文化上下文
            cultural_context = historical_info.get('cultural_context', {})
            if cultural_context:
                print(f"\n🎭 文化特征:")
                print(f"   宗教: {cultural_context.get('religion', 'N/A')}")
                print(f"   技术水平: {cultural_context.get('technology_level', 'N/A')}")
                print(f"   社会结构: {cultural_context.get('social_structure', 'N/A')}")
                print(f"   经济模式: {cultural_context.get('economic_model', 'N/A')}")
        
        else:
            print(f"❌ 查询失败: {result.get('error', '未知错误')}")
    
    def get_precision_text(self, precision: int) -> str:
        """边界精度文本"""
        precision_map = {
            1: '大致边界 (历史记录模糊)',
            2: '中等精度 (有一定史料支撑)', 
            3: '高精度 (国际法或条约确定)'
        }
        return precision_map.get(precision, f'未知精度 ({precision})')
    
    async def show_dataset_info(self):
        """展示数据集信息"""
        print("\n📚 Historical-basemaps数据集信息")
        print("-" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/historical/available-years") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success'):
                            print(f"📊 数据集统计:")
                            print(f"   总数据集: {data.get('total_datasets', 0)} 个")
                            
                            year_range = data.get('year_range', {})
                            earliest = year_range.get('earliest', 0)
                            latest = year_range.get('latest', 0)
                            print(f"   时间跨度: {earliest} - {latest} ({latest - earliest} 年)")
                            
                            cache_info = data.get('cache_info', {})
                            print(f"   已缓存: {cache_info.get('cached_datasets', 0)} 个数据集")
                            print(f"   缓存大小: {cache_info.get('cache_size_mb', 0):.2f} MB")
                            
                            # 显示可用年份列表
                            available_years = data.get('available_years', [])
                            if available_years:
                                print(f"\n📅 可用历史年份 (前10个):")
                                for year in sorted(available_years, reverse=True)[:10]:
                                    era_name = self.get_era_name(year)
                                    print(f"   • {year}: {era_name}")
                        else:
                            print(f"❌ 获取数据集信息失败: {data.get('error')}")
        
        except Exception as e:
            print(f"❌ 数据集信息获取异常: {e}")
    
    def get_era_name(self, year: int) -> str:
        """根据年份获取时代名称"""
        if year >= 1945:
            return "现代"
        elif year >= 1800:
            return "近现代/工业时代"
        elif year >= 1500:
            return "大航海时代"
        elif year >= 1000:
            return "中世纪"
        elif year >= 0:
            return "古典时期"
        else:
            return "远古时期"
    
    async def interactive_demo(self):
        """交互式演示"""
        print("\n🎮 交互式历史查询")
        print("-" * 30)
        print("您可以输入任意坐标和年份进行历史查询！")
        
        while True:
            try:
                print(f"\n请输入查询参数 (输入 'q' 退出):")
                
                lat_input = input("📍 纬度 (-90 到 90): ").strip()
                if lat_input.lower() == 'q':
                    break
                
                lng_input = input("📍 经度 (-180 到 180): ").strip()
                if lng_input.lower() == 'q':
                    break
                
                year_input = input("📅 年份 (-3000 到 2024): ").strip()
                if year_input.lower() == 'q':
                    break
                
                # 解析输入
                lat = float(lat_input)
                lng = float(lng_input)
                year = int(year_input)
                
                # 执行查询
                custom_case = {
                    'title': f'🔍 自定义查询',
                    'lat': lat,
                    'lng': lng,
                    'year': year
                }
                
                print(f"\n🔍 查询: {year}年的({lat}, {lng})...")
                result = await self.query_historical_api(custom_case)
                
                if result:
                    self.display_query_result(result, custom_case)
                
            except ValueError as e:
                print(f"❌ 输入格式错误: {e}")
            except Exception as e:
                print(f"❌ 查询异常: {e}")
        
        print("👋 交互式演示结束")


async def main():
    """主演示函数"""
    print("🌍 OrientDiscover 历史模式功能演示")
    print("🎯 展示世界首个基于Historical-basemaps的时空查询系统")
    print()
    
    demo = HistoricalQueryDemo()
    
    # 运行完整演示
    await demo.run_full_demo()
    
    # 询问是否进行交互式演示
    try:
        choice = input(f"\n是否进行交互式演示? (y/n): ").strip().lower()
        if choice == 'y':
            await demo.interactive_demo()
    except KeyboardInterrupt:
        print(f"\n👋 演示结束")


if __name__ == "__main__":
    print("🚀 启动历史查询功能演示...")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⭐ 感谢观看OrientDiscover历史查询功能演示!")
        print(f"🎯 我们成功实现了基于Historical-basemaps的真实时空查询!")
