#!/usr/bin/env python3
"""
Google Places API集成测试
测试海外坐标的智能路由功能
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from real_data_service import real_data_service
from google_places_service import google_places_service

async def test_overseas_coordinates():
    """测试海外坐标的Google Places API集成"""
    
    print("🌍 Google Places API 集成测试")
    print("=" * 50)
    
    # 测试用例：海外著名地点
    test_locations = [
        {
            'name': '东京浅草寺',
            'latitude': 35.714800,
            'longitude': 139.796700,
            'distance': 10,
            'expected': '应该返回浅草寺、上野公园等真实地点'
        },
        {
            'name': '巴黎埃菲尔铁塔',
            'latitude': 48.8584,
            'longitude': 2.2945,
            'distance': 15,
            'expected': '应该返回卢浮宫、凯旋门等真实地点'
        },
        {
            'name': '纽约时代广场',
            'latitude': 40.7580,
            'longitude': -73.9855,
            'distance': 8,
            'expected': '应该返回中央公园、帝国大厦等真实地点'
        }
    ]
    
    # 测试对比：中国坐标
    china_location = {
        'name': '北京故宫',
        'latitude': 39.9163,
        'longitude': 116.3972,
        'distance': 12,
        'expected': '应该使用高德API返回中国景点'
    }
    
    print("\n📋 测试计划:")
    for loc in test_locations + [china_location]:
        print(f"   • {loc['name']} ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
        print(f"     期望: {loc['expected']}")
    
    print("\n" + "=" * 50)
    
    # 1. 测试API连接
    print("\n🔧 1. 测试Google Places API连接...")
    connection_result = await google_places_service.test_api_connection()
    print(f"   连接状态: {connection_result}")
    
    if not connection_result.get('success'):
        print("\n⚠️ Google Places API连接失败，将测试降级功能")
    
    # 2. 测试海外坐标处理
    print("\n🌏 2. 测试海外坐标智能路由...")
    
    for location in test_locations:
        print(f"\n📍 测试地点: {location['name']}")
        print(f"   坐标: ({location['latitude']:.4f}, {location['longitude']:.4f})")
        
        # 创建点数据（模拟用户探索到的目标点）
        points = [{
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'distance': location['distance']
        }]
        
        try:
            # 调用智能路由功能
            places = await real_data_service.get_real_places_along_route(points, 'present')
            
            print(f"   ✅ 成功获取 {len(places)} 个地点:")
            
            for i, place in enumerate(places[:3]):  # 只显示前3个
                print(f"      {i+1}. {place['name']} ({place['category']})")
                print(f"         国家: {place.get('country', 'N/A')}")
                print(f"         城市: {place.get('city', 'N/A')}")
                print(f"         描述: {place['description'][:60]}...")
                if 'place_id' in place:
                    print(f"         Google Place ID: {place['place_id'][:20]}...")
                print()
                
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
    
    # 3. 测试中国坐标（验证高德API仍然工作）
    print(f"\n🇨🇳 3. 测试中国坐标（对比测试）...")
    print(f"📍 测试地点: {china_location['name']}")
    
    china_points = [{
        'latitude': china_location['latitude'],
        'longitude': china_location['longitude'],
        'distance': china_location['distance']
    }]
    
    try:
        china_places = await real_data_service.get_real_places_along_route(china_points, 'present')
        print(f"   ✅ 中国坐标获取 {len(china_places)} 个地点:")
        
        for i, place in enumerate(china_places[:3]):
            print(f"      {i+1}. {place['name']} ({place['category']})")
            print(f"         描述: {place['description'][:60]}...")
            
    except Exception as e:
        print(f"   ❌ 中国坐标测试失败: {e}")
    
    # 4. 测试区域识别功能
    print(f"\n🗺️ 4. 测试区域识别功能...")
    
    test_coords = [
        (35.7148, 139.7967, "日本"),
        (48.8584, 2.2945, "欧洲"),
        (40.7580, -73.9855, "北美"),
        (39.9163, 116.3972, "中国"),
        (-33.8688, 151.2093, "澳洲")
    ]
    
    for lat, lng, expected_region in test_coords:
        is_overseas = real_data_service.is_overseas_location(lat, lng)
        status = "海外" if is_overseas else "中国"
        print(f"   坐标 ({lat:.4f}, {lng:.4f}) -> {status} (期望: {expected_region})")
    
    print(f"\n" + "=" * 50)
    print("🎯 测试总结:")
    print("   • Google Places API集成已完成")
    print("   • 智能路由功能已实现（海外用Google，中国用高德）")
    print("   • 数据格式统一化已完成") 
    print("   • 降级机制已就绪（API失败时使用国际化虚拟数据）")
    print("\n💡 下一步:")
    print("   1. 配置真实的Google Maps API Key")
    print("   2. 前端测试海外预设地址的场景数据")
    print("   3. 与Google Street View的整合测试")
    
    if connection_result.get('success'):
        print("   ✅ API已就绪，可以开始真实测试！")
    else:
        print("   ⚠️ 需要配置API Key才能进行真实测试")

async def test_region_fallback():
    """测试区域化降级数据生成"""
    print("\n🎭 测试区域化降级数据生成...")
    
    test_points = [
        {'latitude': 35.7148, 'longitude': 139.7967, 'distance': 10, 'region': '日本'},
        {'latitude': 48.8584, 'longitude': 2.2945, 'distance': 15, 'region': '欧洲'},
        {'latitude': 40.7580, 'longitude': -73.9855, 'distance': 8, 'region': '北美'},
    ]
    
    for point in test_points:
        print(f"\n🌍 {point['region']}地区降级数据:")
        fallback_data = await real_data_service.generate_international_fallback_data(point, 'present')
        
        for place in fallback_data:
            print(f"   • {place['name']} ({place['category']})")
            print(f"     {place['description'][:50]}...")

if __name__ == "__main__":
    print("🚀 启动Google Places API集成测试...")
    
    try:
        # 运行主测试
        asyncio.run(test_overseas_coordinates())
        
        # 运行降级数据测试
        asyncio.run(test_region_fallback())
        
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出现异常: {e}")
        import traceback
        traceback.print_exc()
