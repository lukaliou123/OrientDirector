"""
Prompt Generator Module
生成Doro合影的智能提示词
"""

import logging
from typing import Optional, Dict, List
import random

logger = logging.getLogger(__name__)

class DoroPromptGenerator:
    """Doro合影提示词生成器"""
    
    def __init__(self):
        """初始化提示词生成器"""
        # 景点类型到场景描述的映射
        self.scene_templates = {
            "历史遗迹": "ancient historical site with weathered stones and cultural heritage atmosphere",
            "自然景观": "natural landscape with breathtaking views and pristine environment",
            "现代建筑": "modern architectural marvel with contemporary design elements",
            "主题公园": "vibrant theme park with colorful attractions and joyful atmosphere",
            "博物馆": "museum setting with cultural artifacts and educational displays",
            "宗教场所": "sacred religious site with spiritual ambiance and traditional architecture",
            "城市地标": "iconic city landmark with urban skyline and metropolitan vibes",
            "海滩度假": "beautiful beach resort with ocean waves and tropical paradise feel",
            "山地景观": "majestic mountain scenery with peaks and valleys",
            "园林公园": "scenic garden park with lush greenery and peaceful paths"
        }
        
        # Doro风格描述
        self.doro_styles = {
            "cute": "adorable cartoon character with big expressive eyes and friendly smile",
            "adventurous": "brave explorer character ready for adventure",
            "elegant": "sophisticated character with graceful posture",
            "sporty": "athletic character full of energy and vitality",
            "tech": "futuristic character with high-tech accessories",
            "default": "charming animated character companion"
        }
        
        # 互动姿势库
        self.interaction_poses = [
            "standing side by side like best friends",
            "making peace signs together",
            "pointing at the landmark excitedly",
            "taking a selfie pose",
            "waving happily at the camera",
            "doing a fun jump together",
            "giving thumbs up",
            "making heart shapes with hands"
        ]
        
        # 天气和光线条件
        self.lighting_conditions = [
            "golden hour lighting with warm sunset glow",
            "bright sunny day with clear blue sky",
            "soft morning light with gentle shadows",
            "dramatic sunset with orange and pink sky",
            "perfect lighting for photography"
        ]
    
    def generate_attraction_doro_prompt(
        self,
        attraction_name: str,
        attraction_type: Optional[str] = None,
        location: Optional[str] = None,
        with_style: bool = False,
        doro_style: str = "default",
        user_description: Optional[str] = None
    ) -> str:
        """
        生成景点+Doro合影的提示词
        
        Args:
            attraction_name: 景点名称
            attraction_type: 景点类型
            location: 地理位置
            with_style: 是否包含服装风格
            doro_style: Doro的风格类型
            user_description: 用户的额外描述
            
        Returns:
            生成的提示词
        """
        # 基础提示词结构
        prompt_parts = []
        
        # 1. 主体描述
        prompt_parts.append(
            f"Create a high-quality travel photo showing a real person and their {self.doro_styles.get(doro_style, self.doro_styles['default'])} friend Doro"
        )
        
        # 2. 场景设置
        if attraction_name:
            prompt_parts.append(f"at the famous {attraction_name}")
            
        if location:
            prompt_parts.append(f"in {location}")
        
        # 3. 场景类型描述
        if attraction_type and attraction_type in self.scene_templates:
            prompt_parts.append(f", {self.scene_templates[attraction_type]}")
        
        # 4. 互动姿势
        pose = random.choice(self.interaction_poses)
        prompt_parts.append(f". They are {pose}")
        
        # 5. 服装风格（如果需要）
        if with_style:
            prompt_parts.append(", with the clothing style as shown in the reference image")
        else:
            prompt_parts.append(", wearing casual travel attire")
        
        # 6. 光线和氛围
        lighting = random.choice(self.lighting_conditions)
        prompt_parts.append(f". The scene has {lighting}")
        
        # 7. 技术要求
        prompt_parts.append(
            ". Maintain the original person's facial features perfectly unchanged. "
            "Doro should appear as a friendly animated companion character. "
            "The composition should be natural and harmonious, like a real travel photo. "
            "High resolution, professional photography quality"
        )
        
        # 8. 用户自定义描述
        if user_description:
            prompt_parts.append(f". Additional details: {user_description}")
        
        prompt = " ".join(prompt_parts)
        
        logger.info(f"生成Doro合影提示词: {prompt[:100]}...")
        return prompt
    
    def generate_style_transfer_prompt(
        self,
        style_description: Optional[str] = None
    ) -> str:
        """
        生成服装风格迁移提示词
        
        Args:
            style_description: 风格描述
            
        Returns:
            风格迁移提示词
        """
        base_prompt = "Apply the clothing style from the reference image to both the person and Doro character"
        
        if style_description:
            base_prompt += f", specifically: {style_description}"
        
        base_prompt += (
            ". Maintain consistent style elements including colors, patterns, and fashion aesthetics. "
            "The clothing should look natural and appropriate for the travel setting"
        )
        
        return base_prompt
    
    def generate_composition_prompt(
        self,
        composition_type: str = "standard"
    ) -> str:
        """
        生成构图提示词
        
        Args:
            composition_type: 构图类型
            
        Returns:
            构图提示词
        """
        compositions = {
            "standard": "Rule of thirds composition with balanced placement of subjects",
            "centered": "Centered composition with symmetrical balance",
            "dynamic": "Dynamic diagonal composition with energy and movement",
            "close-up": "Close-up shot focusing on the subjects with blurred background",
            "wide": "Wide angle shot showing the full landmark and environment",
            "portrait": "Portrait orientation emphasizing the subjects"
        }
        
        return compositions.get(composition_type, compositions["standard"])
    
    def enhance_prompt_with_details(
        self,
        base_prompt: str,
        time_of_day: Optional[str] = None,
        weather: Optional[str] = None,
        season: Optional[str] = None,
        mood: Optional[str] = None
    ) -> str:
        """
        使用额外细节增强提示词
        
        Args:
            base_prompt: 基础提示词
            time_of_day: 时间（早晨、下午、黄昏等）
            weather: 天气条件
            season: 季节
            mood: 情绪氛围
            
        Returns:
            增强后的提示词
        """
        enhancements = []
        
        if time_of_day:
            time_descriptions = {
                "morning": "early morning with soft golden light",
                "afternoon": "bright afternoon with vibrant colors",
                "sunset": "beautiful sunset with warm orange glow",
                "night": "evening with city lights and starry sky"
            }
            if time_of_day in time_descriptions:
                enhancements.append(time_descriptions[time_of_day])
        
        if weather:
            weather_descriptions = {
                "sunny": "perfect sunny weather",
                "cloudy": "soft cloudy sky creating even lighting",
                "after_rain": "fresh after-rain atmosphere with clean air",
                "snow": "winter wonderland with snow"
            }
            if weather in weather_descriptions:
                enhancements.append(weather_descriptions[weather])
        
        if season:
            season_descriptions = {
                "spring": "spring season with blooming flowers",
                "summer": "vibrant summer atmosphere",
                "autumn": "autumn with colorful foliage",
                "winter": "winter scenery with crisp air"
            }
            if season in season_descriptions:
                enhancements.append(season_descriptions[season])
        
        if mood:
            mood_descriptions = {
                "joyful": "joyful and celebratory mood",
                "peaceful": "peaceful and serene atmosphere",
                "adventurous": "exciting adventure feeling",
                "romantic": "romantic and dreamy ambiance"
            }
            if mood in mood_descriptions:
                enhancements.append(mood_descriptions[mood])
        
        if enhancements:
            enhanced_prompt = f"{base_prompt}. Scene features: {', '.join(enhancements)}"
        else:
            enhanced_prompt = base_prompt
        
        return enhanced_prompt
    
    def get_negative_prompt(self) -> str:
        """
        获取负面提示词（避免生成的内容）
        
        Returns:
            负面提示词
        """
        return (
            "blurry, low quality, distorted faces, extra limbs, "
            "unnatural poses, bad anatomy, ugly, duplicate, "
            "morbid, mutilated, poorly drawn, mutation, deformed, "
            "bad proportions, cloned face, disfigured, malformed limbs, "
            "missing arms, missing legs, extra arms, extra legs, "
            "fused fingers, too many fingers"
        )
    
    def create_batch_prompts(
        self,
        attraction_info: Dict,
        variations: int = 3
    ) -> List[str]:
        """
        创建多个变体提示词
        
        Args:
            attraction_info: 景点信息
            variations: 变体数量
            
        Returns:
            提示词列表
        """
        prompts = []
        
        for i in range(variations):
            # 为每个变体选择不同的参数
            prompt = self.generate_attraction_doro_prompt(
                attraction_name=attraction_info.get("name"),
                attraction_type=attraction_info.get("category"),
                location=attraction_info.get("location"),
                with_style=attraction_info.get("with_style", False),
                doro_style=attraction_info.get("doro_style", "default")
            )
            
            # 添加不同的增强
            if i == 0:
                prompt = self.enhance_prompt_with_details(prompt, time_of_day="sunset")
            elif i == 1:
                prompt = self.enhance_prompt_with_details(prompt, mood="joyful")
            elif i == 2:
                prompt = self.enhance_prompt_with_details(prompt, weather="sunny")
            
            prompts.append(prompt)
        
        return prompts

# 创建全局实例
doro_prompt_generator = DoroPromptGenerator()