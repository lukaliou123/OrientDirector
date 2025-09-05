#!/usr/bin/env python3
"""
简化的后端测试版本
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random

app = FastAPI(title="方向探索派对API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简化的城市数据
CITIES_DATA = [
    {
        "key": "paris",
        "name": "巴黎",
        "country": "法国",
        "coordinates": [48.8566, 2.3522],
        "type": "global",
        "attraction_count": 6
    },
    {
        "key": "london",
        "name": "伦敦",
        "country": "英国",
        "coordinates": [51.5074, -0.1278],
        "type": "global",
        "attraction_count": 6
    },
    {
        "key": "beijing",
        "name": "北京",
        "country": "中国",
        "coordinates": [39.9042, 116.4074],
        "type": "china",
        "attraction_count": 22
    },
    {
        "key": "shanghai",
        "name": "上海",
        "country": "中国",
        "coordinates": [31.2304, 121.4737],
        "type": "china",
        "attraction_count": 6
    }
]

ATTRACTIONS_DATA = {
    "paris": [
        {
            "name": "埃菲尔铁塔",
            "latitude": 48.8584,
            "longitude": 2.2945,
            "category": "地标建筑",
            "description": "巴黎的象征，世界著名的铁塔建筑，高324米。",
            "opening_hours": "09:30-23:45",
            "ticket_price": "成人票：29.4欧元",
            "booking_method": "官方网站预约",
            "image": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?w=800",
            "video": "https://www.youtube.com/watch?v=F7nCDrf90V8",
            "country": "法国",
            "city": "巴黎",
            "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris"
        }
    ]
}

# 数据模型
class CityInfo(BaseModel):
    key: str
    name: str
    country: str
    coordinates: List[float]
    type: str
    attraction_count: int

class AttractionInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    category: str
    description: str
    opening_hours: str
    ticket_price: str
    booking_method: str
    image: Optional[str] = None
    video: Optional[str] = None
    country: str
    city: str
    address: str

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "城市漫游API", "version": "1.0.0"}

@app.get("/api/cities", response_model=List[CityInfo])
async def get_all_cities():
    return CITIES_DATA

@app.get("/api/cities/search")
async def search_cities(query: str):
    query = query.lower()
    results = [city for city in CITIES_DATA 
               if query in city["name"].lower() or query in city["country"].lower()]
    return {"cities": results}

@app.get("/api/cities/{city_key}/attractions", response_model=List[AttractionInfo])
async def get_city_attractions(city_key: str):
    if city_key in ATTRACTIONS_DATA:
        return ATTRACTIONS_DATA[city_key]
    return []

@app.post("/api/cities/roam")
async def roam_to_city(request: dict):
    city_key = request.get("city_key")
    if city_key in ATTRACTIONS_DATA and ATTRACTIONS_DATA[city_key]:
        attraction = random.choice(ATTRACTIONS_DATA[city_key])
        city = next((c for c in CITIES_DATA if c["key"] == city_key), None)
        return {
            "success": True,
            "message": f"成功漫游到 {city['name'] if city else city_key}",
            "city_info": city,
            "attraction": attraction
        }
    return {"success": False, "message": "未找到城市或景点数据"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)