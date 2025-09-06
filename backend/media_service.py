# 媒体服务 - 处理图片和视频资源
import os
import base64
from typing import Optional, Dict

class MediaService:
    """媒体资源管理服务"""
    
    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.static_path = os.path.join(self.base_path, "..", "static")
        self.images_path = os.path.join(self.static_path, "images")
        
        # 确保目录存在
        os.makedirs(self.images_path, exist_ok=True)
    
    def get_placeholder_image(self, name: str, color: str = "4ECDC4") -> str:
        """生成占位图片URL - 使用本地SVG避免外部依赖"""
        # 使用base64编码的SVG作为占位图
        import base64
        svg_content = f'''<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#{color}"/>
            <text x="50%" y="50%" font-family="Arial" font-size="24" fill="#FFFFFF" text-anchor="middle" dy=".3em">{name}</text>
        </svg>'''
        encoded_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded_svg}"
    
    def get_local_image_path(self, attraction_name: str) -> str:
        """获取本地图片路径"""
        # 简化文件名
        filename = attraction_name.replace("博物院", "").replace("公园", "").replace("广场", "")
        return f"/static/images/{filename}.jpg"
    
    def create_svg_placeholder(self, name: str, width: int = 800, height: int = 400) -> str:
        """创建SVG占位图片的data URI"""
        colors = {
            "故宫": "#FF6B6B",
            "天安门": "#4ECDC4", 
            "天坛": "#45B7D1",
            "颐和园": "#96CEB4",
            "长城": "#FECA57",
            "雍和宫": "#FF9FF3",
            "北海": "#54A0FF",
            "景山": "#5F27CD"
        }
        
        # 根据景点名称选择颜色
        color = "#6C5CE7"  # 默认颜色
        for key, value in colors.items():
            if key in name:
                color = value
                break
        
        svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="{color}"/>
            <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="32" 
                  fill="white" text-anchor="middle" dy=".3em">{name}</text>
        </svg>'''
        
        # 转换为data URI
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"
    
    def get_attraction_media(self, attraction: Dict) -> Dict:
        """获取景点的媒体资源"""
        name = attraction.get("name", "未知景点")
        
        # 优先使用本地图片，然后是SVG占位图
        image_url = self.create_svg_placeholder(name)
        
        # 视频处理 - 暂时不提供视频，避免播放问题
        video_url = None
        
        return {
            "image": image_url,
            "video": video_url,
            "has_local_image": False,
            "media_type": "svg_placeholder"
        }

# 创建全局实例
media_service = MediaService()
