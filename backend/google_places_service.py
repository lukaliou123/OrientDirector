"""
Google Places API集成服务
提供全球场所搜索和详情获取功能
"""

import os
import aiohttp
from typing import List, Dict, Optional
import asyncio
import json
from datetime import datetime

class GooglePlacesService:
    """Google Places API服务"""
    
    def __init__(self):
        # 确保从正确路径加载环境变量
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(env_path)
        
        # 与Street View共用API Key
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
        
        print(f"🌍 Google Places API初始化")
        print(f"   API Key: {'已配置' if self.api_key else '未配置'}")
        
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            print("⚠️ Google Places API Key未配置，部分功能将不可用")
    
    async def search_nearby_places(self, lat: float, lng: float, radius: int = 1000, 
                                 place_types: List[str] = None) -> List[Dict]:
        """
        搜索附近的Google Places
        
        Args:
            lat: 纬度
            lng: 经度  
            radius: 搜索半径（米），最大50000
            place_types: 地点类型列表
            
        Returns:
            List[Dict]: 场所列表
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            print("❌ Google Places API Key未配置")
            return []
        
        # 默认搜索旅游相关地点
        if not place_types:
            place_types = ['tourist_attraction', 'point_of_interest', 'park', 
                          'museum', 'amusement_park', 'zoo', 'aquarium']
        
        print(f"🔍 Google Places搜索: ({lat:.4f}, {lng:.4f}) 半径{radius}m")
        print(f"   地点类型: {place_types}")
        
        try:
            url = f"{self.base_url}/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': min(radius, 50000),  # Google API最大半径限制
                'type': '|'.join(place_types),  # 多类型用|分隔
                'key': self.api_key,
                'language': 'zh-CN'  # 返回中文名称（如果有）
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'OK':
                            results = data.get('results', [])
                            print(f"✅ Google Places返回 {len(results)} 个地点")
                            return results
                        else:
                            print(f"⚠️ Google Places API状态: {data.get('status')}")
                            print(f"   错误信息: {data.get('error_message', 'N/A')}")
                            return []
                    else:
                        print(f"❌ Google Places API请求失败: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Google Places API调用异常: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Dict:
        """
        获取场所详细信息
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Dict: 详细信息
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            return {}
        
        try:
            url = f"{self.base_url}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'name,geometry,formatted_address,opening_hours,rating,photos,types,reviews,website,international_phone_number',
                'key': self.api_key,
                'language': 'zh-CN'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'OK':
                            return data.get('result', {})
                    return {}
                    
        except Exception as e:
            print(f"❌ Google Places详情获取失败: {e}")
            return {}
    
    def get_place_photo_url(self, photo_reference: str, max_width: int = 400) -> str:
        """
        获取场所照片URL
        
        Args:
            photo_reference: 照片引用ID
            max_width: 最大宽度
            
        Returns:
            str: 照片URL
        """
        if not self.api_key or not photo_reference:
            return ''
            
        return f"{self.base_url}/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={self.api_key}"
    
    async def search_text_places(self, query: str, lat: float = None, lng: float = None, 
                               radius: int = 10000) -> List[Dict]:
        """
        文本搜索地点
        
        Args:
            query: 搜索关键词
            lat: 可选的中心纬度
            lng: 可选的中心经度
            radius: 搜索半径（米）
            
        Returns:
            List[Dict]: 搜索结果
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            return []
        
        try:
            url = f"{self.base_url}/textsearch/json"
            params = {
                'query': query,
                'key': self.api_key,
                'language': 'zh-CN'
            }
            
            # 如果提供了位置，添加位置参数
            if lat is not None and lng is not None:
                params['location'] = f"{lat},{lng}"
                params['radius'] = radius
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'OK':
                            results = data.get('results', [])
                            print(f"✅ Google Places文本搜索 '{query}' 返回 {len(results)} 个结果")
                            return results
                        else:
                            print(f"⚠️ Google Places文本搜索状态: {data.get('status')}")
                            return []
                    return []
                    
        except Exception as e:
            print(f"❌ Google Places文本搜索失败: {e}")
            return []
    
    def extract_place_info(self, place_data: Dict) -> Dict:
        """
        提取地点信息的统一格式
        
        Args:
            place_data: Google Places返回的原始数据
            
        Returns:
            Dict: 标准化的地点信息
        """
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        # 提取照片URL
        photos = place_data.get('photos', [])
        photo_url = None
        if photos and self.api_key:
            photo_ref = photos[0].get('photo_reference', '')
            if photo_ref:
                photo_url = self.get_place_photo_url(photo_ref, 600)
        
        # 处理营业时间
        opening_hours = place_data.get('opening_hours', {})
        is_open_now = opening_hours.get('open_now', None)
        
        # 处理地点类型
        types = place_data.get('types', [])
        primary_type = self.get_primary_type(types)
        
        return {
            'place_id': place_data.get('place_id', ''),
            'name': place_data.get('name', '未知地点'),
            'latitude': location.get('lat', 0),
            'longitude': location.get('lng', 0),
            'address': place_data.get('formatted_address', place_data.get('vicinity', '')),
            'rating': place_data.get('rating', 0),
            'user_ratings_total': place_data.get('user_ratings_total', 0),
            'price_level': place_data.get('price_level', None),
            'types': types,
            'primary_type': primary_type,
            'photo_url': photo_url,
            'is_open_now': is_open_now,
            'business_status': place_data.get('business_status', ''),
            'permanently_closed': place_data.get('permanently_closed', False)
        }
    
    def get_primary_type(self, types: List[str]) -> str:
        """
        获取主要地点类型（中文）
        
        Args:
            types: Google地点类型列表
            
        Returns:
            str: 中文地点类型
        """
        # 按优先级排序的类型映射
        type_mapping = {
            'tourist_attraction': '旅游景点',
            'museum': '博物馆',
            'amusement_park': '游乐园',
            'zoo': '动物园',
            'aquarium': '水族馆',
            'art_gallery': '艺术馆',
            'park': '公园',
            'church': '教堂',
            'mosque': '清真寺',
            'temple': '寺庙',
            'shrine': '神社',
            'castle': '城堡',
            'palace': '宫殿',
            'monument': '纪念碑',
            'shopping_mall': '购物中心',
            'restaurant': '餐厅',
            'cafe': '咖啡厅',
            'lodging': '住宿',
            'hospital': '医院',
            'school': '学校',
            'university': '大学',
            'library': '图书馆',
            'stadium': '体育场',
            'subway_station': '地铁站',
            'train_station': '火车站',
            'airport': '机场'
        }
        
        # 按优先级查找
        for google_type in types:
            if google_type in type_mapping:
                return type_mapping[google_type]
        
        # 默认返回
        return '景点'
    
    async def test_api_connection(self) -> Dict:
        """
        测试API连接
        
        Returns:
            Dict: 测试结果
        """
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            return {
                'success': False,
                'error': 'API Key未配置'
            }
        
        try:
            # 测试一个简单的搜索（东京塔）
            test_lat, test_lng = 35.658584, 139.745438
            results = await self.search_nearby_places(test_lat, test_lng, radius=500)
            
            return {
                'success': len(results) > 0,
                'api_key_status': 'valid' if results else 'invalid_or_quota_exceeded',
                'test_location': '东京塔附近',
                'results_count': len(results),
                'first_result': results[0]['name'] if results else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 全局实例
google_places_service = GooglePlacesService()


# 测试函数
async def test_google_places():
    """测试Google Places服务"""
    print("🧪 测试Google Places API服务...")
    print()
    
    # 测试API连接
    connection_test = await google_places_service.test_api_connection()
    print(f"📡 API连接测试: {connection_test}")
    print()
    
    if connection_test['success']:
        # 测试东京浅草寺附近搜索
        print("🏯 测试东京浅草寺附近搜索...")
        asakusa_lat, asakusa_lng = 35.714800, 139.796700
        
        places = await google_places_service.search_nearby_places(
            asakusa_lat, asakusa_lng, radius=1000
        )
        
        if places:
            print(f"✅ 找到 {len(places)} 个地点:")
            for i, place in enumerate(places[:5]):  # 显示前5个
                info = google_places_service.extract_place_info(place)
                print(f"   {i+1}. {info['name']} ({info['primary_type']})")
                print(f"      评分: {info['rating']}⭐ | 坐标: ({info['latitude']:.4f}, {info['longitude']:.4f})")
        else:
            print("❌ 未找到地点")
    else:
        print("❌ API连接失败，无法进行测试")


if __name__ == "__main__":
    asyncio.run(test_google_places())
