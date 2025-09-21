from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import math
from geographiclib.geodesic import Geodesic
import json
import os
import asyncio
import time
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# 使用相对导入，在backend包内
try:
    # 尝试作为包导入（Docker环境）
    from .real_data_service import real_data_service
    from .journey_service import journey_service, Journey, JourneyLocation, VisitedScene
    from .ai_service import get_ai_service
    from .historical_service import historical_service
    from .nano_banana_service import nano_banana_service
except ImportError:
    # 直接导入（本地开发环境）
    from real_data_service import real_data_service
    from journey_service import journey_service, Journey, JourneyLocation, VisitedScene
    from ai_service import get_ai_service
    from historical_service import historical_service
    from nano_banana_service import nano_banana_service

# 加载环境变量
load_dotenv()
print(f"🔑 GOOGLE_MAPS_API_KEY: {'已加载' if os.getenv('GOOGLE_MAPS_API_KEY') else '未找到'}")

app = FastAPI(title="方向探索派对API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
# 尝试找到static目录
if os.path.exists("static"):
    static_dir = "static"
elif os.path.exists("/app/static"):
    static_dir = "/app/static"
else:
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 数据模型
class ExploreRequest(BaseModel):
    latitude: float
    longitude: float
    heading: float
    segment_distance: int = 100  # 默认100km
    time_mode: str = "present"  # present, past, future
    speed: int = 120  # 默认120km/h

class PlaceInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    distance: float
    description: str
    image: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    opening_hours: Optional[str] = None
    ticket_price: Optional[str] = None
    booking_method: Optional[str] = None
    category: Optional[str] = None

class ExploreResponse(BaseModel):
    places: List[PlaceInfo]
    total_distance: float
    calculation_time: float

# 历史模式相关数据模型
class HistoricalQueryRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    
class HistoricalLocationInfo(BaseModel):
    success: bool
    political_entity: Optional[str] = None
    ruler_or_power: Optional[str] = None
    cultural_region: Optional[str] = None
    border_precision: Optional[int] = None
    query_year: Optional[int] = None
    coordinates: Optional[Dict] = None
    description: Optional[str] = None
    time_period: Optional[str] = None
    cultural_context: Optional[Dict] = None
    is_approximate: Optional[bool] = False
    distance_to_border: Optional[float] = None
    error: Optional[str] = None

class HistoricalQueryResponse(BaseModel):
    success: bool
    historical_info: Optional[HistoricalLocationInfo] = None
    calculation_time: float
    data_source: str = "Historical-basemaps"
    error: Optional[str] = None

# 历史场景生成相关数据模型
class HistoricalSceneRequest(BaseModel):
    latitude: float
    longitude: float
    year: int

class HistoricalSceneInfo(BaseModel):
    success: bool
    scene_description: Optional[str] = None
    generation_model: Optional[str] = None
    generation_time: Optional[float] = None
    demo_mode: Optional[bool] = False
    images: Optional[List[str]] = None  # 添加图片URL列表字段
    image_count: Optional[int] = None   # 添加图片数量字段
    note: Optional[str] = None
    error: Optional[str] = None

class HistoricalSceneResponse(BaseModel):
    success: bool
    historical_info: Optional[HistoricalLocationInfo] = None
    generated_scene: Optional[HistoricalSceneInfo] = None
    ai_review: Optional[Dict] = None
    image_url: Optional[str] = None  # 添加主图片URL字段，方便前端直接访问
    calculation_time: float
    data_source: str = "Historical-basemaps + Gemini"
    error: Optional[str] = None

# 时光自拍相关模型
class HistoricalSelfieRequest(BaseModel):
    scene_id: str  # 场景ID
    political_entity: str  # 政治实体
    year: int  # 年份
    user_image: Optional[str] = None  # 用户照片（演示模式可选）

class HistoricalSelfieResponse(BaseModel):
    success: bool
    selfie_url: Optional[str] = None  # 生成的自拍图片URL
    scene_info: Optional[Dict] = None  # 场景信息
    generation_time: float
    demo_mode: bool = True
    error: Optional[str] = None

class AvatarUploadResponse(BaseModel):
    success: bool
    avatar_url: Optional[str] = None  # 上传后的头像URL
    file_size: Optional[int] = None  # 文件大小（字节）
    upload_time: float  # 上传处理时间
    error: Optional[str] = None

# 全局变量
geod = Geodesic.WGS84
places_data = {}

def load_places_data():
    """加载地点数据"""
    global places_data
    
    # 创建示例数据（实际项目中应该从数据库或文件加载）
    places_data = {
        "present": [
            {
                "name": "东京",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "country": "日本",
                "city": "东京",
                "description": "现代化的国际大都市，科技与传统文化的完美融合。",
                "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400"
            },
            {
                "name": "纽约",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "country": "美国",
                "city": "纽约",
                "description": "世界金融中心，拥有标志性的天际线和自由女神像。",
                "image": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400"
            },
            {
                "name": "伦敦",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "country": "英国",
                "city": "伦敦",
                "description": "历史悠久的国际都市，大本钟和泰晤士河闻名世界。",
                "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=400"
            },
            {
                "name": "巴黎",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "country": "法国",
                "city": "巴黎",
                "description": "浪漫之都，埃菲尔铁塔和卢浮宫的所在地。",
                "image": "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=400"
            },
            {
                "name": "悉尼",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "country": "澳大利亚",
                "city": "悉尼",
                "description": "拥有标志性歌剧院和海港大桥的美丽海滨城市。",
                "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
            },
            {
                "name": "开普敦",
                "latitude": -33.9249,
                "longitude": 18.4241,
                "country": "南非",
                "city": "开普敦",
                "description": "非洲大陆南端的美丽城市，桌山和好望角闻名。",
                "image": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=400"
            },
            {
                "name": "里约热内卢",
                "latitude": -22.9068,
                "longitude": -43.1729,
                "country": "巴西",
                "city": "里约热内卢",
                "description": "拥有基督像和科帕卡巴纳海滩的热情城市。",
                "image": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=400"
            },
            {
                "name": "迪拜",
                "latitude": 25.2048,
                "longitude": 55.2708,
                "country": "阿联酋",
                "city": "迪拜",
                "description": "现代奇迹之城，拥有世界最高建筑哈利法塔。",
                "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400"
            },
            {
                "name": "新加坡",
                "latitude": 1.3521,
                "longitude": 103.8198,
                "country": "新加坡",
                "city": "新加坡",
                "description": "花园城市国家，多元文化和现代建筑的完美结合。",
                "image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=400"
            },
            {
                "name": "冰岛雷克雅未克",
                "latitude": 64.1466,
                "longitude": -21.9426,
                "country": "冰岛",
                "city": "雷克雅未克",
                "description": "世界最北的首都，极光和地热温泉的天堂。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            },
            {
                "name": "首尔",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "country": "韩国",
                "city": "首尔",
                "description": "现代科技与传统文化并存的活力都市，K-pop和韩流文化的发源地。",
                "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400"
            },
            {
                "name": "上海",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "country": "中国",
                "city": "上海",
                "description": "国际化大都市，东方明珠塔和外滩的璀璨夜景令人难忘。",
                "image": "https://images.unsplash.com/photo-1545893835-abaa50cbe628?w=400"
            },
            {
                "name": "香港",
                "latitude": 22.3193,
                "longitude": 114.1694,
                "country": "中国",
                "city": "香港",
                "description": "东西方文化交融的国际金融中心，维多利亚港的夜景世界闻名。",
                "image": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=400"
            },
            {
                "name": "曼谷",
                "latitude": 13.7563,
                "longitude": 100.5018,
                "country": "泰国",
                "city": "曼谷",
                "description": "佛教文化浓厚的热带都市，金碧辉煌的寺庙和热闹的水上市场。",
                "image": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400"
            },
            {
                "name": "孟买",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "country": "印度",
                "city": "孟买",
                "description": "印度的商业首都，宝莱坞电影工业的中心，充满活力和色彩。",
                "image": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=400"
            },
            {
                "name": "莫斯科",
                "latitude": 55.7558,
                "longitude": 37.6176,
                "country": "俄罗斯",
                "city": "莫斯科",
                "description": "红场和克里姆林宫见证着俄罗斯的历史变迁，冬日雪景如童话世界。",
                "image": "https://images.unsplash.com/photo-1513326738677-b964603b136d?w=400"
            },
            {
                "name": "开罗",
                "latitude": 30.0444,
                "longitude": 31.2357,
                "country": "埃及",
                "city": "开罗",
                "description": "古老的金字塔和狮身人面像守护着这座千年古城。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            }
        ],
        "past": [
            {
                "name": "古罗马",
                "latitude": 41.9028,
                "longitude": 12.4964,
                "country": "意大利",
                "city": "罗马",
                "description": "100年前的罗马，古老的斗兽场见证着历史的变迁。",
                "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400"
            },
            {
                "name": "维多利亚时代伦敦",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "country": "英国",
                "city": "伦敦",
                "description": "1920年代的伦敦，工业革命后的繁华与雾霾并存。",
                "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=400"
            },
            {
                "name": "民国上海",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "country": "中国",
                "city": "上海",
                "description": "1920年代的上海，东西方文化交融的十里洋场。",
                "image": "https://images.unsplash.com/photo-1545893835-abaa50cbe628?w=400"
            },
            {
                "name": "古埃及开罗",
                "latitude": 30.0444,
                "longitude": 31.2357,
                "country": "埃及",
                "city": "开罗",
                "description": "100年前的开罗，金字塔旁的古老文明依然辉煌。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            }
        ],
        "future": [
            {
                "name": "未来东京2124",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "country": "日本",
                "city": "东京",
                "description": "2124年的东京，飞行汽车穿梭在摩天大楼间，全息投影随处可见。",
                "image": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400"
            },
            {
                "name": "火星新城",
                "latitude": 14.5995,
                "longitude": -87.7680,
                "country": "火星殖民地",
                "city": "新奥林匹亚",
                "description": "2124年的火星殖民城市，透明穹顶下的绿色花园。",
                "image": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400"
            },
            {
                "name": "海底亚特兰蒂斯",
                "latitude": 25.0000,
                "longitude": -30.0000,
                "country": "海底城市",
                "city": "新亚特兰蒂斯",
                "description": "2124年的海底城市，生物发光建筑与海洋生物和谐共存。",
                "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400"
            }
        ]
    }

def calculate_great_circle_points(start_lat, start_lon, heading, max_distance, segment_distance):
    """计算大圆航线上的点"""
    points = []
    current_distance = 0
    
    while current_distance <= max_distance:
        # 使用大圆航线计算
        result = geod.Direct(start_lat, start_lon, heading, current_distance * 1000)  # 转换为米
        
        points.append({
            'latitude': result['lat2'],
            'longitude': result['lon2'],
            'distance': current_distance
        })
        
        current_distance += segment_distance
        
        # 最多计算20个点，避免过多数据
        if len(points) >= 20:
            break
    
    return points

def find_nearby_attractions(points, time_mode, search_radius_km=5):
    """在目标点周围搜索景点"""
    places = []
    available_places = places_data.get(time_mode, places_data["present"])
    
    for point in points:
        target_lat = point['latitude']
        target_lon = point['longitude']
        target_distance = point['distance']
        
        # 在目标点周围搜索景点
        nearby_places = []
        
        for place_data in available_places:
            # 计算到目标点的距离
            distance_result = geod.Inverse(
                target_lat, target_lon,
                place_data['latitude'], place_data['longitude']
            )
            distance_km = distance_result['s12'] / 1000  # 转换为公里
            
            # 如果在搜索半径内，添加到候选列表
            if distance_km <= search_radius_km:
                place_copy = place_data.copy()
                place_copy['distance_to_target'] = distance_km
                nearby_places.append(place_copy)
        
        # 按距离排序，选择最近的几个
        nearby_places.sort(key=lambda x: x['distance_to_target'])
        
        # 如果找到了真实景点，使用它们
        if nearby_places:
            for i, place_data in enumerate(nearby_places[:3]):  # 最多3个景点
                # 为真实景点生成详细信息
                attraction_info = generate_attraction_details_for_real_place(place_data)
                
                place_info = PlaceInfo(
                    name=place_data['name'],
                    latitude=place_data['latitude'],
                    longitude=place_data['longitude'],
                    distance=target_distance,
                    description=f"距此约{place_data['distance_to_target']:.1f}公里 - {place_data['description']}",
                    image=place_data.get('image', attraction_info['image']),
                    country=place_data.get('country'),
                    city=place_data.get('city'),
                    opening_hours=attraction_info['opening_hours'],
                    ticket_price=attraction_info['ticket_price'],
                    booking_method=attraction_info['booking_method'],
                    category=attraction_info['category']
                )
                places.append(place_info)
        else:
            # 如果没有找到真实景点，生成虚拟景点（确保是景点类型）
            virtual_places = generate_virtual_attractions(point, time_mode, search_radius_km)
            # 过滤掉可能的行政区域信息
            filtered_places = [place for place in virtual_places if is_valid_attraction_name(place.name)]
            places.extend(filtered_places)
    
    return places

def generate_virtual_attractions(point, time_mode, search_radius_km):
    """为目标点生成虚拟景点"""
    lat, lon = point['latitude'], point['longitude']
    target_distance = point['distance']
    
    # 根据经纬度判断大致区域
    region_info = get_region_info(lat, lon)
    
    # 生成3个虚拟景点
    attractions = []
    attraction_types = ['自然景观', '文化古迹', '城市地标']
    
    for i, attraction_type in enumerate(attraction_types):
        # 在目标点周围随机生成景点位置
        import random
        offset_km = random.uniform(0.5, search_radius_km)
        bearing = random.uniform(0, 360)
        
        # 计算景点坐标
        attraction_point = geod.Direct(lat, lon, bearing, offset_km * 1000)
        
        # 根据时间模式和类型生成描述
        descriptions = {
            "present": {
                '自然景观': f"这里是{region_info['name']}的一处美丽自然景观，拥有独特的地理风貌和生态环境。",
                '文化古迹': f"位于{region_info['name']}的历史文化遗址，承载着丰富的历史文化内涵。",
                '城市地标': f"{region_info['name']}的现代化地标建筑，展现了当地的发展成就。"
            },
            "past": {
                '自然景观': f"一百年前，这里是{region_info['name']}的原始自然景观，保持着最初的生态面貌。",
                '文化古迹': f"古代{region_info['name']}的重要文化遗址，见证了历史的兴衰变迁。",
                '城市地标': f"过去的{region_info['name']}重要建筑，曾是当地的政治或商业中心。"
            }
        }
        
        # 生成详细信息
        attraction_info = generate_attraction_details(attraction_type, time_mode, region_info)
        attraction_name = f"{region_info['name']}{attraction_type}{i+1}"
        description = descriptions.get(time_mode, descriptions["present"])[attraction_type]
        
        place_info = PlaceInfo(
            name=attraction_name,
            latitude=attraction_point['lat2'],
            longitude=attraction_point['lon2'],
            distance=target_distance,
            description=f"距此约{offset_km:.1f}公里 - {description}",
            image=attraction_info['image'],
            country=region_info['country'],
            city=region_info['city'],
            opening_hours=attraction_info['opening_hours'],
            ticket_price=attraction_info['ticket_price'],
            booking_method=attraction_info['booking_method'],
            category=attraction_type
        )
        attractions.append(place_info)
    
    return attractions

def is_valid_attraction_name(name: str) -> bool:
    """验证是否为有效的景点名称（非行政区域）"""
    name_lower = name.lower()
    
    # 行政区域关键词
    administrative_keywords = [
        '区', '市', '县', '省', '街道', '镇', '乡', '村', '路', '街',
        'district', 'city', 'county', 'province', 'street', 'road',
        '行政区', '管辖区', '辖区', '开发区', '新区'
    ]
    
    # 景点关键词
    attraction_keywords = [
        '陵', '寺', '庙', '宫', '园', '山', '湖', '塔', '桥', '城', '馆', '院',
        '景区', '景点', '风景', '名胜', '古迹', '遗址', '博物', '纪念', '公园',
        'temple', 'palace', 'park', 'mountain', 'lake', 'tower', 'museum',
        'attraction', 'scenic', 'monument', 'memorial'
    ]
    
    # 检查是否包含景点关键词
    has_attraction_keyword = any(keyword in name_lower for keyword in attraction_keywords)
    
    # 检查是否为行政区域
    is_administrative = any(keyword in name_lower for keyword in administrative_keywords)
    
    # 如果明确包含景点关键词，认为是有效景点
    if has_attraction_keyword:
        return True
    
    # 如果是行政区域，过滤掉
    if is_administrative:
        return False
    
    return True

def generate_attraction_details(attraction_type, time_mode, region_info):
    """生成景点的详细信息"""
    import random
    
    # 根据景点类型和时间模式生成信息
    details = {
        "自然景观": {
            "present": {
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约，直接前往",
                "images": [
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
                    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
                ]
            },
            "past": {
                "opening_hours": "日出至日落",
                "ticket_price": "免费",
                "booking_method": "古代无需门票，自由游览",
                "images": [
                    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
                ]
            }
        },
        "文化古迹": {
            "present": {
                "opening_hours": "09:00-17:00（周一闭馆）",
                "ticket_price": f"成人票：{random.choice(['30', '50', '80', '120'])}元",
                "booking_method": "现场购票或官方网站预约",
                "images": [
                    "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400"
                ]
            },
            "past": {
                "opening_hours": "古代全天开放",
                "ticket_price": "古代免费参观",
                "booking_method": "古代无需预约",
                "images": [
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                    "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400"
                ]
            }
        },
        "城市地标": {
            "present": {
                "opening_hours": "10:00-22:00",
                "ticket_price": f"观景台：{random.choice(['60', '80', '100', '150'])}元",
                "booking_method": "现场购票、手机APP或官方网站",
                "images": [
                    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400",
                    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400"
                ]
            },
            "past": {
                "opening_hours": "古代建筑全天可观赏",
                "ticket_price": "古代免费参观",
                "booking_method": "古代无需预约",
                "images": [
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400"
                ]
            }
        }
    }
    
    type_details = details.get(attraction_type, details["自然景观"])
    mode_details = type_details.get(time_mode, type_details["present"])
    
    return {
        "opening_hours": mode_details["opening_hours"],
        "ticket_price": mode_details["ticket_price"],
        "booking_method": mode_details["booking_method"],
        "image": random.choice(mode_details["images"])
    }

def generate_attraction_details_for_real_place(place_data):
    """为真实景点生成详细信息"""
    import random
    
    # 根据景点名称推测类型
    name = place_data['name'].lower()
    if any(word in name for word in ['山', '湖', '河', '海', '森林', '公园', '自然', '风景']):
        category = '自然景观'
    elif any(word in name for word in ['寺', '庙', '宫', '城', '古', '遗址', '博物馆', '纪念']):
        category = '文化古迹'
    else:
        category = '城市地标'
    
    # 生成合理的营业信息
    if category == '自然景观':
        opening_hours = random.choice([
            "全天开放",
            "06:00-18:00",
            "日出至日落"
        ])
        ticket_price = random.choice([
            "免费",
            "成人票：20元",
            "成人票：30元"
        ])
        booking_method = "无需预约，直接前往"
        image = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
        
    elif category == '文化古迹':
        opening_hours = random.choice([
            "09:00-17:00（周一闭馆）",
            "08:30-17:30",
            "09:00-16:30（冬季）"
        ])
        ticket_price = f"成人票：{random.choice(['40', '60', '80', '100'])}元"
        booking_method = random.choice([
            "现场购票或官方网站预约",
            "建议提前网上预约",
            "现场购票，旺季建议预约"
        ])
        image = "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400"
        
    else:  # 城市地标
        opening_hours = random.choice([
            "10:00-22:00",
            "09:00-21:00",
            "全天开放（外观）"
        ])
        ticket_price = f"观景台：{random.choice(['50', '80', '120', '150'])}元"
        booking_method = random.choice([
            "现场购票、手机APP或官方网站",
            "支持现场购票和在线预订",
            "建议提前在线购票"
        ])
        image = "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400"
    
    return {
        "opening_hours": opening_hours,
        "ticket_price": ticket_price,
        "booking_method": booking_method,
        "category": category,
        "image": image
    }

def generate_virtual_place(point, time_mode):
    """为没有匹配地点的路径点生成虚拟地点信息"""
    lat, lon = point['latitude'], point['longitude']
    
    # 根据经纬度判断大致区域
    region_info = get_region_info(lat, lon)
    
    # 根据时间模式生成不同的描述
    descriptions = {
        "present": f"这里是{region_info['name']}的一片神秘土地，等待着探索者的发现。现代文明的痕迹在这里若隐若现。",
        "past": f"一百年前，这里是{region_info['name']}的荒野之地，只有少数勇敢的探险家曾经踏足。",
        "future": f"未来的{region_info['name']}，这里可能建立起新的城市，或成为重要的科研基地。"
    }
    
    return PlaceInfo(
        name=f"{region_info['name']}神秘之地",
        latitude=lat,
        longitude=lon,
        distance=point['distance'],
        description=descriptions.get(time_mode, descriptions["present"]),
        image="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
        country=region_info['country'],
        city=region_info['city']
    )

def get_region_info(lat, lon):
    """根据经纬度获取区域信息"""
    # 简单的区域判断逻辑
    if lat > 60:
        return {"name": "北极", "country": "极地", "city": "极地"}
    elif lat < -60:
        return {"name": "南极", "country": "极地", "city": "极地"}
    elif -30 <= lat <= 70 and -10 <= lon <= 60:
        return {"name": "欧亚大陆", "country": "欧亚", "city": "未知"}
    elif -30 <= lat <= 50 and 60 <= lon <= 150:
        return {"name": "亚洲内陆", "country": "亚洲", "city": "未知"}
    elif -50 <= lat <= 40 and -180 <= lon <= -30:
        return {"name": "美洲大陆", "country": "美洲", "city": "未知"}
    elif -40 <= lat <= 10 and 110 <= lon <= 180:
        return {"name": "大洋洲", "country": "大洋洲", "city": "未知"}
    elif -40 <= lat <= 40 and -20 <= lon <= 60:
        return {"name": "非洲大陆", "country": "非洲", "city": "未知"}
    else:
        return {"name": "海洋", "country": "海洋", "city": "海域"}

@app.on_event("startup")
async def startup_event():
    """应用启动时加载数据"""
    load_places_data()
    print("✅ 应用启动完成")

@app.get("/")
async def root():
    """服务前端页面"""
    from fastapi.responses import FileResponse
    return FileResponse('index.html')

@app.get("/styles.css")
async def get_css():
    from fastapi.responses import FileResponse
    return FileResponse('styles.css')

@app.get("/app.js")
async def get_js():
    from fastapi.responses import FileResponse
    return FileResponse('app.js')

@app.post("/api/explore", response_model=ExploreResponse)
async def explore_direction(request: ExploreRequest):
    """探索指定方向的地点"""
    import time
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (0 <= request.heading < 360):
            raise HTTPException(status_code=400, detail="方向必须在0到360度之间")
        if request.segment_distance <= 0:
            raise HTTPException(status_code=400, detail="分段距离必须大于0")
        
        # 只计算到目标距离点
        target_distance = request.segment_distance
        
        # 计算目标距离点的坐标
        target_point = geod.Direct(
            request.latitude, 
            request.longitude, 
            request.heading, 
            target_distance * 1000  # 转换为米
        )
        
        # 创建目标点
        points = [{
            'latitude': target_point['lat2'],
            'longitude': target_point['lon2'],
            'distance': target_distance
        }]
        
        # 在目标点周围5km范围内搜索景点
        places = find_nearby_attractions(points, request.time_mode, search_radius_km=5)
        
        # 计算总距离
        total_distance = points[-1]['distance'] if points else 0
        
        calculation_time = time.time() - start_time
        
        return ExploreResponse(
            places=places,
            total_distance=total_distance,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")

@app.post("/api/explore-real", response_model=ExploreResponse)
async def explore_direction_real(request: ExploreRequest):
    """探索指定方向的地点（使用真实数据）"""
    import time
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (0 <= request.heading < 360):
            raise HTTPException(status_code=400, detail="方向必须在0到360度之间")
        if request.segment_distance <= 0:
            raise HTTPException(status_code=400, detail="分段距离必须大于0")
        
        # 只计算到目标距离点
        target_distance = request.segment_distance
        
        # 计算目标距离点的坐标
        target_point = geod.Direct(
            request.latitude, 
            request.longitude, 
            request.heading, 
            target_distance * 1000  # 转换为米
        )
        
        # 创建目标点
        points = [{
            'latitude': target_point['lat2'],
            'longitude': target_point['lon2'],
            'distance': target_distance
        }]
        
        # 使用真实数据服务获取地点信息
        places_data_list = await real_data_service.get_real_places_along_route(points, request.time_mode)
        
        # 转换为PlaceInfo对象
        places = []
        for place_data in places_data_list:
            place_info = PlaceInfo(
                name=place_data['name'],
                latitude=place_data['latitude'],
                longitude=place_data['longitude'],
                distance=place_data['distance'],
                description=place_data['description'],
                image=place_data.get('image'),
                country=place_data.get('country'),
                city=place_data.get('city'),
                opening_hours=place_data.get('opening_hours'),
                ticket_price=place_data.get('ticket_price'),
                booking_method=place_data.get('booking_method'),
                category=place_data.get('category')
            )
            places.append(place_info)
        
        # 计算总距离
        total_distance = points[-1]['distance'] if points else 0
        
        calculation_time = time.time() - start_time
        
        return ExploreResponse(
            places=places,
            total_distance=total_distance,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        print(f"真实数据探索错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"真实数据获取错误: {str(e)}")

@app.get("/api/places/{time_mode}")
async def get_places(time_mode: str):
    """获取指定时间模式的所有地点"""
    if time_mode not in places_data:
        raise HTTPException(status_code=404, detail="时间模式不存在")
    
    return {"places": places_data[time_mode]}

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "方向探索派对API",
        "version": "1.0.0"
    }

@app.post("/api/upload-avatar", response_model=AvatarUploadResponse)
async def upload_avatar(avatar: UploadFile = File(...)):
    """
    用户头像上传API
    
    允许用户上传头像图片，自动进行压缩和格式转换
    支持的格式：jpg, jpeg, png, gif, webp
    最大文件大小：5MB
    """
    start_time = time.time()
    
    try:
        # 验证文件类型
        if not avatar.content_type.startswith('image/'):
            return AvatarUploadResponse(
                success=False,
                upload_time=time.time() - start_time,
                error=f"不支持的文件类型: {avatar.content_type}"
            )
        
        # 检查文件大小 (5MB限制)
        file_size = 0
        content = await avatar.read()
        file_size = len(content)
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return AvatarUploadResponse(
                success=False,
                upload_time=time.time() - start_time,
                error=f"文件过大: {file_size / 1024 / 1024:.1f}MB，最大允许5MB"
            )
        
        # 创建profile_photo目录
        profile_dir = Path("../static/profile_photo")
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用PIL处理图片
        from io import BytesIO
        image = Image.open(BytesIO(content))
        
        # 转换为RGB模式（去除透明通道）
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 调整图片大小（最大400x400，保持比例）
        image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # 保存为profile.jpg
        output_path = profile_dir / "profile.jpg"
        image.save(output_path, "JPEG", quality=85, optimize=True)
        
        # 计算处理后的文件大小
        final_size = output_path.stat().st_size
        
        # 生成访问URL - 使用相对路径适配云环境
        avatar_url = "/static/profile_photo/profile.jpg"
        
        print(f"✅ 头像上传成功:")
        print(f"   原始大小: {file_size / 1024:.1f}KB")
        print(f"   压缩后: {final_size / 1024:.1f}KB")
        print(f"   图片尺寸: {image.size}")
        print(f"   访问URL: {avatar_url}")
        
        return AvatarUploadResponse(
            success=True,
            avatar_url=avatar_url,
            file_size=final_size,
            upload_time=time.time() - start_time
        )
        
    except Exception as e:
        print(f"❌ 头像上传失败: {str(e)}")
        return AvatarUploadResponse(
            success=False,
            upload_time=time.time() - start_time,
            error=f"处理失败: {str(e)}"
        )

# ========== 历史模式API端点 ==========

@app.post("/api/query-historical", response_model=HistoricalQueryResponse)
async def query_historical_location(request: HistoricalQueryRequest):
    """
    历史位置查询API
    
    根据坐标和年份查询该时空点的历史政治实体信息
    基于Historical-basemaps学术项目的历史边界数据
    
    Args:
        request: 包含纬度、经度和年份的查询请求
        
    Returns:
        历史位置信息，包括政治实体、统治者、文化圈等
    """
    start_time = time.time()
    
    try:
        print(f"🏛️ 历史查询请求: {request.year}年 ({request.latitude}, {request.longitude})")
        
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (-3000 <= request.year <= 2024):
            raise HTTPException(status_code=400, detail="年份必须在公元前3000年到2024年之间")
        
        # 调用历史查询服务
        historical_result = await historical_service.query_historical_location(
            request.latitude, 
            request.longitude, 
            request.year
        )
        
        # 格式化响应
        calculation_time = time.time() - start_time
        
        if historical_result['success']:
            # 转换为响应模型
            historical_info = HistoricalLocationInfo(**historical_result)
            
            response = HistoricalQueryResponse(
                success=True,
                historical_info=historical_info,
                calculation_time=calculation_time,
                data_source="Historical-basemaps (GitHub)"
            )
            
            print(f"✅ 历史查询成功: {historical_result['political_entity']} ({request.year})")
            print(f"⚡ 查询耗时: {calculation_time:.3f}秒")
            
            return response
        else:
            # 查询失败的情况
            response = HistoricalQueryResponse(
                success=False,
                historical_info=None,
                calculation_time=calculation_time,
                error=historical_result.get('error', '历史查询失败')
            )
            
            print(f"❌ 历史查询失败: {historical_result.get('error')}")
            return response
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他异常
        calculation_time = time.time() - start_time
        print(f"❌ 历史查询API异常: {e}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"历史查询处理失败: {str(e)}"
        )

@app.get("/api/historical/available-years")
async def get_available_historical_years():
    """
    获取可用的历史年份列表
    
    Returns:
        可用年份列表和数据集信息
    """
    try:
        available_years = await historical_service.data_loader.get_available_years()
        cache_info = historical_service.data_loader.get_cache_info()
        
        return {
            'success': True,
            'available_years': available_years,
            'total_datasets': len(available_years),
            'year_range': {
                'earliest': min(available_years),
                'latest': max(available_years)
            },
            'cache_info': {
                'cached_datasets': cache_info['cache_count'],
                'cache_size_mb': cache_info['total_cache_size_mb']
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.get("/api/historical/dataset-info/{year}")
async def get_dataset_info(year: int):
    """
    获取指定年份的数据集信息
    
    Args:
        year: 目标年份
        
    Returns:
        数据集详细信息
    """
    try:
        dataset_info = historical_service.data_loader.get_dataset_info(year)
        return {
            'success': True,
            'dataset_info': dataset_info
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.post("/api/query-historical-info")
async def query_historical_info(request: HistoricalSceneRequest):
    """
    仅查询历史信息API（不生成图片）
    
    专门为meme页面设计，只查询Historical-basemaps数据，
    不进行图片生成，避免长时间等待
    
    Args:
        request: 包含纬度、经度和年份的查询请求
        
    Returns:
        仅包含历史信息的响应
    """
    start_time = time.time()
    
    try:
        print(f"🔍 历史信息查询请求: {request.year}年 ({request.latitude}, {request.longitude})")
        
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (-3000 <= request.year <= 2024):
            raise HTTPException(status_code=400, detail="年份必须在公元前3000年到2024年之间")
        
        # 仅查询Historical-basemaps获取真实历史位置信息
        historical_result = await historical_service.query_historical_location(
            request.latitude, 
            request.longitude, 
            request.year
        )
        
        if not historical_result['success']:
            raise HTTPException(status_code=404, detail="未找到该时空点的历史信息")
        
        calculation_time = time.time() - start_time
        
        print(f"✅ 历史信息查询完成: {historical_result['political_entity']}")
        print(f"⚡ 查询耗时: {calculation_time:.3f}秒")
        
        # 转换为响应格式
        historical_info = HistoricalLocationInfo(**historical_result)
        
        return {
            'success': True,
            'historical_info': historical_info.dict(),
            'calculation_time': calculation_time,
            'message': '历史信息查询成功'
        }
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        calculation_time = time.time() - start_time
        print(f"❌ 历史信息查询失败: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"历史信息查询失败: {str(e)}"
        )

@app.post("/api/generate-historical-scene", response_model=HistoricalSceneResponse)
async def generate_historical_scene(request: HistoricalSceneRequest):
    """
    历史场景生成API
    
    结合Historical-basemaps查询和Gemini图像生成，创建完整的历史场景体验
    
    Args:
        request: 包含纬度、经度和年份的场景生成请求
        
    Returns:
        包含历史信息和AI生成场景的完整响应
    """
    start_time = time.time()
    
    try:
        print(f"🎨 历史场景生成请求: {request.year}年 ({request.latitude}, {request.longitude})")
        
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (-3000 <= request.year <= 2024):
            raise HTTPException(status_code=400, detail="年份必须在公元前3000年到2024年之间")
        
        # 1. 查询Historical-basemaps获取真实历史位置信息
        historical_result = await historical_service.query_historical_location(
            request.latitude, 
            request.longitude, 
            request.year
        )
        
        if not historical_result['success']:
            raise HTTPException(status_code=404, detail="未找到该时空点的历史信息")
        
        # 2. 使用Gemini生成历史场景描述/图像
        scene_result = await nano_banana_service.generate_historical_scene_image(
            historical_result, request.latitude, request.longitude
        )
        
        # 3. 生成AI历史锐评（使用现有AI服务）
        historical_review = await generate_historical_review(historical_result, scene_result)
        
        # 格式化响应
        calculation_time = time.time() - start_time
        
        # 转换为响应模型
        historical_info = HistoricalLocationInfo(**historical_result)
        scene_info = HistoricalSceneInfo(**scene_result)
        
        # 提取主要图片URL（用于前端直接显示）
        main_image_url = None
        if scene_result.get('images') and len(scene_result['images']) > 0:
            main_image_url = scene_result['images'][0]  # 使用第一张图片作为主图
        
        response = HistoricalSceneResponse(
            success=True,
            historical_info=historical_info,
            generated_scene=scene_info,
            image_url=main_image_url,  # 添加主图片URL
            calculation_time=calculation_time,
            data_source="Historical-basemaps + Gemini",
            ai_review=historical_review  # 添加AI历史锐评
        )
        
        print(f"✅ 历史场景生成完成: {historical_result['political_entity']} ({request.year})")
        print(f"⚡ 总耗时: {calculation_time:.3f}秒")
        print(f"🎨 生成模式: {scene_result.get('generation_model', 'Unknown')}")
        
        return response
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他异常
        calculation_time = time.time() - start_time
        print(f"❌ 历史场景生成API异常: {e}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"历史场景生成失败: {str(e)}"
        )

@app.post("/api/generate-historical-selfie", response_model=HistoricalSelfieResponse)
async def generate_historical_selfie(request: HistoricalSelfieRequest):
    """
    历史自拍生成API
    
    在演示模式中使用预设的自拍照片，
    在实际模式中将使用Gemini的图生图功能合成用户照片与历史场景
    
    Args:
        request: 包含场景信息和用户图片的自拍请求
        
    Returns:
        包含生成的自拍图片URL的响应
    """
    start_time = time.time()
    
    try:
        print(f"📸 历史自拍生成请求: {request.political_entity} ({request.year}年)")
        
        # 演示模式：使用预设自拍照片
        demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
        
        if demo_mode:
            print("🎭 演示模式：使用预设时光自拍照片")
            
            # 预设自拍照片URL - 使用相对路径适配云环境
            demo_selfie_url = "/static/take_photo/0b8459cf-b5ce-4c44-b3e3-352abe04d2de.jpg"
            
            # 构建场景信息
            scene_info = {
                "political_entity": request.political_entity,
                "year": request.year,
                "selfie_description": f"与{request.political_entity}({request.year}年)的时光合影",
                "demo_character": "时光旅行者",
                "generation_method": "预设演示图片"
            }
            
            calculation_time = time.time() - start_time
            
            print(f"✅ 演示自拍生成完成: {request.political_entity}")
            print(f"⚡ 响应时间: {calculation_time:.3f}秒")
            
            return HistoricalSelfieResponse(
                success=True,
                selfie_url=demo_selfie_url,
                scene_info=scene_info,
                generation_time=calculation_time,
                demo_mode=True
            )
        else:
            # 实际模式：使用Gemini图生图
            print("🎨 实际模式：调用Gemini图生图API")
            
            # 获取用户头像路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            user_image_path = os.path.join(project_root, "static", "profile_photo", "profile.jpg")
            
            # 检查用户头像是否存在
            if not os.path.exists(user_image_path):
                raise HTTPException(
                    status_code=400,
                    detail="请先上传头像照片才能生成历史自拍"
                )
            
            # 根据scene_id查找对应的历史场景图片
            # 使用新的目录结构查找
            scene_images_dir = os.path.join(project_root, "static", "meme", "scene_view")
            generated_images_dir = os.path.join(project_root, "static", "generated_images")  # 向后兼容
            pregenerated_images_dir = os.path.join(project_root, "static", "pregenerated_images")
            
            historical_scene_image_path = None
            
            # 方法1: 如果scene_id是完整的文件名，直接查找
            if request.scene_id.endswith(('.png', '.jpg', '.jpeg')):
                # 首先尝试在新的meme/scene_view目录中查找
                potential_path = os.path.join(scene_images_dir, request.scene_id)
                if os.path.exists(potential_path):
                    historical_scene_image_path = potential_path
                else:
                    # 向后兼容：尝试在旧的generated_images目录中查找
                    potential_path = os.path.join(generated_images_dir, request.scene_id)
                    if os.path.exists(potential_path):
                        historical_scene_image_path = potential_path
                    else:
                        # 尝试在预生成图片目录中查找
                        potential_path = os.path.join(pregenerated_images_dir, request.scene_id)
                        if os.path.exists(potential_path):
                            historical_scene_image_path = potential_path
            
            # 方法2: 如果scene_id不是完整文件名，尝试匹配包含scene_id的文件
            if not historical_scene_image_path:
                # 首先在新的meme/scene_view目录中查找包含scene_id的文件
                try:
                    for filename in os.listdir(scene_images_dir):
                        if request.scene_id in filename and filename.endswith(('.png', '.jpg', '.jpeg')):
                            historical_scene_image_path = os.path.join(scene_images_dir, filename)
                            break
                except:
                    pass
                
                # 向后兼容：在旧的generated_images目录中查找
                if not historical_scene_image_path:
                    try:
                        for filename in os.listdir(generated_images_dir):
                            if request.scene_id in filename and filename.endswith(('.png', '.jpg', '.jpeg')):
                                historical_scene_image_path = os.path.join(generated_images_dir, filename)
                                break
                    except:
                        pass
                
                # 如果还没找到，在预生成图片目录中查找
                if not historical_scene_image_path:
                    try:
                        for filename in os.listdir(pregenerated_images_dir):
                            if request.scene_id in filename and filename.endswith(('.png', '.jpg', '.jpeg')):
                                historical_scene_image_path = os.path.join(pregenerated_images_dir, filename)
                                break
                    except:
                        pass
            
            # 方法3: 根据political_entity和year查找最近的历史场景图片
            if not historical_scene_image_path:
                try:
                    entity_name = request.political_entity.replace(' ', '_').replace('/', '_')
                    pattern = f"nano_banana_{entity_name}_{request.year}_"
                    
                    # 查找最新的匹配文件
                    latest_file = None
                    latest_time = 0
                    
                    # 首先在新的scene_view目录中查找
                    try:
                        for filename in os.listdir(scene_images_dir):
                            if filename.startswith(pattern) and filename.endswith('.png'):
                                file_path = os.path.join(scene_images_dir, filename)
                                file_time = os.path.getmtime(file_path)
                                if file_time > latest_time:
                                    latest_time = file_time
                                    latest_file = file_path
                    except:
                        pass
                    
                    # 向后兼容：在旧的generated_images目录中查找
                    if not latest_file:
                        for filename in os.listdir(generated_images_dir):
                            if filename.startswith(pattern) and filename.endswith('.png'):
                                file_path = os.path.join(generated_images_dir, filename)
                                file_time = os.path.getmtime(file_path)
                                if file_time > latest_time:
                                    latest_time = file_time
                                    latest_file = file_path
                    
                    if latest_file:
                        historical_scene_image_path = latest_file
                except:
                    pass
            
            # 如果找不到历史场景图片，返回错误
            if not historical_scene_image_path:
                raise HTTPException(
                    status_code=400,
                    detail=f"找不到场景ID '{request.scene_id}' 对应的历史场景图片。请先生成历史场景图片。"
                )
            
            print(f"✅ 找到历史场景图片: {os.path.basename(historical_scene_image_path)}")
            
            # 调用图生图服务
            selfie_result = await nano_banana_service.generate_historical_selfie(
                user_image_path=user_image_path,
                historical_scene_image_path=historical_scene_image_path
            )
            
            calculation_time = time.time() - start_time
            
            if selfie_result['success']:
                print(f"✅ 图生图自拍生成成功: {request.political_entity}")
                print(f"⚡ 总处理时间: {calculation_time:.3f}秒")
                
                return HistoricalSelfieResponse(
                    success=True,
                    selfie_url=selfie_result['selfie_url'],
                    scene_info=selfie_result['scene_info'],
                    generation_time=calculation_time,
                    demo_mode=False
                )
            else:
                # 图生图失败，提供演示模式备选方案
                print(f"❌ 图生图生成失败: {selfie_result.get('error')}")
                
                if selfie_result.get('demo_mode_available') or selfie_result.get('fallback_available'):
                    print("🔄 回退到演示模式...")
                    
                    demo_selfie_url = "/static/take_photo/0b8459cf-b5ce-4c44-b3e3-352abe04d2de.jpg"
                    scene_info = {
                        "political_entity": request.political_entity,
                        "year": request.year,
                        "selfie_description": f"与{request.political_entity}({request.year}年)的时光合影（演示模式备选）",
                        "generation_method": "演示模式（API故障备选）",
                        "original_error": selfie_result.get('error')
                    }
                    
                    return HistoricalSelfieResponse(
                        success=True,
                        selfie_url=demo_selfie_url,
                        scene_info=scene_info,
                        generation_time=calculation_time,
                        demo_mode=True
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"历史自拍生成失败: {selfie_result.get('error')}"
                    )
            
    except HTTPException:
        raise
    except Exception as e:
        calculation_time = time.time() - start_time
        print(f"❌ 历史自拍生成API异常: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"历史自拍生成失败: {str(e)}"
        )

@app.get("/api/historical/generation-capabilities")
async def get_historical_generation_capabilities():
    """
    获取当前历史场景生成能力
    
    Returns:
        当前支持的生成功能和配置状态
    """
    try:
        # 使用新版Nano Banana服务
        return {
            'success': True,
            'capabilities': {
                'client_available': nano_banana_service.client_available,
                'api_version': 'google-genai 1.32.0',
                'supported_model': 'gemini-2.5-flash-image-preview',
                'demo_mode': not nano_banana_service.client_available
            },
            'api_configured': nano_banana_service.client_available,
            'demo_mode_available': True
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def generate_historical_review(historical_info: Dict, scene_data: Dict) -> Dict:
    """
    生成AI历史锐评 - 基于现有AI服务
    """
    try:
        print(f"🤖 开始生成历史锐评: {historical_info['political_entity']} ({historical_info['query_year']}年)")
        
        # 获取现有AI服务
        ai_service = get_ai_service()
        
        # 构建适合历史场景的参数
        historical_scene_name = f"{historical_info['political_entity']} ({historical_info['query_year']}年)"
        historical_scene_type = f"历史文明场景 - {historical_info.get('time_period', '古代')}"
        
        # 构建丰富的历史场景描述
        enhanced_description = f"""
🏛️ 政治实体：{historical_info['political_entity']}
👑 统治者：{historical_info.get('ruler_or_power', '未知')}
🌍 文化圈：{historical_info['cultural_region']}
📊 边界精度：{historical_info.get('border_precision', 1)}级 (Historical-basemaps数据)

🎨 AI场景重现：
{scene_data.get('scene_description', '历史场景已生成')}

🕰️ 历史背景：
{historical_info.get('description', '')}

这是基于Historical-basemaps学术数据和Nano Banana AI技术重现的{historical_info['query_year']}年真实历史场景。
        """
        
        # 构建历史探索的用户上下文
        historical_user_context = {
            'visit_count': 0,  # 历史探索通常是单次体验
            'time_of_day': time.strftime('%H:%M'),
            'previous_places': [],
            'exploration_type': 'historical_time_travel',
            'data_source': 'Historical-basemaps + Nano Banana AI',
            'special_note': f'这是一次时空穿越体验，用户探索了{historical_info["query_year"]}年的{historical_info["political_entity"]}'
        }
        
        # 调用现有AI服务生成锐评
        review_result = await ai_service.generate_scene_review(
            scene_name=historical_scene_name,
            scene_description=enhanced_description.strip(),
            scene_type=historical_scene_type,
            user_context=historical_user_context
        )
        
        print(f"✅ AI历史锐评生成成功: {review_result.get('title', 'N/A')}")
        
        return review_result
        
    except Exception as e:
        print(f"❌ AI历史锐评生成失败: {e}")
        
        # 返回简单的历史锐评
        return {
            'success': False,
            'title': f"历史探索：{historical_info['political_entity']}",
            'review': f"您探索了{historical_info['query_year']}年的{historical_info['political_entity']}！这个时代充满了独特的文化魅力和历史价值。通过AI重现的历史场景，我们得以一窥那个时代的政治制度、社会生活和文化特色。这样的时空探索体验具有珍贵的教育意义。",
            'highlights': ['时空穿越体验', '历史文化学习', 'AI场景重现'],
            'tips': '用心感受历史文明的独特魅力',
            'rating_reason': '珍贵的历史探索体验',
            'mood': '穿越时空',
            'fallback': True
        }

# ========== 旅程管理API端点 ==========

# 旅程管理的请求模型
class StartJourneyRequest(BaseModel):
    """开始新旅程的请求模型"""
    start_lat: float
    start_lng: float
    start_name: str
    start_address: Optional[str] = None
    journey_title: Optional[str] = None

class VisitSceneRequest(BaseModel):
    """访问场景的请求模型"""
    journey_id: str
    scene_name: str
    scene_lat: float
    scene_lng: float
    scene_address: Optional[str] = None
    user_rating: Optional[int] = None
    notes: Optional[str] = None

class SceneReviewRequest(BaseModel):
    """场景锐评请求模型"""
    scene_name: str
    scene_description: str
    scene_type: Optional[str] = "自然景观"
    scene_lat: Optional[float] = None
    scene_lng: Optional[float] = None
    user_context: Optional[Dict] = None

class SceneReviewResponse(BaseModel):
    """场景锐评响应模型"""
    success: bool
    review_data: Dict
    generation_time: float
    message: str

class JourneySummaryRequest(BaseModel):
    """旅程总结请求模型"""
    visited_scenes: List[Dict]
    total_distance: float
    journey_duration: str
    scenes_count: int

class JourneySummaryResponse(BaseModel):
    """旅程总结响应模型"""
    success: bool
    summary: str
    generation_time: float
    message: str

@app.post("/api/journey/start")
async def start_journey(request: StartJourneyRequest):
    """
    开始新的旅程
    
    Args:
        request: 包含起始位置和旅程标题的请求
        
    Returns:
        新创建的旅程ID和基本信息
    """
    try:
        # 创建起始位置对象
        start_location = JourneyLocation(
            lat=request.start_lat,
            lng=request.start_lng,
            name=request.start_name,
            address=request.start_address
        )
        
        # 创建新旅程
        journey_id = journey_service.create_journey(
            start_location=start_location,
            journey_title=request.journey_title
        )
        
        # 获取创建的旅程信息
        journey = journey_service.get_journey(journey_id)
        
        return {
            "success": True,
            "journey_id": journey_id,
            "journey_title": journey.journey_title,
            "start_time": journey.start_time,
            "start_location": journey.start_location.dict(),
            "message": f"🎒 新旅程已开始：{journey.journey_title}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建旅程失败：{str(e)}")

@app.post("/api/journey/visit")
async def visit_scene(request: VisitSceneRequest):
    """
    记录访问场景
    
    Args:
        request: 包含旅程ID和场景信息的请求
        
    Returns:
        访问记录的结果
    """
    try:
        # 创建场景位置对象
        scene_location = JourneyLocation(
            lat=request.scene_lat,
            lng=request.scene_lng,
            name=request.scene_name,
            address=request.scene_address
        )
        
        # 记录场景访问
        success = journey_service.visit_scene(
            journey_id=request.journey_id,
            scene_name=request.scene_name,
            scene_location=scene_location,
            user_rating=request.user_rating,
            notes=request.notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="旅程不存在")
        
        # 获取更新后的旅程信息
        journey = journey_service.get_journey(request.journey_id)
        
        return {
            "success": True,
            "journey_id": request.journey_id,
            "visited_scenes_count": len(journey.visited_scenes),
            "current_location": journey.current_location.dict(),
            "message": f"🏁 已到达：{request.scene_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录访问失败：{str(e)}")

@app.get("/api/journey/{journey_id}")
async def get_journey(journey_id: str):
    """
    获取指定旅程的详细信息
    
    Args:
        journey_id: 旅程ID
        
    Returns:
        完整的旅程信息
    """
    try:
        journey = journey_service.get_journey(journey_id)
        
        if not journey:
            raise HTTPException(status_code=404, detail="旅程不存在")
        
        return {
            "success": True,
            "journey": journey.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取旅程失败：{str(e)}")

@app.get("/api/journey/{journey_id}/summary")
async def get_journey_summary(journey_id: str):
    """
    获取旅程摘要信息
    
    Args:
        journey_id: 旅程ID
        
    Returns:
        旅程摘要信息
    """
    try:
        summary = journey_service.get_journey_summary(journey_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="旅程不存在")
        
        return {
            "success": True,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取旅程摘要失败：{str(e)}")

@app.post("/api/journey/{journey_id}/end")
async def end_journey(journey_id: str):
    """
    结束指定的旅程
    
    Args:
        journey_id: 旅程ID
        
    Returns:
        结束操作的结果
    """
    try:
        success = journey_service.end_journey(journey_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="旅程不存在")
        
        # 获取结束后的旅程信息
        journey = journey_service.get_journey(journey_id)
        
        return {
            "success": True,
            "journey_id": journey_id,
            "end_time": journey.end_time,
            "visited_scenes_count": len(journey.visited_scenes),
            "total_distance_km": journey.total_distance_km,
            "message": f"🏠 旅程结束：{journey.journey_title}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"结束旅程失败：{str(e)}")

@app.get("/api/journeys/active")
async def get_active_journeys():
    """
    获取所有活跃的旅程
    
    Returns:
        活跃旅程列表
    """
    try:
        active_journeys = journey_service.get_active_journeys()
        
        return {
            "success": True,
            "count": len(active_journeys),
            "journeys": [journey.dict() for journey in active_journeys]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃旅程失败：{str(e)}")

@app.post("/api/scene-review", response_model=SceneReviewResponse)
async def generate_scene_review(request: SceneReviewRequest):
    """
    生成场景锐评
    
    Args:
        request: 场景锐评请求，包含场景信息和用户上下文
    
    Returns:
        SceneReviewResponse: 包含AI生成的锐评内容
    """
    start_time = time.time()
    
    try:
        # 获取AI服务
        ai_service = get_ai_service()
        
        if not ai_service:
            # AI服务不可用，返回备用内容
            return SceneReviewResponse(
                success=False,
                review_data={
                    "title": f"探索发现：{request.scene_name}",
                    "review": f"欢迎来到{request.scene_name}！{request.scene_description} 虽然AI服务暂时不可用，但这个地方仍然值得您深入探索。",
                    "highlights": ["真实场景探索", "独特地理位置", "值得记录的时刻"],
                    "tips": "用心感受每个地方的独特魅力",
                    "rating_reason": "探索本身就是最好的理由",
                    "mood": "冒险"
                },
                generation_time=time.time() - start_time,
                message="AI服务不可用，返回备用锐评内容"
            )
        
        # 准备用户上下文
        user_context = request.user_context or {}
        
        # 调用AI服务生成锐评
        review_data = await ai_service.generate_scene_review(
            scene_name=request.scene_name,
            scene_description=request.scene_description,
            scene_type=request.scene_type,
            user_context=user_context
        )
        
        generation_time = time.time() - start_time
        
        return SceneReviewResponse(
            success=True,
            review_data=review_data,
            generation_time=generation_time,
            message=f"🤖 AI锐评生成成功：{request.scene_name}"
        )
        
    except Exception as e:
        generation_time = time.time() - start_time
        
        # 错误处理：返回备用内容
        return SceneReviewResponse(
            success=False,
            review_data={
                "title": f"探索发现：{request.scene_name}",
                "review": f"这里是{request.scene_name}，{request.scene_description} 每个地方都有其独特的魅力，值得您亲自体验和发现。",
                "highlights": ["独特的地理位置", "值得记录的探索", "真实的旅行体验"],
                "tips": "保持好奇心，用心感受",
                "rating_reason": "探索的乐趣",
                "mood": "发现"
            },
            generation_time=generation_time,
            message=f"AI服务错误，返回备用内容：{str(e)}"
        )

@app.post("/api/journey-summary", response_model=JourneySummaryResponse)
async def generate_journey_summary(request: JourneySummaryRequest):
    """
    生成AI旅程总结
    
    Args:
        request: 旅程总结请求，包含访问场景、距离、时长等信息
    
    Returns:
        JourneySummaryResponse: 包含AI生成的旅程总结文本
    """
    start_time = time.time()
    
    try:
        # 获取AI服务
        ai_service = get_ai_service()
        
        if not ai_service:
            raise HTTPException(status_code=503, detail="AI服务不可用")
        
        # 调用AI服务生成旅程总结
        summary_text = await ai_service.generate_journey_summary_ai(
            visited_scenes=request.visited_scenes,
            total_distance=request.total_distance,
            journey_duration=request.journey_duration
        )
        
        generation_time = time.time() - start_time
        
        return JourneySummaryResponse(
            success=True,
            summary=summary_text,
            generation_time=generation_time,
            message=f"🤖 AI旅程总结生成成功：{request.scenes_count}个场景"
        )
        
    except Exception as e:
        generation_time = time.time() - start_time
        
        # 错误处理：返回备用总结
        fallback_summary = f"🎉 恭喜完成这次精彩的探索之旅！您访问了{request.scenes_count}个地点，总共行进了{request.total_distance:.1f}公里，耗时{request.journey_duration}。每一步都是独特的发现，每一处风景都值得珍藏。感谢您选择方向探索派对，期待您的下次冒险！🧭✨"
        
        return JourneySummaryResponse(
            success=False,
            summary=fallback_summary,
            generation_time=generation_time,
            message=f"AI服务错误，返回备用总结：{str(e)}"
        )

@app.get("/api/config/maps")
async def get_maps_config():
    """
    获取Google Maps相关配置
    注意：生产环境应该从环境变量或配置文件读取
    """
    # 从环境变量获取API Key
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')

    return {
        "apiKey": api_key,
        "enabled": api_key != 'YOUR_GOOGLE_MAPS_API_KEY',
        "message": "Google Maps配置已加载"
    }

# ====================================
# 新增：历史梗图生成器 API端点
# ====================================

from pydantic import BaseModel
from typing import Optional, List
from fastapi import UploadFile, File, Form
import uuid

class CustomHistoricalSceneRequest(BaseModel):
    """自定义历史场景生成请求"""
    historical_info: Dict
    custom_prompt: str
    template_id: Optional[str] = None

class CustomHistoricalSceneResponse(BaseModel):
    """自定义历史场景生成响应"""
    success: bool
    image_url: str
    scene_description: str
    generation_time: float

class SceneAnalysisRequest(BaseModel):
    """场景分析请求"""
    image_url: str

class SceneAnalysisResponse(BaseModel):
    """场景分析响应"""
    success: bool
    elements: List[str]
    analysis_time: float

class HistoricalMemeResponse(BaseModel):
    """历史梗图生成响应"""
    success: bool
    meme_url: str
    generation_time: float

@app.post("/api/generate-custom-historical-scene", response_model=CustomHistoricalSceneResponse)
async def generate_custom_historical_scene(request: CustomHistoricalSceneRequest):
    """
    使用自定义提示词生成历史场景
    """
    start_time = time.time()
    
    try:
        print(f"🎨 自定义历史场景生成: {request.historical_info['political_entity']} ({request.historical_info['query_year']}年)")
        print(f"💬 用户提示词: {request.custom_prompt}")
        if request.template_id:
            print(f"📋 使用场景模板: {request.template_id}")
        
        # 构建提示词：使用模板或自定义
        if request.template_id:
            # 使用场景模板，直接传递给服务层处理
            final_prompt = request.custom_prompt  # 这里传递原始prompt，让服务层处理模板
            print(f"📋 将使用场景模板进行处理: {request.template_id}")
        else:
            # 使用传统的历史背景构建方式
            final_prompt = f"""
你是一位专业的历史场景画家，请根据以下历史背景和用户需求，生成一幅详细的历史场景图：

📍 历史背景：
- 政治实体: {request.historical_info['political_entity']}
- 年份: {request.historical_info['query_year']}年
- 文化区域: {request.historical_info['cultural_region']}
- 统治者: {request.historical_info.get('ruler_or_power', '未知')}

🎯 用户需求: {request.custom_prompt}

请生成一幅历史准确、视觉丰富的场景图，展现该时期的建筑风格、服装特色、日常生活场景等。
图片应该具有高品质的艺术效果，色彩丰富，细节丰富。
"""
            print(f"📝 使用传统历史背景构建方式")
        
        # 使用nano_banana_service生成图像
        result = await nano_banana_service.generate_scene_with_custom_prompt(
            final_prompt, request.historical_info, request.template_id
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail="场景图片生成失败")
        
        generation_time = time.time() - start_time
        
        return CustomHistoricalSceneResponse(
            success=True,
            image_url=result['image_url'],
            scene_description=result.get('scene_description', '自定义历史场景'),
            generation_time=generation_time
        )
        
    except Exception as e:
        generation_time = time.time() - start_time
        print(f"❌ 自定义历史场景生成失败: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"自定义历史场景生成失败: {str(e)}"
        )

@app.post("/api/analyze-scene-elements", response_model=SceneAnalysisResponse)
async def analyze_scene_elements(request: SceneAnalysisRequest):
    """
    分析历史场景图，提取关键元素
    """
    start_time = time.time()
    
    try:
        print(f"🔍 开始分析场景元素: {request.image_url}")
        
        # 使用Gemini Vision进行图片分析
        result = await nano_banana_service.analyze_image_elements(request.image_url)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail="图片分析失败")
        
        analysis_time = time.time() - start_time
        
        return SceneAnalysisResponse(
            success=True,
            elements=result['elements'],
            analysis_time=analysis_time
        )
        
    except Exception as e:
        analysis_time = time.time() - start_time
        print(f"❌ 场景元素分析失败: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"场景元素分析失败: {str(e)}"
        )

@app.post("/api/generate-historical-meme", response_model=HistoricalMemeResponse)
async def generate_historical_meme(
    character_image: UploadFile = File(...),
    composition_image: Optional[UploadFile] = File(None),
    scene_elements: str = Form(...),
    meme_prompt: str = Form(...),
    historical_info: str = Form(...),
    template_id: Optional[str] = Form(None),
    interaction_id: Optional[str] = Form(None),
    companion_image: Optional[UploadFile] = File(None)
):
    """
    生成历史梗图
    
    Args:
        character_image: 人物素材图片
        composition_image: 构图参考图片（可选）
        scene_elements: 场景元素列表（JSON字符串）
        meme_prompt: 用户自定义梗图提示词
        historical_info: 历史背景信息（JSON字符串）
        template_id: 预设模板ID（可选，如'cinematic_selfie'）
    """
    start_time = time.time()
    
    try:
        print(f"🎭 开始生成历史梗图")
        if template_id:
            print(f"📋 使用预设模板: {template_id}")
        
        # 解析JSON字符串
        import json
        scene_elements_list = json.loads(scene_elements)
        historical_info_dict = json.loads(historical_info)
        
        print(f"💬 梗图提示: {meme_prompt}")
        print(f"🏛️ 场景元素: {scene_elements_list}")
        print(f"🎯 模板ID: {template_id or '无'}")
        
        # 保存上传的图片
        character_image_path = None
        composition_image_path = None
        
        if character_image:
            character_image_path = f"/tmp/character_{uuid.uuid4().hex}.{character_image.filename.split('.')[-1]}"
            with open(character_image_path, "wb") as f:
                content = await character_image.read()
                f.write(content)
        
        if composition_image:
            composition_image_path = f"/tmp/composition_{uuid.uuid4().hex}.{composition_image.filename.split('.')[-1]}"
            with open(composition_image_path, "wb") as f:
                content = await composition_image.read()
                f.write(content)
        
        companion_image_path = None
        if companion_image:
            companion_image_path = f"/tmp/companion_{uuid.uuid4().hex}.{companion_image.filename.split('.')[-1]}"
            with open(companion_image_path, "wb") as f:
                content = await companion_image.read()
                f.write(content)
        
        # 使用nano_banana_service生成梗图
        result = await nano_banana_service.generate_historical_meme(
            character_image_path=character_image_path,
            composition_image_path=composition_image_path,
            scene_elements=scene_elements_list,
            meme_prompt=meme_prompt,
            historical_info=historical_info_dict,
            template_id=template_id,
            interaction_id=interaction_id,
            companion_image_path=companion_image_path
        )
        
        # 清理临时文件
        if character_image_path and os.path.exists(character_image_path):
            os.remove(character_image_path)
        if composition_image_path and os.path.exists(composition_image_path):
            os.remove(composition_image_path)
        if companion_image_path and os.path.exists(companion_image_path):
            os.remove(companion_image_path)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail="梗图生成失败")
        
        generation_time = time.time() - start_time
        
        return HistoricalMemeResponse(
            success=True,
            meme_url=result['meme_url'],
            generation_time=generation_time
        )
        
    except Exception as e:
        generation_time = time.time() - start_time
        print(f"❌ 历史梗图生成失败: {e}")
        
        # 清理临时文件
        try:
            if 'character_image_path' in locals() and character_image_path and os.path.exists(character_image_path):
                os.remove(character_image_path)
            if 'composition_image_path' in locals() and composition_image_path and os.path.exists(composition_image_path):
                os.remove(composition_image_path)
            if 'companion_image_path' in locals() and companion_image_path and os.path.exists(companion_image_path):
                os.remove(companion_image_path)
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"历史梗图生成失败: {str(e)}"
        )

@app.get("/api/meme-templates")
async def get_meme_templates():
    """
    获取可用的梗图模板列表
    """
    try:
        from nano_banana_service import nano_banana_service
        
        templates = nano_banana_service.meme_templates.get('templates', [])
        
        # 返回简化的模板信息（用于前端显示）
        simplified_templates = []
        for template in templates:
            template_data = {
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'category': template.get('category', 'general'),
                'tags': template.get('tags', []),
                'usage_count': template.get('usage_count', 0)
            }
            # 如果模板支持互动选择，标记它
            if template.get('has_interactions'):
                template_data['has_interactions'] = True
            simplified_templates.append(template_data)
        
        return {
            'success': True,
            'templates': simplified_templates,
            'total_count': len(simplified_templates),
            'interactions': nano_banana_service.meme_templates.get('interactions', {})
        }
        
    except Exception as e:
        print(f"❌ 获取梗图模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取梗图模板失败: {str(e)}"
        )

@app.get("/api/scene-templates")
async def get_scene_templates():
    """
    获取可用的场景模板列表
    """
    try:
        from nano_banana_service import nano_banana_service
        
        templates = nano_banana_service.scene_templates.get('scene_templates', [])
        
        # 返回简化的模板信息（用于前端显示）
        simplified_templates = []
        for template in templates:
            simplified_templates.append({
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'category': template.get('category', 'general'),
                'tags': template.get('tags', []),
                'usage_count': template.get('usage_count', 0)
            })
        
        return {
            'success': True,
            'templates': simplified_templates,
            'total_count': len(simplified_templates)
        }
        
    except Exception as e:
        print(f"❌ 获取场景模板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取场景模板失败: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)