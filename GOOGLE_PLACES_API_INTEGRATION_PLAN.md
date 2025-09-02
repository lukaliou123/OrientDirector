# 🌍 Google Places API 集成方案

## 📋 问题背景

**当前问题：**
- 用户选择海外预设地址（如东京）后，后端仍返回中国式场所数据
- 根因：高德API主要覆盖中国大陆，海外POI数据缺失
- 现象：东京坐标 → 高德API无数据 → 回退到虚拟数据 → 生成"生态公园"等中国式名称

**目标效果：**
- 选择东京 → 真实东京场所 → "浅草寺"、"东京塔"、"上野公园"等
- 与现有Google Street View无缝集成
- 保持中国地区高德API的优势

## 🎯 核心流程设计

```
用户选择预设地址（如东京）
↓
前端发送探索请求到后端
↓
后端计算目标坐标（已有geographiclib）
↓
**新增：坐标位置判断**
├─ 海外坐标 → Google Places API搜索
└─ 中国坐标 → 高德API搜索（保持现有）
↓
格式化为统一数据格式
↓
返回真实的场所数据
↓
前端显示场所卡片
↓
用户点击"我已到达"
↓
**现有：自动打开Google Street View**
```

## 🔧 技术实现架构

### 1. 新增后端服务

#### **创建文件：backend/google_places_service.py**

```python
"""
Google Places API集成服务
提供全球场所搜索和详情获取功能
"""

import os
import aiohttp
from typing import List, Dict, Optional

class GooglePlacesService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')  # 与Street View共用
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
        self.session = None
    
    async def search_nearby_places(self, lat: float, lng: float, radius: int = 1000) -> List[Dict]:
        """
        搜索附近的Google Places
        
        Args:
            lat: 纬度
            lng: 经度  
            radius: 搜索半径（米）
            
        Returns:
            List[Dict]: 场所列表
        """
        url = f"{self.base_url}/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': 'tourist_attraction|point_of_interest|park|museum',
            'key': self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data.get('results', [])
    
    async def get_place_details(self, place_id: str) -> Dict:
        """
        获取场所详细信息
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Dict: 详细信息
        """
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,geometry,formatted_address,opening_hours,rating,photos,types',
            'key': self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data.get('result', {})
    
    def get_place_photo_url(self, photo_reference: str, max_width: int = 400) -> str:
        """
        获取场所照片URL
        
        Args:
            photo_reference: 照片引用ID
            max_width: 最大宽度
            
        Returns:
            str: 照片URL
        """
        return f"{self.base_url}/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={self.api_key}"

# 全局实例
google_places_service = GooglePlacesService()
```

### 2. 修改现有数据服务

#### **修改文件：backend/real_data_service.py**

