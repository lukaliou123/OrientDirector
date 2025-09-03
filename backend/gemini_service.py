import os
import base64
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from datetime import datetime
import logging
from typing import Optional, Tuple
import tempfile
from fastapi import UploadFile
import json

# 配置日志
logger = logging.getLogger(__name__)

# 配置 Google Gemini API
GEMINI_API_KEY = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=GEMINI_API_KEY)

class GeminiImageService:
    """Google Gemini 图片生成服务"""
    
    def __init__(self):
        # 使用支持图片生成的模型 (Nano Banana)
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        self.output_dir = "backend/generated_images"
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_attraction_prompt(
        self, 
        attraction_name: str, 
        location: str = None,
        category: str = None,
        description: str = None,
        opening_hours: str = None,
        ticket_price: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> str:
        """
        根据景点完整信息生成智能合影提示词
        
        Args:
            attraction_name: 景点名称
            location: 景点位置（城市或国家）
            category: 景点类别
            description: 景点描述
            opening_hours: 开放时间
            ticket_price: 门票价格
            latitude: 纬度
            longitude: 经度
            
        Returns:
            生成的智能提示词
        """
        # 景点特定的提示词模板
        attraction_prompts = {
            # 中国景点
            "长城": "让图中的人站在万里长城上，背景是蜿蜒的长城和远山，穿着休闲旅游装，做出胜利的手势，天气晴朗，蓝天白云。保持人脸的原貌不变。",
            "故宫": "让图中的人站在故宫太和殿前，背景是金碧辉煌的宫殿建筑，穿着现代休闲装，自然地微笑，阳光明媚。保持人脸的原貌不变。",
            "天安门": "让图中的人站在天安门广场前，背景是雄伟的天安门城楼，穿着休闲装，自然地站立或做和平手势，蓝天白云。保持人脸的原貌不变。",
            "兵马俑": "让图中的人站在秦始皇兵马俑坑旁，背景是整齐排列的兵马俑军阵，穿着现代装束，表情惊叹，保持人脸的原貌不变。",
            
            # 日本景点
            "富士山": "让图中的人站在富士山前，背景是雪顶的富士山和樱花树，穿着日式休闲装或和服，开心地微笑，春天的氛围。保持人脸的原貌不变。",
            "东京铁塔": "让图中的人站在东京铁塔前，背景是红白相间的铁塔和现代化城市，穿着时尚休闲装，做出拍照姿势。保持人脸的原貌不变。",
            "清水寺": "让图中的人站在京都清水寺前，背景是传统的日式寺庙建筑和红叶，穿着和服或休闲装，优雅地站立。保持人脸的原貌不变。",
            
            # 欧洲景点
            "埃菲尔铁塔": "让图中的人站在埃菲尔铁塔前，背景是标志性的铁塔和塞纳河，穿着优雅的休闲装，浪漫的氛围，黄昏时分。保持人脸的原貌不变。",
            "罗马斗兽场": "让图中的人站在罗马斗兽场前，背景是古老的圆形竞技场，穿着休闲夏装，做出胜利手势，阳光明媚。保持人脸的原貌不变。",
            "大本钟": "让图中的人站在伦敦大本钟前，背景是威斯敏斯特宫和泰晤士河，穿着英伦风格服装，优雅地站立。保持人脸的原貌不变。",
            
            # 美洲景点
            "自由女神像": "让图中的人站在自由女神像前，背景是纽约港和自由女神像，穿着美式休闲装，举起手臂模仿自由女神的姿势。保持人脸的原貌不变。",
            "金门大桥": "让图中的人站在旧金山金门大桥前，背景是红色的大桥和海湾，穿着休闲装，享受海风，夕阳西下。保持人脸的原貌不变。",
            "尼亚加拉瀑布": "让图中的人站在尼亚加拉瀑布观景台，背景是壮观的瀑布和彩虹，穿着防水外套，表情兴奋。保持人脸的原貌不变。",
            
            # 其他著名景点
            "金字塔": "让图中的人站在埃及金字塔前，背景是吉萨金字塔群和狮身人面像，穿着探险装束，沙漠的金色阳光。保持人脸的原貌不变。",
            "泰姬陵": "让图中的人站在印度泰姬陵前，背景是白色大理石的泰姬陵，穿着印度传统服装或休闲装，日出时分。保持人脸的原貌不变。",
            "悉尼歌剧院": "让图中的人站在悉尼歌剧院前，背景是标志性的贝壳形建筑和海港大桥，穿着夏装，阳光灿烂。保持人脸的原貌不变。"
        }
        
        # 查找匹配的景点提示词
        for key, prompt in attraction_prompts.items():
            if key in attraction_name:
                return prompt
        
        # 使用智能提示词生成
        return self._generate_intelligent_prompt(
            attraction_name, location, category, description, 
            opening_hours, ticket_price, latitude, longitude
        )
    
    def _generate_intelligent_prompt(
        self, 
        name: str, 
        location: str = None, 
        category: str = None, 
        description: str = None,
        opening_hours: str = None,
        ticket_price: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> str:
        """
        生成智能提示词
        """
        # 基础提示词模板
        prompt = f"请将图中的人物与{name}进行完美合影合成。"
        
        # 根据景点类别添加特定描述
        if category:
            category_prompts = {
                '寺庙': '背景是庄严神圣的寺庙建筑，金碧辉煌的佛殿和古典的中式建筑风格',
                '博物馆': '背景是现代化的博物馆建筑，展现文化艺术的氛围',
                '公园': '背景是美丽的自然公园景观，绿树成荫，花草繁茂',
                '古迹': '背景是历史悠久的古代建筑遗迹，展现深厚的历史文化底蕴',
                '山峰': '背景是雄伟壮观的山峰景色，云雾缭绕，气势磅礴',
                '海滩': '背景是碧海蓝天的海滩风光，白沙细软，海浪轻拍',
                '城市地标': '背景是标志性的城市建筑，现代化的都市风光',
                '自然景观': '背景是壮美的自然风光，山川河流，景色宜人',
                '文化景点': '背景是具有文化特色的建筑和环境，体现当地文化特色',
                '购物': '背景是繁华的商业街区或购物中心',
                '娱乐': '背景是充满活力的娱乐场所'
            }
            
            for key, desc in category_prompts.items():
                if key in category:
                    prompt += f"{desc}，"
                    break
        
        # 根据描述添加具体细节
        if description:
            keywords = {
                '古老': '古朴典雅的建筑风格',
                '现代': '现代化的建筑设计',
                '宏伟': '气势恢宏的建筑规模',
                '精美': '精美细致的装饰细节',
                '壮观': '令人震撼的壮观景象',
                '美丽': '风景如画的美丽环境',
                '历史': '深厚的历史文化氛围',
                '神圣': '庄严神圣的宗教氛围',
                '自然': '原生态的自然环境',
                '繁华': '繁华热闹的都市景象'
            }
            
            for keyword, enhancement in keywords.items():
                if keyword in description:
                    prompt += f"{enhancement}，"
                    break
        
        # 添加位置信息
        if location:
            prompt += f"位于{location}，"
        
        # 添加通用的合影要求 - 使用更明确的图片编辑指令
        prompt += "将图中的人物背景替换为该景点，人物穿着适合旅游的休闲装，自然地微笑，天气晴朗。保持人脸的原貌和特征不变，只改变服装和背景。原图中只有人物需要保留，其他背景物品都不要保留。整体画面和谐自然，具有真实的旅游合影效果。"
        
        return prompt
    
    async def generate_attraction_photo(
        self, 
        user_photo: UploadFile,
        attraction_name: str,
        style_photo: Optional[UploadFile] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        opening_hours: Optional[str] = None,
        ticket_price: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        custom_prompt: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        生成景点合影照片
        
        Args:
            user_photo: 用户上传的照片
            attraction_name: 景点名称
            style_photo: 范例风格图片（可选）
            location: 景点位置
            category: 景点类别
            description: 景点描述
            opening_hours: 开放时间
            ticket_price: 门票价格
            latitude: 纬度
            longitude: 经度
            custom_prompt: 自定义提示词（可选）
            
        Returns:
            (成功标志, 消息, 生成的图片路径或错误信息)
        """
        try:
            # 读取用户上传的图片
            image_data = await user_photo.read()
            user_image = Image.open(BytesIO(image_data))
            
            # 将图片转换为RGB格式（如果需要）
            if user_image.mode not in ('RGB', 'RGBA'):
                user_image = user_image.convert('RGB')
            
            # 处理范例风格图片（如果有）
            style_image = None
            if style_photo:
                style_data = await style_photo.read()
                style_image = Image.open(BytesIO(style_data))
                
                # 将范例图片转换为RGB格式（如果需要）
                if style_image.mode not in ('RGB', 'RGBA'):
                    style_image = style_image.convert('RGB')
                
                logger.info(f"📎 已加载范例风格图片: {style_photo.filename}")
            
            # 生成提示词
            if custom_prompt:
                prompt = custom_prompt
            elif style_image:
                # 如果有范例风格图片，使用风格迁移提示词
                prompt = f"Create a beautiful composite image: Take the person from the first image and dress them in the outfit style from the second image, placing them at {attraction_name}. The person should be wearing similar clothing as shown in image 2, with natural lighting and realistic shadows. Make the scene look like a genuine tourist photo at {attraction_name}."
                logger.info(f"🎨 使用风格迁移提示词: {prompt}")
            else:
                prompt = self.generate_attraction_prompt(
                    attraction_name=attraction_name,
                    location=location,
                    category=category,
                    description=description,
                    opening_hours=opening_hours,
                    ticket_price=ticket_price,
                    latitude=latitude,
                    longitude=longitude
                )
            
            logger.info(f"生成景点合影 - 景点: {attraction_name}, 提示词: {prompt}")
            
            # 调用 Gemini API 生成图片
            if style_image:
                # 如果有范例风格图片，按照指定顺序传递图片
                contents = [prompt, user_image, style_image]
                logger.info(f"🚀 开始调用Gemini API生成图片（包含范例风格图片）...")
                logger.info(f"📝 输入内容: 提示词 + 用户图片 + 风格图片")
            else:
                contents = [prompt, user_image]
                logger.info(f"🚀 开始调用Gemini API生成图片...")
                logger.info(f"📝 输入内容: 提示词 + 用户图片")
            
            # 生成图像
            response = self.model.generate_content(contents)
            logger.info(f"✅ Gemini API调用完成")
            
            # 处理响应
            response_dict = response.to_dict()
            logger.info(f"📋 Gemini API响应结构: {list(response_dict.keys())}")
            
            if "candidates" in response_dict and len(response_dict["candidates"]) > 0:
                parts = response_dict["candidates"][0]["content"]["parts"]
                
                for part in parts:
                    if "inline_data" in part:
                        # 解码base64图像数据
                        image_data = base64.b64decode(part["inline_data"]["data"])
                        
                        # 使用PIL保存图像
                        generated_image = Image.open(BytesIO(image_data))
                        
                        # 生成带时间戳的文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_attraction_name = "".join(c for c in attraction_name if c.isalnum() or c in ('_', '-'))[:30]
                        filename = f"attraction_{safe_attraction_name}_{timestamp}.png"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        # 保存图片
                        generated_image.save(filepath)
                        logger.info(f"✅ 景点合影已生成: {filepath}")
                        
                        # 同时返回base64编码的图片数据，方便前端直接显示
                        buffered = BytesIO()
                        generated_image.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        return True, "景点合影生成成功", {
                            "filepath": filepath,
                            "filename": filename,
                            "image_url": f"data:image/png;base64,{img_base64}",
                            "base64": f"data:image/png;base64,{img_base64}",
                            "attraction": attraction_name,
                            "prompt": prompt
                        }
            
            logger.warning("⚠️ API响应中未找到图片数据")
            if "candidates" in response_dict:
                logger.info(f"📊 候选响应数量: {len(response_dict['candidates'])}")
                if len(response_dict["candidates"]) > 0:
                    candidate = response_dict["candidates"][0]
                    logger.info(f"🔍 候选响应内容: {candidate}")
            return False, "生成失败：API未返回图片数据", None
            
        except Exception as e:
            error_msg = f"生成景点合影时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(f"🔥 详细错误信息: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"📍 错误堆栈: {traceback.format_exc()}")
            return False, error_msg, None
    
    def get_generated_images(self, limit: int = 10) -> list:
        """
        获取最近生成的图片列表
        
        Args:
            limit: 返回的图片数量限制
            
        Returns:
            图片信息列表
        """
        try:
            images = []
            if os.path.exists(self.output_dir):
                files = os.listdir(self.output_dir)
                image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
                
                # 按修改时间排序
                image_files.sort(
                    key=lambda x: os.path.getmtime(os.path.join(self.output_dir, x)),
                    reverse=True
                )
                
                for filename in image_files[:limit]:
                    filepath = os.path.join(self.output_dir, filename)
                    images.append({
                        "filename": filename,
                        "filepath": filepath,
                        "created_at": datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).isoformat()
                    })
            
            return images
            
        except Exception as e:
            logger.error(f"获取生成的图片列表时出错: {str(e)}")
            return []

# 创建全局服务实例
gemini_service = GeminiImageService()
