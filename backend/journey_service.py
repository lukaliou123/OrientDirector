"""
旅程管理服务
用于管理用户的探索旅程，包括旅程创建、场景访问记录、数据持久化等功能
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

# 数据模型定义
class JourneyLocation(BaseModel):
    """旅程中的位置点"""
    lat: float
    lng: float
    name: str
    address: Optional[str] = None

class VisitedScene(BaseModel):
    """访问过的场景"""
    scene_id: str
    name: str
    location: JourneyLocation
    visit_time: str  # ISO格式时间戳
    duration_minutes: Optional[int] = None  # 停留时间（分钟）
    user_rating: Optional[int] = None  # 用户评分 1-5
    notes: Optional[str] = None  # 用户备注

class Journey(BaseModel):
    """完整的旅程记录"""
    journey_id: str
    start_time: str
    end_time: Optional[str] = None
    start_location: JourneyLocation
    current_location: JourneyLocation
    visited_scenes: List[VisitedScene] = []
    total_distance_km: float = 0.0
    is_active: bool = True
    journey_title: Optional[str] = None
    created_at: str

class JourneyService:
    """旅程管理服务类"""
    
    def __init__(self, data_file: str = "data/journeys.json"):
        """
        初始化旅程服务
        
        Args:
            data_file: JSON数据文件路径
        """
        self.data_file = data_file
        self.ensure_data_directory()
        self.journeys_cache = self.load_journeys()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.data_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def load_journeys(self) -> Dict[str, Dict]:
        """从JSON文件加载所有旅程数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading journeys: {e}")
            return {}
    
    def save_journeys(self):
        """保存旅程数据到JSON文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.journeys_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving journeys: {e}")
            raise
    
    def create_journey(
        self, 
        start_location: JourneyLocation,
        journey_title: Optional[str] = None
    ) -> str:
        """
        创建新的旅程
        
        Args:
            start_location: 起始位置
            journey_title: 旅程标题（可选）
            
        Returns:
            新创建的旅程ID
        """
        journey_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        # 如果没有提供标题，自动生成
        if not journey_title:
            journey_title = f"探索之旅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        journey = Journey(
            journey_id=journey_id,
            start_time=current_time,
            start_location=start_location,
            current_location=start_location,
            journey_title=journey_title,
            created_at=current_time
        )
        
        # 保存到缓存
        self.journeys_cache[journey_id] = journey.dict()
        
        # 持久化到文件
        self.save_journeys()
        
        return journey_id
    
    def get_journey(self, journey_id: str) -> Optional[Journey]:
        """
        获取指定的旅程信息
        
        Args:
            journey_id: 旅程ID
            
        Returns:
            旅程对象或None
        """
        if journey_id in self.journeys_cache:
            try:
                return Journey(**self.journeys_cache[journey_id])
            except Exception as e:
                print(f"Error parsing journey {journey_id}: {e}")
                return None
        return None
    
    def visit_scene(
        self,
        journey_id: str,
        scene_name: str,
        scene_location: JourneyLocation,
        user_rating: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        记录访问场景
        
        Args:
            journey_id: 旅程ID
            scene_name: 场景名称
            scene_location: 场景位置
            user_rating: 用户评分（1-5）
            notes: 用户备注
            
        Returns:
            是否成功记录
        """
        if journey_id not in self.journeys_cache:
            return False
        
        journey_data = self.journeys_cache[journey_id]
        
        # 创建访问记录
        visited_scene = VisitedScene(
            scene_id=str(uuid.uuid4()),
            name=scene_name,
            location=scene_location,
            visit_time=datetime.now().isoformat(),
            user_rating=user_rating,
            notes=notes
        )
        
        # 添加到旅程记录
        if "visited_scenes" not in journey_data:
            journey_data["visited_scenes"] = []
        
        journey_data["visited_scenes"].append(visited_scene.dict())
        
        # 更新当前位置
        journey_data["current_location"] = scene_location.dict()
        
        # 计算总距离（简单的累加，可以后续优化为精确计算）
        if len(journey_data["visited_scenes"]) > 1:
            # 这里可以添加距离计算逻辑
            pass
        
        # 保存更改
        self.save_journeys()
        
        return True
    
    def end_journey(self, journey_id: str) -> bool:
        """
        结束指定的旅程
        
        Args:
            journey_id: 旅程ID
            
        Returns:
            是否成功结束
        """
        if journey_id not in self.journeys_cache:
            return False
        
        journey_data = self.journeys_cache[journey_id]
        journey_data["end_time"] = datetime.now().isoformat()
        journey_data["is_active"] = False
        
        # 保存更改
        self.save_journeys()
        
        return True
    
    def get_active_journeys(self) -> List[Journey]:
        """获取所有活跃的旅程"""
        active_journeys = []
        for journey_data in self.journeys_cache.values():
            if journey_data.get("is_active", False):
                try:
                    active_journeys.append(Journey(**journey_data))
                except Exception as e:
                    print(f"Error parsing active journey: {e}")
        return active_journeys
    
    def get_journey_summary(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """
        获取旅程摘要信息
        
        Args:
            journey_id: 旅程ID
            
        Returns:
            旅程摘要字典
        """
        journey = self.get_journey(journey_id)
        if not journey:
            return None
        
        return {
            "journey_id": journey.journey_id,
            "title": journey.journey_title,
            "start_time": journey.start_time,
            "end_time": journey.end_time,
            "is_active": journey.is_active,
            "visited_scenes_count": len(journey.visited_scenes),
            "total_distance_km": journey.total_distance_km,
            "start_location": journey.start_location.dict(),
            "current_location": journey.current_location.dict()
        }

# 全局旅程服务实例
journey_service = JourneyService()
