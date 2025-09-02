"""
Historical-basemaps 数据加载器
实现GitHub Raw文件访问、智能缓存和历史边界数据获取
"""

import aiohttp
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

class HistoricalDataLoader:
    """Historical-basemaps数据加载器"""
    
    def __init__(self):
        # GitHub raw文件的基础URL
        self.github_raw_base = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson"
        self.cache_dir = "backend/data/historical_cache"
        
        # 可用的历史数据文件映射 (基于Historical-basemaps项目的实际文件)
        # 注意：文件名使用下划线 (_) 而不是连字符 (-)
        self.available_datasets = {
            2000: "world_2000.geojson",
            1994: "world_1994.geojson", 
            1960: "world_1960.geojson",
            1945: "world_1945.geojson",
            1938: "world_1938.geojson",
            1920: "world_1920.geojson",
            1914: "world_1914.geojson",
            1880: "world_1880.geojson",
            1815: "world_1815.geojson",
            1783: "world_1783.geojson",
            1715: "world_1715.geojson",
            1650: "world_1650.geojson",
            1530: "world_1530.geojson",
            1492: "world_1492.geojson",
            1279: "world_1279.geojson",
            800: "world_800.geojson",
            1000: "world_1000.geojson",
            400: "world_400.geojson",
            -1: "world__1.geojson"  # 公元前1年 (双下划线)
        }
        
        # 缓存配置
        self.cache_expiry_days = 7  # 缓存7天
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print(f"📚 Historical数据加载器已初始化")
        print(f"   GitHub源: {self.github_raw_base}")
        print(f"   缓存目录: {self.cache_dir}")
        print(f"   可用数据集: {len(self.available_datasets)} 个历史时期")
    
    async def get_historical_data(self, year: int) -> Dict:
        """
        获取指定年份的历史边界数据
        
        Args:
            year: 目标年份
            
        Returns:
            Dict: GeoJSON格式的历史边界数据
        """
        print(f"🔍 请求历史数据: {year}年")
        
        # 找到最接近的年份数据
        closest_year = self.find_closest_year(year)
        filename = self.available_datasets.get(closest_year)
        
        if not filename:
            raise ValueError(f"❌ 没有找到{year}年附近的历史数据")
        
        print(f"📊 映射到数据文件: {filename} ({closest_year}年)")
        
        # 尝试从本地缓存加载
        cached_data = await self.load_from_cache(filename)
        if cached_data:
            return cached_data
        
        # 从GitHub下载数据
        return await self.download_and_cache(filename, closest_year)
    
    def find_closest_year(self, target_year: int) -> int:
        """
        找到最接近目标年份的可用数据年份
        
        Args:
            target_year: 目标年份
            
        Returns:
            int: 最接近的可用年份
        """
        available_years = list(self.available_datasets.keys())
        
        # 找到最接近的年份
        closest_year = min(available_years, key=lambda x: abs(x - target_year))
        
        year_diff = abs(closest_year - target_year)
        print(f"🎯 目标年份: {target_year}, 使用数据: {closest_year} (差距: {year_diff}年)")
        
        return closest_year
    
    async def download_and_cache(self, filename: str, year: int) -> Dict:
        """
        从GitHub下载GeoJSON文件并缓存到本地
        
        Args:
            filename: GeoJSON文件名
            year: 对应年份
            
        Returns:
            Dict: 下载的GeoJSON数据
        """
        url = f"{self.github_raw_base}/{filename}"
        
        try:
            print(f"🌐 正在从GitHub下载历史数据: {filename}")
            print(f"   URL: {url}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # GitHub Raw文件返回text/plain，需要手动解析JSON
                        text_content = await response.text(encoding='utf-8')
                        
                        try:
                            # 手动解析JSON内容
                            data = json.loads(text_content)
                        except json.JSONDecodeError as e:
                            raise ValueError(f"JSON解析失败: {e}")
                        
                        # 验证数据完整性
                        if not self.validate_geojson_data(data):
                            raise ValueError("下载的数据格式不正确")
                        
                        # 缓存到本地
                        await self.save_to_cache(filename, data)
                        
                        features_count = len(data.get('features', []))
                        print(f"✅ 历史数据下载成功: {features_count} 个政治实体")
                        
                        return data
                    else:
                        raise Exception(f"GitHub数据下载失败: HTTP {response.status}")
        
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            # 返回降级数据
            return await self.get_fallback_data(year)
    
    async def load_from_cache(self, filename: str) -> Optional[Dict]:
        """
        从本地缓存加载数据
        
        Args:
            filename: 缓存文件名
            
        Returns:
            Optional[Dict]: 缓存的数据，如果不存在或过期则返回None
        """
        cache_path = os.path.join(self.cache_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(cache_path):
            return None
        
        try:
            # 检查缓存是否过期
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            expiry_time = file_modified_time + timedelta(days=self.cache_expiry_days)
            
            if datetime.now() > expiry_time:
                print(f"⏰ 缓存已过期: {filename} (修改时间: {file_modified_time})")
                return None
            
            # 加载缓存数据
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"📁 从缓存加载历史数据: {filename}")
            print(f"   缓存时间: {file_modified_time}")
            print(f"   数据特征数: {len(data.get('features', []))}")
            
            return data
            
        except Exception as e:
            print(f"⚠️ 缓存文件损坏或读取失败: {e}")
            # 删除损坏的缓存文件
            try:
                os.remove(cache_path)
                print(f"🗑️ 已删除损坏的缓存文件: {filename}")
            except:
                pass
            return None
    
    async def save_to_cache(self, filename: str, data: Dict):
        """
        保存数据到本地缓存
        
        Args:
            filename: 文件名
            data: 要缓存的数据
        """
        cache_path = os.path.join(self.cache_dir, filename)
        
        try:
            # 确保目录存在
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # 保存数据
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 获取文件大小
            file_size = os.path.getsize(cache_path)
            print(f"💾 历史数据已缓存: {cache_path}")
            print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def validate_geojson_data(self, data: Dict) -> bool:
        """
        验证GeoJSON数据的完整性
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查基本GeoJSON结构
            if not isinstance(data, dict):
                return False
            
            if data.get('type') != 'FeatureCollection':
                return False
            
            features = data.get('features', [])
            if not isinstance(features, list) or len(features) == 0:
                return False
            
            # 检查特征的基本结构
            sample_feature = features[0]
            if not isinstance(sample_feature, dict):
                return False
            
            # 检查必需的属性
            if 'geometry' not in sample_feature or 'properties' not in sample_feature:
                return False
            
            print(f"✅ GeoJSON数据验证通过: {len(features)} 个特征")
            return True
            
        except Exception as e:
            print(f"❌ GeoJSON数据验证失败: {e}")
            return False
    
    async def get_fallback_data(self, year: int) -> Dict:
        """
        当下载失败时提供降级数据
        
        Args:
            year: 目标年份
            
        Returns:
            Dict: 简单的降级数据结构
        """
        print(f"🔄 生成{year}年的降级历史数据")
        
        # 创建简单的全球降级数据
        fallback_features = []
        
        # 根据年份创建一些基本的政治实体
        if year >= 1900:
            # 现代国家
            entities = [
                {"name": "中国", "coords": [[100, 20], [140, 20], [140, 50], [100, 50], [100, 20]]},
                {"name": "美国", "coords": [[-125, 25], [-65, 25], [-65, 50], [-125, 50], [-125, 25]]},
                {"name": "欧盟", "coords": [[-10, 35], [30, 35], [30, 70], [-10, 70], [-10, 35]]}
            ]
        elif year >= 1500:
            # 早期现代
            entities = [
                {"name": "明朝", "coords": [[100, 20], [140, 20], [140, 50], [100, 50], [100, 20]]},
                {"name": "奥斯曼帝国", "coords": [[20, 30], [50, 30], [50, 45], [20, 45], [20, 30]]},
                {"name": "西班牙帝国", "coords": [[-10, 35], [5, 35], [5, 45], [-10, 45], [-10, 35]]}
            ]
        else:
            # 古代文明
            entities = [
                {"name": "汉朝", "coords": [[100, 20], [140, 20], [140, 50], [100, 50], [100, 20]]},
                {"name": "罗马帝国", "coords": [[-10, 30], [30, 30], [30, 50], [-10, 50], [-10, 30]]},
                {"name": "古印度", "coords": [[65, 5], [95, 5], [95, 35], [65, 35], [65, 5]]}
            ]
        
        for entity in entities:
            feature = {
                "type": "Feature",
                "properties": {
                    "NAME": entity["name"],
                    "SUBJECTO": entity["name"],
                    "PARTOF": "世界文明",
                    "BORDERPRECISION": 1
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [entity["coords"]]
                }
            }
            fallback_features.append(feature)
        
        fallback_data = {
            "type": "FeatureCollection",
            "features": fallback_features
        }
        
        return fallback_data
    
    async def get_available_years(self) -> List[int]:
        """
        获取所有可用的历史年份列表
        
        Returns:
            List[int]: 可用年份列表
        """
        return sorted(list(self.available_datasets.keys()), reverse=True)
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存信息和统计
        
        Returns:
            Dict: 缓存统计信息
        """
        cache_info = {
            'cache_dir': self.cache_dir,
            'cached_files': [],
            'total_cache_size': 0,
            'cache_count': 0
        }
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.geojson'):
                    file_path = os.path.join(self.cache_dir, filename)
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    cache_info['cached_files'].append({
                        'filename': filename,
                        'size_mb': file_size / 1024 / 1024,
                        'modified': file_modified.isoformat(),
                        'is_expired': (datetime.now() - file_modified).days > self.cache_expiry_days
                    })
                    
                    cache_info['total_cache_size'] += file_size
                    cache_info['cache_count'] += 1
        
        cache_info['total_cache_size_mb'] = cache_info['total_cache_size'] / 1024 / 1024
        return cache_info
    
    async def clear_expired_cache(self):
        """
        清理过期的缓存文件
        """
        if not os.path.exists(self.cache_dir):
            return
        
        expired_count = 0
        freed_size = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.geojson'):
                file_path = os.path.join(self.cache_dir, filename)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if (datetime.now() - file_modified).days > self.cache_expiry_days:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    expired_count += 1
                    freed_size += file_size
                    print(f"🗑️ 删除过期缓存: {filename}")
        
        if expired_count > 0:
            print(f"🧹 缓存清理完成: 删除{expired_count}个文件, 释放{freed_size/1024/1024:.2f}MB空间")
        else:
            print(f"✨ 缓存无需清理")
    
    async def preload_common_datasets(self, years: List[int] = None):
        """
        预加载常用的历史数据集
        
        Args:
            years: 要预加载的年份列表，默认为常用年份
        """
        if years is None:
            # 默认预加载一些关键历史时期
            years = [2000, 1945, 1914, 1880, 1650, 1492, 1000, 400]
        
        print(f"📥 开始预加载历史数据集: {len(years)} 个时期")
        
        # 并发下载以提高效率
        download_tasks = []
        for year in years:
            if year in self.available_datasets:
                task = self.get_historical_data(year)
                download_tasks.append(task)
        
        if download_tasks:
            try:
                results = await asyncio.gather(*download_tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if not isinstance(r, Exception))
                print(f"✅ 预加载完成: {success_count}/{len(download_tasks)} 个数据集成功")
                
            except Exception as e:
                print(f"⚠️ 预加载过程中出现错误: {e}")
    
    def get_dataset_info(self, year: int) -> Dict:
        """
        获取指定年份数据集的信息
        
        Args:
            year: 年份
            
        Returns:
            Dict: 数据集信息
        """
        closest_year = self.find_closest_year(year)
        filename = self.available_datasets.get(closest_year)
        
        if not filename:
            return {'error': '数据集不存在'}
        
        cache_path = os.path.join(self.cache_dir, filename)
        
        info = {
            'target_year': year,
            'closest_available_year': closest_year,
            'year_difference': abs(year - closest_year),
            'filename': filename,
            'github_url': f"{self.github_raw_base}/{filename}",
            'cached': os.path.exists(cache_path)
        }
        
        if info['cached']:
            file_size = os.path.getsize(cache_path)
            file_modified = datetime.fromtimestamp(os.path.getmtime(cache_path))
            info.update({
                'cache_size_mb': file_size / 1024 / 1024,
                'cache_modified': file_modified.isoformat(),
                'cache_expired': (datetime.now() - file_modified).days > self.cache_expiry_days
            })
        
        return info


# 全局实例
historical_data_loader = HistoricalDataLoader()


# 测试和调试函数
async def test_data_loader():
    """测试数据加载器功能"""
    print("🧪 开始测试Historical数据加载器...")
    
    try:
        # 测试几个关键年份
        test_years = [1600, 1945, 800, 2000]
        
        for year in test_years:
            print(f"\n📅 测试年份: {year}")
            data = await historical_data_loader.get_historical_data(year)
            
            if data and 'features' in data:
                print(f"✅ 成功获取数据: {len(data['features'])} 个政治实体")
            else:
                print(f"❌ 数据获取失败")
    
        # 显示缓存统计
        print(f"\n📊 缓存统计:")
        cache_info = historical_data_loader.get_cache_info()
        print(f"   缓存文件数: {cache_info['cache_count']}")
        print(f"   总缓存大小: {cache_info['total_cache_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    # 如果直接运行此文件，执行测试
    asyncio.run(test_data_loader())
