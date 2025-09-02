from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import math
from geographiclib.geodesic import Geodesic
import json
import os
import asyncio
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from real_data_service import real_data_service
from journey_service import journey_service, Journey, JourneyLocation, VisitedScene
from ai_service import get_ai_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = FastAPI(title="方向探索派对API", version="1.0.0")

def load_attractions_from_json() -> Dict:
    """从journeys.json文件加载景点数据"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), "data", "journeys.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("beijing_top_attractions", {}).get("attractions", {})
    except Exception as e:
        logger.error(f"加载景点数据失败: {e}")
        return {}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两点之间的距离（公里）"""
    geod = Geodesic.WGS84
    result = geod.Inverse(lat1, lon1, lat2, lon2)
    return result['s12'] / 1000  # 转换为公里

def get_nearby_attractions_from_json(target_lat: float, target_lon: float, max_distance_km: float = 50) -> List[Dict]:
    """从JSON文件中获取附近的景点，按距离排序"""
    attractions_data = load_attractions_from_json()
    nearby_attractions = []
    
    for attraction_id, attraction in attractions_data.items():
        # 获取景点坐标
        coords = attraction.get("coordinates", {})
        attr_lat = coords.get("lat")
        attr_lon = coords.get("lng")
        
        if attr_lat is None or attr_lon is None:
            continue
            
        # 计算距离
        distance_km = calculate_distance(target_lat, target_lon, attr_lat, attr_lon)
        
        # 只包含指定距离内的景点
        if distance_km <= max_distance_km:
            attraction_info = {
                "id": attraction_id,
                "name": attraction.get("name", "未知景点"),
                "latitude": attr_lat,
                "longitude": attr_lon,
                "distance": round(distance_km, 2),
                "description": attraction.get("description", ""),
                "category": attraction.get("category", ""),
                "address": attraction.get("address", ""),
                "opening_hours": attraction.get("opening_hours", ""),
                "ticket_price": attraction.get("ticket_price", ""),
                "rating": attraction.get("rating", 0),
                "photos": attraction.get("photos", []),
                "highlights": attraction.get("highlights", []),
                "visit_duration": attraction.get("visit_duration", ""),
                "best_visit_time": attraction.get("best_visit_time", ""),
                "transportation": attraction.get("transportation", "")
            }
            nearby_attractions.append(attraction_info)
    
    # 按距离排序（从近到远）
    nearby_attractions.sort(key=lambda x: x["distance"])
    
    logger.info(f"从JSON文件中找到 {len(nearby_attractions)} 个景点，距离目标点 ({target_lat:.4f}, {target_lon:.4f}) {max_distance_km}km 以内")
    
    return nearby_attractions

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print("地点数据加载完成")

