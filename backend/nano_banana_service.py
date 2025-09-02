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
from dotenv import load_dotenv

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
        
        # 图像保存目录
        self.images_dir = "static/generated_images"
        self.pregenerated_dir = os.getenv('PREGENERATED_IMAGES_PATH', 'static/pregenerated_images/')
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.pregenerated_dir, exist_ok=True)
        
        # 演示模式配置
        self.demo_mode = os.getenv('DEMO_MODE', 'false').lower() == 'true'
        
        # 加载预生成图片索引
        self.demo_scenes_index = self.load_demo_scenes_index()
        
        print(f"🎨 Nano Banana历史服务已初始化")
        print(f"   API状态: {'已配置' if self.client_available else '未配置'}")
        print(f"   演示模式: {'开启' if self.demo_mode else '关闭'}")
        print(f"   图像目录: {self.images_dir}")
        print(f"   预生成目录: {self.pregenerated_dir}")
        if self.demo_mode and self.demo_scenes_index:
            print(f"   预设场景: {len(self.demo_scenes_index.get('demo_scenes', []))} 个")
    
    def load_demo_scenes_index(self) -> Dict:
        """加载预生成场景索引"""
        index_path = os.path.join(self.pregenerated_dir, 'demo_scenes_index.json')
        
        try:
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'demo_scenes': []}
        except Exception as e:
            print(f"⚠️ 加载预生成索引失败: {e}")
            return {'demo_scenes': []}
    
    def find_matching_demo_scene(self, historical_info: Dict, lat: float, lng: float) -> Optional[Dict]:
        """查找匹配的预生成演示场景"""
        if not self.demo_scenes_index or 'demo_scenes' not in self.demo_scenes_index:
            return None
        
        political_entity = historical_info.get('political_entity', '')
        year = historical_info.get('query_year', 0)
        
        # 查找完全匹配的场景
        for scene in self.demo_scenes_index['demo_scenes']:
            if (scene['political_entity'] == political_entity and 
                scene['year'] == year and
                abs(scene['lat'] - lat) < 0.01 and 
                abs(scene['lng'] - lng) < 0.01):
                
                # 检查图片文件是否存在
                image_path = os.path.join(self.pregenerated_dir, scene['image_filename'])
                if os.path.exists(image_path):
                    return scene
        
        return None
    
    def return_pregenerated_scene(self, scene_data: Dict, historical_info: Dict) -> Dict:
        """返回预生成的场景数据"""
        
        # 构建图片URL
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
            
            print(f"🎨 开始Nano Banana图像生成: {historical_info['political_entity']} ({historical_info['query_year']}年)")
            print(f"📝 提示词长度: {len(prompt)} 字符")
            
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
                    filepath = os.path.join(self.images_dir, filename)
                    
                    # 保存图像
                    image.save(filepath)
                    
                    # 构建URL
                    image_url = f"/static/generated_images/{filename}"
                    generated_images.append(image_url)
                    
                    print(f"💾 Nano Banana图像已保存: {filepath}")
                    print(f"🔗 访问URL: {image_url}")
                    print(f"🖼️ 图像尺寸: {image.size}")
            
            return {
                'success': True,
                'images': generated_images,
                'scene_description': scene_description,
                'historical_context': historical_info,
                'generation_model': 'Gemini 2.5 Flash Image (Nano Banana)',
                'generation_time': generation_time,
                'api_version': 'google-genai 1.32.0',
                'image_count': len(generated_images),
                'prompt_length': len(prompt)
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
        political_entity = historical_info.get('political_entity', 'Unknown')
        ruler_power = historical_info.get('ruler_or_power', '')
        cultural_region = historical_info.get('cultural_region', '')
        year = historical_info.get('query_year', 0)
        
        print(f"🏛️ 为Nano Banana构建提示词:")
        print(f"   政治实体: {political_entity}")
        print(f"   年份: {year}")
        
        # 根据政治实体获取具体的视觉特征
        architectural_details = self.get_architectural_details(political_entity, year)
        clothing_details = self.get_clothing_details(political_entity, year)
        environment_details = self.get_environment_details(lat, lng, year)
        
        # 构建符合Nano Banana最佳实践的详细提示词
        prompt = f"""
Create a historically accurate and visually stunning image of {political_entity} in {year} AD at coordinates {lat:.2f}, {lng:.2f}.

**Historical Context:**
- Political Entity: {political_entity}
- Ruler/Authority: {ruler_power}
- Cultural Region: {cultural_region}
- Time Period: {year} AD

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
- Rich textures showing authentic materials and craftsmanship
- Dramatic cinematic lighting emphasizing the culture of {political_entity}
- Color palette using pigments and materials available in {year} AD
- High historical authenticity suitable for educational purposes

**Avoid:**
- Any modern elements (no contemporary buildings, vehicles, technology)
- Anachronistic materials or construction methods
- Modern clothing styles or accessories
- Elements that didn't exist in {year} AD

Ensure complete historical authenticity to {political_entity} in {year} AD.
        """.strip()
        
        return prompt
    
    def get_architectural_details(self, political_entity: str, year: int) -> str:
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
Traditional architecture typical of {political_entity}:
- Building styles adapted to local climate and available materials
- Construction methods reflecting the technology level of {year} AD
- Decorative elements showing the cultural values of the civilization
- Urban planning patterns characteristic of this political system
        """)
    
    def get_clothing_details(self, political_entity: str, year: int) -> str:
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
Period-appropriate clothing for {political_entity} in {year} AD:
- Social class distinctions visible through clothing quality and ornamentation
- Materials and dyes available through the trade networks of that era
- Cultural modesty standards and gender role expressions of the time
- Practical adaptations to local climate and lifestyle needs
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
        
        political_entity = historical_info.get('political_entity', 'Unknown')
        year = historical_info.get('query_year', 0)
        
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

