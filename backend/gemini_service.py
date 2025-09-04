import os
import base64
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from datetime import datetime
import logging
from typing import Optional, Tuple, Dict
import tempfile
from fastapi import UploadFile
import json
import time
import asyncio
from google.api_core import exceptions as google_exceptions
from prompt_generator import doro_prompt_generator
from google import genai as genai_client

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 配置 Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is not set")
    raise ValueError("GEMINI_API_KEY environment variable is required")
genai.configure(api_key=GEMINI_API_KEY)

class GeminiImageService:
    """Google Gemini 图片生成服务"""
    
    def __init__(self):
        # 使用支持图片生成的模型 (Nano Banana)
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        self.output_dir = "backend/generated_images"
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        self.backoff_factor = 2  # 指数退避因子
        
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
    
    def _validate_image(self, image: Image.Image) -> bool:
        """
        验证图片是否符合要求
        
        Args:
            image: PIL图片对象
            
        Returns:
            是否通过验证
        """
        try:
            # 检查图片尺寸
            width, height = image.size
            if width < 50 or height < 50:
                logger.error(f"图片尺寸过小: {width}x{height}")
                return False
            
            if width > 4096 or height > 4096:
                logger.error(f"图片尺寸过大: {width}x{height}")
                return False
            
            # 检查图片模式
            if image.mode not in ['RGB', 'RGBA']:
                logger.warning(f"图片模式不是RGB/RGBA: {image.mode}，尝试转换")
                image = image.convert('RGB')
            
            return True
            
        except Exception as e:
            logger.error(f"图片验证失败: {e}")
            return False
    
    def _preprocess_image(self, image: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        预处理图片，确保符合API要求
        
        Args:
            image: PIL图片对象
            max_size: 最大尺寸（像素）
            
        Returns:
            处理后的图片
        """
        # 转换为RGB格式
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # 调整图片大小
        width, height = image.size
        if max(width, height) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"📏 图片已调整大小: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    async def _call_gemini_with_retry(self, contents, attempt=1):
        """
        带重试机制的Gemini API调用
        
        Args:
            contents: 要发送给API的内容
            attempt: 当前尝试次数
            
        Returns:
            API响应
        """
        try:
            logger.info(f"🚀 第{attempt}次尝试调用Gemini API...")
            response = self.model.generate_content(contents)
            logger.info(f"✅ Gemini API调用成功 (第{attempt}次尝试)")
            return response
            
        except google_exceptions.InternalServerError as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini API内部服务器错误 (第{attempt}次尝试): {error_msg}")
            
            # 检查是否是内容安全问题
            if "safety" in error_msg.lower() or "policy" in error_msg.lower():
                logger.error("🚫 内容可能违反了Gemini的安全政策")
                raise Exception("图片内容可能包含不适当的内容，请尝试其他图片")
            
            if attempt < self.max_retries:
                delay = self.retry_delay * (self.backoff_factor ** (attempt - 1))
                logger.info(f"⏳ 等待{delay}秒后重试...")
                await asyncio.sleep(delay)
                return await self._call_gemini_with_retry(contents, attempt + 1)
            else:
                # 在最后一次失败时，提供更友好的错误信息
                if "500 Internal error encountered" in error_msg:
                    raise Exception("Gemini服务暂时不可用，请稍后重试。这通常是临时性问题。")
                raise e
                
        except google_exceptions.ResourceExhausted as e:
            logger.error(f"❌ Gemini API配额耗尽 (第{attempt}次尝试): {e}")
            if attempt < self.max_retries:
                delay = self.retry_delay * (self.backoff_factor ** (attempt - 1)) * 2  # 配额问题等待更久
                logger.info(f"⏳ 配额耗尽，等待{delay}秒后重试...")
                await asyncio.sleep(delay)
                return await self._call_gemini_with_retry(contents, attempt + 1)
            else:
                raise e
                
        except google_exceptions.InvalidArgument as e:
            logger.error(f"❌ Gemini API参数错误 (第{attempt}次尝试): {e}")
            # 参数错误不需要重试
            raise e
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Gemini API未知错误 (第{attempt}次尝试): {type(e).__name__}: {e}")
            
            # 检查是否是地理位置限制错误
            if "User location is not supported" in error_message or "not supported for the API use" in error_message:
                logger.error("❌ Gemini API在当前地理位置不可用")
                raise ValueError("Gemini API在当前地理位置不可用，请使用VPN或联系管理员")
            
            # 检查是否是内容安全问题
            if "SAFETY" in error_message or "BLOCKED" in error_message or "safety" in error_message.lower():
                logger.error("🚫 内容被安全过滤器拦截")
                raise Exception("图片内容可能不符合安全要求，请尝试其他图片")
            
            # 检查是否是图片格式问题
            if "image" in error_message.lower() and ("format" in error_message.lower() or "invalid" in error_message.lower()):
                logger.error("🖼️ 图片格式问题")
                raise Exception("图片格式不支持，请使用JPG、PNG或WEBP格式")
            
            if attempt < self.max_retries:
                delay = self.retry_delay * (self.backoff_factor ** (attempt - 1))
                logger.info(f"⏳ 等待{delay}秒后重试...")
                await asyncio.sleep(delay)
                return await self._call_gemini_with_retry(contents, attempt + 1)
            else:
                # 提供更友好的最终错误信息
                if "500" in error_message:
                    raise Exception("AI服务暂时不可用，请稍后重试")
                elif "timeout" in error_message.lower():
                    raise Exception("请求超时，请检查网络连接后重试")
                else:
                    raise Exception(f"生成失败，请稍后重试")
    
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
            
            # 预处理用户图片
            user_image = self._preprocess_image(user_image)
            
            # 处理范例风格图片（如果有）
            style_image = None
            if style_photo:
                style_data = await style_photo.read()
                style_image = Image.open(BytesIO(style_data))
                
                # 预处理范例图片
                style_image = self._preprocess_image(style_image)
                
                logger.info(f"📎 已加载范例风格图片: {style_photo.filename}")
            
            # 生成基础提示词
            if style_image:
                # 如果有范例风格图片，使用风格迁移提示词
                base_prompt = f"请创建一张合成图片：以第一张图片中的人物为主体，保留他的面部特征和头像，但将他的服装（包括衣服和裤子）替换成第二张图片中指定人物的服装风格。背景设置为{attraction_name}。"
                logger.info(f"🎨 使用风格迁移提示词作为基础")
            else:
                base_prompt = self.generate_attraction_prompt(
                    attraction_name=attraction_name,
                    location=location,
                    category=category,
                    description=description,
                    opening_hours=opening_hours,
                    ticket_price=ticket_price,
                    latitude=latitude,
                    longitude=longitude
                )
            
            # 如果有自定义提示词，追加到基础提示词后面
            if custom_prompt and custom_prompt.strip():
                prompt = f"{base_prompt} 额外要求：{custom_prompt.strip()}"
                logger.info(f"📝 追加自定义提示词: {custom_prompt.strip()}")
            else:
                prompt = base_prompt
            
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
            
            # 生成图像 - 使用重试机制
            response = await self._call_gemini_with_retry(contents)
            
            # 处理响应
            response_dict = response.to_dict()
            logger.info(f"📋 Gemini API响应结构: {list(response_dict.keys())}")
            
            if "candidates" in response_dict and len(response_dict["candidates"]) > 0:
                parts = response_dict["candidates"][0]["content"]["parts"]
                
                for part in parts:
                    if "inline_data" in part:
                        try:
                            # 获取图像数据
                            raw_data = part["inline_data"]["data"]
                            
                            # 检查数据类型并相应处理
                            if isinstance(raw_data, str):
                                # 如果是字符串，进行base64解码
                                logger.info("📦 景点图片数据是base64字符串，进行解码...")
                                image_data = base64.b64decode(raw_data)
                            elif isinstance(raw_data, bytes):
                                # 如果已经是字节数据，直接使用
                                logger.info("📦 景点图片数据已经是字节格式，直接使用...")
                                image_data = raw_data
                            else:
                                logger.error(f"❌ 未知的景点图片数据类型: {type(raw_data)}")
                                continue
                            
                            # 创建BytesIO对象并重置指针
                            image_buffer = BytesIO(image_data)
                            image_buffer.seek(0)  # 重置指针到开始位置
                            
                            # 使用PIL打开图像
                            generated_image = Image.open(image_buffer)
                            logger.info(f"✅ 成功从响应中提取景点合影图片: {generated_image.size}")
                        except Exception as e:
                            logger.error(f"❌ 提取景点合影图片失败: {e}")
                            logger.error(f"   数据类型: {type(raw_data) if 'raw_data' in locals() else 'unknown'}")
                            continue
                        
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
                        buffered.seek(0)  # 重置指针到开始位置
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        buffered.close()  # 关闭BytesIO对象
                        
                        return True, "景点合影生成成功", {
                            "filepath": filepath,
                            "filename": filename,
                            "image_url": f"data:image/png;base64,{img_base64}",
                            "base64": f"data:image/png;base64,{img_base64}",
                            "attraction": attraction_name,
                            "prompt": prompt
                        }
            
            logger.warning("⚠️ API响应中未找到图片数据")
            
            # 提取AI的文本响应，提供给用户参考
            ai_response = ""
            if "candidates" in response_dict:
                logger.info(f"📊 候选响应数量: {len(response_dict['candidates'])}")
                if len(response_dict["candidates"]) > 0:
                    candidate = response_dict["candidates"][0]
                    logger.info(f"🔍 候选响应内容: {candidate}")
                    
                    # 提取AI的文本回复
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                ai_response = part["text"]
                                break
            
            # 构建详细的错误信息
            error_details = {
                "type": "ai_feedback",
                "message": "AI无法生成图片，返回了文本说明",
                "ai_response": ai_response,
                "suggestion": "请尝试修改提示词，使用更简单明确的描述，或者更换参考图片",
                "prompt_used": prompt
            }
            
            return False, "生成失败：AI返回了文本说明而非图片", error_details
            
        except google_exceptions.InternalServerError as e:
            error_msg = "Gemini服务暂时不可用，请稍后重试"
            logger.error(f"🔥 Gemini内部服务器错误: {e}")
            return False, error_msg, {
                "type": "service_unavailable",
                "message": "AI图像生成服务暂时不可用",
                "suggestion": "请稍等几分钟后重试，或者尝试使用不同的图片",
                "error_code": "GEMINI_500"
            }
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = "API使用配额已耗尽，请稍后重试"
            logger.error(f"🔥 Gemini配额耗尽: {e}")
            return False, error_msg, {
                "type": "quota_exceeded",
                "message": "今日AI图像生成次数已达上限",
                "suggestion": "请明天再试，或者联系管理员增加配额",
                "error_code": "GEMINI_QUOTA"
            }
            
        except google_exceptions.InvalidArgument as e:
            error_msg = "图片内容不符合要求，请更换图片"
            logger.error(f"🔥 Gemini参数错误: {e}")
            return False, error_msg, {
                "type": "invalid_content",
                "message": "上传的图片可能包含不适当的内容",
                "suggestion": "请确保图片清晰、内容健康，并重新上传",
                "error_code": "GEMINI_INVALID"
            }
            
        except Exception as e:
            error_msg = f"生成景点合影时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(f"🔥 详细错误信息: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"📍 错误堆栈: {traceback.format_exc()}")
            
            # 根据错误类型提供更友好的错误信息
            if "500" in str(e) or "Internal" in str(e):
                return False, "AI服务暂时不可用，请稍后重试", {
                    "type": "service_error",
                    "message": "图像生成服务遇到临时问题",
                    "suggestion": "请稍等几分钟后重试",
                    "error_code": "SERVICE_ERROR"
                }
            elif "timeout" in str(e).lower():
                return False, "请求超时，请重试", {
                    "type": "timeout",
                    "message": "图像生成请求超时",
                    "suggestion": "请检查网络连接并重试",
                    "error_code": "TIMEOUT"
                }
            else:
                return False, error_msg, {
                    "type": "unknown_error",
                    "message": "发生未知错误",
                    "suggestion": "请重试或联系技术支持",
                    "error_code": "UNKNOWN"
                }
    
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
    
    async def generate_doro_selfie_with_attraction(
        self,
        user_photo: UploadFile,
        doro_photo: UploadFile,
        style_photo: Optional[UploadFile],
        attraction_info: Dict
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        生成包含景点背景的Doro合影
        
        Args:
            user_photo: 用户照片
            doro_photo: Doro形象
            style_photo: 服装参考（可选）
            attraction_info: 景点信息（名称、位置、类型等）
            
        Returns:
            (成功标志, 消息, 结果数据)
        """
        try:
            logger.info(f"开始生成Doro合影: 景点={attraction_info.get('name', 'Unknown')}")
            
            # 读取用户照片
            try:
                user_photo.file.seek(0)  # 确保文件指针在开始位置
                user_image = Image.open(user_photo.file)
                if user_image.mode != 'RGB':
                    user_image = user_image.convert('RGB')
                logger.info(f"✅ 用户照片加载成功: {user_image.size}, 模式: {user_image.mode}")
                
                # 验证用户照片
                if not self._validate_image(user_image):
                    return False, "用户照片不符合要求，请使用清晰的JPG或PNG格式图片", None
            except Exception as e:
                logger.error(f"❌ 用户照片加载失败: {e}")
                return False, f"用户照片加载失败: {str(e)}", None
            
            # 读取Doro图片
            try:
                doro_photo.file.seek(0)  # 确保文件指针在开始位置
                doro_image = Image.open(doro_photo.file)
                if doro_image.mode != 'RGB':
                    doro_image = doro_image.convert('RGB')
                logger.info(f"✅ Doro图片加载成功: {doro_image.size}, 模式: {doro_image.mode}")
                
                # 验证Doro图片
                if not self._validate_image(doro_image):
                    return False, "Doro图片不符合要求，请联系管理员", None
            except Exception as e:
                logger.error(f"❌ Doro图片加载失败: {e}")
                return False, f"Doro图片加载失败: {str(e)}", None
            
            # 读取服装风格图片（如果提供）
            style_image = None
            if style_photo:
                try:
                    style_photo.file.seek(0)  # 确保文件指针在开始位置
                    style_image = Image.open(style_photo.file)
                    if style_image.mode != 'RGB':
                        style_image = style_image.convert('RGB')
                    logger.info(f"✅ 风格图片加载成功: {style_image.size}, 模式: {style_image.mode}")
                    
                    # 验证风格图片
                    if not self._validate_image(style_image):
                        logger.warning("⚠️ 风格图片不符合要求，将跳过")
                        style_image = None
                except Exception as e:
                    logger.warning(f"⚠️ 风格图片加载失败，将跳过: {e}")
                    style_image = None
            
            # 生成智能提示词
            main_prompt = doro_prompt_generator.generate_attraction_doro_prompt(
                attraction_name=attraction_info.get("name"),
                attraction_type=attraction_info.get("category"),
                location=attraction_info.get("location", attraction_info.get("city", attraction_info.get("country"))),
                with_style=style_photo is not None,
                doro_style=attraction_info.get("doro_style", "default"),
                user_description=attraction_info.get("user_description")
            )
            
            # 如果有服装风格，添加风格迁移提示
            if style_photo:
                style_prompt = doro_prompt_generator.generate_style_transfer_prompt()
                main_prompt = f"{main_prompt}. {style_prompt}"
            
            # 增强提示词（根据额外参数）
            main_prompt = doro_prompt_generator.enhance_prompt_with_details(
                main_prompt,
                time_of_day=attraction_info.get("time_of_day"),
                weather=attraction_info.get("weather"),
                season=attraction_info.get("season"),
                mood=attraction_info.get("mood")
            )
            
            # 构建内容列表
            contents = [main_prompt]
            
            # 添加图片
            contents.append(user_image)
            contents.append(doro_image)
            if style_image:
                contents.append(style_image)
            
            # 添加负面提示词
            negative_prompt = doro_prompt_generator.get_negative_prompt()
            contents.append(f"Avoid: {negative_prompt}")
            
            logger.info(f"使用提示词: {main_prompt[:200]}...")
            
            # 调用Gemini API生成图片
            response = await self._call_gemini_with_retry(contents)
            
            # 提取生成的图片
            generated_image = None
            
            # 方法1: 直接从response.parts提取
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # 检查是否有mime_type且是图片
                    if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type and part.inline_data.mime_type.startswith('image/'):
                        try:
                            image_data = part.inline_data.data
                            
                            # 检查数据类型并相应处理
                            if isinstance(image_data, str):
                                # 如果是字符串，假设是base64编码
                                logger.info("📦 图片数据是base64字符串，进行解码...")
                                decoded_data = base64.b64decode(image_data)
                            elif isinstance(image_data, bytes):
                                # 如果已经是字节数据，直接使用
                                logger.info("📦 图片数据已经是字节格式，直接使用...")
                                decoded_data = image_data
                            else:
                                logger.error(f"❌ 未知的图片数据类型: {type(image_data)}")
                                continue
                            
                            # 创建BytesIO对象并重置指针
                            image_buffer = BytesIO(decoded_data)
                            image_buffer.seek(0)  # 重置指针到开始位置
                            generated_image = Image.open(image_buffer)
                            logger.info(f"✅ 成功从Gemini响应中提取图片: {generated_image.size}")
                            break  # 找到图片就退出循环
                        except Exception as e:
                            logger.error(f"❌ 从响应中提取图片失败: {e}")
                            logger.error(f"   数据类型: {type(image_data) if 'image_data' in locals() else 'unknown'}")
                            continue
            
            if not generated_image:
                # 方法2: 使用to_dict()方法提取
                try:
                    logger.info("📦 尝试使用to_dict()方法提取图片...")
                    response_dict = response.to_dict()
                    if 'candidates' in response_dict and response_dict['candidates']:
                        parts = response_dict['candidates'][0].get('content', {}).get('parts', [])
                        for part in parts:
                            if 'inline_data' in part:
                                inline_data = part['inline_data']
                                if 'data' in inline_data and inline_data.get('mime_type', '').startswith('image/'):
                                    try:
                                        # to_dict()返回的data通常是base64字符串
                                        image_data = inline_data['data']
                                        if isinstance(image_data, str):
                                            logger.info("📦 to_dict()返回base64字符串，进行解码...")
                                            decoded_data = base64.b64decode(image_data)
                                        else:
                                            decoded_data = image_data
                                        
                                        image_buffer = BytesIO(decoded_data)
                                        image_buffer.seek(0)
                                        generated_image = Image.open(image_buffer)
                                        logger.info(f"✅ 使用to_dict()成功提取图片: {generated_image.size}")
                                        break
                                    except Exception as e:
                                        logger.error(f"❌ to_dict()方法提取失败: {e}")
                                        continue
                except Exception as e:
                    logger.error(f"❌ to_dict()方法失败: {e}")
            
            if not generated_image:
                # 方法3: 尝试从文本中提取data URL
                try:
                    response_text = response.text if hasattr(response, 'text') else None
                    if response_text and 'data:image' in response_text:
                        # 提取base64图片数据
                        start = response_text.find('data:image')
                        end = response_text.find('"', start)
                        if start != -1 and end != -1:
                            image_data_url = response_text[start:end]
                            # 解析data URL
                            header, data = image_data_url.split(',', 1)
                            # 创建BytesIO对象并重置指针
                            image_buffer = BytesIO(base64.b64decode(data))
                            image_buffer.seek(0)  # 重置指针到开始位置
                            generated_image = Image.open(image_buffer)
                            logger.info(f"✅ 从文本响应中成功提取图片")
                except Exception as e:
                    logger.error(f"❌ 从文本响应中提取图片失败: {e}")
            
            if generated_image:
                # 保存生成的图片
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = "".join(c for c in attraction_info.get('name', 'unknown') if c.isalnum() or c in ('_', '-'))[:30]
                filename = f"doro_selfie_{safe_name}_{timestamp}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                try:
                    generated_image.save(filepath, 'PNG')
                    logger.info(f"Doro合影已保存: {filename}")
                    
                    # 转换为base64 - 修复BytesIO指针问题
                    buffered = BytesIO()
                    generated_image.save(buffered, format="PNG")
                    buffered.seek(0)  # 重置指针到开始位置
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()
                    buffered.close()  # 关闭BytesIO对象
                except Exception as save_error:
                    logger.error(f"保存图片时出错: {save_error}")
                    return False, f"保存图片失败: {str(save_error)}", None
                
                return True, "Doro合影生成成功！", {
                    "image_url": f"data:image/png;base64,{img_base64}",
                    "filename": filename,
                    "filepath": filepath,
                    "prompt_used": main_prompt,
                    "attraction_name": attraction_info.get("name"),
                    "timestamp": timestamp
                }
            else:
                logger.warning("Gemini响应中没有找到生成的图片")
                return False, "生成失败：响应中没有图片", None
                
        except google_exceptions.ResourceExhausted:
            logger.error("Gemini API配额已耗尽")
            return False, "API配额已耗尽，请稍后再试", None
            
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Gemini API参数错误: {str(e)}")
            return False, f"参数错误: {str(e)}", None
            
        except Exception as e:
            logger.error(f"生成Doro合影时出错: {str(e)}")
            return False, f"生成失败: {str(e)}", None
    
    async def generate_doro_video_with_attraction(
        self,
        user_photo: UploadFile,
        doro_photo: UploadFile,
        style_photo: Optional[UploadFile],
        attraction_info: Dict
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        生成包含景点背景的Doro合影视频
        
        使用两步法：
        1. 先用当前的图片生成功能创建静态合影
        2. 再用Veo 3将静态图片转换为动态视频
        
        Args:
            user_photo: 用户照片
            doro_photo: Doro形象
            style_photo: 服装参考（可选）
            attraction_info: 景点信息
            
        Returns:
            (成功标志, 消息, 结果数据)
        """
        try:
            logger.info(f"开始生成Doro合影视频: 景点={attraction_info.get('name', 'Unknown')}")
            
            # 使用新的google.genai客户端
            client = genai_client.Client()
            
            # 第一步：使用Imagen 3生成静态合影图片
            logger.info("🎨 第一步：使用Imagen 3生成静态合影图片...")
            
            # 生成图片提示词
            image_prompt = await self._generate_image_prompt_for_video(
                user_photo=user_photo,
                doro_photo=doro_photo,
                attraction_info=attraction_info,
                style_photo=style_photo
            )
            logger.info(f"📝 图片提示词: {image_prompt[:200]}...")
            
            try:
                # 使用Imagen 3生成图片
                imagen_response = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=image_prompt,
                )
                
                if not imagen_response.generated_images:
                    return False, "Imagen未能生成图片", None
                    
                # 获取生成的图片
                generated_image = imagen_response.generated_images[0].image
                logger.info(f"✅ 静态图片生成成功")
                
            except Exception as e:
                logger.error(f"❌ Imagen生成失败: {e}")
                # 如果Imagen失败，尝试使用原有方法作为后备
                logger.info("📸 尝试使用备用方法生成图片...")
                success, message, image_result = await self.generate_doro_selfie_with_attraction(
                    user_photo=user_photo,
                    doro_photo=doro_photo,
                    style_photo=style_photo,
                    attraction_info=attraction_info
                )
                
                if not success:
                    return False, f"图片生成失败: {message}", None
                
                # 从base64数据创建图片对象
                image_base64 = image_result['image_url'].split(',')[1]
                image_data = base64.b64decode(image_base64)
                static_image = Image.open(BytesIO(image_data))
                
                # 将PIL图片转换为API格式
                buffered = BytesIO()
                static_image.save(buffered, format="PNG")
                buffered.seek(0)
                image_bytes = buffered.getvalue()
                buffered.close()
                
                # 创建一个模拟的图片对象
                class ImageWrapper:
                    def __init__(self, data):
                        self.data = data
                        
                generated_image = ImageWrapper(image_bytes)
            
            # 第二步：使用Veo 3生成视频
            logger.info("🎬 第二步：使用Veo 3生成动态视频...")
            
            # 生成视频提示词
            video_prompt = self._generate_video_prompt(attraction_info, (1024, 1024))
            logger.info(f"🎬 视频提示词: {video_prompt[:200]}...")
            
            # 调用Veo 3生成视频，使用Imagen生成的图片
            operation = client.models.generate_videos(
                model="veo-3.0-generate-preview",
                prompt=video_prompt,
                image=generated_image,  # 直接使用Imagen生成的图片对象
            )
            
            logger.info(f"🎬 视频生成作业已启动: {operation.name}")
            
            # 使用 GenerateVideosOperation 来跟踪操作
            from google.genai import types
            video_operation = types.GenerateVideosOperation(name=operation.name)
            
            logger.info("🕐 等待视频生成完成...")
            
            # 轮询操作状态
            max_wait_time = 600  # 最多等待10分钟
            check_interval = 10  # 每10秒检查一次
            waited_time = 0
            
            while not video_operation.done and waited_time < max_wait_time:
                logger.info(f"⏳ 视频生成中... 已等待 {waited_time}秒")
                await asyncio.sleep(check_interval)
                # 刷新操作对象以获取最新状态
                video_operation = client.operations.get(video_operation)
                waited_time += check_interval
                
                # 检查是否有错误
                if hasattr(video_operation, 'error') and video_operation.error:
                    logger.error(f"❌ 视频生成失败: {video_operation.error}")
                    return False, f"视频生成失败: {video_operation.error}", None
            
            if not video_operation.done:
                logger.error("❌ 视频生成超时")
                return False, "视频生成超时，请稍后重试", None
            
            # 确保响应存在
            if not hasattr(video_operation, 'response') or not video_operation.response:
                logger.error("❌ 视频生成完成但没有响应")
                return False, "视频生成失败：没有生成结果", None
            
            # 获取生成的视频
            if not video_operation.response.generated_videos:
                logger.error("❌ 没有生成视频")
                return False, "视频生成失败：没有视频输出", None
                
            generated_video = video_operation.response.generated_videos[0]
            
            # 保存视频文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in attraction_info.get('name', 'unknown') if c.isalnum() or c in ('_', '-'))[:30]
            video_filename = f"doro_video_{safe_name}_{timestamp}.mp4"
            video_filepath = os.path.join(self.output_dir, video_filename)
            
            # 下载并保存视频
            try:
                client.files.download(file=generated_video.video)
                generated_video.video.save(video_filepath)
            except Exception as e:
                logger.error(f"❌ 视频下载失败: {e}")
                # 尝试直接保存视频数据
                if hasattr(generated_video, 'video_data'):
                    with open(video_filepath, 'wb') as f:
                        f.write(generated_video.video_data)
                else:
                    return False, f"视频下载失败: {e}", None
            
            logger.info(f"✅ Doro合影视频生成成功: {video_filename}")
            
            # 读取视频文件并转换为base64（用于前端显示）
            with open(video_filepath, 'rb') as f:
                video_data = f.read()
            video_base64 = base64.b64encode(video_data).decode()
            
            return True, "Doro合影视频生成成功！", {
                "video_url": f"data:video/mp4;base64,{video_base64}",
                "filename": video_filename,
                "filepath": video_filepath,
                "static_image_url": image_result['image_url'],  # 也返回静态图片
                "prompt_used": video_prompt,
                "attraction_name": attraction_info.get("name"),
                "timestamp": timestamp,
                "generation_time": waited_time
            }
            
        except Exception as e:
            logger.error(f"生成Doro合影视频时出错: {str(e)}")
            return False, f"视频生成失败: {str(e)}", None
    
    async def _generate_image_prompt_for_video(
        self, 
        user_photo: UploadFile,
        doro_photo: UploadFile,
        attraction_info: Dict,
        style_photo: Optional[UploadFile] = None
    ) -> str:
        """
        为视频生成创建图片提示词
        
        Args:
            user_photo: 用户照片
            doro_photo: Doro形象
            attraction_info: 景点信息
            style_photo: 风格参考（可选）
            
        Returns:
            图片生成提示词
        """
        # 基础提示词
        prompt = f"Create a high-quality travel photo showing a real person and their charming animated character companion Doro at the famous {attraction_info.get('name', 'landmark')} in {attraction_info.get('address', 'location')}"
        
        # 添加景点描述
        if attraction_info.get('description'):
            prompt += f", {attraction_info['description']}"
        
        # 添加姿势和互动
        poses = [
            "taking a selfie together",
            "posing happily",
            "giving thumbs up",
            "making peace signs",
            "smiling at the camera"
        ]
        import random
        pose = random.choice(poses)
        prompt += f". They are {pose}"
        
        # 添加服装描述
        if style_photo:
            prompt += ", wearing stylish travel outfits"
        else:
            prompt += ", wearing casual travel attire"
        
        # 添加环境和光线描述
        time_descriptions = {
            "morning": "with soft morning light",
            "afternoon": "under bright afternoon sun",
            "evening": "during golden hour with warm sunset light",
            "night": "with beautiful night lights"
        }
        
        time_of_day = attraction_info.get('time_of_day', 'afternoon')
        prompt += f", {time_descriptions.get(time_of_day, 'with natural lighting')}"
        
        # 添加质量要求
        prompt += ". Professional photography, high resolution, vibrant colors, perfect composition, travel photography style"
        
        return prompt
    
    def _generate_video_prompt(self, attraction_info: Dict, image_size: tuple) -> str:
        """
        生成视频提示词
        
        Args:
            attraction_info: 景点信息
            image_size: 图片尺寸
            
        Returns:
            视频生成提示词
        """
        attraction_name = attraction_info.get('name', '景点')
        location = attraction_info.get('location', '')
        
        # 基础视频提示词
        base_prompt = f"""Create a cinematic travel video showing a person and their animated companion Doro at {attraction_name}"""
        
        if location:
            base_prompt += f" in {location}"
        
        # 添加视频效果描述
        video_effects = [
            "The camera slowly pans around them as they pose together",
            "Gentle breeze moves their hair and clothes naturally",
            "The landmark background is clearly visible and majestic",
            "Warm, golden hour lighting creates a beautiful atmosphere",
            "The person and Doro are smiling and enjoying the moment",
            "Subtle camera movement adds cinematic quality",
            "The scene feels authentic and joyful"
        ]
        
        base_prompt += ". " + ". ".join(video_effects)
        
        # 添加技术要求
        base_prompt += ". High-quality 8-second video with realistic motion and natural lighting."
        
        return base_prompt
    
    async def health_check(self) -> dict:
        """
        检查Gemini服务健康状态
        
        Returns:
            服务状态信息
        """
        try:
            # 创建一个简单的测试图片
            test_image = Image.new('RGB', (100, 100), color='blue')
            
            # 尝试调用API进行简单的图片描述
            simple_prompt = "请简单描述这张图片的颜色。"
            contents = [simple_prompt, test_image]
            
            response = await self._call_gemini_with_retry(contents)
            
            return {
                "status": "healthy",
                "message": "Gemini服务运行正常",
                "api_accessible": True,
                "model": "gemini-2.5-flash-image-preview",
                "timestamp": datetime.now().isoformat()
            }
            
        except google_exceptions.ResourceExhausted:
            return {
                "status": "quota_exceeded",
                "message": "API配额已耗尽",
                "api_accessible": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except google_exceptions.InternalServerError:
            return {
                "status": "service_unavailable",
                "message": "Gemini服务暂时不可用",
                "api_accessible": False,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"服务检查失败: {str(e)}",
                "api_accessible": False,
                "timestamp": datetime.now().isoformat()
            }

# 创建全局服务实例
gemini_service = GeminiImageService()
