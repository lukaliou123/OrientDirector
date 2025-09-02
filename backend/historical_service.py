"""
历史查询服务
基于Historical-basemaps数据实现时空查询功能
"""

from shapely.geometry import Point, shape
from shapely.errors import ShapelyError
from typing import Dict, List, Optional, Tuple
import math
from historical_data_loader import historical_data_loader


class HistoricalService:
    """历史查询服务类"""
    
    def __init__(self):
        self.data_loader = historical_data_loader
        print(f"🏛️ 历史查询服务已初始化")
    
    async def query_historical_location(self, lat: float, lng: float, year: int) -> Dict:
        """
        根据坐标和年份查询历史政治实体
        
        Args:
            lat: 纬度 (-90 to 90)
            lng: 经度 (-180 to 180)
            year: 年份 (-3000 to 2024)
            
        Returns:
            Dict: 历史位置信息
        """
        # 验证输入参数
        if not self.validate_coordinates(lat, lng):
            return {
                'success': False,
                'error': '坐标参数无效',
                'details': f'纬度应在-90到90之间，经度应在-180到180之间'
            }
        
        if not self.validate_year(year):
            return {
                'success': False,
                'error': '年份参数无效',
                'details': '年份应在-3000到2024之间'
            }
        
        print(f"🔍 查询历史位置: ({lat:.4f}, {lng:.4f}) at {year} AD")
        
        try:
            # 获取对应年份的历史数据
            historical_data = await self.data_loader.get_historical_data(year)
            
            # 在历史边界中查找包含此点的政治实体
            result = await self.find_political_entity_in_boundaries(historical_data, lat, lng, year)
            
            return result
            
        except Exception as e:
            print(f"❌ 历史查询失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_result': self.create_fallback_historical_info(lat, lng, year)
            }
    
    async def find_political_entity_in_boundaries(self, geojson_data: Dict, lat: float, lng: float, year: int) -> Dict:
        """
        在GeoJSON边界数据中查找包含指定坐标的政治实体
        
        Args:
            geojson_data: Historical-basemaps的GeoJSON数据
            lat: 纬度
            lng: 经度
            year: 查询年份
            
        Returns:
            Dict: 查询结果
        """
        # 创建查询点 (注意Shapely使用lng, lat的顺序)
        query_point = Point(lng, lat)
        
        features = geojson_data.get('features', [])
        print(f"🔎 在{len(features)}个政治实体中搜索包含点({lat}, {lng})的边界...")
        
        # 精确匹配：查找完全包含此点的政治实体
        exact_matches = []
        
        for i, feature in enumerate(features):
            try:
                # 创建多边形几何
                geometry = feature.get('geometry')
                if not geometry:
                    continue
                
                polygon = shape(geometry)
                
                # 检查点是否在多边形内
                if polygon.contains(query_point):
                    properties = feature.get('properties', {})
                    exact_matches.append({
                        'feature': feature,
                        'properties': properties,
                        'index': i
                    })
                    
            except ShapelyError as e:
                print(f"⚠️ 几何图形{i}处理失败: {e}")
                continue
            except Exception as e:
                print(f"⚠️ 特征{i}处理异常: {e}")
                continue
        
        if exact_matches:
            # 如果有多个匹配，选择最合适的一个
            best_match = self.select_best_match(exact_matches, lat, lng)
            result = self.format_historical_result(best_match['properties'], year, lat, lng)
            result['data_source_year'] = self.extract_year_from_data(geojson_data)
            print(f"✅ 找到精确匹配: {result['political_entity']}")
            return result
        
        # 如果没有精确匹配，查找最近的实体
        print(f"🔍 未找到精确匹配，搜索最近的政治实体...")
        nearest_result = await self.find_nearest_historical_entity(geojson_data, lat, lng, year)
        return nearest_result
    
    def select_best_match(self, matches: List[Dict], lat: float, lng: float) -> Dict:
        """
        从多个匹配中选择最佳的政治实体
        
        Args:
            matches: 匹配的政治实体列表
            lat: 查询纬度
            lng: 查询经度
            
        Returns:
            Dict: 最佳匹配结果
        """
        if len(matches) == 1:
            return matches[0]
        
        # 如果有多个匹配，优先选择边界精度更高的
        matches_by_precision = sorted(matches, 
                                    key=lambda x: x['properties'].get('BORDERPRECISION', 0), 
                                    reverse=True)
        
        best_match = matches_by_precision[0]
        
        print(f"📊 从{len(matches)}个匹配中选择最佳: {best_match['properties'].get('NAME')} (精度: {best_match['properties'].get('BORDERPRECISION', 0)})")
        
        return best_match
    
    async def find_nearest_historical_entity(self, geojson_data: Dict, lat: float, lng: float, year: int) -> Dict:
        """
        查找最近的历史政治实体
        
        Args:
            geojson_data: GeoJSON数据
            lat: 纬度  
            lng: 经度
            year: 年份
            
        Returns:
            Dict: 最近实体的查询结果
        """
        query_point = Point(lng, lat)
        features = geojson_data.get('features', [])
        
        nearest_entity = None
        min_distance = float('inf')
        
        for feature in features[:50]:  # 限制搜索范围以提高性能
            try:
                geometry = feature.get('geometry')
                if not geometry:
                    continue
                
                polygon = shape(geometry)
                
                # 计算到边界的最短距离
                distance = polygon.distance(query_point)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_entity = feature
                    
            except Exception as e:
                continue
        
        if nearest_entity:
            properties = nearest_entity.get('properties', {})
            result = self.format_historical_result(properties, year, lat, lng)
            result['is_approximate'] = True
            result['distance_to_border'] = round(min_distance * 111.32, 2)  # 转换为公里
            result['data_source_year'] = self.extract_year_from_data(geojson_data)
            
            print(f"📍 找到最近实体: {result['political_entity']} (距离: {result['distance_to_border']}km)")
            return result
        
        # 如果还是找不到，返回降级信息
        return self.create_fallback_historical_info(lat, lng, year)
    
    def format_historical_result(self, properties: Dict, year: int, lat: float, lng: float) -> Dict:
        """
        格式化历史查询结果
        
        Args:
            properties: GeoJSON特征的properties
            year: 查询年份
            lat: 纬度
            lng: 经度
            
        Returns:
            Dict: 格式化的结果
        """
        political_entity = properties.get('NAME', '未知政治实体')
        ruler_power = properties.get('SUBJECTO', '')
        cultural_region = properties.get('PARTOF', '')
        border_precision = properties.get('BORDERPRECISION', 1)
        
        return {
            'success': True,
            'political_entity': political_entity,
            'ruler_or_power': ruler_power,
            'cultural_region': cultural_region,
            'border_precision': border_precision,
            'query_year': year,
            'coordinates': {'lat': lat, 'lng': lng},
            'description': self.generate_historical_description(properties, year),
            'time_period': self.classify_time_period(year),
            'cultural_context': self.get_cultural_context(properties, year),
            'is_approximate': False
        }
    
    def generate_historical_description(self, properties: Dict, year: int) -> str:
        """
        生成历史场景描述
        
        Args:
            properties: 政治实体属性
            year: 年份
            
        Returns:
            str: 历史描述文本
        """
        name = properties.get('NAME', '未知地区')
        ruler = properties.get('SUBJECTO', '')
        cultural = properties.get('PARTOF', '')
        
        # 根据时期生成背景描述
        era_info = self.get_era_info(year)
        
        description = f"{era_info['era']}({year}年)，这里是{era_info['context']}{name}"
        
        # 添加统治者信息
        if ruler and ruler != name and ruler.strip():
            description += f"，受{ruler}统治"
        
        # 添加文化圈信息  
        if cultural and cultural.strip():
            description += f"，属于{cultural}文化圈"
        
        # 添加时代特征
        description += f"。{era_info['characteristics']}"
        
        return description
    
    def get_era_info(self, year: int) -> Dict:
        """
        获取时代信息和特征
        
        Args:
            year: 年份
            
        Returns:
            Dict: 时代信息
        """
        if year >= 1945:
            return {
                'era': '现代',
                'context': '现代化进程中的',
                'characteristics': '这是一个科技快速发展、全球化加速的时代'
            }
        elif year >= 1800:
            return {
                'era': '近现代',
                'context': '工业革命浪潮下的',
                'characteristics': '蒸汽机和工业化改变了社会结构和生产方式'
            }
        elif year >= 1500:
            return {
                'era': '大航海时代',
                'context': '全球贸易兴起中的',
                'characteristics': '地理大发现开启了全球贸易和文化交流的新纪元'
            }
        elif year >= 1000:
            return {
                'era': '中世纪',
                'context': '封建制度下的',
                'characteristics': '宗教文化繁荣，农业社会结构稳定发展'
            }
        elif year >= 0:
            return {
                'era': '古典时期',
                'context': '古代文明的',
                'characteristics': '这是文字、哲学和艺术蓬勃发展的黄金时代'
            }
        else:
            return {
                'era': '远古时期',
                'context': '早期文明的',
                'characteristics': '人类社会从部落走向早期国家的重要转折期'
            }
    
    def classify_time_period(self, year: int) -> str:
        """
        对年份进行时期分类
        
        Args:
            year: 年份
            
        Returns:
            str: 时期分类
        """
        if year >= 1945:
            return "现代"
        elif year >= 1800:
            return "近现代"
        elif year >= 1500:
            return "早期现代"
        elif year >= 1000:
            return "中世纪"
        elif year >= 500:
            return "古典晚期"
        elif year >= 0:
            return "古典时期"
        elif year >= -500:
            return "轴心时代"
        else:
            return "远古时期"
    
    def get_cultural_context(self, properties: Dict, year: int) -> Dict:
        """
        获取文化背景上下文
        
        Args:
            properties: 政治实体属性
            year: 年份
            
        Returns:
            Dict: 文化上下文信息
        """
        cultural_region = properties.get('PARTOF', '')
        political_entity = properties.get('NAME', '')
        
        context = {
            'religion': self.infer_dominant_religion(cultural_region, political_entity, year),
            'technology_level': self.assess_technology_level(year),
            'social_structure': self.describe_social_structure(cultural_region, year),
            'economic_model': self.describe_economic_model(year)
        }
        
        return context
    
    def infer_dominant_religion(self, cultural_region: str, political_entity: str, year: int) -> str:
        """推断主要宗教"""
        cultural_lower = cultural_region.lower()
        entity_lower = political_entity.lower()
        
        if any(keyword in cultural_lower for keyword in ['christian', 'byzantine', 'orthodox']):
            return '基督教'
        elif any(keyword in cultural_lower for keyword in ['islamic', 'muslim', 'arab']):
            return '伊斯兰教'
        elif any(keyword in entity_lower for keyword in ['china', 'chinese', 'tang', 'ming', 'han']):
            if year < 100:
                return '传统信仰'
            else:
                return '佛教/道教'
        elif any(keyword in cultural_lower for keyword in ['hindu', 'india']):
            return '印度教'
        else:
            return '传统信仰'
    
    def assess_technology_level(self, year: int) -> str:
        """评估技术水平"""
        if year >= 1900:
            return '电气化时代'
        elif year >= 1800:
            return '蒸汽工业时代'
        elif year >= 1500:
            return '火药和印刷术时代'
        elif year >= 1000:
            return '铁器和农具时代'
        elif year >= 0:
            return '古典技术时代'
        else:
            return '青铜器时代'
    
    def describe_social_structure(self, cultural_region: str, year: int) -> str:
        """描述社会结构"""
        if year >= 1800:
            return '现代社会结构'
        elif year >= 1000:
            return '封建等级制度'
        elif year >= 0:
            return '古代王权制度'
        else:
            return '部落社会结构'
    
    def describe_economic_model(self, year: int) -> str:
        """描述经济模式"""
        if year >= 1800:
            return '工业化经济'
        elif year >= 1500:
            return '商业贸易经济'
        elif year >= 1000:
            return '农业庄园经济'
        else:
            return '农牧渔猎经济'
    
    def create_fallback_historical_info(self, lat: float, lng: float, year: int) -> Dict:
        """
        创建降级历史信息（当无法查找到准确数据时）
        
        Args:
            lat: 纬度
            lng: 经度
            year: 年份
            
        Returns:
            Dict: 降级历史信息
        """
        # 基于地理位置推断可能的文明区域
        region_info = self.infer_region_from_coordinates(lat, lng)
        
        return {
            'success': True,
            'political_entity': f'{region_info["region"]}地区政治实体',
            'ruler_or_power': '当地统治者',
            'cultural_region': region_info['cultural_area'],
            'border_precision': 1,
            'query_year': year,
            'coordinates': {'lat': lat, 'lng': lng},
            'description': f'{self.classify_time_period(year)}({year}年)，这里是{region_info["region"]}地区的一个政治实体，具有当时典型的{region_info["cultural_area"]}文化特征。',
            'time_period': self.classify_time_period(year),
            'cultural_context': self.get_basic_cultural_context(year),
            'is_fallback': True
        }
    
    def infer_region_from_coordinates(self, lat: float, lng: float) -> Dict:
        """
        基于坐标推断地理文化区域
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            Dict: 区域信息
        """
        # 简单的地理区域划分
        if 18 <= lat <= 54 and 73 <= lng <= 135:
            return {'region': '东亚', 'cultural_area': '中华文明圈'}
        elif 24 <= lat <= 46 and 123 <= lng <= 146:
            return {'region': '东亚', 'cultural_area': '日本文明'}
        elif 35 <= lat <= 70 and -10 <= lng <= 40:
            return {'region': '欧洲', 'cultural_area': '欧洲文明'}
        elif 25 <= lat <= 60 and -130 <= lng <= -60:
            return {'region': '北美', 'cultural_area': '美洲文明'}
        elif -35 <= lat <= 35 and 20 <= lng <= 50:
            return {'region': '非洲', 'cultural_area': '非洲文明'}
        elif -45 <= lat <= 10 and -80 <= lng <= -35:
            return {'region': '南美', 'cultural_area': '南美文明'}
        elif -50 <= lat <= -10 and 110 <= lng <= 155:
            return {'region': '大洋洲', 'cultural_area': '太平洋文明'}
        else:
            return {'region': '未知', 'cultural_area': '当地文明'}
    
    def get_basic_cultural_context(self, year: int) -> Dict:
        """获取基础文化背景"""
        return {
            'religion': '当地传统信仰',
            'technology_level': self.assess_technology_level(year),
            'social_structure': self.describe_social_structure('', year),
            'economic_model': self.describe_economic_model(year)
        }
    
    def extract_year_from_data(self, geojson_data: Dict) -> int:
        """
        从GeoJSON数据中提取数据源年份
        
        Args:
            geojson_data: GeoJSON数据
            
        Returns:
            int: 数据源年份
        """
        # 尝试从数据中提取年份信息
        # 这里可以根据Historical-basemaps的数据结构来实现
        # 暂时返回一个估计值
        return 0  # 可以后续根据实际数据结构优化
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        验证坐标参数的有效性
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            bool: 坐标是否有效
        """
        return -90 <= lat <= 90 and -180 <= lng <= 180
    
    def validate_year(self, year: int) -> bool:
        """
        验证年份参数的有效性
        
        Args:
            year: 年份
            
        Returns:
            bool: 年份是否有效
        """
        return -3000 <= year <= 2024
    
    async def get_historical_summary(self, lat: float, lng: float, year_range: Tuple[int, int]) -> Dict:
        """
        获取指定坐标在时间范围内的历史变迁摘要
        
        Args:
            lat: 纬度
            lng: 经度  
            year_range: 年份范围 (start_year, end_year)
            
        Returns:
            Dict: 历史变迁摘要
        """
        start_year, end_year = year_range
        
        # 在时间范围内取几个关键时间点
        sample_years = []
        year_span = end_year - start_year
        
        if year_span <= 100:
            step = 25
        elif year_span <= 500:
            step = 50
        else:
            step = 100
        
        current_year = start_year
        while current_year <= end_year:
            sample_years.append(current_year)
            current_year += step
        
        # 确保包含结束年份
        if sample_years[-1] != end_year:
            sample_years.append(end_year)
        
        print(f"📊 分析历史变迁: {start_year}-{end_year} ({len(sample_years)}个时间点)")
        
        # 查询每个时间点的政治实体
        historical_timeline = []
        for year in sample_years:
            try:
                result = await self.query_historical_location(lat, lng, year)
                if result['success']:
                    historical_timeline.append({
                        'year': year,
                        'entity': result['political_entity'],
                        'ruler': result['ruler_or_power'],
                        'culture': result['cultural_region']
                    })
            except:
                continue
        
        return {
            'coordinates': {'lat': lat, 'lng': lng},
            'time_range': year_range,
            'timeline': historical_timeline,
            'changes_count': len(set(item['entity'] for item in historical_timeline)),
            'summary': self.generate_change_summary(historical_timeline)
        }
    
    def generate_change_summary(self, timeline: List[Dict]) -> str:
        """生成历史变迁摘要"""
        if not timeline:
            return "该地区的历史信息不详"
        
        entities = [item['entity'] for item in timeline]
        unique_entities = list(dict.fromkeys(entities))  # 保持顺序去重
        
        if len(unique_entities) == 1:
            return f"该地区在此期间主要由{unique_entities[0]}统治"
        else:
            summary = "该地区经历了复杂的政治变迁："
            for entity in unique_entities[:3]:  # 最多显示3个主要实体
                summary += f" {entity},"
            summary = summary.rstrip(',')
            
            if len(unique_entities) > 3:
                summary += f" 等{len(unique_entities)}个政治实体"
            
            return summary


# 全局实例
historical_service = HistoricalService()


# 测试和调试函数
async def test_historical_query():
    """测试历史查询功能"""
    print("🧪 开始测试历史查询服务...")
    
    # 测试案例：关键历史地点和年份
    test_cases = [
        {'lat': 35.7148, 'lng': 139.7967, 'year': 1600, 'description': '江户时代的东京'},
        {'lat': 48.8584, 'lng': 2.2945, 'year': 1789, 'description': '法国大革命前的巴黎'},
        {'lat': 41.9028, 'lng': 12.4964, 'year': 100, 'description': '罗马帝国鼎盛期的罗马'},
        {'lat': 39.9042, 'lng': 116.4074, 'year': 1400, 'description': '明朝永乐年间的北京'},
        {'lat': 40.7580, 'lng': -73.9855, 'year': 1776, 'description': '美国独立战争时期的纽约'}
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n📍 测试案例 {i+1}: {case['description']}")
        
        try:
            result = await historical_service.query_historical_location(
                case['lat'], case['lng'], case['year']
            )
            
            if result['success']:
                print(f"✅ 查询成功:")
                print(f"   政治实体: {result['political_entity']}")
                print(f"   统治者: {result.get('ruler_or_power', 'N/A')}")
                print(f"   文化圈: {result.get('cultural_region', 'N/A')}")
                print(f"   边界精度: {result.get('border_precision', 'N/A')}")
                if result.get('is_approximate'):
                    print(f"   ⚠️ 近似结果 (距离: {result.get('distance_to_border', 'N/A')}km)")
            else:
                print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n📊 缓存信息:")
    cache_info = historical_data_loader.get_cache_info()
    print(f"   缓存文件: {cache_info['cache_count']} 个")
    print(f"   缓存大小: {cache_info['total_cache_size_mb']:.2f} MB")


if __name__ == "__main__":
    # 如果直接运行此文件，执行测试
    import asyncio
    asyncio.run(test_historical_query())