```python
# 在文件顶部导入
from google_places_service import google_places_service

class RealDataService:
    # ... 现有代码 ...
    
    def is_overseas_location(self, lat: float, lng: float) -> bool:
        """
        判断坐标是否在海外
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            bool: True表示海外，False表示中国大陆
        """
        # 中国大陆边界框（简化版）
        china_bounds = {
            'north': 53.5,  # 黑龙江北端
            'south': 18.2,  # 海南南端  
            'east': 134.7,  # 黑龙江东端
            'west': 73.6    # 新疆西端
        }
        
        return not (china_bounds['south'] <= lat <= china_bounds['north'] and 
                   china_bounds['west'] <= lng <= china_bounds['east'])
    
    async def get_real_places_along_route(self, points: List[Dict], time_mode: str = 'present') -> List[Dict]:
        """获取目标点周围的真实地点信息（智能API选择）"""
        places = []
        
        for point in points:
            lat, lng = point['latitude'], point['longitude']
            
            print(f"检查坐标位置: ({lat:.4f}, {lng:.4f})")
            
            # 🔑 关键：根据坐标判断使用哪个API
            if self.is_overseas_location(lat, lng):
                print(f"✈️ 检测为海外坐标，使用Google Places API")
                # 海外坐标：使用Google Places API
                try:
                    google_places = await google_places_service.search_nearby_places(lat, lng)
                    formatted_places = await self.format_google_places_data(google_places, point)
                    places.extend(formatted_places)
                    print(f"🌍 Google Places API返回 {len(formatted_places)} 个场所")
                except Exception as e:
                    print(f"❌ Google Places API调用失败: {e}")
                    # 降级到虚拟数据，但使用国际化名称
                    fallback_places = await self.generate_international_fallback_data(point, time_mode)
                    places.extend(fallback_places)
            else:
                print(f"🇨🇳 检测为中国坐标，使用高德API")
                # 中国坐标：使用高德API（保持现有逻辑）
                amap_places = await amap_service.search_nearby_pois(lat, lng)
                formatted_places = self.format_amap_data(amap_places, point)
                places.extend(formatted_places)
        
        self.save_cache()
        return places
    
    async def format_google_places_data(self, google_places: List[Dict], point: Dict) -> List[Dict]:
        """
        将Google Places数据转换为统一格式
        
        Args:
            google_places: Google Places API返回的原始数据
            point: 目标点信息
            
        Returns:
            List[Dict]: 格式化后的场所数据
        """
        formatted_places = []
        
        for place in google_places:
            # 获取详细信息
            place_details = await google_places_service.get_place_details(place['place_id'])
            
            # 提取场所照片
            photo_url = None
            if 'photos' in place and place['photos']:
                photo_ref = place['photos'][0]['photo_reference']
                photo_url = google_places_service.get_place_photo_url(photo_ref)
            
            formatted_place = {
                'name': place['name'],
                'latitude': place['geometry']['location']['lat'],
                'longitude': place['geometry']['location']['lng'], 
                'distance': point['distance'],
                'description': self.generate_place_description_from_google(place, place_details),
                'image': photo_url or self.get_fallback_image_for_type(place.get('types', [])),
                'category': self.map_google_category_to_chinese(place.get('types', [])),
                'opening_hours': self.format_google_opening_hours(place_details.get('opening_hours')),
                'rating': f"Google评分：{place.get('rating', 'N/A')}⭐",
                'place_id': place['place_id'],  # 🔑 重要：用于Street View定位
                'country': self.extract_country_from_google_address(place),
                'city': self.extract_city_from_google_address(place),
                'ticket_price': self.estimate_ticket_price_by_type(place.get('types', [])),
                'booking_method': '现场购票或在线预约'
            }
            formatted_places.append(formatted_place)
        
        return formatted_places
    
    def map_google_category_to_chinese(self, types: List[str]) -> str:
        """将Google Places类型映射为中文类别"""
        category_mapping = {
            'tourist_attraction': '旅游景点',
            'museum': '博物馆', 
            'park': '公园',
            'amusement_park': '游乐园',
            'zoo': '动物园',
            'aquarium': '水族馆',
            'art_gallery': '艺术馆',
            'church': '教堂',
            'mosque': '清真寺',
            'temple': '寺庙',
            'shopping_mall': '购物中心',
            'restaurant': '餐厅',
            'cafe': '咖啡厅'
        }
        
        for google_type in types:
            if google_type in category_mapping:
                return category_mapping[google_type]
        
        return '景点'
    
    async def generate_international_fallback_data(self, point: Dict, time_mode: str) -> List[Dict]:
        """
        生成国际化的降级数据（当API调用失败时）
        根据坐标位置生成对应地区风格的场所名称
        """
        lat, lng = point['latitude'], point['longitude']
        
        # 根据坐标判断大致地区，生成对应风格的名称
        region_styles = self.detect_region_style(lat, lng)
        
        fallback_places = []
        for i, style in enumerate(region_styles):
            place = {
                'name': style['name'],
                'latitude': lat + (i * 0.01),  # 略微偏移坐标
                'longitude': lng + (i * 0.01),
                'distance': point['distance'],
                'description': style['description'],
                'image': style['image'],
                'category': style['category'],
                'country': style['country'],
                'city': style['city'],
                'opening_hours': '09:00-17:00',
                'ticket_price': style['price'],
                'booking_method': '现场购票'
            }
            fallback_places.append(place)
        
        return fallback_places
    
    def detect_region_style(self, lat: float, lng: float) -> List[Dict]:
        """根据坐标检测地区风格并生成对应的场所名称"""
        # 日本地区 (大致范围)
        if 24 <= lat <= 46 and 123 <= lng <= 146:
            return [
                {
                    'name': '神社',
                    'description': '传统的日式神社，体现了日本的宗教文化',
                    'category': '文化古迹',
                    'country': '日本',
                    'city': '当地',
                    'price': '免费参观',
                    'image': 'https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=400'
                },
                {
                    'name': '庭园',
                    'description': '精致的日式庭园，展现自然与人工的完美结合',
                    'category': '自然风光', 
                    'country': '日本',
                    'city': '当地',
                    'price': '成人票：500日元',
                    'image': 'https://images.unsplash.com/photo-1480796927426-f609979314bd?w=400'
                }
            ]
        
        # 欧洲地区 (大致范围)
        elif 35 <= lat <= 70 and -10 <= lng <= 40:
            return [
                {
                    'name': '大教堂',
                    'description': '历史悠久的欧式大教堂，哥特式建筑的典型代表',
                    'category': '文化古迹',
                    'country': '欧洲',
                    'city': '当地',
                    'price': '成人票：8€',
                    'image': 'https://images.unsplash.com/photo-1520637836862-4d197d17c91a?w=400'
                },
                {
                    'name': '城市广场',
                    'description': '充满历史气息的欧洲城市广场，是当地文化的中心',
                    'category': '文化景点',
                    'country': '欧洲', 
                    'city': '当地',
                    'price': '免费开放',
                    'image': 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=400'
                }
            ]
        
        # 北美地区
        elif 25 <= lat <= 60 and -130 <= lng <= -60:
            return [
                {
                    'name': '国家公园',
                    'description': '壮丽的北美自然风光，保护完好的野生生态系统',
                    'category': '自然风光',
                    'country': '北美',
                    'city': '当地',
                    'price': '成人票：$15',
                    'image': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400'
                },
                {
                    'name': '艺术博物馆',
                    'description': '收藏丰富的现代艺术博物馆，展示当代文化艺术',
                    'category': '博物馆',
                    'country': '北美',
                    'city': '当地', 
                    'price': '成人票：$20',
                    'image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400'
                }
            ]
        
        # 默认国际化场所
        else:
            return [
                {
                    'name': '地标建筑',
                    'description': '当地著名的地标性建筑，展现独特的建筑风格',
                    'category': '文化景点',
                    'country': '当地',
                    'city': '当地',
                    'price': '请咨询当地',
                    'image': 'https://images.unsplash.com/photo-1577836381629-eb4b0d34e5f4?w=400'
                }
            ]
```

