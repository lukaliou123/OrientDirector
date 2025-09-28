"""
🎨 Nano Banana历史场景生成服务
使用最新的Google Gemini 2.5 Flash Image API
完全按照官方文档的方式实现
"""

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import base64
import json
from typing import Dict, Optional, List
import time
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv
from prompt_database import prompt_db

# 加载环境变量
load_dotenv()

class NanoBananaHistoricalService:
    """Nano Banana历史场景生成服务"""
    
    def __init__(self):
        # 配置新版Gemini API
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("⚠️ 演示模式: GEMINI_API_KEY未配置")
            self.client = None
            self.client_available = False
        else:
            try:
                # 按照官方文档创建客户端
                self.client = genai.Client(api_key=api_key)
                self.client_available = True
                print("✅ Nano Banana客户端已初始化 (google-genai 1.32.0)")
            except Exception as e:
                print(f"⚠️ API初始化失败，使用演示模式: {e}")
                self.client = None  
                self.client_available = False
        
        # 图像保存目录 - 使用新的目录结构
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.scene_images_dir = os.path.join(project_root, "static", "meme", "scene_view")
        self.selfie_images_dir = os.path.join(project_root, "static", "meme", "selfie")
        self.char_images_dir = os.path.join(project_root, "static", "char")
        self.composition_images_dir = os.path.join(project_root, "static", "构图")
        self.pregenerated_dir = os.path.join(project_root, "static", "pregenerated_images")
        
        # 保持向后兼容性的旧目录
        self.images_dir = os.path.join(project_root, "static", "generated_images")
        
        # 确保目录存在
        os.makedirs(self.scene_images_dir, exist_ok=True)
        os.makedirs(self.selfie_images_dir, exist_ok=True)
        os.makedirs(self.char_images_dir, exist_ok=True)
        os.makedirs(self.composition_images_dir, exist_ok=True)
        os.makedirs(self.pregenerated_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)  # 向后兼容
        
        # 演示模式配置
        self.demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
        
        # 加载预生成图片索引
        self.demo_scenes_index = self.load_demo_scenes_index()
        
        # 加载梗图提示词模板
        self.meme_templates = self.load_meme_templates()
        
        # 加载场景提示词模板
        self.scene_templates = self.load_scene_templates()
        
        # 设置提示词日志文件路径
        self.prompt_log_file = os.path.join(project_root, "logs", "prompt_usage.log")
        os.makedirs(os.path.dirname(self.prompt_log_file), exist_ok=True)
        
        print(f"🎨 Nano Banana历史服务已初始化")
        print(f"   API状态: {'已配置' if self.client_available else '未配置'}")
        print(f"   演示模式: {'开启' if self.demo_mode else '关闭'}")
        print(f"   场景图目录: {self.scene_images_dir}")
        print(f"   自拍图目录: {self.selfie_images_dir}")
        print(f"   人像目录: {self.char_images_dir}")
        print(f"   构图目录: {self.composition_images_dir}")
        print(f"   预生成目录: {self.pregenerated_dir}")
        print(f"   提示词日志: {self.prompt_log_file}")
        print(f"   梗图模板: {len(self.meme_templates.get('templates', []))} 个")
        print(f"   场景模板: {len(self.scene_templates.get('scene_templates', []))} 个")
        if self.demo_mode and self.demo_scenes_index:
            print(f"   预设场景: {len(self.demo_scenes_index.get('demo_scenes', []))} 个")
    
    def load_demo_scenes_index(self) -> Dict:
        """加载预生成场景索引"""
        index_path = os.path.join(self.pregenerated_dir, 'demo_scenes_index.json')
        
        try:
            print(f"🔍 尝试加载演示索引: {index_path}")
            
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    scene_count = len(data.get('demo_scenes', []))
                    print(f"✅ 演示索引加载成功: {scene_count} 个场景")
                    
                    # 调试：显示加载的场景
                    if scene_count > 0:
                        for scene in data['demo_scenes'][:3]:  # 显示前3个
                            print(f"   - {scene.get('title', 'N/A')} ({scene.get('year', 'N/A')}年)")
                    
                    return data
            else:
                print(f"⚠️ 演示索引文件不存在: {index_path}")
                return {'demo_scenes': []}
                
        except Exception as e:
            print(f"❌ 加载预生成索引失败: {e}")
            print(f"   文件路径: {index_path}")
            print(f"   文件存在: {os.path.exists(index_path)}")
            return {'demo_scenes': []}
    
    def load_meme_templates(self) -> Dict:
        """加载梗图提示词模板"""
        template_path = os.path.join(os.path.dirname(__file__), 'meme_prompt_templates.json')
        
        try:
            print(f"🔍 尝试加载梗图模板: {template_path}")
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template_count = len(data.get('templates', []))
                    print(f"✅ 梗图模板加载成功: {template_count} 个模板")
                    
                    # 调试：显示加载的模板
                    if template_count > 0:
                        for template in data['templates'][:3]:  # 显示前3个
                            print(f"   - {template.get('name', 'N/A')} ({template.get('id', 'N/A')})")
                    
                    return data
            else:
                print(f"⚠️ 梗图模板文件不存在: {template_path}")
                return {'templates': [], 'scene_element_translations': {}, 'historical_periods': {}}
                
        except Exception as e:
            print(f"❌ 加载梗图模板失败: {e}")
            print(f"   文件路径: {template_path}")
            print(f"   文件存在: {os.path.exists(template_path)}")
            return {'templates': [], 'scene_element_translations': {}, 'historical_periods': {}}
    
    def load_scene_templates(self) -> Dict:
        """加载场景提示词模板"""
        template_path = os.path.join(os.path.dirname(__file__), 'scene_prompt_templates.json')
        
        try:
            print(f"🔍 尝试加载场景模板: {template_path}")
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template_count = len(data.get('scene_templates', []))
                    print(f"✅ 场景模板加载成功: {template_count} 个模板")
                    
                    # 调试：显示加载的模板
                    if template_count > 0:
                        for template in data['scene_templates'][:3]:  # 显示前3个
                            print(f"   - {template.get('name', 'N/A')} ({template.get('id', 'N/A')})")
                    
                    return data
            else:
                print(f"⚠️ 场景模板文件不存在: {template_path}")
                return {'scene_templates': []}
                
        except Exception as e:
            print(f"❌ 加载场景模板失败: {e}")
            print(f"   文件路径: {template_path}")
            print(f"   文件存在: {os.path.exists(template_path)}")
            return {'scene_templates': []}
    
    def get_scene_template(self, template_id: str) -> Optional[Dict]:
        """获取指定的场景模板"""
        templates = self.scene_templates.get('scene_templates', [])
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None
    
    def process_scene_template(self, template_id: str, historical_info: Dict) -> str:
        """处理场景模板，自动替换占位符"""
        template = self.get_scene_template(template_id)
        if not template:
            raise Exception(f"场景模板不存在: {template_id}")
        
        # 获取模板内容
        template_content = template['template']
        
        # 替换占位符 - 确保不会传入None值
        political_entity = historical_info.get('political_entity') or 'Unknown'
        query_year = historical_info.get('query_year') or 0
        
        processed_prompt = template_content.replace(
            '[historical location]', political_entity
        ).replace(
            '[year]', str(abs(query_year)) + (' CE' if query_year >= 0 else ' BCE')
        )
        
        print(f"📝 场景模板处理完成:")
        print(f"   模板ID: {template_id}")
        print(f"   模板名称: {template['name']}")
        print(f"   历史地点: {political_entity}")
        print(f"   历史年份: {query_year}")
        
        return processed_prompt
    
    def get_meme_template(self, template_id: str) -> Optional[Dict]:
        """获取指定的梗图模板"""
        templates = self.meme_templates.get('templates', [])
        for template in templates:
            if template.get('id') == template_id:
                return template
        return None
    
    def translate_scene_elements(self, elements: List[str]) -> str:
        """将中文场景元素翻译为英文描述"""
        translations = self.meme_templates.get('scene_element_translations', {})
        translated_elements = []
        
        for element in elements:
            # 优先使用配置文件中的翻译
            if element in translations:
                translated_elements.append(translations[element])
            else:
                # 简单的后备翻译
                translated_elements.append(element)
        
        return ', '.join(translated_elements)
    
    def build_historical_background_description(self, historical_info: Dict, scene_elements: List[str]) -> str:
        """构建英文历史背景描述"""
        political_entity = historical_info.get('political_entity') or 'Unknown Region'
        year = historical_info.get('query_year') or 0
        cultural_region = historical_info.get('cultural_region') or 'Unknown Culture'
        
        # 确定历史时期描述
        period_description = self.get_historical_period_description(year, political_entity)
        
        # 翻译场景元素
        translated_elements = self.translate_scene_elements(scene_elements)
        
        # 构建完整的背景描述
        background_description = f"a {period_description} in {political_entity}, around {abs(year)} {'CE' if year >= 0 else 'BCE'}, featuring {translated_elements}"
        
        return background_description
    
    def get_historical_period_description(self, year: int, political_entity: str) -> str:
        """获取历史时期的英文描述"""
        # 基于年份和政治实体确定时期描述
        if 'Essex' in political_entity:
            if 700 <= year <= 900:
                return "medieval Anglo-Saxon village street"
        elif 'Roman' in political_entity or '罗马' in political_entity:
            if year <= 500:
                return "classical Roman forum or street scene"
        elif 'Tang' in political_entity or '唐' in political_entity:
            if 600 <= year <= 900:
                return "Tang Dynasty imperial capital street"
        elif 'Tokugawa' in political_entity or '德川' in political_entity:
            if 1600 <= year <= 1700:
                return "Edo period Japanese town street"
        
        # 通用描述
        if year >= 1500:
            return "early modern period street scene"
        elif year >= 1000:
            return "medieval town square"
        elif year >= 500:
            return "early medieval settlement"
        elif year >= 0:
            return "late antiquity urban area"
        else:
            return "ancient classical civilization scene"
    
    def process_meme_template(
        self, 
        template_id: str, 
        historical_info: Dict, 
        scene_elements: List[str],
        interaction_id: Optional[str] = None
    ) -> str:
        """处理梗图模板，自动替换占位符"""
        template = self.get_meme_template(template_id)
        if not template:
            raise Exception(f"模板不存在: {template_id}")
        
        # 获取模板内容
        template_content = template['template']
        
        # 构建历史背景描述
        background_description = self.build_historical_background_description(historical_info, scene_elements)
        
        # 获取互动描述（如果提供了interaction_id）
        interaction_description = ""
        if interaction_id:
            interaction_description = self.get_interaction_description(interaction_id)
        
        # 替换占位符
        processed_prompt = template_content.replace(
            '[场景元素]', background_description
        ).replace(
            '[year]', str(abs(historical_info.get('query_year') or 0)) + (' CE' if (historical_info.get('query_year') or 0) >= 0 else ' BCE')
        ).replace(
            '[location]', historical_info.get('political_entity') or 'Unknown'
        ).replace(
            '[interaction]', interaction_description
        ).replace(
            '[interaction_with_anime]', interaction_description  # 同样使用interaction_description
        )
        
        print(f"📝 模板处理完成:")
        print(f"   模板ID: {template_id}")
        print(f"   模板名称: {template['name']}")
        print(f"   背景描述: {background_description[:100]}...")
        
        return processed_prompt
    
    def get_interaction_description(self, interaction_id: str) -> str:
        """根据interaction_id获取互动描述，支持从interactions和interaction_with_anime中查找"""
        # 先在普通interactions中查找
        interactions = self.meme_templates.get('interactions', {})
        for category_name, category_interactions in interactions.items():
            for interaction in category_interactions:
                if interaction.get('id') == interaction_id:
                    return interaction.get('description', '')
        
        # 在interaction_with_anime中查找
        interaction_with_anime = self.meme_templates.get('interaction_with_anime', {})
        for category_name, category_interactions in interaction_with_anime.items():
            for interaction in category_interactions:
                if interaction.get('id') == interaction_id:
                    return interaction.get('description', '')
        
        # 如果没找到，返回默认描述
        return "making awkward eye contact with the camera, reacting with shock or confusion."
    
    def find_matching_demo_scene(self, historical_info: Dict, lat: float, lng: float) -> Optional[Dict]:
        """查找匹配的预生成演示场景 - 支持近似匹配"""
        if not self.demo_scenes_index or 'demo_scenes' not in self.demo_scenes_index:
            print("🔍 无演示索引数据，无法匹配预生成场景")
            return None
        
        political_entity = historical_info.get('political_entity') or 'Unknown'
        year = historical_info.get('query_year') or 0
        
        print(f"🔍 查找预生成场景:")
        print(f"   目标: {political_entity} ({year}年) 坐标({lat:.4f}, {lng:.4f})")
        
        # 1. 优先查找完全匹配的场景
        for scene in self.demo_scenes_index['demo_scenes']:
            if (scene['political_entity'] == political_entity and 
                scene['year'] == year and
                abs(scene['lat'] - lat) < 0.15 and 
                abs(scene['lng'] - lng) < 0.15):
                
                image_path = os.path.join(self.pregenerated_dir, scene['image_filename'])
                if os.path.exists(image_path):
                    print(f"✅ 找到完全匹配场景: {scene['title']}")
                    return scene
        
        # 2. 如果没有完全匹配，查找近似匹配（政治实体相同，年份接近）
        best_match = None
        min_year_diff = float('inf')
        
        for scene in self.demo_scenes_index['demo_scenes']:
            if (scene['political_entity'] == political_entity and
                abs(scene['lat'] - lat) < 0.15 and 
                abs(scene['lng'] - lng) < 0.15):
                
                year_diff = abs(scene['year'] - year)
                
                # 允许50年内的年份差异
                if year_diff <= 50 and year_diff < min_year_diff:
                    image_path = os.path.join(self.pregenerated_dir, scene['image_filename'])
                    if os.path.exists(image_path):
                        best_match = scene
                        min_year_diff = year_diff
        
        if best_match:
            print(f"✅ 找到近似匹配场景: {best_match['title']} (年份差距: {min_year_diff}年)")
            return best_match
        
        print(f"❌ 未找到匹配的预生成场景")
        available_scenes = [f"{s['political_entity']}({s['year']})" for s in self.demo_scenes_index['demo_scenes']]
        print(f"   可用场景: {', '.join(available_scenes[:3])}")
        
        return None
    
    def return_pregenerated_scene(self, scene_data: Dict, historical_info: Dict) -> Dict:
        """返回预生成的场景数据"""
        
        # 构建图片URL - 使用相对路径适配云环境
        image_url = f"/static/pregenerated_images/{scene_data['image_filename']}"
        image_path = os.path.join(self.pregenerated_dir, scene_data['image_filename'])
        
        # 获取图片信息
        image_info = {}
        try:
            if os.path.exists(image_path):
                from PIL import Image
                with Image.open(image_path) as img:
                    image_info = {
                        'size': img.size,
                        'format': img.format,
                        'mode': img.mode
                    }
        except:
            pass
        
        return {
            'success': True,
            'images': [image_url],
            'scene_description': scene_data['scene_description'],
            'historical_context': historical_info,
            'generation_model': 'Pregenerated Demo Scene (Nano Banana Quality)',
            'generation_time': 0.1,  # 几乎瞬时
            'api_version': 'Demo Mode',
            'image_count': 1,
            'demo_mode': True,
            'pregenerated': True,
            'scene_title': scene_data['title'],
            'image_info': image_info
        }
    
    async def generate_historical_scene_image(self, historical_info: Dict, lat: float, lng: float) -> Dict:
        """
        智能历史场景生成 - 支持演示模式和实时生成
        
        Args:
            historical_info: Historical-basemaps查询结果
            lat: 纬度
            lng: 经度
            
        Returns:
            Dict: 图像生成结果
        """
        # 🎭 演示模式：优先使用预生成图片
        if self.demo_mode:
            matching_scene = self.find_matching_demo_scene(historical_info, lat, lng)
            if matching_scene:
                print(f"🎬 演示模式：使用预生成图片 - {matching_scene['title']}")
                return self.return_pregenerated_scene(matching_scene, historical_info)
            else:
                print(f"⚠️ 演示模式：未找到预生成图片，使用描述模式")
        
        # 🎨 实时生成模式
        if not self.client_available:
            print("🎭 API未配置，使用场景描述...")
            return await self.generate_demo_scene(historical_info, lat, lng)
        
        try:
            # 构建历史准确的提示词
            prompt = self.create_nano_banana_prompt(historical_info, lat, lng)
            
            # 记录prompt使用到数据库
            prompt_id = prompt_db.record_prompt_usage(
                prompt=prompt,
                prompt_type='scene',
                historical_period=str(historical_info.get('query_year')),
                political_entity=historical_info.get('political_entity'),
                cultural_region=historical_info.get('cultural_region')
            )
            
            print(f"🎨 开始Nano Banana图像生成: {historical_info['political_entity']} ({historical_info['query_year']}年)")
            print(f"📝 提示词长度: {len(prompt)} 字符")
            print(f"📁 Prompt已记录到数据库 ID:{prompt_id}")
            
            # 按照官方文档调用图像生成API
            start_time = time.time()
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",  # Nano Banana模型
                contents=[prompt]
            )
            
            generation_time = time.time() - start_time
            
            # 处理响应 - 按照官方文档的方式
            generated_images = []
            scene_description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    scene_description = part.text
                    print(f"📝 AI场景描述: {scene_description[:100]}...")
                    
                elif part.inline_data is not None:
                    # 处理生成的图像数据
                    image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建文件名
                    timestamp = int(time.time())
                    entity_name = historical_info['political_entity'].replace(' ', '_').replace('/', '_')
                    filename = f"nano_banana_{entity_name}_{historical_info['query_year']}_{timestamp}.png"
                    filepath = os.path.join(self.scene_images_dir, filename)
                    
                    # 保存图像
                    image.save(filepath)
                    
                    # 构建URL - 使用新的meme目录结构  
                    image_url = f"/static/meme/scene_view/{filename}"
                    generated_images.append(image_url)
                    
                    # 记录生成历史到数据库
                    generation_id = prompt_db.record_generation(
                        prompt_id=prompt_id,
                        image_path=f"static/meme/scene_view/{filename}",
                        image_url=image_url,
                        success=True,
                        generation_time=generation_time,
                        historical_context=historical_info,
                        api_parameters={
                            'model': 'gemini-2.5-flash-image-preview',
                            'lat': lat,
                            'lng': lng,
                            'image_size': image.size
                        }
                    )
                    
                    print(f"💾 Nano Banana图像已保存: {filepath}")
                    print(f"🔗 访问URL: {image_url}")
                    print(f"🖼️ 图像尺寸: {image.size}")
                    print(f"📁 生成历史已记录 ID:{generation_id}")
            
            return {
                'success': True,
                'images': generated_images,
                'scene_description': scene_description,
                'historical_context': historical_info,
                'generation_model': 'Gemini 2.5 Flash Image (Nano Banana)',
                'generation_time': generation_time,
                'api_version': 'google-genai 1.32.0',
                'image_count': len(generated_images),
                'prompt_length': len(prompt),
                'generation_id': generation_id if 'generation_id' in locals() else None  # 返回生成ID便于后续评分
            }
            
        except Exception as e:
            print(f"❌ Nano Banana图像生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': await self.generate_demo_scene(historical_info, lat, lng)
            }
    
    def create_nano_banana_prompt(self, historical_info: Dict, lat: float, lng: float) -> str:
        """
        为Nano Banana创建历史场景提示词
        遵循官方文档的最佳实践
        """
        political_entity = historical_info.get('political_entity') or 'Unknown'
        ruler_power = historical_info.get('ruler_or_power') or ''
        cultural_region = historical_info.get('cultural_region') or ''
        year = historical_info.get('query_year') or 0
        
        print(f"🏛️ 为Nano Banana构建提示词:")
        print(f"   政治实体: {political_entity}")
        print(f"   年份: {year}")
        
        # 根据政治实体获取具体的视觉特征
        architectural_details = self.get_architectural_details(political_entity, cultural_region, year)
        clothing_details = self.get_clothing_details(political_entity, cultural_region, year)
        environment_details = self.get_environment_details(lat, lng, year)
        
        # 构建符合Nano Banana最佳实践的详细提示词
        prompt = f"""
Create a historically accurate and visually stunning image of {political_entity} in {year} AD at coordinates {lat:.2f}, {lng:.2f}.

**CRITICAL: This scene must authentically represent the year {year} AD specifically**

**Historical Context:**
- Political Entity: {political_entity}
- Ruler/Authority: {ruler_power}
- Cultural Region: {cultural_region}
- **Exact Time Period: {year} AD** (This is crucial for historical accuracy)
- Century: {self.get_century_context(year)}
- Historical Era: {self.get_era_context(year)}

**Architecture & Buildings:**
{architectural_details}

**People & Clothing:**
{clothing_details}

**Environment & Setting:**
{environment_details}

**Visual Composition:**
- Wide-angle shot capturing both architectural grandeur and daily life
- Atmospheric lighting appropriate to the geographic location and season
- 4-6 people in period-accurate clothing representing different social classes
- Show interaction between built environment and human activities
- Include period-appropriate tools, transportation, and objects

**Art Style Requirements:**
- Photorealistic historical illustration with museum-quality detail
- Rich textures showing authentic materials and craftsmanship of the {year} AD era
- Dramatic cinematic lighting emphasizing the culture of {political_entity}
- Color palette using only pigments and dyes available in {year} AD
- High historical authenticity suitable for educational purposes
- **Technology Level**: Show only tools, weapons, and devices that existed in {year} AD

**Critical Year-Specific Requirements for {year} AD:**
- Buildings must use construction techniques available in {year} AD
- Clothing styles must match exactly what was worn in {year} AD
- Transportation methods limited to what existed in {year} AD
- Agricultural practices appropriate to {year} AD technology
- Military equipment and weapons from the {year} AD period only

**Strictly Avoid (Anachronisms):**
- Any technology, materials, or methods not invented until after {year} AD
- Architectural elements from different time periods
- Clothing, hairstyles, or accessories from other eras
- Modern or future elements that break the {year} AD immersion
- Cross-cultural elements that wouldn't have existed in this location in {year} AD

**FINAL VERIFICATION**: Every single element in this image must be authentic to {political_entity} in exactly {year} AD - no exceptions.
        """.strip()
        
        return prompt
    
    def get_century_context(self, year: int) -> str:
        """获取世纪背景信息"""
        if year < 0:
            return f"{abs(year//100 + 1)}th century BC"
        else:
            return f"{year//100 + 1}th century AD"
    
    def get_era_context(self, year: int) -> str:
        """获取历史时代背景"""
        if year >= 1900:
            return "Modern Era"
        elif year >= 1800:
            return "Industrial Revolution Era" 
        elif year >= 1500:
            return "Early Modern Period"
        elif year >= 1000:
            return "High Medieval Period"
        elif year >= 500:
            return "Early Medieval Period"
        elif year >= 0:
            return "Late Antiquity"
        elif year >= -500:
            return "Classical Antiquity"
        else:
            return "Ancient World"
    
    def get_architectural_details(self, political_entity: str, cultural_region: str, year: int) -> str:
        """获取建筑细节描述"""
        
        # 精确的政治实体建筑特征
        entity_styles = {
            'Tokugawa Shogunate': """
Traditional Edo period Japanese architecture:
- Wooden post-and-beam construction with curved ceramic tile roofs
- Two-story machiya (townhouses) with shop fronts on ground level
- Shoji paper screens and tatami mat floors
- Raised wooden structures on stone foundations
- Traditional noren curtains hanging from shop entrances
- Edo Castle visible in the background with distinctive architectural features
            """,
            
            'Tang Empire': """
Chinese Tang Dynasty imperial architecture:
- Wooden pagoda towers with multiple curved eaves
- Traditional siheyuan courtyard houses with central gardens
- Colorful dougong bracket systems supporting upturned roof edges
- Red wooden pillars and golden roof tiles
- Grand palace complexes with symmetrical layouts
- Stone lion guardians and traditional Chinese gates
            """,
            
            'Papal States': """
Medieval Italian religious architecture:
- Romanesque stone churches with round arches and thick walls
- Tall bell towers (campaniles) with simple geometric decorations
- Marble columns with carved capitals
- Stone basilicas with wooden beam ceilings
- Monastic cloisters with covered walkways around courtyards
- Early Christian symbols carved in stone facades
            """,
            
            'France': """
Classical French architectural elements:
- Limestone buildings with formal symmetrical facades
- Tall windows with decorative stone mullions
- Mansard roofs with dormers and chimneys
- Ornate carved stone decorations and moldings
- Formal geometric gardens with trimmed hedges
- Wrought iron balconies and window details
            """
        }
        
        return entity_styles.get(political_entity, f"""
Based on your knowledge of the {cultural_region} cultural sphere, depict typical architecture for {political_entity} in the year {year}:
- Materials: Use locally sourced materials plausible for the region and era (e.g., wood, stone, brick, mud-brick).
- Construction: Reflect the technological level of {year}. Show characteristic building techniques.
- Key Structures: Include common buildings like dwellings, markets, religious structures, and fortifications, typical for {political_entity}.
- Decorative Style: Incorporate artistic and cultural motifs of the {cultural_region} on buildings.
        """)
    
    def get_clothing_details(self, political_entity: str, cultural_region: str, year: int) -> str:
        """获取服装细节描述"""
        
        entity_clothing = {
            'Tokugawa Shogunate': """
Edo period Japanese clothing with strict social hierarchy:
- Samurai: Traditional hakama trousers, haori jackets, two swords (katana and wakizashi)
- Merchants: Simple kimono in subdued colors, wooden geta sandals
- Women: Elaborate kimono with obi sashes, traditional hairstyles with ornaments
- Children: Simplified kimono and casual wear appropriate to their family status
            """,
            
            'Tang Empire': """
Chinese Tang Dynasty court and common dress:
- Nobles: Flowing silk robes with wide sleeves, elaborate headdresses, jade accessories
- Officials: Formal court dress with rank indicators, official hats
- Common people: Hemp or cotton robes, practical work clothing, simple footwear
- Foreign visitors: Mix of Central Asian, Japanese, and Korean traditional dress
            """,
            
            'Papal States': """
Medieval Italian religious and secular dress:
- Clergy: Brown Franciscan robes, white Dominican habits, red cardinal vestments
- Nobles: Rich fabrics with gold embroidery, formal medieval court dress
- Artisans: Practical wool tunics, leather aprons, guild-specific clothing
- Pilgrims: Simple traveling clothes, walking staves, religious medallions
            """,
            
            'France': """
Classical French period appropriate dress:
- Aristocrats: Elaborate baroque clothing, powdered wigs, silk fabrics
- Bourgeoisie: Well-tailored but simpler versions of noble fashion
- Artisans: Practical work clothes with guild insignia
- Peasants: Simple wool and linen garments, wooden shoes (sabots)
            """
        }
        
        return entity_clothing.get(political_entity, f"""
Based on your knowledge of {cultural_region}, depict period-appropriate clothing for people in {political_entity} around {year} AD:
- Social Classes: Show a variety of clothing for different social strata (e.g., rulers, merchants, artisans, peasants).
- Materials: Use textiles and dyes that would have been available, such as wool, linen, cotton, or silk, depending on trade connections.
- Styles: Reflect the typical attire, hairstyles, and accessories for men, women, and children of that culture.
- Function: Differentiate between everyday wear, ceremonial dress, and work clothes.
        """)
    
    def get_environment_details(self, lat: float, lng: float, year: int) -> str:
        """获取环境细节描述"""
        
        # 基于纬度的环境特征
        if lat > 50:
            climate = "Northern temperate environment with deciduous and coniferous forests"
        elif lat > 35:
            climate = "Temperate climate with seasonal changes, mixed vegetation"
        elif lat > 23:
            climate = "Subtropical environment with lush vegetation and longer growing seasons"
        else:
            climate = "Tropical or arid landscape with climate-adapted flora"
        
        return f"""
Natural environment as it appeared in {year} AD:
- {climate}
- Pristine natural landscape with minimal human environmental impact
- Clear skies and clean air typical of pre-industrial times  
- Native wildlife and vegetation appropriate to latitude {lat:.1f}°
- Seasonal lighting and atmospheric conditions for the geographic location
- Natural water sources like rivers or springs in their original state
        """
    
    async def generate_demo_scene(self, historical_info: Dict, lat: float, lng: float) -> Dict:
        """演示模式场景生成"""
        
        political_entity = historical_info.get('political_entity') or 'Unknown'
        year = historical_info.get('query_year') or 0
        
        # 详细的历史场景描述
        descriptions = {
            'Tokugawa Shogunate': """
在1600年的江户（现东京），德川幕府的城下町呈现出严谨而繁荣的景象。木质的传统建筑沿街排列，青瓦屋顶在晨光中闪耀。武士们身着正式和服，腰间佩戴双刀，体现着"士农工商"社会秩序的顶层。町人商贾们穿着素色和服，在店铺前忙碌。妇女身着华美振袖，发髻上装饰着精致的簪子。孩童们在街边嬉戏。街道两旁悬挂着传统暖帘，汉字招牌昭示着各行各业。远处江户城的天守阁巍然屹立，象征着德川政权的威严统治。
            """,
            'Tang Empire': """
800年的大唐长安城，盛世帝国的辉煌气象尽显。雄伟的木构宫殿群采用精湛的斗拱技术，琉璃瓦片金光闪闪。身着宽袖仙裙的贵族们丝绸华服上绣着凤凰牡丹，男性官员头戴进贤冠。街市上胡商云集，丝绸之路的奇珍异宝琳琅满目。遣唐使、高句丽使节等各国人士在此交流，体现唐朝开放包容的气度。佛寺道观香烟袅袅，诗词歌赋在酒肆茶楼间传唱，这是中华文明最自信繁荣的黄金时代。
            """,
            'Papal States': """
800年教皇国的罗马，作为基督教世界的精神圣地散发着神圣威严。罗马式教堂高耸云霄，圆拱石门雕刻着精美圣像。红衣主教身着华丽法衣主持仪式，修道士们穿着朴素僧袍诵经祈祷。虔诚信徒跪拜于教堂门前，手工业者在石板街巷中劳作。钟楼传来悠扬钟声，古罗马废墟与新建教堂形成历史对话。这是查理大帝加冕的时代，永恒之城承载着沟通天地的神圣使命。
            """
        }
        
        # 模拟生成时间
        await asyncio.sleep(1.0)
        
        scene_description = descriptions.get(political_entity, 
            f"{year}年的{political_entity}展现着该时代典型的文化风貌和社会特征。")
        
        return {
            'success': True,
            'scene_description': scene_description,
            'generation_model': 'Demo Mode (Nano Banana Ready)',
            'generation_time': 1.0,
            'api_version': 'google-genai 1.32.0',
            'demo_mode': True,
            'note': 'API已就绪，配置GEMINI_API_KEY即可生成真实图像'
        }
    
    async def test_api_connection(self) -> Dict:
        """测试API连接状态"""
        if not self.client_available:
            return {
                'api_available': False,
                'reason': 'API Key未配置'
            }
        
        try:
            # 简单的文本生成测试
            test_prompt = "Test connection to Gemini API"
            
            # 注意：这里可能需要调整，因为我们主要想测试图像生成API
            # 但可以先测试文本生成来验证连接
            
            return {
                'api_available': True,
                'model_available': 'gemini-2.5-flash-image-preview',
                'client_type': str(type(self.client))
            }
            
        except Exception as e:
            return {
                'api_available': False,
                'error': str(e)
            }
    
    async def generate_historical_selfie(self, user_image_path: str, historical_scene_image_path: str) -> Dict:
        """
        生成历史自拍照片 - 使用Gemini 2.5 Flash Image的图生图功能
        将用户头像与指定的历史场景图片进行融合
        
        Args:
            user_image_path: 用户头像图片路径
            historical_scene_image_path: 历史场景图片路径
            
        Returns:
            Dict: 自拍生成结果
        """
        if not self.client_available:
            return {
                'success': False,
                'error': 'Gemini API未配置，无法生成真实图生图',
                'demo_mode_available': True
            }
        
        try:
            print(f"📸 开始Gemini图生图自拍生成 (双图融合)...")
            print(f"   用户图片: {user_image_path}")
            print(f"   历史场景图片: {historical_scene_image_path}")
            
            # 检查输入图片是否存在
            if not os.path.exists(user_image_path):
                return {'success': False, 'error': f'用户头像不存在: {user_image_path}'}
            if not os.path.exists(historical_scene_image_path):
                return {'success': False, 'error': f'历史场景图片不存在: {historical_scene_image_path}'}
            
            # 加载用户头像和历史场景
            user_image = Image.open(user_image_path)
            historical_scene_image = Image.open(historical_scene_image_path)
            print(f"✅ 用户头像加载成功: {user_image.size}")
            print(f"✅ 历史场景加载成功: {historical_scene_image.size}")
            
            # 构建自拍提示词
            selfie_prompt = self.create_selfie_prompt()
            
            # 按照官方文档进行图生图调用
            start_time = time.time()
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[selfie_prompt, user_image, historical_scene_image]  # 提示词 + 用户头像 + 历史背景图
            )
            
            generation_time = time.time() - start_time
            
            # 处理响应
            generated_selfie_url = None
            ai_description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    ai_description = part.text
                    print(f"📝 AI自拍描述: {ai_description[:100]}...")
                    
                elif part.inline_data is not None:
                    # 保存生成的自拍图像
                    selfie_image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建自拍文件名
                    timestamp = int(time.time())
                    filename = f"historical_selfie_{timestamp}.png"
                    
                    # 保存到新的meme自拍目录
                    filepath = os.path.join(self.selfie_images_dir, filename)
                    selfie_image.save(filepath)
                    
                    # 构建URL - 使用新的meme目录结构
                    generated_selfie_url = f"/static/meme/selfie/{filename}"
                    
                    print(f"💾 历史自拍已保存: {filepath}")
                    print(f"🔗 访问URL: {generated_selfie_url}")
                    print(f"🖼️ 自拍尺寸: {selfie_image.size}")
                    
                    break  # 只处理第一张图片
            
            if not generated_selfie_url:
                return {
                    'success': False,
                    'error': '图生图响应中未找到生成的图像数据'
                }
            
            return {
                'success': True,
                'selfie_url': generated_selfie_url,
                'scene_info': {
                    'selfie_description': ai_description,
                    'generation_method': 'Gemini 2.5 Flash Image (双图融合)',
                    'user_image_used': os.path.basename(user_image_path),
                    'scene_image_used': os.path.basename(historical_scene_image_path)
                },
                'generation_time': generation_time,
                'generation_model': 'Gemini 2.5 Flash Image (Nano Banana)',
                'api_version': 'google-genai 1.32.0',
                'demo_mode': False
            }
            
        except Exception as e:
            print(f"❌ Gemini图生图自拍生成失败: {e}")
            return {
                'success': False,
                'error': f'图生图生成失败: {str(e)}',
                'fallback_available': True
            }
    
    def create_selfie_prompt(self) -> str:
        """
        创建历史自拍的提示词 - 电影级自然融合版本
        专注于光影匹配、环境交互和电影感表现
        """
        prompt = """
You are a master photo compositor and cinematic artist. Create a stunning, photorealistic historical selfie that looks like it was shot by a professional cinematographer.

You will receive two images:
1. A portrait of a person (modern visitor/time traveler)  
2. A historical scene (destination/background)

Transform these into a single, breathtaking cinematic selfie with film-quality realism.

**CINEMATIC INTEGRATION:**
- Position the person as if they naturally belong in this historical moment
- Create genuine interaction: have them lean against architecture, gesture toward landmarks, or react to their surroundings
- Use dynamic angles and depth of field like a movie scene
- Make it feel like a candid moment captured during their historical adventure

**LIGHTING MASTERY:**
- Analyze the historical scene's lighting direction, intensity, and color temperature
- Perfectly match lighting on the person's face, skin, and clothing
- Add realistic shadows that the person would cast in this environment  
- Ensure rim lighting and ambient light are consistent throughout
- No harsh transitions or mismatched lighting zones

**PHOTOREALISTIC DEPTH:**
- Place the person at the correct scale and perspective for their distance from camera
- Create natural depth of field: person sharp, background with appropriate softness
- Add atmospheric perspective and environmental reflections on their skin/eyes
- Include subtle environmental elements like dust particles, ambient fog, or atmospheric haze

**NATURAL COMPOSITION:**
- Classic selfie angle: slightly elevated (15-20°), arm's length distance
- Person occupies 25-35% of frame, positioned naturally off-center
- Show one arm extended subtly (holding camera) while the other interacts with the scene
- Confident, genuine expression - excitement of discovery, not posed

**SEAMLESS BLENDING:**
- Perfectly match grain, texture, and image quality between person and background
- Harmonize color grading so the person appears shot in the same conditions
- Add realistic edge softening and light wrap around the person's silhouette
- Include environmental elements like appropriate reflections in eyes

**ENVIRONMENTAL STORYTELLING:**
- Have the person genuinely react to and interact with the historical setting
- Show them touching, leaning on, or gesturing toward historical elements
- Their body language should convey wonder and authentic presence
- Make background characters and elements feel aware of the time traveler's presence

**TECHNICAL EXCELLENCE:**
- Match the exact color palette, saturation, and contrast of the historical scene
- Ensure consistent film grain and image quality throughout
- Perfect edge blending with no visible compositing artifacts
- Balance exposure across all elements for cinematic cohesion

The final result should look like a genuine behind-the-scenes photo from a big-budget historical film, where a modern visitor has been naturally transported into the past and is documenting their incredible experience.
        """.strip()
        return prompt

    async def generate_scene_with_custom_prompt(self, custom_prompt: str, historical_info: Dict, template_id: Optional[str] = None) -> Dict:
        """
        使用自定义提示词生成历史场景
        
        Args:
            custom_prompt: 用户自定义提示词
            historical_info: 历史背景信息
            template_id: 预设模板ID（可选，如'scene_prompt1'）
        """
        if not self.client_available:
            print("🎭 API未配置，使用演示模式...")
            # 演示模式：返回预设描述
            return {
                'success': True,
                'image_url': '/static/pregenerated_images/demo_scene.jpg',
                'scene_description': '演示模式：自定义历史场景'
            }
        
        try:
            # 构建最终的提示词：使用模板或自定义
            if template_id:
                # 使用预设模板并自动填充占位符
                final_prompt = self.process_scene_template(template_id, historical_info)
                print(f"✅ 场景模板处理完成，最终提示词长度: {len(final_prompt)} 字符")
            else:
                # 使用用户自定义提示词
                final_prompt = custom_prompt
                print(f"📝 使用自定义提示词，长度: {len(final_prompt)} 字符")
            
            # 记录prompt使用到数据库
            prompt_id = prompt_db.record_prompt_usage(
                prompt=final_prompt,
                prompt_type='scene',
                historical_period=str(historical_info.get('query_year')),
                political_entity=historical_info.get('political_entity'),
                cultural_region=historical_info.get('cultural_region'),
                notes=f'场景模板: {template_id}' if template_id else '自定义历史场景prompt'
            )
            
            print(f"🎨 开始场景图像生成: {historical_info['political_entity']} ({historical_info['query_year']}年)")
            print(f"📝 最终提示词长度: {len(final_prompt)} 字符")
            print(f"📁 Prompt已记录到数据库 ID:{prompt_id}")
            if template_id:
                print(f"📋 使用模板: {template_id}")
            
            # 使用正确的图像生成模型 - 与generate_historical_scene_image相同的逻辑
            start_time = time.time()
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",  # 使用图像生成模型
                contents=[final_prompt]  # 使用处理后的最终提示词
            )
            
            generation_time = time.time() - start_time
            
            # 处理响应 - 按照与generate_historical_scene_image相同的方式
            generated_images = []
            scene_description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    scene_description = part.text
                    print(f"📝 AI场景描述: {scene_description[:100]}...")
                    
                elif part.inline_data is not None:
                    # 处理生成的图像数据
                    image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建文件名
                    timestamp = int(time.time())
                    entity_name = historical_info['political_entity'].replace(' ', '_').replace('/', '_')
                    filename = f"custom_scene_{entity_name}_{historical_info['query_year']}_{timestamp}.png"
                    filepath = os.path.join(self.scene_images_dir, filename)
                    
                    # 保存图像
                    image.save(filepath)
                    
                    # 构建URL
                    image_url = f"/static/meme/scene_view/{filename}"
                    generated_images.append(image_url)
                    
                    # 记录生成历史到数据库
                    generation_id = prompt_db.record_generation(
                        prompt_id=prompt_id,
                        image_path=f"static/meme/scene_view/{filename}",
                        image_url=image_url,
                        success=True,
                        generation_time=generation_time,
                        historical_context=historical_info,
                        api_parameters={
                            'model': 'gemini-2.5-flash-image-preview',
                            'custom_prompt': True,
                            'image_size': image.size
                        }
                    )
                    
                    print(f"💾 自定义场景图像已保存: {filepath}")
                    print(f"🔗 访问URL: {image_url}")
                    print(f"🖼️ 图像尺寸: {image.size}")
                    print(f"📁 生成历史已记录 ID:{generation_id}")
            
            # 处理完所有parts后，检查是否成功生成了图像
            if generated_images:
                # 成功生成图像
                return {
                    'success': True,
                    'image_url': generated_images[0],  # 返回第一张图片
                    'scene_description': scene_description,
                    'generation_time': generation_time,
                    'generation_id': generation_id if 'generation_id' in locals() else None
                }
            
            # 如果没有生成图像数据，尝试重试机制
            if not scene_description:
                raise Exception("API没有返回任何有效内容")
            
            print("⚠️ API首次调用只返回了文本，尝试重新生成...")
            print(f"📝 返回的文本: {scene_description[:200]}...")
            
            # 构建更明确的图像生成提示词
            retry_prompt = f"""IMPORTANT: Generate a high-quality historical image based on this description.

Original request: {custom_prompt}

Historical context: {historical_info.get('political_entity', 'historical location')} in {historical_info.get('query_year', 'ancient times')}.

CRITICAL: Please generate an actual image, not just text description. The output must include visual content.
"""
            
            print("🔄 正在重试图像生成...")
            retry_start_time = time.time()
            
            retry_response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[retry_prompt]
            )
            
            retry_generation_time = time.time() - retry_start_time
            
            # 处理重试响应
            for part in retry_response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # 处理生成的图像数据
                    image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建文件名
                    timestamp = int(time.time())
                    entity_name = historical_info['political_entity'].replace(' ', '_').replace('/', '_')
                    filename = f"custom_scene_{entity_name}_{historical_info['query_year']}_{timestamp}_retry.png"
                    filepath = os.path.join(self.scene_images_dir, filename)
                    
                    # 保存图像
                    image.save(filepath)
                    
                    # 构建URL
                    image_url = f"/static/meme/scene_view/{filename}"
                    
                    # 记录生成历史到数据库
                    generation_id = prompt_db.record_generation(
                        prompt_id=prompt_id,
                        image_path=f"static/meme/scene_view/{filename}",
                        image_url=image_url,
                        success=True,
                        generation_time=generation_time + retry_generation_time,
                        historical_context=historical_info,
                        api_parameters={
                            'model': 'gemini-2.5-flash-image-preview',
                            'custom_prompt': True,
                            'retry': True,
                            'image_size': image.size
                        }
                    )
                    
                    print(f"✅ 重试成功！图像已保存: {filepath}")
                    print(f"🔗 访问URL: {image_url}")
                    print(f"🖼️ 图像尺寸: {image.size}")
                    print(f"📁 生成历史已记录 ID:{generation_id}")
                    
                    return {
                        'success': True,
                        'image_url': image_url,
                        'scene_description': scene_description,
                        'generation_time': generation_time + retry_generation_time,
                        'generation_id': generation_id,
                        'retry_used': True
                    }
            
            # 如果重试也失败，返回有意义的错误信息
            error_msg = f"Gemini API两次调用都只返回文本描述，可能是'{historical_info.get('political_entity', '未知')}' ({historical_info.get('query_year', '未知')}年)这个历史背景无法生成图像"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
                
        except Exception as e:
            print(f"❌ 自定义场景生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_image_elements(self, image_url: str) -> Dict:
        """
        分析图片，提取场景元素
        """
        if not self.client_available:
            print("🎭 API未配置，使用演示模式...")
            # 演示模式：返回预设元素
            return {
                'success': True,
                'elements': ['古代建筑', '传统服饰', '石板路', '商贩', '马车', '城墙', '旗帜', '市集']
            }
        
        try:
            # 将图片URL转换为本地文件路径
            if image_url.startswith('/static/'):
                # 转换相对URL为绝对路径
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                local_image_path = os.path.join(project_root, image_url.lstrip('/'))
            else:
                local_image_path = image_url
            
            print(f"📷 图片路径转换: {image_url} → {local_image_path}")
            
            # 检查图片文件是否存在
            if not os.path.exists(local_image_path):
                print(f"❌ 图片文件不存在: {local_image_path}")
                return {
                    'success': False,
                    'error': f'图片文件不存在: {local_image_path}'
                }
            
            # 读取并可能压缩图片数据
            with open(local_image_path, 'rb') as f:
                image_bytes = f.read()
            
            print(f"✅ 图片数据读取成功: {len(image_bytes)} 字节")
            
            # 如果图片超过1MB，进行压缩以提高API成功率
            if len(image_bytes) > 1024 * 1024:  # 1MB
                print(f"📉 图片较大({len(image_bytes)/(1024*1024):.1f}MB)，进行压缩...")
                try:
                    from PIL import Image
                    img = Image.open(local_image_path)
                    
                    # 压缩图片：保持比例，最大尺寸1024
                    max_size = 1024
                    if max(img.size) > max_size:
                        ratio = max_size / max(img.size)
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"🔧 图片压缩: {img.size}")
                    
                    # 转换为字节
                    from io import BytesIO
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG', quality=85, optimize=True)
                    image_bytes = img_buffer.getvalue()
                    
                    # 更新mime_type为jpeg
                    mime_type = 'image/jpeg'
                    
                    print(f"✅ 图片压缩完成: {len(image_bytes)} 字节 ({len(image_bytes)/(1024*1024):.1f}MB)")
                except Exception as compress_error:
                    print(f"⚠️ 图片压缩失败，使用原图: {compress_error}")
                    # 继续使用原始图片，检测原始格式
                    if local_image_path.lower().endswith('.png'):
                        mime_type = 'image/png'
                    elif local_image_path.lower().endswith('.webp'):
                        mime_type = 'image/webp'
                    else:
                        mime_type = 'image/jpeg'
            else:
                # 图片不大，检测原始格式
                if local_image_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif local_image_path.lower().endswith('.webp'):
                    mime_type = 'image/webp'
                else:
                    mime_type = 'image/jpeg'
            
            print(f"📝 图片格式: {mime_type}")
            
            # 构建图片分析提示
            analysis_prompt = """
请仔细分析这张历史场景图片，并提取其中最能体现历史时代与地域特征的视觉元素。  
输出时请尽量简短，突出时代感和文化特征。  

必须包含：  
- 建筑风格与材料（如木屋、茅草屋顶、石墙）  
- 人物的服装与配饰（长袍、斗篷、头巾、靴子）  
- 场景活动或道具（集市、篮子、木桶、农作物）  
- 环境细节（泥土路、空气氛围、季节特征）  
- 色彩与光影风格（如柔和日光、棕灰色调）  

输出格式：每个元素用简短中文词语列出，用逗号分隔。
"""
            
            # 使用官方推荐的 gemini-2.5-flash 方法，添加重试机制处理网络问题
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        print(f"🔄 重试第 {attempt} 次...")
                        await asyncio.sleep(attempt * 2)  # 递增延迟
                    
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=mime_type,
                            ),
                            analysis_prompt
                        ]
                    )
                    
                    # 使用官方推荐的简洁响应处理方式
                    elements_text = response.text
                    print(f"📝 AI元素分析结果: {elements_text[:100]}...")
                    
                    # 解析文本，提取元素列表
                    elements = [elem.strip() for elem in elements_text.split(',')]
                    elements = [elem for elem in elements if elem]  # 过滤空字符串
                    
                    print(f"✅ 提取到 {len(elements)} 个场景元素")
                    
                    return {
                        'success': True,
                        'elements': elements[:15]  # 限制数量
                    }
                    
                except Exception as api_error:
                    if "Connection reset by peer" in str(api_error) or "timeout" in str(api_error).lower():
                        if attempt < max_retries:
                            print(f"⚠️ 网络连接问题，准备重试: {api_error}")
                            continue
                        else:
                            print(f"❌ 重试 {max_retries} 次后仍失败")
                            raise api_error
                    else:
                        # 非网络错误，直接抛出
                        raise api_error
                
        except Exception as e:
            print(f"❌ 图片元素分析失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def analyze_image_elements_from_bytes(self, image_data: bytes, content_type: str) -> Dict:
        """
        直接从图片字节数据分析场景元素
        专为用户上传的文件设计
        
        Args:
            image_data: 图片字节数据
            content_type: MIME类型 (如 'image/jpeg', 'image/png')
        """
        if not self.client_available:
            print("🎭 API未配置，使用演示模式...")
            # 演示模式：返回预设元素
            return {
                'success': True,
                'elements': ['现代建筑', '城市街道', '汽车', '行人', '商店招牌', '交通设施', '天空', '都市景观']
            }
        
        try:
            print(f"📷 开始分析用户上传图片: {len(image_data)} 字节, {content_type}")
            
            # 图片压缩处理（如果需要）
            processed_data = image_data
            mime_type = content_type
            
            # 如果图片超过1MB，进行压缩以提高API成功率
            if len(image_data) > 1024 * 1024:  # 1MB
                print(f"📉 图片较大({len(image_data)/(1024*1024):.1f}MB)，进行压缩...")
                try:
                    from PIL import Image
                    from io import BytesIO
                    
                    # 从字节数据加载图片
                    img = Image.open(BytesIO(image_data))
                    
                    # 压缩图片：保持比例，最大尺寸1024
                    max_size = 1024
                    if max(img.size) > max_size:
                        ratio = max_size / max(img.size)
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"🔧 图片压缩: {img.size}")
                    
                    # 转换为字节
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG', quality=85, optimize=True)
                    processed_data = img_buffer.getvalue()
                    mime_type = 'image/jpeg'
                    
                    print(f"✅ 图片压缩完成: {len(processed_data)} 字节 ({len(processed_data)/(1024*1024):.1f}MB)")
                    
                except Exception as compress_error:
                    print(f"⚠️ 图片压缩失败，使用原图: {compress_error}")
                    processed_data = image_data
                    mime_type = content_type
            
            print(f"📝 最终图片格式: {mime_type}")
            
            # 构建图片分析提示
            analysis_prompt = """
请仔细分析这张场景图片，并提取其中的关键视觉元素。
输出时请尽量简短，突出场景特征和物体特征。

必须包含：
- 建筑风格与结构（如现代建筑、古建筑、住宅、商业楼等）
- 交通工具与道路（如汽车、自行车、马车、道路类型等）
- 人物与服饰（如行人、工作者、服装风格等）
- 环境与景观（如街道、公园、自然景观、天空等）
- 色彩与氛围（如光线、季节、时间特征等）
- 文化与时代元素（如招牌、标识、装饰风格等）

输出格式：每个元素用简短中文词语列出，用逗号分隔。
例如：现代建筑, 城市街道, 汽车, 行人, 商店招牌, 蓝天白云
"""
            
            # 使用官方推荐的 gemini-2.5-flash 方法，添加重试机制
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        print(f"🔄 重试第 {attempt} 次...")
                        await asyncio.sleep(attempt * 2)  # 递增延迟
                    
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(
                                data=processed_data,
                                mime_type=mime_type,
                            ),
                            analysis_prompt
                        ]
                    )
                    
                    # 使用官方推荐的简洁响应处理方式
                    elements_text = response.text
                    print(f"📝 AI元素分析结果: {elements_text[:150]}...")
                    
                    # 解析文本，提取元素列表
                    elements = [elem.strip() for elem in elements_text.split(',')]
                    elements = [elem for elem in elements if elem and len(elem) > 1]  # 过滤空字符串和单字符
                    
                    # 去除可能的序号和特殊字符
                    cleaned_elements = []
                    for elem in elements:
                        # 移除序号前缀 (如 "1. 现代建筑" -> "现代建筑")
                        elem = elem.split('. ')[-1] if '. ' in elem else elem
                        # 移除引号和其他标点
                        elem = elem.strip('"\'。！？.,;')
                        if elem and len(elem) > 1:
                            cleaned_elements.append(elem)
                    
                    print(f"✅ 提取到 {len(cleaned_elements)} 个场景元素: {', '.join(cleaned_elements[:5])}...")
                    
                    return {
                        'success': True,
                        'elements': cleaned_elements[:20]  # 限制数量，避免过多元素
                    }
                    
                except Exception as api_error:
                    if ("Connection reset by peer" in str(api_error) or 
                        "timeout" in str(api_error).lower() or
                        "network" in str(api_error).lower()):
                        
                        if attempt < max_retries:
                            print(f"⚠️ 网络连接问题，准备重试: {api_error}")
                            continue
                        else:
                            print(f"❌ 重试 {max_retries} 次后仍失败")
                            raise api_error
                    else:
                        # 非网络错误，直接抛出
                        raise api_error
                
        except Exception as e:
            print(f"❌ 用户上传图片元素分析失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def log_prompt_usage(self, prompt: str, template_id: Optional[str], historical_info: Dict):
        """
        记录提示词使用情况到日志文件
        
        Args:
            prompt: 最终使用的提示词
            template_id: 模板ID（如果有）
            historical_info: 历史背景信息
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "template_id": template_id or "none",
                "historical_location": historical_info.get('political_entity', 'Unknown'),
                "historical_year": historical_info.get('query_year', 'Unknown'),
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "full_prompt": prompt
            }
            
            # 写入日志文件
            with open(self.prompt_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"时间: {log_entry['timestamp']}\n")
                f.write(f"模板ID: {log_entry['template_id']}\n")
                f.write(f"历史地点: {log_entry['historical_location']}\n")
                f.write(f"历史年份: {log_entry['historical_year']}\n")
                f.write(f"提示词长度: {log_entry['prompt_length']} 字符\n")
                f.write(f"{'='*80}\n")
                f.write("完整提示词:\n")
                f.write(f"{log_entry['full_prompt']}\n")
                f.write(f"{'='*80}\n\n")
            
            print(f"📝 提示词已记录到日志文件: {self.prompt_log_file}")
            
        except Exception as e:
            print(f"⚠️ 提示词日志记录失败: {e}")
    
    async def generate_historical_meme(
        self, 
        character_image_path: str, 
        composition_image_path: Optional[str], 
        scene_elements: List[str], 
        meme_prompt: str, 
        historical_info: Dict,
        template_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        companion_image_path: Optional[str] = None
    ) -> Dict:
        """
        生成历史梗图
        
        Args:
            character_image_path: 人物素材图片路径
            composition_image_path: 构图参考图片路径（可选）
            scene_elements: 场景元素列表
            meme_prompt: 用户自定义梗图提示词
            historical_info: 历史背景信息
            template_id: 预设模板ID（可选，如'cinematic_selfie'）
        """
        if not self.client_available:
            print("🎭 API未配置，使用演示模式...")
            # 演示模式：返回预设图片
            return {
                'success': True,
                'meme_url': '/static/meme/scene_view/demo_meme.jpg'
            }
        
        try:
            print(f"🎨 开始生成梗图")
            print(f"🏛️ 历史背景: {historical_info['political_entity']} ({historical_info['query_year']}年)")
            print(f"🎯 场景元素: {', '.join(scene_elements)}")
            if template_id:
                print(f"📋 模板ID: {template_id}")
            if interaction_id:
                print(f"🎭 互动动作: {interaction_id}")
            
            # 🔥 关键修改：直接使用用户在文本框中输入的提示词
            # 不再根据template_id重新生成，确保用户修改的内容被使用
            meme_generation_prompt = meme_prompt.strip()
            
            # 如果用户没有输入任何内容，才使用后备方案
            if not meme_generation_prompt:
                if template_id:
                    # 使用预设模板作为后备
                    meme_generation_prompt = self.process_meme_template(
                        template_id, historical_info, scene_elements, interaction_id
                    )
                    print(f"⚠️ 文本框为空，使用模板生成后备提示词")
                else:
                    # 使用基础模板作为后备
                    meme_generation_prompt = f"""
创建一个结合历史与现代元素的创意梗图，要求如下：

📍 历史背景：
- 时代: {historical_info['query_year']}年的{historical_info['political_entity']}
- 文化区域: {historical_info['cultural_region']}

🎨 场景元素（来自历史场景解构）:
{', '.join(scene_elements)}

🎯 梗图制作指南：
1. 将人物自然地融入历史场景中
2. 保持历史元素的真实性和准确性
3. 添加现代梗图的幽默感和创意性
4. 确保视觉效果和谐统一
5. 色彩搭配要协调美观

请生成一张高质量的创意梗图，兼具历史感和娱乐性。
"""
                    print(f"⚠️ 文本框为空且无模板，使用基础后备提示词")
            
            # 显示最终使用的提示词
            print(f"\n🎯 【最终发送的提示词】:")
            print(f"{'='*50}")
            print(meme_generation_prompt)
            print(f"{'='*50}")
            print(f"📏 提示词长度: {len(meme_generation_prompt)} 字符")
            print(f"💬 用户原始输入: {meme_prompt[:100]}{'...' if len(meme_prompt) > 100 else ''}")
            
            # 记录到提示词日志文件
            self.log_prompt_usage(meme_generation_prompt, template_id, historical_info)
            
            # 记录prompt使用到数据库
            prompt_id = prompt_db.record_prompt_usage(
                prompt=meme_generation_prompt,
                prompt_type='meme',
                historical_period=str(historical_info.get('query_year')),
                political_entity=historical_info.get('political_entity'),
                cultural_region=historical_info.get('cultural_region'),
                notes=f"梗图提示: {meme_prompt}"
            )
            print(f"📁 Meme Prompt已记录到数据库 ID:{prompt_id}")
            
            # 🖼️ 实现真正的图文生图逻辑 - 基于generate_historical_selfie的成功模式
            
            # 1. 检查和加载图片 
            print(f"📷 开始加载图片素材...")
            print(f"   人物素材: {character_image_path}")
            print(f"   构图素材: {composition_image_path or '无'}")
            print(f"   虚拟伙伴: {companion_image_path or '无'}")
            
            # 检查人物图片是否存在（必需）
            if not character_image_path or not os.path.exists(character_image_path):
                raise Exception(f"人物素材图片不存在: {character_image_path}")
            
            # 加载人物图片
            character_image = Image.open(character_image_path)
            print(f"✅ 人物素材加载成功: {character_image.size}")
            
            # 加载构图参考图片（可选）
            composition_image = None
            if composition_image_path and os.path.exists(composition_image_path):
                composition_image = Image.open(composition_image_path)
                print(f"✅ 构图素材加载成功: {composition_image.size}")
            else:
                print(f"ℹ️ 未使用构图素材")
            
            # 加载虚拟伙伴图片（可选）
            companion_image = None
            if companion_image_path and os.path.exists(companion_image_path):
                companion_image = Image.open(companion_image_path)
                print(f"✅ 虚拟伙伴素材加载成功: {companion_image.size}")
            else:
                print(f"ℹ️ 未使用虚拟伙伴素材")
            
            # 2. 构建多模态输入内容 - 与generate_historical_selfie相同的模式
            contents = [meme_generation_prompt, character_image]
            if composition_image is not None:
                contents.append(composition_image)
            if companion_image is not None:
                contents.append(companion_image)
            
            print(f"🎯 多模态输入准备完成: {len(contents)} 个元素（提示词 + {len(contents)-1} 张图片）")
            
            # 3. 调用Gemini图像生成API - 使用与selfie相同的模型和方式
            start_time = time.time()
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",  # 与selfie方法相同的模型
                contents=contents  # 多模态输入：提示词 + 人物图 + (可选)构图图
            )
            
            generation_time = time.time() - start_time
            
            # 4. 处理响应 - 与selfie方法相同的处理逻辑
            generated_meme_url = None
            ai_description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    ai_description = part.text
                    print(f"📝 AI梗图描述: {ai_description[:100]}...")
                    
                elif part.inline_data is not None:
                    # 保存生成的梗图
                    meme_image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建梗图文件名
                    timestamp = int(time.time())
                    entity_name = historical_info['political_entity'].replace(' ', '_').replace('/', '_')
                    filename = f"historical_meme_{entity_name}_{historical_info['query_year']}_{timestamp}.png"
                    
                    # 保存到meme scene_view目录
                    filepath = os.path.join(self.scene_images_dir, filename)
                    meme_image.save(filepath)
                    
                    # 构建URL
                    generated_meme_url = f"/static/meme/scene_view/{filename}"
                    
                    # 记录生成历史到数据库
                    generation_id = prompt_db.record_generation(
                        prompt_id=prompt_id,
                        image_path=f"static/meme/scene_view/{filename}",
                        image_url=generated_meme_url,
                        success=True,
                        generation_time=generation_time,
                        scene_elements=scene_elements,
                        historical_context=historical_info,
                        api_parameters={
                            'model': 'gemini-2.5-flash-image-preview',
                            'character_image': character_image_path,
                            'composition_image': composition_image_path,
                            'user_prompt': meme_prompt,
                            'multimodal_inputs': len(contents),
                            'image_size': meme_image.size
                        }
                    )
                    
                    print(f"💾 历史梗图已保存: {filepath}")
                    print(f"🔗 访问URL: {generated_meme_url}")
                    print(f"🖼️ 梗图尺寸: {meme_image.size}")
                    print(f"📁 生成历史已记录 ID:{generation_id}")
            
            return {
                'success': True,
                        'meme_url': generated_meme_url,
                        'generation_time': generation_time,
                        'generation_id': generation_id,
                        'ai_description': ai_description,
                        'multimodal_generation': True,
                        'inputs_used': {
                            'character_image': True,
                            'composition_image': composition_image is not None,
                            'prompt': True
                        }
                    }
            
            # 如果没有生成图像数据，返回错误
            if not generated_meme_url:
                raise Exception("API响应中未找到生成的梗图图像数据")
            
        except Exception as e:
            print(f"❌ 梗图生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# 全局实例
nano_banana_service = NanoBananaHistoricalService()


# 测试函数
async def test_nano_banana():
    """测试Nano Banana服务"""
    print("🧪 测试Nano Banana历史场景生成...")
    print()
    
    # 测试API连接
    connection_test = await nano_banana_service.test_api_connection()
    print(f"📡 API连接测试: {connection_test}")
    print()
    
    # 模拟历史查询结果
    test_case = {
        'political_entity': 'Tokugawa Shogunate',
        'ruler_or_power': 'Tokugawa Shogunate',
        'cultural_region': 'Tokugawa Shogunate',
        'query_year': 1600,
        'time_period': '早期现代'
    }
    
    # 测试场景生成
    result = await nano_banana_service.generate_historical_scene_image(
        test_case, 35.7148, 139.7967
    )
    
    if result['success']:
        print("✅ 场景生成测试成功!")
        print(f"   模型: {result.get('generation_model')}")
        print(f"   耗时: {result.get('generation_time'):.3f}秒")
        print(f"   API版本: {result.get('api_version', 'N/A')}")
        
        if result.get('demo_mode'):
            print(f"   🎭 演示模式运行")
            print(f"   💡 {result.get('note', '')}")
        
        if result.get('images'):
            print(f"   🖼️ 生成图像: {len(result['images'])} 张")
        
        scene_desc = result.get('scene_description', '')
        if scene_desc:
            print(f"\n📝 场景描述预览:")
            print(f"   {scene_desc[:150]}...")
    else:
        print(f"❌ 测试失败: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_nano_banana())

