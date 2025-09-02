# 🏛️ OrientDiscover 历史模式集成方案

## 📋 项目概述

**历史模式功能**将OrientDiscover从普通的地理探索应用升级为**时空探索工具**，用户可以：
- 选择任意年份（公元前3000年 - 现代）
- 输入地理坐标
- 获取该时空点的真实历史政治实体信息
- 通过AI生成该时代的真实历史场景图像
- 获得专业的AI历史文化锐评

## 🎯 核心功能特性

### 1. **时空查询系统**
- 基于 [Historical-basemaps](https://github.com/aourednik/historical-basemaps) 的学术级历史边界数据
- 支持5000年历史跨度的精确政治实体查询
- 真实的历史边界变迁数据

### 2. **AI历史场景生成**
- 集成Google Gemini 2.5 Flash Image (Nano Banana) 最新生图API
- 基于历史数据生成文化准确的场景图像
- 支持对话式场景优化和细节调整

### 3. **智能历史分析**
- AI驱动的历史文化背景分析
- 专业的历史场景锐评系统
- 教育价值与娱乐性完美结合

## 🏗️ 技术架构设计

### 整体流程架构

```
用户输入：坐标 + 年份
↓
Historical-basemaps数据查询
↓
获取真实历史政治实体信息
├─ 政治实体：Byzantine Empire
├─ 统治者：Emperor Justinian
├─ 文化圈：Christian World
└─ 边界精度：2 (moderately precise)
↓
历史文化特征分析
├─ 建筑风格：Byzantine domed basilicas
├─ 服装特征：Silk robes with gold embroidery
├─ 社会活动：Religious ceremonies, trade
└─ 环境特征：Mediterranean climate
↓
构建Nano Banana提示词
↓
Gemini 2.5 Flash Image生成历史场景
↓
AI历史锐评生成
↓
前端展示完整的时空探索结果
```

## 📊 数据源集成方案

### Historical-basemaps数据获取 

**混合方案（推荐）：智能缓存 + GitHub Raw访问**

#### 1. GitHub Raw文件直接访问
```python
# backend/historical_data_loader.py
import aiohttp
import json
import os
from typing import Dict, List

class HistoricalDataLoader:
    def __init__(self):
        # GitHub raw文件的基础URL
        self.github_raw_base = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson"
        self.cache_dir = "data/historical_cache"
        
        # 可用的历史数据文件映射
        self.available_datasets = {
            2000: "world-2000.geojson",
            1994: "world-1994.geojson", 
            1960: "world-1960.geojson",
            1945: "world-1945.geojson",
            1938: "world-1938.geojson",
            1920: "world-1920.geojson",
            1914: "world-1914.geojson",
            1880: "world-1880.geojson",
            1815: "world-1815.geojson",
            1783: "world-1783.geojson",
            1715: "world-1715.geojson",
            1648: "world-1648.geojson",
            1530: "world-1530.geojson",
            1492: "world-1492.geojson",
            1279: "world-1279.geojson",
            800: "world-800.geojson",
            1000: "world-1000.geojson",
            400: "world-400.geojson",
            -1: "world--1.geojson"  # 公元前1年
        }
    
    async def get_historical_data(self, year: int) -> Dict:
        """获取指定年份的历史边界数据"""
        # 找到最接近的年份数据
        closest_year = self.find_closest_year(year)
        filename = self.available_datasets.get(closest_year)
        
        if not filename:
            raise ValueError(f"没有找到{year}年附近的历史数据")
        
        # 尝试从本地缓存加载
        cached_data = await self.load_from_cache(filename)
        if cached_data:
            return cached_data
        
        # 从GitHub下载数据
        return await self.download_and_cache(filename, closest_year)
    
    async def download_and_cache(self, filename: str, year: int) -> Dict:
        """从GitHub下载GeoJSON文件并缓存"""
        url = f"{self.github_raw_base}/{filename}"
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"🌐 正在从GitHub下载历史数据: {filename}")
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 缓存到本地
                        await self.save_to_cache(filename, data)
                        print(f"✅ 历史数据下载成功: {len(data.get('features', []))} 个政治实体")
                        
                        return data
                    else:
                        raise Exception(f"GitHub数据下载失败: HTTP {response.status}")
        
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return await self.get_fallback_data(year)
    
    def find_closest_year(self, target_year: int) -> int:
        """找到最接近目标年份的可用数据年份"""
        available_years = list(self.available_datasets.keys())
        closest_year = min(available_years, key=lambda x: abs(x - target_year))
        print(f"🎯 目标年份: {target_year}, 使用数据: {closest_year}")
        return closest_year

# 全局实例
historical_data_loader = HistoricalDataLoader()
```

#### 2. 智能历史查询服务
```python
# backend/historical_service.py
from shapely.geometry import Point, shape
from typing import Dict, List, Optional

class HistoricalService:
    def __init__(self):
        self.data_loader = HistoricalDataLoader()
    
    async def query_historical_location(self, lat: float, lng: float, year: int) -> Dict:
        """
        根据坐标和年份查询历史政治实体
        
        Args:
            lat: 纬度
            lng: 经度
            year: 年份
            
        Returns:
            Dict: 历史位置信息
        """
        print(f"🔍 查询历史位置: ({lat:.4f}, {lng:.4f}) at {year} AD")
        
        # 获取历史数据
        historical_data = await self.data_loader.get_historical_data(year)
        
        # 在历史边界中查找包含此点的政治实体
        result = self.find_political_entity_in_boundaries(historical_data, lat, lng, year)
        
        return result
    
    def find_political_entity_in_boundaries(self, geojson_data: Dict, lat: float, lng: float, year: int) -> Dict:
        """在GeoJSON边界数据中查找包含指定坐标的政治实体"""
        query_point = Point(lng, lat)  # 注意Shapely使用(lng, lat)
        
        for feature in geojson_data.get('features', []):
            try:
                # 创建多边形几何
                polygon = shape(feature['geometry'])
                
                # 检查点是否在多边形内
                if polygon.contains(query_point):
                    properties = feature.get('properties', {})
                    
                    return self.format_historical_result(properties, year, lat, lng)
                    
            except Exception as e:
                continue  # 跳过有问题的几何图形
        
        # 如果没找到精确匹配，返回最近的实体
        return self.find_nearest_historical_entity(geojson_data, lat, lng, year)
    
    def format_historical_result(self, properties: Dict, year: int, lat: float, lng: float) -> Dict:
        """格式化历史查询结果"""
        political_entity = properties.get('NAME', '未知政治实体')
        ruler_power = properties.get('SUBJECTO', '')
        cultural_region = properties.get('PARTOF', '')
        
        return {
            'success': True,
            'political_entity': political_entity,
            'ruler_or_power': ruler_power,
            'cultural_region': cultural_region,
            'border_precision': properties.get('BORDERPRECISION', 1),
            'query_year': year,
            'coordinates': {'lat': lat, 'lng': lng},
            'description': self.generate_historical_description(properties, year),
            'time_period': self.classify_time_period(year),
            'cultural_context': self.get_cultural_context(properties, year)
        }
    
    def generate_historical_description(self, properties: Dict, year: int) -> str:
        """生成历史场景描述"""
        name = properties.get('NAME', '未知地区')
        ruler = properties.get('SUBJECTO', '')
        cultural = properties.get('PARTOF', '')
        
        # 根据时期生成描述
        if year > 1800:
            era = "近现代时期"
            context = "工业革命浪潮下的"
        elif year > 1500:
            era = "大航海时代"
            context = "全球贸易兴起中的"  
        elif year > 1000:
            era = "中世纪"
            context = "封建制度下的"
        elif year > 0:
            era = "古典时期"
            context = "古代文明的"
        else:
            era = "远古时期" 
            context = "早期文明的"
            
        description = f"{era}({year}年)，这里是{context}{name}"
        
        if ruler and ruler != name:
            description += f"，受{ruler}统治"
        
        if cultural:
            description += f"，属于{cultural}文化圈"
            
        return description

# 全局实例
historical_service = HistoricalService()
```

## 🎨 AI图像生成集成

### Gemini 2.5 Flash Image (Nano Banana) 集成

```python
# backend/historical_image_service.py
from google import genai
import os
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, Optional, List
import time

class HistoricalImageGenerationService:
    def __init__(self):
        # 配置新版Gemini API
        self.client = genai.Client()
        
        # 历史文化特征数据库
        self.culture_database = {
            'architectural_styles': {
                'Byzantine Empire': {
                    'description': 'Byzantine architecture with massive domed basilicas, intricate mosaics, marble columns with elaborate capitals, gold leaf decorations',
                    'key_features': ['Hagia Sophia-style domes', 'Christian iconography', 'marble and gold decorations', 'cross-shaped floor plans'],
                    'materials': 'limestone, marble, gold leaf, colored glass mosaics'
                },
                'Ottoman Empire': {
                    'description': 'Ottoman Islamic architecture featuring pointed minarets, large central courtyards, geometric tile patterns, horseshoe arches',
                    'key_features': ['tall minarets', 'geometric patterns', 'courtyards with fountains', 'Islamic calligraphy'],
                    'materials': 'stone, ceramic tiles, wood with mother-of-pearl inlay'
                },
                'Roman Empire': {
                    'description': 'Classical Roman architecture with marble columns, basilicas, amphitheaters, aqueducts, and tessellated floors',
                    'key_features': ['Corinthian columns', 'barrel vaults', 'Roman arches', 'public baths and forums'],
                    'materials': 'white marble, travertine stone, brick and concrete'
                },
                'Tang Dynasty': {
                    'description': 'Chinese Tang Dynasty architecture with wooden pagodas, traditional courtyard houses, upturned eaves, colorful brackets',
                    'key_features': ['multi-story pagodas', 'wooden post-and-beam construction', 'traditional Chinese gardens', 'ceramic tile roofs'],
                    'materials': 'wood, ceramic tiles, stone foundations, paper windows'
                }
                # ... 可扩展更多历史政治实体
            },
            
            'clothing_styles': {
                'Christian World': {
                    'noble': 'Rich Byzantine silk robes with gold embroidery, jeweled crowns, purple dye indicating high status',
                    'common': 'Simple woolen tunics, leather belts, wooden shoes, linen undergarments',
                    'religious': 'Monastic robes in brown or black, religious medallions, tonsured hairstyles'
                },
                'Islamic World': {
                    'noble': 'Flowing silk caftans with intricate geometric embroidery, turbans with jewels, pointed shoes',
                    'common': 'Cotton tunics and trousers, simple head coverings, leather sandals',
                    'religious': 'White prayer robes, skull caps, prayer beads'
                },
                'Chinese Civilization': {
                    'noble': 'Silk robes with dragon motifs, elaborate headdresses, jade accessories, embroidered shoes',
                    'common': 'Cotton or hemp garments, simple tunics, straw sandals, practical work clothes',
                    'religious': 'Buddhist monk robes in saffron or gray, prayer beads, shaved heads'
                }
                # ... 可扩展更多文化圈
            }
        }
    
    async def generate_historical_scene(self, historical_info: Dict, lat: float, lng: float) -> Dict:
        """
        使用Gemini 2.5 Flash Image (Nano Banana) 生成历史场景
        """
        try:
            # 构建基于真实历史数据的详细提示词
            prompt = await self.create_historical_prompt_from_real_data(historical_info, lat, lng)
            
            print(f"🎨 开始生成历史场景图像: {historical_info['political_entity']} ({historical_info['query_year']}年)")
            
            # 调用最新的Gemini图像生成API
            response = await self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",  # Nano Banana 模型
                contents=[prompt],
            )
            
            generated_images = []
            scene_description = ""
            
            # 处理返回结果
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    scene_description = part.text
                    print(f"📝 场景描述: {scene_description[:100]}...")
                
                elif part.inline_data is not None:
                    # 保存生成的图像
                    image = Image.open(BytesIO(part.inline_data.data))
                    
                    # 创建唯一的文件名
                    timestamp = int(time.time())
                    entity_name = historical_info['political_entity'].replace(' ', '_').replace('/', '_')
                    filename = f"historical_scene_{entity_name}_{historical_info['query_year']}_{timestamp}.png"
                    filepath = f"static/generated_images/{filename}"
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    image.save(filepath)
                    
                    # 构建访问URL
                    image_url = f"/static/generated_images/{filename}"
                    generated_images.append(image_url)
                    
                    print(f"💾 图像已保存: {image_url}")
            
            return {
                'success': True,
                'images': generated_images,
                'scene_description': scene_description,
                'historical_context': historical_info,
                'generation_model': 'Gemini 2.5 Flash Image (Nano Banana)',
                'generation_time': time.time(),
                'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
            
        except Exception as e:
            print(f"❌ 图像生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_description': self.create_fallback_description(historical_info)
            }
    
    async def create_historical_prompt_from_real_data(self, historical_info: Dict, lat: float, lng: float) -> str:
        """
        🔑 基于Historical-basemaps的真实数据创建提示词
        """
        # 从Historical-basemaps获取的真实历史数据
        political_entity = historical_info.get('political_entity', 'Unknown')
        ruler_power = historical_info.get('ruler_or_power', '')
        cultural_region = historical_info.get('cultural_region', '')
        year = historical_info.get('query_year', 0)
        
        print(f"🏛️ 基于真实历史数据生成场景:")
        print(f"   政治实体: {political_entity}")
        print(f"   统治者: {ruler_power}")  
        print(f"   文化圈: {cultural_region}")
        print(f"   年份: {year}")
        
        # 根据真实历史实体获取建筑风格
        architectural_style = self.get_architectural_style_from_entity(
            political_entity, ruler_power, cultural_region, year
        )
        
        # 根据文化圈获取服装风格
        clothing_style = self.get_clothing_style_from_culture(
            cultural_region, political_entity, year
        )
        
        # 根据坐标和历史时期获取环境特征
        environmental_features = self.get_historical_environment(
            lat, lng, year, political_entity
        )
        
        # 根据政治制度获取社会活动
        social_activities = self.get_social_activities_from_system(
            political_entity, ruler_power, year
        )
        
        # 构建历史准确的详细提示词
        prompt = f"""
Create a historically accurate and visually stunning scene of {political_entity} in {year} AD at coordinates {lat:.2f}, {lng:.2f}.

**Historical Authentication:**
- Political Entity: {political_entity}
- Ruler/Authority: {ruler_power}
- Cultural Region: {cultural_region}  
- Historical Period: {historical_info.get('time_period', 'Ancient')}

**Architecture & Built Environment:**
{architectural_style}

**People & Clothing:**
{clothing_style}

**Natural Environment:**
{environmental_features}

**Social & Cultural Activities:**
{social_activities}

**Visual Composition Requirements:**
- Wide-angle shot capturing both architectural grandeur and human activity
- Atmospheric lighting appropriate to the geographic location and season
- 4-6 people in historically accurate clothing representing different social classes
- Show the interaction between built environment and daily life
- Include period-appropriate tools, transportation, and objects
- Demonstrate the power and culture of {political_entity}

**Historical Accuracy Standards:**
- All architectural details must match {political_entity} construction methods from {year} AD
- Clothing and accessories must reflect {cultural_region} traditions of that era
- Social hierarchies and gender roles appropriate to the historical context
- No anachronistic elements from later periods
- Materials and technology available in {year} AD only

**Art Style & Quality:**
- Photorealistic historical illustration with cinematic quality
- Rich textures showing authentic materials and craftsmanship
- Dramatic lighting emphasizing the grandeur of {political_entity}
- Color palette reflecting pigments and materials available in {year} AD
- High detail and historical authenticity
- Professional museum-quality visualization

Ensure complete historical authenticity to {political_entity} in {year} AD. This image should be suitable for educational purposes and historical documentation.
        """.strip()
        
        return prompt
    
    def get_architectural_style_from_entity(self, political_entity: str, ruler_power: str, cultural_region: str, year: int) -> str:
        """根据Historical-basemaps的具体政治实体返回建筑风格"""
        
        # 优先匹配具体的政治实体
        if political_entity in self.culture_database['architectural_styles']:
            style_data = self.culture_database['architectural_styles'][political_entity]
            
            features_list = ', '.join(style_data['key_features'])
            
            return f"""
{style_data['description']}

Key Architectural Features:
- {features_list}
- Construction materials: {style_data['materials']}
- Typical structures: palaces, religious buildings, public spaces representative of {political_entity}
- Architectural scale and grandeur reflecting the power of {ruler_power if ruler_power else political_entity}
            """.strip()
        
        # 如果没有精确匹配，根据文化圈和时期推断
        else:
            return self.infer_architectural_style_from_culture(political_entity, cultural_region, year)
    
    def infer_architectural_style_from_culture(self, political_entity: str, cultural_region: str, year: int) -> str:
        """当数据库中没有精确匹配时，根据文化圈和时期进行推断"""
        
        # 根据文化圈的关键词匹配
        if any(keyword in cultural_region.lower() for keyword in ['christian', 'byzantine', 'orthodox']):
            base_style = "Christian Byzantine-influenced architecture"
            features = "domed churches, religious mosaics, stone construction with Christian iconography"
        elif any(keyword in cultural_region.lower() for keyword in ['islamic', 'muslim', 'arab']):
            base_style = "Islamic architectural traditions"  
            features = "geometric patterns, courtyards, minarets, pointed arches, Islamic calligraphy"
        elif any(keyword in cultural_region.lower() for keyword in ['chinese', 'han', 'tang', 'ming']):
            base_style = "Traditional Chinese architecture"
            features = "wooden post-and-beam construction, curved roofs, courtyards, pagodas"
        elif any(keyword in cultural_region.lower() for keyword in ['roman', 'latin']):
            base_style = "Classical Roman architecture"
            features = "marble columns, basilicas, aqueducts, forums, Roman engineering"
        else:
            # 通用古代建筑风格
            base_style = f"Traditional architecture of {political_entity}"
            features = "local materials adapted to climate, vernacular building methods of the region"
        
        # 根据时期调整风格复杂度
        if year < 500:
            period_modifier = "with simpler, more primitive construction techniques"
        elif year < 1000:
            period_modifier = "showing early medieval building methods" 
        elif year < 1500:
            period_modifier = "displaying medieval architectural sophistication"
        else:
            period_modifier = "with renaissance or early modern refinements"
        
        return f"""
{base_style} {period_modifier}

Architectural characteristics typical of {political_entity}:
- {features}
- Building scale and decoration reflecting the political and economic power of the era
- Materials and construction methods available in {year} AD
- Urban planning and settlement patterns characteristic of this civilization
        """.strip()
    
    def get_clothing_style_from_culture(self, cultural_region: str, political_entity: str, year: int) -> str:
        """根据文化圈和政治实体返回服装风格"""
        
        if cultural_region in self.culture_database['clothing_styles']:
            style_data = self.culture_database['clothing_styles'][cultural_region]
            
            return f"""
Show people wearing clothing authentic to {cultural_region} in {year} AD:

Social Classes Represented:
- Noble/Elite Class: {style_data['noble']}
- Common People: {style_data['common']}
- Religious Figures: {style_data.get('religious', 'Simple religious garments appropriate to the faith')}

All clothing should reflect the textile technologies, dyes, and fashion conventions of {political_entity} during this historical period.
            """.strip()
        else:
            return self.infer_clothing_style(cultural_region, political_entity, year)
    
    def get_historical_environment(self, lat: float, lng: float, year: int, political_entity: str) -> str:
        """根据地理位置和历史时期获取环境特征"""
        
        # 基于纬度判断气候带
        if lat > 60:
            climate = "Northern boreal landscape with coniferous forests, shorter growing season"
        elif lat > 35:
            climate = "Temperate climate with deciduous and mixed forests, four distinct seasons"
        elif lat > 23:
            climate = "Subtropical environment with varied vegetation, longer growing seasons"
        else:
            climate = "Tropical or arid landscape with appropriate native vegetation"
        
        # 考虑历史时期的环境差异
        if year < 1800:
            environmental_context = f"{climate}, pristine natural environment with minimal human impact, abundant wildlife, clear rivers and streams"
        else:
            environmental_context = f"{climate}, showing early agricultural modification but still largely natural"
        
        return f"""
Natural environment as it would have appeared in {year} AD:
- {environmental_context}
- Landscape features showing the geographic setting where {political_entity} flourished
- Seasonal characteristics appropriate to the latitude {lat:.1f}°
- Flora and fauna typical of the region before modern environmental changes
        """
    
    def get_social_activities_from_system(self, political_entity: str, ruler_power: str, year: int) -> str:
        """根据政治制度和时期获取社会活动"""
        
        if year >= 1500:
            activities = "People engaged in trade and craftsmanship: merchants examining goods, artisans working with tools, farmers with advanced techniques"
        elif year >= 1000:
            activities = "Medieval daily life: blacksmiths at forges, women spinning thread, farmers with oxen, religious ceremonies"
        elif year >= 0:
            activities = "Ancient civilization activities: scholars and scribes, religious rituals, military training, public gatherings"
        else:
            activities = "Early civilization activities: tribal gatherings, primitive craftsmanship, early agriculture, community rituals"
        
        return f"""
Daily life and social activities typical of {political_entity}:
- {activities}
- Social interactions reflecting the political system under {ruler_power if ruler_power else 'local leadership'}
- Cultural and religious practices characteristic of this civilization
- Economic activities and trade appropriate to the historical period
- Demonstration of social hierarchies and power structures of the era
        """

# 全局实例
historical_image_service = HistoricalImageGenerationService()
```

### 场景优化功能

```python
async def refine_historical_scene(self, previous_image_url: str, refinement_request: str, historical_info: Dict) -> Dict:
    """
    利用Nano Banana的迭代优化能力来精细调整历史场景
    """
    try:
        # 读取之前生成的图像
        previous_image_path = previous_image_url.replace('/static/', 'static/')
        with open(previous_image_path, 'rb') as f:
            image_data = f.read()
        
        # 构建编辑提示词
        edit_prompt = f"""
Take this historical scene of {historical_info['political_entity']} from {historical_info['query_year']} AD and make the following adjustment:

{refinement_request}

Keep all other historical details accurate and maintain the same time period and cultural context. Ensure the modification enhances historical authenticity.
        """
        
        # 调用图像编辑功能
        response = await self.client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[
                edit_prompt,
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(image_data).decode()
                    }
                }
            ],
        )
        
        # 处理编辑结果
        refined_images = []
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # 保存编辑后的图像
                image = Image.open(BytesIO(part.inline_data.data))
                
                timestamp = int(time.time())
                entity_name = historical_info['political_entity'].replace(' ', '_')
                filename = f"refined_scene_{entity_name}_{timestamp}.png"
                filepath = f"static/generated_images/{filename}"
                
                image.save(filepath)
                refined_images.append(f"/static/generated_images/{filename}")
        
        return {
            'success': True,
            'refined_image_url': refined_images[0] if refined_images else None,
            'refinement_applied': refinement_request
        }
        
    except Exception as e:
        print(f"❌ 图像编辑失败: {e}")
        return {'success': False, 'error': str(e)}
```

## 🔧 API端点实现

### 后端API集成

```python
# 在 backend/main.py 中添加
from historical_service import historical_service
from historical_image_service import historical_image_service

class HistoricalExploreRequest(BaseModel):
    latitude: float
    longitude: float
    year: int
    heading: float = 0
    segment_distance: int = 10

class RefineHistoricalRequest(BaseModel):
    image_url: str
    refinement_request: str
    historical_info: Dict

@app.post("/api/explore-historical")
async def explore_historical_location(request: HistoricalExploreRequest):
    """历史模式探索API - 完整的时空探索功能"""
    start_time = time.time()
    
    try:
        print(f"🏛️ 历史探索请求: {request.year}年 ({request.latitude}, {request.longitude})")
        
        # 1. 查询Historical-basemaps获取真实历史位置信息
        historical_info = await historical_service.query_historical_location(
            request.latitude, request.longitude, request.year
        )
        
        if not historical_info['success']:
            raise HTTPException(status_code=404, detail="未找到该时空点的历史信息")
        
        # 2. 使用Nano Banana生成历史场景图像
        scene_generation_result = await historical_image_service.generate_historical_scene(
            historical_info, request.latitude, request.longitude
        )
        
        # 3. 生成AI历史场景锐评
        historical_review = await generate_historical_scene_review(
            historical_info, scene_generation_result
        )
        
        response_data = {
            'success': True,
            'historical_info': historical_info,
            'generated_scene': scene_generation_result,
            'ai_review': historical_review,
            'calculation_time': time.time() - start_time,
            'model_used': 'Gemini 2.5 Flash Image (Nano Banana)',
            'data_source': 'Historical-basemaps (GitHub)'
        }
        
        print(f"✅ 历史探索完成: {historical_info['political_entity']} ({request.year})")
        return response_data
        
    except Exception as e:
        print(f"❌ 历史探索失败: {e}")
        raise HTTPException(status_code=500, detail=f"历史场景生成失败: {str(e)}")

@app.post("/api/refine-historical-scene")
async def refine_historical_scene(request: RefineHistoricalRequest):
    """历史场景精细调整API - 利用Nano Banana的对话式编辑能力"""
    try:
        print(f"🎨 场景调整请求: {request.refinement_request}")
        
        result = await historical_image_service.refine_historical_scene(
            request.image_url, 
            request.refinement_request,
            request.historical_info
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"场景调整失败: {str(e)}")

async def generate_historical_scene_review(historical_info: Dict, scene_result: Dict) -> Dict:
    """生成AI历史场景锐评"""
    
    try:
        # 构建历史锐评提示词
        review_prompt = f"""
作为一名专业的历史学家和文化评论专家，请对以下历史场景进行深度锐评：

历史背景：
- 政治实体：{historical_info['political_entity']}
- 统治者：{historical_info.get('ruler_or_power', '未知')}
- 文化圈：{historical_info['cultural_region']}
- 年份：{historical_info['query_year']}年
- 地理位置：{historical_info['coordinates']['lat']}, {historical_info['coordinates']['lng']}

场景描述：
{scene_result.get('scene_description', '历史场景已生成')}

请从以下角度进行专业锐评：
1. 历史准确性评估
2. 文化特征分析
3. 社会结构解读
4. 艺术风格特点
5. 教育价值评价

要求：
- 语言专业且易懂
- 融入历史知识
- 突出文化内涵
- 具有教育启发性
- 字数控制在200-300字
        """
        
        # 调用AI服务生成锐评
        ai_service = get_ai_service()
        review_response = await ai_service.generate_review(review_prompt)
        
        return {
            'title': f"穿越时空：{historical_info['political_entity']}的{historical_info['query_year']}年",
            'review': review_response,
            'historical_context': historical_info,
            'review_type': 'historical_scene_analysis',
            'generation_time': time.time()
        }
        
    except Exception as e:
        print(f"❌ 历史锐评生成失败: {e}")
        return {
            'title': f"历史探索：{historical_info['political_entity']}",
            'review': f"您探索了{historical_info['query_year']}年的{historical_info['political_entity']}，这个时代充满了独特的文化魅力和历史价值。通过AI生成的场景，我们得以一窥那个时代的建筑风格、社会生活和文化特色。",
            'fallback': True
        }
```

## 🎨 前端UI设计

### 历史模式选择器

```html
<!-- 在预设地址选择器下方添加历史模式面板 -->
<div class="historical-mode-panel" id="historicalModePanel" style="display: none;">
    <div class="historical-header">
        <span class="historical-label">⏰ 时光机模式</span>
        <button class="historical-toggle" onclick="toggleHistoricalMode()">
            🕰️ 启用历史探索
        </button>
    </div>
    
    <div class="historical-controls" id="historicalControls" style="display: none;">
        <div class="time-period-selector">
            <label>📅 选择历史时期:</label>
            <select id="historicalPeriod" onchange="updateHistoricalYear()">
                <option value="">选择历史时期...</option>
                <option value="2000">现代 (2000年)</option>
                <option value="1945">二战后 (1945年)</option>
                <option value="1914">一战前 (1914年)</option>
                <option value="1880">工业革命 (1880年)</option>
                <option value="1815">拿破仑战争后 (1815年)</option>
                <option value="1648">威斯特伐利亚和约 (1648年)</option>
                <option value="1492">大航海时代 (1492年)</option>
                <option value="1279">元朝建立 (1279年)</option>
                <option value="800">查理大帝加冕 (800年)</option>
                <option value="400">罗马帝国分裂 (400年)</option>
                <option value="-1">古典时期 (公元前1年)</option>
                <option value="custom">自定义年份...</option>
            </select>
        </div>
        
        <div class="custom-year-input" id="customYearDiv" style="display: none;">
            <label>🎯 自定义年份:</label>
            <input type="number" id="customYearInput" placeholder="输入年份" 
                   min="-3000" max="2024" value="1000">
            <span class="year-hint">（公元前年份请输入负数）</span>
        </div>
        
        <div class="historical-info-display" id="historicalInfoDisplay">
            <div class="selected-year">
                <span class="label">🗓️ 探索年份:</span>
                <span id="selectedYear">未选择</span>
            </div>
        </div>
        
        <button class="time-travel-btn" id="timeTravelBtn" onclick="startHistoricalExploration()" disabled>
            🚀 开始时空探索
        </button>
    </div>
</div>
```

### JavaScript交互逻辑

```javascript
// 历史模式相关功能
let isHistoricalMode = false;
let selectedHistoricalYear = null;

function toggleHistoricalMode() {
    const panel = document.getElementById('historicalModePanel');
    const controls = document.getElementById('historicalControls');
    const toggleBtn = document.querySelector('.historical-toggle');
    
    isHistoricalMode = !isHistoricalMode;
    
    if (isHistoricalMode) {
        controls.style.display = 'block';
        toggleBtn.textContent = '🌍 常规探索模式';
        toggleBtn.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        logger.info('✅ 已切换到历史模式');
        showSuccess('🏛️ 历史模式已启用！选择时期开始时空探索');
    } else {
        controls.style.display = 'none';
        toggleBtn.textContent = '🕰️ 启用历史探索';
        toggleBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        logger.info('📍 已切换到常规模式');
        showSuccess('🌍 已返回常规探索模式');
    }
}

function updateHistoricalYear() {
    const periodSelect = document.getElementById('historicalPeriod');
    const customYearDiv = document.getElementById('customYearDiv');
    const selectedYearSpan = document.getElementById('selectedYear');
    const timeTravelBtn = document.getElementById('timeTravelBtn');
    
    const selectedValue = periodSelect.value;
    
    if (selectedValue === 'custom') {
        customYearDiv.style.display = 'block';
        selectedYearSpan.textContent = '自定义年份';
        selectedHistoricalYear = null;
        timeTravelBtn.disabled = true;
    } else if (selectedValue) {
        customYearDiv.style.display = 'none';
        selectedHistoricalYear = parseInt(selectedValue);
        
        if (selectedHistoricalYear < 0) {
            selectedYearSpan.textContent = `公元前${Math.abs(selectedHistoricalYear)}年`;
        } else {
            selectedYearSpan.textContent = `公元${selectedHistoricalYear}年`;
        }
        
        timeTravelBtn.disabled = false;
        logger.info(`📅 选择历史年份: ${selectedHistoricalYear}`);
    } else {
        customYearDiv.style.display = 'none';
        selectedYearSpan.textContent = '未选择';
        selectedHistoricalYear = null;
        timeTravelBtn.disabled = true;
    }
}

// 自定义年份输入处理
document.addEventListener('DOMContentLoaded', function() {
    const customYearInput = document.getElementById('customYearInput');
    
    if (customYearInput) {
        customYearInput.addEventListener('input', function() {
            const year = parseInt(this.value);
            const selectedYearSpan = document.getElementById('selectedYear');
            const timeTravelBtn = document.getElementById('timeTravelBtn');
            
            if (!isNaN(year) && year >= -3000 && year <= 2024) {
                selectedHistoricalYear = year;
                
                if (year < 0) {
                    selectedYearSpan.textContent = `公元前${Math.abs(year)}年`;
                } else {
                    selectedYearSpan.textContent = `公元${year}年`;
                }
                
                timeTravelBtn.disabled = false;
            } else {
                selectedHistoricalYear = null;
                selectedYearSpan.textContent = '无效年份';
                timeTravelBtn.disabled = true;
            }
        });
    }
});

async function startHistoricalExploration() {
    if (!currentPosition) {
        showError('请先选择位置或获取当前位置');
        return;
    }
    
    if (!selectedHistoricalYear) {
        showError('请先选择历史年份');
        return;
    }
    
    logger.info(`🏛️ 开始历史探索: ${selectedHistoricalYear}年`);
    logger.info(`📍 探索坐标: ${currentPosition.latitude}, ${currentPosition.longitude}`);
    
    showLoading(true, '正在穿越时空，探索历史场景...');
    
    try {
        const requestData = {
            latitude: currentPosition.latitude,
            longitude: currentPosition.longitude,
            year: selectedHistoricalYear,
            heading: currentHeading || 0,
            segment_distance: settings.segmentDistance
        };
        
        const response = await fetch('/api/explore-historical', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            logger.success(`🎉 时空探索成功！发现：${data.historical_info.political_entity}`);
            displayHistoricalScene(data);
        } else {
            throw new Error('历史探索返回失败结果');
        }
        
    } catch (error) {
        logger.error(`❌ 时空探索失败: ${error.message}`);
        showError(`时空探索失败: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function displayHistoricalScene(data) {
    const container = document.getElementById('placesContainer');
    
    if (!container) {
        logger.error('❌ 找不到显示容器');
        return;
    }
    
    const historicalInfo = data.historical_info;
    const sceneData = data.generated_scene;
    const aiReview = data.ai_review;
    
    const sceneHtml = `
        <div class="historical-scene-container">
            <!-- 历史信息卡片 -->
            <div class="historical-info-card">
                <div class="info-header">
                    <h2>🏛️ ${historicalInfo.political_entity}</h2>
                    <div class="year-badge">${historicalInfo.query_year}年</div>
                </div>
                
                <div class="historical-details">
                    <div class="detail-row">
                        <span class="label">👑 统治者:</span>
                        <span class="value">${historicalInfo.ruler_or_power || '未知'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">🌍 文化圈:</span>
                        <span class="value">${historicalInfo.cultural_region}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">📍 坐标:</span>
                        <span class="value">${historicalInfo.coordinates.lat.toFixed(4)}, ${historicalInfo.coordinates.lng.toFixed(4)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">📊 边界精度:</span>
                        <span class="value">${getPrecisionText(historicalInfo.border_precision)}</span>
                    </div>
                </div>
                
                <div class="historical-description">
                    <p>${historicalInfo.description}</p>
                </div>
            </div>
            
            <!-- AI生成的历史场景图 -->
            ${sceneData.success ? `
                <div class="generated-scene-card">
                    <div class="scene-header">
                        <h3>🎨 AI重现历史场景</h3>
                        <span class="generation-model">✨ Powered by Nano Banana</span>
                    </div>
                    
                    <div class="scene-image-container">
                        <img src="${sceneData.images[0]}" 
                             alt="Historical scene of ${historicalInfo.political_entity}" 
                             class="historical-scene-image"
                             onclick="openHistoricalImageModal('${sceneData.images[0]}', '${historicalInfo.political_entity}', '${historicalInfo.query_year}')">
                        <div class="image-watermark">🔒 SynthID Protected</div>
                        <div class="image-overlay">
                            <span class="zoom-hint">🔍 点击查看大图</span>
                        </div>
                    </div>
                    
                    <div class="scene-description">
                        <h4>📝 场景解析</h4>
                        <p>${sceneData.scene_description}</p>
                    </div>
                    
                    <!-- 场景优化控制 -->
                    <div class="scene-refinement">
                        <h4>🎨 场景调整</h4>
                        <div class="refinement-input-group">
                            <input type="text" id="refinementInput" 
                                   placeholder="如：让光线更暖一些，添加更多历史细节...">
                            <button onclick="refineHistoricalScene('${sceneData.images[0]}')">
                                ✨ 优化场景
                            </button>
                        </div>
                        
                        <div class="refinement-suggestions">
                            <span class="suggestion-label">💡 建议调整:</span>
                            <button class="suggestion-btn" onclick="quickRefine('让建筑更宏伟一些')">🏛️ 建筑更宏伟</button>
                            <button class="suggestion-btn" onclick="quickRefine('添加更多人物活动')">👥 增加人物</button>
                            <button class="suggestion-btn" onclick="quickRefine('让色彩更丰富历史感更强')">🎨 增强历史感</button>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="scene-error-card">
                    <h3>❌ 场景生成失败</h3>
                    <p>${sceneData.error}</p>
                    <button onclick="retryHistoricalScene()">🔄 重新生成</button>
                </div>
            `}
            
            <!-- AI历史锐评 -->
            <div class="historical-review-card">
                <div class="review-header">
                    <h3>🤖 AI历史文化锐评</h3>
                </div>
                <div class="review-content">
                    <h4>${aiReview.title}</h4>
                    <div class="review-text">
                        ${aiReview.review}
                    </div>
                </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="historical-actions">
                <button class="action-btn primary" onclick="saveHistoricalScene(data)">
                    💾 保存历史探索
                </button>
                <button class="action-btn secondary" onclick="shareHistoricalScene(data)">
                    📤 分享发现
                </button>
                <button class="action-btn" onclick="exploreNearbyHistoricalPeriod()">
                    ⏰ 探索其他时期
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = sceneHtml;
    
    // 滚动到结果
    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// 历史场景优化功能
async function refineHistoricalScene(imageUrl) {
    const refinementInput = document.getElementById('refinementInput');
    const refinementRequest = refinementInput.value.trim();
    
    if (!refinementRequest) {
        showError('请输入优化要求');
        return;
    }
    
    showLoading(true, '正在优化历史场景...');
    
    try {
        const response = await fetch('/api/refine-historical-scene', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                image_url: imageUrl,
                refinement_request: refinementRequest,
                historical_info: currentHistoricalInfo  // 需要全局保存当前历史信息
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 更新显示的图像
            document.querySelector('.historical-scene-image').src = result.refined_image_url;
            showSuccess('✨ 历史场景优化完成！');
            refinementInput.value = ''; // 清空输入框
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        showError('场景优化失败：' + error.message);
    } finally {
        hideLoading();
    }
}

// 快速优化建议
function quickRefine(suggestion) {
    document.getElementById('refinementInput').value = suggestion;
}

// 辅助函数
function getPrecisionText(precision) {
    switch(precision) {
        case 1: return '大致边界';
        case 2: return '中等精度';
        case 3: return '国际法确定';
        default: return '未知精度';
    }
}

// 全局变量保存当前历史信息
let currentHistoricalInfo = null;

// 修改displayHistoricalScene函数，保存历史信息到全局变量
function displayHistoricalScene(data) {
    currentHistoricalInfo = data.historical_info;
    // ... 其他代码保持不变
}
```

## 💰 成本分析与预算

### Gemini Nano Banana定价

**图像生成成本：**
- 每张图片：1,290 tokens (固定)
- 价格：$30 per 1M tokens
- **单张历史场景图：约 $0.039 (¥0.28)**

**使用量预估：**
```
日使用量预估：
- 历史探索：30次/天 × $0.039 = $1.17/天
- 场景优化：15次/天 × $0.039 = $0.585/天
- 总计：约 $1.76/天 (¥12.6/天)

月成本预估：
- 月度总计：约 $53 (¥380)
- 相比DALL-E 3便宜约50%
```

### Historical-basemaps数据成本

**GitHub访问成本：**
- ✅ **完全免费**（开源项目）
- ✅ 无API调用限制
- ✅ 实时更新数据

**存储成本：**
- 本地缓存：约100MB历史数据
- 生成图片存储：每月约2GB (按30天×20张×3MB计算)

### 总成本预估

| 项目 | 月成本 | 年成本 |
|------|--------|--------|
| Gemini Nano Banana | $53 | $636 |
| 数据存储 | $2 | $24 |
| 带宽费用 | $5 | $60 |
| **总计** | **$60** | **$720** |

## 🚀 实施计划

### Phase 1: 基础架构开发 (2-3周)

**Week 1:**
- ✅ 集成Historical-basemaps数据获取
- ✅ 实现历史边界查询功能
- ✅ 创建基础的历史服务API

**Week 2:**  
- ✅ 集成Gemini Nano Banana图像生成
- ✅ 实现历史文化特征数据库
- ✅ 创建提示词生成逻辑

**Week 3:**
- ✅ 完成前端历史模式UI
- ✅ 实现AI历史锐评功能
- ✅ 基础功能测试和调试

### Phase 2: 功能完善和优化 (2-3周)

**Week 4:**
- ✅ 实现场景优化和迭代功能
- ✅ 添加历史准确性验证机制
- ✅ 优化数据缓存和性能

**Week 5:**
- ✅ 扩展历史文化知识库
- ✅ 完善错误处理和降级机制
- ✅ 添加用户引导和帮助文档

**Week 6:**
- ✅ 全面功能测试
- ✅ 性能优化和成本控制
- ✅ 用户体验测试

### Phase 3: 测试和发布 (1-2周)

**Week 7:**
- ✅ 历史准确性验证测试
- ✅ 全球各地历史数据测试
- ✅ API性能和稳定性测试

**Week 8:**
- ✅ 用户接受测试
- ✅ 最终优化和Bug修复
- ✅ 正式发布历史模式功能

## 🎯 预期效果和价值

### 用户体验提升

**独特价值主张：**
- 🌍 **全球首创**：真正的4D时空探索应用
- 🎓 **教育价值**：寓教于乐的历史地理学习
- 🎨 **视觉震撼**：AI生成的历史场景重现
- 📚 **学术准确**：基于权威历史边界数据

### 技术创新点

1. **Historical-basemaps + AI生图**：首次将学术历史数据与AI图像生成结合
2. **时空查询系统**：支持任意时空点的历史查询
3. **文化智能分析**：AI驱动的历史文化特征识别
4. **对话式优化**：基于Nano Banana的场景迭代改进

### 商业价值

**目标用户群体：**
- 📚 教育机构和历史爱好者
- 🎮 历史题材游戏玩家  
- 🏛️ 文化旅游从业者
- 🎨 内容创作者和研究人员

**市场差异化：**
- 与Google Earth时光机功能形成差异化竞争
- 填补历史场景可视化应用的市场空白
- 为教育科技领域提供创新解决方案

## 🔒 数据安全和合规

### 数据来源合规

- ✅ **Historical-basemaps**：GPL-3.0开源许可证
- ✅ **Gemini API**：Google官方服务条款
- ✅ **SynthID水印**：确保AI生成内容的可追溯性

### 隐私保护

- ✅ 不存储用户个人位置信息
- ✅ 历史查询记录可选择性保存
- ✅ AI生成图像符合内容安全政策

## 📊 成功指标和评估

### 技术指标

- 🎯 历史查询准确率 > 95%
- ⚡ 场景生成响应时间 < 30秒
- 🎨 图像生成成功率 > 90%  
- 💾 数据缓存命中率 > 80%

### 用户体验指标

- 😊 用户满意度评分 > 4.5/5
- 📈 功能使用率 > 60%
- 🔄 场景优化使用率 > 30%
- 📤 分享转发率 > 20%

### 教育价值指标

- 📚 历史知识准确性验证
- 🎓 教育机构合作反馈
- 📖 用户学习效果评估

---

## 📝 开发备注

### 技术决策记录

1. **选择Historical-basemaps**: 相比自建历史数据库，使用开源学术项目确保数据权威性和及时更新
2. **选择Nano Banana**: 相比其他生图模型，Nano Banana的对话式优化和历史准确性更适合教育场景
3. **混合数据方案**: 平衡性能、成本和实时性的最优解决方案

### 风险评估和应对

**技术风险：**
- Historical-basemaps数据更新延迟 → 本地缓存 + 降级机制
- Gemini API调用失败 → 备用描述 + 重试机制
- 历史准确性争议 → 多源数据验证 + 免责声明

**成本风险：**
- AI生图成本超预算 → 用量监控 + 分级服务
- 存储成本增长 → 数据清理 + 压缩优化

### 扩展计划

**未来功能规划：**
- 📹 集成Gemini Veo生成历史场景视频
- 🗣️ 添加语音导游和历史故事讲述
- 🎮 开发历史探索小游戏模式
- 🌐 支持多语言历史文化内容

---

*文档创建时间：2024年12月20日*  
*方案状态：详细设计完成，待开发实施*  
*预计开发周期：6-8周*  
*技术负责人：AI Assistant*