## 🔑 API配置要求

### 需要启用的Google APIs

```yaml
google_apis:
  required:
    - Maps JavaScript API          # ✅ 已有（Street View用）
    - Places API                  # 🆕 新增（搜索场所）
  optional:
    - Photos API                  # 🆕 获取场所照片
    - Geocoding API              # 🆕 地址解析增强
```

### 环境变量配置

```bash
# .env 文件更新
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Google Places API配额建议
# - 免费额度：每月$200信用额度
# - Nearby Search: $32 per 1000 requests  
# - Place Details: $17 per 1000 requests
# - Place Photos: $7 per 1000 requests
```

## 📊 预期效果对比

### 修复前（当前问题）
```
用户选择：🏯 东京 - 浅草寺区域
坐标更新：✅ 35.714800, 139.796700
后端处理：❌ 高德API无海外数据
数据回退：❌ 虚拟中国数据生成
显示结果：❌ "生态公园" (中国式名称)
Street View: ✅ 正确显示东京街景
```

### 修复后（期望效果）
```
用户选择：🏯 东京 - 浅草寺区域  
坐标更新：✅ 35.714800, 139.796700
后端判断：✅ 检测为海外坐标
API调用：✅ Google Places API
数据获取：✅ 真实东京场所数据
显示结果：✅ "浅草寺"、"东京塔"、"上野公园"
Street View: ✅ 正确显示对应街景
```

## 🎯 实现优势

### 技术优势
1. **🌍 全球覆盖**：Google Places API覆盖全球200+国家
2. **🔄 无缝集成**：与现有Google Street View完美配合
3. **📍 精确数据**：真实坐标、评分、营业时间、照片
4. **🚀 向后兼容**：中国地区仍使用高德API，保持现有优势
5. **🛡️ 降级机制**：API失败时提供国际化的备用数据

### 用户体验优势
1. **🎯 真实性**：显示真正的当地场所，不再是虚拟数据
2. **🏞️ 丰富内容**：场所照片、用户评价、详细信息
3. **🗺️ 地图联动**：场所数据与Street View完美配合
4. **🌐 国际化**：支持全球任意预设地址的真实数据

### 开发维护优势  
1. **📦 模块化设计**：新增GooglePlacesService，不影响现有代码
2. **🔧 智能路由**：根据坐标自动选择最佳API
3. **💰 成本控制**：仅海外坐标调用Google API，中国仍用免费高德
4. **📈 易扩展**：后续可轻松添加其他地区的专用API

## 📋 实施计划

### Phase 1: 核心功能开发
1. **创建 GooglePlacesService**
2. **修改 RealDataService 添加智能路由**  
3. **实现数据格式转换和统一化**
4. **添加地区检测逻辑**

### Phase 2: 优化和增强
1. **添加错误处理和降级机制**
2. **实现国际化备用数据生成**
3. **优化API调用频率和缓存策略**
4. **添加场所照片和详细信息**

### Phase 3: 测试和部署  
1. **全球各预设地址功能测试**
2. **API配额和成本监控**
3. **性能优化和缓存策略调整**
4. **用户体验测试和反馈收集**

## 💡 成本和配额考虑

### Google Places API定价（2024）
- **Nearby Search**: $32 per 1000 requests
- **Place Details**: $17 per 1000 requests  
- **Place Photos**: $7 per 1000 requests
- **Monthly Free Credit**: $200

### 预估使用量
假设每天100次海外探索请求：
- Nearby Search: 100 requests = $3.2/天
- Place Details: 300 requests = $5.1/天 (每次探索3个场所详情)
- Place Photos: 300 requests = $2.1/天
- **总计**: ~$10.4/天，月度约$312

### 成本优化策略
1. **缓存机制**：相同坐标结果缓存24小时
2. **批量请求**：合并相近坐标的搜索请求  
3. **智能阈值**：仅在中国边界外使用Google API
4. **降级策略**：API配额用完时使用国际化虚拟数据

---

## 📝 待讨论事项

1. **API成本预算**：是否可以接受上述成本预估？
2. **实施时间**：希望何时开始实施此方案？
3. **功能范围**：是否需要场所评分、照片等高级功能？
4. **测试策略**：如何测试全球各地的数据质量？
5. **备用方案**：是否需要准备其他免费/低成本的数据源？

---

*文档创建时间：2024年12月20日*  
*方案状态：待讨论和实施*

