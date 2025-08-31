#!/usr/bin/env python3
"""
测试AI旅程总结功能
"""

import asyncio
import requests
import json
import time

# 测试数据
test_data = {
    "visited_scenes": [
        {"name": "天安门广场", "description": "中华人民共和国的象征"},
        {"name": "故宫博物院", "description": "明清两代的皇家宫殿"},
        {"name": "北海公园", "description": "北京最古老的皇家园林之一"}
    ],
    "total_distance": 5.8,
    "journey_duration": "120分钟",
    "scenes_count": 3
}

def test_journey_summary_api():
    """测试旅程总结API"""
    print("🧪 开始测试AI旅程总结功能...")
    
    try:
        # 发送POST请求
        response = requests.post(
            'http://localhost:8000/api/journey-summary',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=30
        )
        
        print(f"📡 API响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 请求成功!")
            print(f"🤖 AI服务状态: {'成功' if data['success'] else '失败'}")
            print(f"⏱️  生成时间: {data['generation_time']:.2f}秒")
            print(f"📝 消息: {data['message']}")
            print("\n🎨 AI生成的旅程总结:")
            print("=" * 60)
            print(data['summary'])
            print("=" * 60)
            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端服务正在运行")
        print("💡 提示: 运行 'python start_app.py' 启动后端服务")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_various_scenarios():
    """测试不同的旅程场景"""
    print("\n🎭 测试不同的旅程场景...")
    
    scenarios = [
        {
            "name": "短途城市游",
            "data": {
                "visited_scenes": [
                    {"name": "城市广场", "description": "市中心的繁华地带"}
                ],
                "total_distance": 2.1,
                "journey_duration": "45分钟", 
                "scenes_count": 1
            }
        },
        {
            "name": "长途探索之旅",
            "data": {
                "visited_scenes": [
                    {"name": "山峰观景台", "description": "俯瞰群山的绝佳位置"},
                    {"name": "古老寺庙", "description": "千年历史的佛教圣地"},
                    {"name": "湖边小镇", "description": "风景如画的水乡"},
                    {"name": "森林公园", "description": "原始森林生态保护区"},
                    {"name": "海滨度假村", "description": "面朝大海的休闲胜地"}
                ],
                "total_distance": 156.7,
                "journey_duration": "8小时30分钟",
                "scenes_count": 5
            }
        }
    ]
    
    results = []
    for scenario in scenarios:
        print(f"\n🎯 测试场景: {scenario['name']}")
        try:
            response = requests.post(
                'http://localhost:8000/api/journey-summary',
                headers={'Content-Type': 'application/json'},
                json=scenario['data'],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {scenario['name']} - 成功")
                print(f"📝 总结预览: {data['summary'][:100]}...")
                results.append(True)
            else:
                print(f"❌ {scenario['name']} - 失败 ({response.status_code})")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {scenario['name']} - 异常: {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 测试结果: {sum(results)}/{len(results)} 成功率: {success_rate:.1f}%")
    return success_rate > 80

def main():
    """主测试函数"""
    print("🚀 OrientDiscover AI旅程总结功能测试")
    print("=" * 50)
    
    # 基础功能测试
    basic_test = test_journey_summary_api()
    
    if basic_test:
        # 扩展场景测试
        scenario_test = test_various_scenarios()
        
        if scenario_test:
            print("\n🎉 所有测试通过！AI旅程总结功能工作正常")
            print("💡 提示：现在您可以在前端完成旅程时看到AI生成的幽默总结了！")
        else:
            print("\n⚠️  基础功能正常，但部分场景测试失败")
    else:
        print("\n❌ 基础功能测试失败，请检查后端服务和AI配置")
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()