@app.get("/")
async def root():
    return {"message": "方向探索派对API服务正在运行"}

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
        
        # 使用本地JSON数据获取附近景点信息
        target_lat = target_point['lat2']
        target_lon = target_point['lon2']
        
        # 从JSON文件中获取附近景点，搜索半径50km
        places_data_list = get_nearby_attractions_from_json(target_lat, target_lon, max_distance_km=50)
        
        # 转换为PlaceInfo对象
        places = []
        for place_data in places_data_list:
            # 构建图片URL（取第一张图片）
            image_url = place_data.get('photos', [None])[0] if place_data.get('photos') else None
            
            place_info = PlaceInfo(
                name=place_data['name'],
                latitude=place_data['latitude'],
                longitude=place_data['longitude'],
                distance=place_data['distance'],
                description=place_data['description'],
                image=image_url,
                country="中国",
                city="北京",
                opening_hours=place_data.get('opening_hours'),
                ticket_price=place_data.get('ticket_price'),
                booking_method="现场购票或在线预约",
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

# 漫游功能相关数据模型
class GeocodeRequest(BaseModel):
    query: str
    language: str = "zh-CN"

class PlaceDetailsRequest(BaseModel):
    place_id: Optional[str] = None
    location: Dict[str, float]  # {"lat": float, "lng": float}

# 备用地理编码函数
async def fallback_geocode(query: str):
    """
    备用地理编码方案 - 使用预定义的常见地点坐标
    """
    # 常见地点的坐标数据库
    common_places = {
        # 中国主要城市
        "北京": {"lat": 39.9042, "lng": 116.4074, "address": "北京市, 中华人民共和国"},
        "上海": {"lat": 31.2304, "lng": 121.4737, "address": "上海市, 中华人民共和国"},
        "广州": {"lat": 23.1291, "lng": 113.2644, "address": "广州市, 广东省, 中华人民共和国"},
        "深圳": {"lat": 22.5431, "lng": 114.0579, "address": "深圳市, 广东省, 中华人民共和国"},
        "杭州": {"lat": 30.2741, "lng": 120.1551, "address": "杭州市, 浙江省, 中华人民共和国"},
        "南京": {"lat": 32.0603, "lng": 118.7969, "address": "南京市, 江苏省, 中华人民共和国"},
        "成都": {"lat": 30.5728, "lng": 104.0668, "address": "成都市, 四川省, 中华人民共和国"},
        "西安": {"lat": 34.3416, "lng": 108.9398, "address": "西安市, 陕西省, 中华人民共和国"},
        
        # 著名景点
        "天安门": {"lat": 39.9055, "lng": 116.3976, "address": "天安门广场, 北京市, 中华人民共和国"},
        "天安门广场": {"lat": 39.9055, "lng": 116.3976, "address": "天安门广场, 北京市, 中华人民共和国"},
        "故宫": {"lat": 39.9163, "lng": 116.3972, "address": "故宫博物院, 北京市, 中华人民共和国"},
        "外滩": {"lat": 31.2396, "lng": 121.4906, "address": "外滩, 上海市, 中华人民共和国"},
        "上海外滩": {"lat": 31.2396, "lng": 121.4906, "address": "外滩, 上海市, 中华人民共和国"},
        "东方明珠": {"lat": 31.2397, "lng": 121.4999, "address": "东方明珠塔, 上海市, 中华人民共和国"},
        "西湖": {"lat": 30.2369, "lng": 120.1457, "address": "西湖, 杭州市, 浙江省, 中华人民共和国"},
        "杭州西湖": {"lat": 30.2369, "lng": 120.1457, "address": "西湖, 杭州市, 浙江省, 中华人民共和国"},
        
        # 国际城市
        "东京": {"lat": 35.6762, "lng": 139.6503, "address": "东京, 日本"},
        "纽约": {"lat": 40.7128, "lng": -74.0060, "address": "纽约, 美国"},
        "伦敦": {"lat": 51.5074, "lng": -0.1278, "address": "伦敦, 英国"},
        "巴黎": {"lat": 48.8566, "lng": 2.3522, "address": "巴黎, 法国"},
    }
    
    # 尝试匹配查询字符串
    query_lower = query.lower()
    for place_name, coords in common_places.items():
        if place_name in query or place_name.lower() in query_lower:
            return {
                "success": True,
                "data": {
                    "formatted_address": coords["address"],
                    "place_id": f"fallback_{place_name}",
                    "geometry": {
                        "location": {
                            "lat": coords["lat"],
                            "lng": coords["lng"]
                        },
                        "location_type": "APPROXIMATE"
                    },
                    "address_components": [],
                    "types": ["locality", "political"]
                },
                "message": f"使用备用数据找到位置: {coords['address']} (Google Maps API不可用)"
            }
    
    # 如果没有找到匹配的地点
    return {
        "success": False,
        "error": f"未找到位置: {query}。Google Maps API不可用，且备用数据库中没有匹配的地点。"
    }

@app.post("/api/geocode")
async def geocode_location(request: GeocodeRequest):
    """
    地理编码API - 将地址转换为坐标
    优先级：1. 高德地图API -> 2. Google Maps API -> 3. 备用数据库
    """
    logger.info(f"🌍 开始地理编码搜索: '{request.query}'")
    start_time = time.time()
    
    # 方案1: 尝试使用高德地图API
    try:
        logger.info("📡 尝试使用高德地图地理编码API...")
        amap_result = await try_amap_geocode(request.query)
        if amap_result["success"]:
            elapsed_time = time.time() - start_time
            logger.info(f"✅ 高德地图API调用成功，耗时: {elapsed_time:.2f}秒")
            return amap_result
        else:
            logger.warning(f"⚠️ 高德地图API未找到结果: {amap_result.get('error', '未知错误')}")
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.warning(f"❌ 高德地图API调用失败 (耗时: {elapsed_time:.2f}秒): {e}")
    
    # 方案2: 尝试使用Google Maps API
    try:
        logger.info("📡 切换到Google Maps地理编码API...")
        google_result = await try_google_geocode(request.query, request.language)
        if google_result["success"]:
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Google Maps API调用成功，耗时: {elapsed_time:.2f}秒")
            return google_result
        else:
            logger.warning(f"⚠️ Google Maps API未找到结果: {google_result.get('error', '未知错误')}")
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.warning(f"❌ Google Maps API调用失败 (耗时: {elapsed_time:.2f}秒): {e}")
    
    # 方案3: 使用备用数据库
    logger.info("🔄 切换到备用地理编码方案...")
    elapsed_time = time.time() - start_time
    logger.info(f"⏱️ 前两种方案总耗时: {elapsed_time:.2f}秒")
    return await fallback_geocode(request.query)

# 高德地图地理编码
async def try_amap_geocode(query: str):
    """
    使用高德地图API进行地理编码
    """
    try:
        import requests
        
        # 获取高德地图API Key
        amap_key = os.getenv('AMAP_API_KEY')
        if not amap_key or amap_key == 'YOUR_AMAP_API_KEY':
            return {
                "success": False,
                "error": "高德地图API Key未配置"
            }
        
        # 调用高德地图地理编码API
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            'key': amap_key,
            'address': query,
            'output': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1' and data.get('geocodes'):
            geocode = data['geocodes'][0]
            location = geocode['location'].split(',')
            
            return {
                "success": True,
                "data": {
                    "formatted_address": geocode.get('formatted_address', query),
                    "place_id": f"amap_{geocode.get('adcode', 'unknown')}",
                    "geometry": {
                        "location": {
                            "lat": float(location[1]),
                            "lng": float(location[0])
                        },
                        "location_type": "ROOFTOP"
                    },
                    "address_components": [],
                    "types": ["geocode"]
                },
                "message": f"高德地图找到位置: {geocode.get('formatted_address', query)}"
            }
        else:
            return {
                "success": False,
                "error": f"高德地图未找到位置: {query}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"高德地图API调用失败: {str(e)}"
        }

# Google Maps地理编码
async def try_google_geocode(query: str, language: str = "zh-CN"):
    """
    使用Google Maps API进行地理编码
    """
    try:
        import googlemaps
        import asyncio
        import concurrent.futures
        
        # 获取Google Maps API Key
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key or api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            return {
                "success": False,
                "error": "Google Maps API Key未配置"
            }
        
        # 初始化Google Maps客户端，设置超时
        gmaps = googlemaps.Client(key=api_key, timeout=10)
        
        def sync_geocode():
            return gmaps.geocode(
                address=query,
                language=language
            )
        
        # 使用线程池执行同步操作，避免阻塞
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            geocode_result = await loop.run_in_executor(executor, sync_geocode)
        
        if not geocode_result:
            return {
                "success": False,
                "error": f"Google Maps未找到位置: {query}"
            }
        
        # 返回第一个结果
        result = geocode_result[0]
        
        return {
            "success": True,
            "data": {
                "formatted_address": result["formatted_address"],
                "place_id": result["place_id"],
                "geometry": {
                    "location": {
                        "lat": result["geometry"]["location"]["lat"],
                        "lng": result["geometry"]["location"]["lng"]
                    },
                    "location_type": result["geometry"]["location_type"]
                },
                "address_components": result["address_components"],
                "types": result["types"]
            },
            "message": f"Google Maps找到位置: {result['formatted_address']}"
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "googlemaps库未安装"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Google Maps API调用失败: {str(e)}"
        }

@app.post("/api/place-details")
async def get_place_details(request: PlaceDetailsRequest):
    """
    获取地点详细信息API
    """
    try:
        import googlemaps
        
        # 获取Google Maps API Key
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key or api_key == 'YOUR_GOOGLE_MAPS_API_KEY':
            raise HTTPException(status_code=500, detail="Google Maps API Key未配置")
        
        # 初始化Google Maps客户端
        gmaps = googlemaps.Client(key=api_key)
        
        place_details = None
        
        # 如果有place_id，直接获取详情
        if request.place_id:
            try:
                                    place_details = gmaps.place(
                        place_id=request.place_id,
                        fields=[
                            'name', 'formatted_address', 'geometry', 'rating', 
                            'formatted_phone_number', 'website', 'opening_hours',
                            'photo', 'reviews', 'price_level'
                        ],
                        language='zh-CN'
                    )["result"]
            except Exception as e:
                print(f"使用place_id获取详情失败: {e}")
        
        # 如果没有place_id或获取失败，使用坐标搜索附近地点
        if not place_details:
            try:
                nearby_places = gmaps.places_nearby(
                    location=(request.location["lat"], request.location["lng"]),
                    radius=100,  # 100米范围内
                    language='zh-CN'
                )
                
                if nearby_places["results"]:
                    # 获取第一个地点的详细信息
                    first_place = nearby_places["results"][0]
                    place_details = gmaps.place(
                        place_id=first_place["place_id"],
                        fields=[
                            'name', 'formatted_address', 'geometry', 'rating', 
                            'formatted_phone_number', 'website', 'opening_hours',
                            'photo', 'reviews', 'price_level'
                        ],
                        language='zh-CN'
                    )["result"]
            except Exception as e:
                print(f"搜索附近地点失败: {e}")
        
        if not place_details:
            # 使用备用方案提供基本信息
            return {
                "success": True,
                "data": {
                    "name": "未知地点",
                    "formatted_address": f"坐标: {request.location['lat']:.6f}, {request.location['lng']:.6f}",
                    "rating": None,
                    "formatted_phone_number": None,
                    "website": None,
                    "opening_hours": None,
                    "photos": [],
                    "types": ["point_of_interest"],
                    "price_level": None,
                    "geometry": {
                        "location": request.location
                    }
                },
                "message": "Google Maps API不可用，返回基本位置信息"
            }
        
        # 处理照片URL
        photos = []
        if "photo" in place_details:
            # Google Maps API现在返回单个photo字段而不是photos数组
            photo_data = place_details["photo"]
            if isinstance(photo_data, list):
                for photo in photo_data[:5]:  # 最多5张照片
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo['photo_reference']}&key={api_key}"
                    photos.append({
                        "photo_reference": photo["photo_reference"],
                        "photo_url": photo_url,
                        "width": photo.get("width", 400),
                        "height": photo.get("height", 300)
                    })
            elif isinstance(photo_data, dict) and "photo_reference" in photo_data:
                # 单张照片
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_data['photo_reference']}&key={api_key}"
                photos.append({
                    "photo_reference": photo_data["photo_reference"],
                    "photo_url": photo_url,
                    "width": photo_data.get("width", 400),
                    "height": photo_data.get("height", 300)
                })
        
        # 构建返回数据
        result_data = {
            "name": place_details.get("name", "未知地点"),
            "formatted_address": place_details.get("formatted_address", ""),
            "rating": place_details.get("rating"),
            "formatted_phone_number": place_details.get("formatted_phone_number"),
            "website": place_details.get("website"),
            "opening_hours": place_details.get("opening_hours"),
            "photos": photos,
            "types": place_details.get("types", []),
            "price_level": place_details.get("price_level"),
            "geometry": place_details.get("geometry", {})
        }
        
        # 处理评论
        if "reviews" in place_details:
            result_data["reviews"] = place_details["reviews"][:3]  # 最多3条评论
        
        return {
            "success": True,
            "data": result_data,
            "message": f"成功获取地点详情: {result_data['name']}"
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "googlemaps库未安装，请运行: pip install googlemaps"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取地点详情失败: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)