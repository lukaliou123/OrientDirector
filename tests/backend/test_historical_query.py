"""
历史查询功能测试脚本
验证Historical-basemaps数据集成和查询功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
import json
import time
from historical_data_loader import historical_data_loader
from historical_service import historical_service

class HistoricalQueryTester:
    """历史查询功能测试器"""
    
    def __init__(self):
        self.test_cases = [
            {
                'name': '江户时代的东京',
                'lat': 35.7148, 
                'lng': 139.7967, 
                'year': 1600,
                'expected_keywords': ['japan', 'japanese', 'tokugawa', 'edo']
            },
            {
                'name': '法国大革命前的巴黎',
                'lat': 48.8584,
                'lng': 2.2945,
                'year': 1789,
                'expected_keywords': ['france', 'french', 'bourbon']
            },
            {
                'name': '罗马帝国鼎盛期的罗马',
                'lat': 41.9028,
                'lng': 12.4964,
                'year': 100,
                'expected_keywords': ['roman', 'rome', 'empire']
            },
            {
                'name': '明朝永乐年间的北京',
                'lat': 39.9042,
                'lng': 116.4074,
                'year': 1400,
                'expected_keywords': ['china', 'chinese', 'ming']
            },
            {
                'name': '美国独立前的纽约',
                'lat': 40.7580,
                'lng': -73.9855,
                'year': 1750,
                'expected_keywords': ['british', 'england', 'colony']
            }
        ]
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🏛️ 开始Historical查询功能完整测试")
        print("="*60)
        
        # 测试1: 数据加载器功能
        await self.test_data_loader()
        print()
        
        # 测试2: 历史查询服务
        await self.test_historical_service()
        print()
        
        # 测试3: 边界情况测试
        await self.test_edge_cases()
        print()
        
        # 测试4: 性能测试
        await self.test_performance()
        print()
        
        # 测试5: 缓存功能测试
        await self.test_cache_functionality()
        
        print("\n🎉 所有测试完成!")
    
    async def test_data_loader(self):
        """测试数据加载器"""
        print("📥 测试数据加载器功能...")
        
        try:
            # 测试获取可用年份
            available_years = await historical_data_loader.get_available_years()
            print(f"✅ 可用年份: {len(available_years)} 个")
            print(f"   年份范围: {min(available_years)} - {max(available_years)}")
            
            # 测试数据加载
            test_year = 1600
            print(f"\n📊 测试加载 {test_year} 年数据...")
            start_time = time.time()
            
            data = await historical_data_loader.get_historical_data(test_year)
            load_time = time.time() - start_time
            
            if data and 'features' in data:
                features_count = len(data['features'])
                print(f"✅ 数据加载成功: {features_count} 个政治实体")
                print(f"⚡ 加载耗时: {load_time:.3f}秒")
                
                # 检查数据结构
                if features_count > 0:
                    sample_feature = data['features'][0]
                    properties = sample_feature.get('properties', {})
                    print(f"📋 样本实体: {properties.get('NAME', 'N/A')}")
            else:
                print(f"❌ 数据加载失败")
            
            # 测试缓存信息
            cache_info = historical_data_loader.get_cache_info()
            print(f"\n💾 缓存统计:")
            print(f"   缓存文件: {cache_info['cache_count']} 个")
            print(f"   缓存大小: {cache_info['total_cache_size_mb']:.2f} MB")
            
        except Exception as e:
            print(f"❌ 数据加载器测试失败: {e}")
    
    async def test_historical_service(self):
        """测试历史查询服务"""
        print("🔍 测试历史查询服务...")
        
        success_count = 0
        
        for i, case in enumerate(self.test_cases):
            print(f"\n📍 测试案例 {i+1}: {case['name']}")
            print(f"   坐标: ({case['lat']}, {case['lng']})")
            print(f"   年份: {case['year']}")
            
            try:
                start_time = time.time()
                result = await historical_service.query_historical_location(
                    case['lat'], case['lng'], case['year']
                )
                query_time = time.time() - start_time
                
                if result['success']:
                    print(f"✅ 查询成功 (耗时: {query_time:.3f}秒)")
                    print(f"   政治实体: {result['political_entity']}")
                    print(f"   统治者: {result.get('ruler_or_power', 'N/A')}")
                    print(f"   文化圈: {result.get('cultural_region', 'N/A')}")
                    print(f"   时期: {result.get('time_period', 'N/A')}")
                    print(f"   边界精度: {result.get('border_precision', 'N/A')}")
                    
                    if result.get('is_approximate'):
                        print(f"   ⚠️ 近似结果 (距离: {result.get('distance_to_border', 'N/A')}km)")
                    
                    # 检查关键词匹配（简单验证）
                    entity_lower = result['political_entity'].lower()
                    cultural_lower = result.get('cultural_region', '').lower()
                    ruler_lower = result.get('ruler_or_power', '').lower()
                    
                    keyword_match = any(
                        keyword in entity_lower or keyword in cultural_lower or keyword in ruler_lower
                        for keyword in case['expected_keywords']
                    )
                    
                    if keyword_match:
                        print(f"✅ 关键词验证通过")
                    else:
                        print(f"⚠️ 关键词验证未匹配 (预期: {case['expected_keywords']})")
                    
                    success_count += 1
                else:
                    print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                    if 'fallback_result' in result:
                        print(f"🔄 降级结果: {result['fallback_result']}")
                
            except Exception as e:
                print(f"❌ 测试异常: {e}")
        
        print(f"\n📊 历史查询测试总结:")
        print(f"   成功率: {success_count}/{len(self.test_cases)} ({success_count/len(self.test_cases)*100:.1f}%)")
    
    async def test_edge_cases(self):
        """测试边界情况"""
        print("🔬 测试边界情况...")
        
        edge_cases = [
            {'lat': 0, 'lng': 0, 'year': 1000, 'name': '赤道几内亚湾'},
            {'lat': 90, 'lng': 0, 'year': 1000, 'name': '北极点'},
            {'lat': -90, 'lng': 0, 'year': 1000, 'name': '南极点'},
            {'lat': 39.9042, 'lng': 116.4074, 'year': -500, 'name': '公元前古代中国'},
            {'lat': 48.8584, 'lng': 2.2945, 'year': 3000, 'name': '超出范围年份'}
        ]
        
        for case in edge_cases:
            print(f"\n🧪 边界测试: {case['name']}")
            
            try:
                result = await historical_service.query_historical_location(
                    case['lat'], case['lng'], case['year']
                )
                
                if result['success']:
                    print(f"✅ 处理成功: {result['political_entity']}")
                else:
                    print(f"⚠️ 预期失败: {result.get('error', 'N/A')}")
                
            except Exception as e:
                print(f"❌ 异常处理: {e}")
    
    async def test_performance(self):
        """测试性能"""
        print("⚡ 测试查询性能...")
        
        # 批量查询测试
        batch_size = 5
        test_coordinates = [
            (35.7148, 139.7967, 1600),  # 东京
            (48.8584, 2.2945, 1789),    # 巴黎
            (41.9028, 12.4964, 100),    # 罗马
            (39.9042, 116.4074, 1400),  # 北京
            (40.7580, -73.9855, 1750)   # 纽约
        ]
        
        print(f"📊 批量查询 {batch_size} 个位置...")
        
        start_time = time.time()
        tasks = []
        
        for lat, lng, year in test_coordinates:
            task = historical_service.query_historical_location(lat, lng, year)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        
        print(f"✅ 批量查询完成:")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   平均耗时: {total_time/batch_size:.3f}秒/查询")
        print(f"   成功率: {success_count}/{batch_size}")
        
        # 测试缓存性能
        print(f"\n💾 测试缓存性能...")
        cache_start = time.time()
        
        # 重复查询同一个位置，应该命中缓存
        cached_result = await historical_service.query_historical_location(35.7148, 139.7967, 1600)
        cache_time = time.time() - cache_start
        
        if cached_result['success']:
            print(f"✅ 缓存查询成功: {cache_time:.3f}秒")
            print(f"🚀 缓存加速: {total_time/batch_size/cache_time:.1f}x 倍")
        else:
            print(f"⚠️ 缓存查询失败")
    
    async def test_cache_functionality(self):
        """测试缓存功能"""
        print("💾 测试缓存功能...")
        
        try:
            # 获取缓存信息
            cache_info = historical_data_loader.get_cache_info()
            print(f"📊 缓存状态:")
            print(f"   缓存文件: {cache_info['cache_count']} 个")
            print(f"   总大小: {cache_info['total_cache_size_mb']:.2f} MB")
            
            if cache_info['cached_files']:
                print(f"📁 缓存文件详情:")
                for file_info in cache_info['cached_files'][:3]:  # 只显示前3个
                    print(f"   - {file_info['filename']}: {file_info['size_mb']:.2f}MB")
                    print(f"     修改时间: {file_info['modified']}")
                    print(f"     是否过期: {'是' if file_info['is_expired'] else '否'}")
            
            # 测试清理过期缓存
            print(f"\n🧹 测试缓存清理...")
            await historical_data_loader.clear_expired_cache()
            
        except Exception as e:
            print(f"❌ 缓存功能测试失败: {e}")
    
    async def test_api_endpoints(self):
        """测试API端点（需要服务器运行）"""
        print("🔌 测试API端点...")
        
        import aiohttp
        
        base_url = "http://localhost:8000"
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试历史查询API
                test_data = {
                    'latitude': 35.7148,
                    'longitude': 139.7967, 
                    'year': 1600
                }
                
                print(f"📡 测试 POST /api/query-historical")
                async with session.post(f"{base_url}/api/query-historical", 
                                       json=test_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ API调用成功:")
                        print(f"   政治实体: {result.get('historical_info', {}).get('political_entity', 'N/A')}")
                        print(f"   查询耗时: {result.get('calculation_time', 'N/A')}秒")
                    else:
                        print(f"❌ API调用失败: HTTP {response.status}")
                
                # 测试可用年份API
                print(f"\n📡 测试 GET /api/historical/available-years")
                async with session.get(f"{base_url}/api/historical/available-years") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 年份列表API成功:")
                        print(f"   可用数据集: {result.get('total_datasets', 'N/A')} 个")
                        years = result.get('available_years', [])
                        if years:
                            print(f"   年份范围: {min(years)} - {max(years)}")
                    else:
                        print(f"❌ 年份列表API失败: HTTP {response.status}")
                
        except aiohttp.ClientConnectorError:
            print(f"⚠️ 无法连接到API服务器 ({base_url})")
            print(f"   请确保后端服务正在运行")
        except Exception as e:
            print(f"❌ API测试失败: {e}")


async def main():
    """主测试函数"""
    print("🧪 Historical查询功能测试套件")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tester = HistoricalQueryTester()
    
    # 运行基础功能测试
    await tester.run_all_tests()
    
    # 如果检测到服务器运行，也测试API端点
    print("\n🔌 尝试测试API端点...")
    await tester.test_api_endpoints()
    
    print("\n" + "="*60)
    print("✅ 测试套件执行完成!")
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")


def run_quick_test():
    """快速测试（同步版本）"""
    print("⚡ 快速功能测试...")
    
    # 测试数据加载器初始化
    try:
        print(f"📚 数据加载器状态: 初始化成功")
        print(f"   可用数据集: {len(historical_data_loader.available_datasets)} 个")
        
        # 测试年份映射
        test_years = [1600, 1945, 800]
        for year in test_years:
            closest = historical_data_loader.find_closest_year(year)
            print(f"   {year}年 → {closest}年 数据")
        
        print("✅ 快速测试完成")
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")


if __name__ == "__main__":
    print("Historical查询功能测试")
    print("选择测试模式:")
    print("1. 完整测试 (包含网络下载)")
    print("2. 快速测试 (仅本地功能)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == '1':
        asyncio.run(main())
    else:
        run_quick_test()
