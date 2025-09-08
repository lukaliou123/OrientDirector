#!/usr/bin/env python3
"""
重试失败景点的媒体更新

使用有效的Pexels API密钥重新更新之前失败的景点
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# 添加backend目录到路径
sys.path.append('backend')

from supabase_client import supabase_client

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retry_failed_attractions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RetryFailedAttractionsUpdater:
    """重试失败景点的媒体更新器"""
    
    def __init__(self):
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        self.updated_count = 0
        self.failed_count = 0
        
        # 之前失败的景点列表（主要是国外景点）
        self.failed_attractions = [
            "慕田峪长城", "埃菲尔铁塔", "卢浮宫", "凯旋门", "香榭丽舍大街",
            "巴黎圣母院", "蒙马特高地", "大本钟", "伦敦眼", "白金汉宫",
            "大英博物馆", "塔桥", "西敏寺", "斗兽场", "万神殿",
            "罗马广场", "特雷维喷泉", "西班牙阶梯"
        ]
        
        # 英文搜索关键词映射
        self.english_keywords = {
            "慕田峪长城": ["Mutianyu Great Wall", "Great Wall China", "Beijing Great Wall"],
            "埃菲尔铁塔": ["Eiffel Tower", "Paris tower", "France landmark"],
            "卢浮宫": ["Louvre Museum", "Paris museum", "Mona Lisa museum"],
            "凯旋门": ["Arc de Triomphe", "Paris arch", "Champs Elysees"],
            "香榭丽舍大街": ["Champs Elysees", "Paris avenue", "French street"],
            "巴黎圣母院": ["Notre Dame", "Paris cathedral", "Gothic cathedral"],
            "蒙马特高地": ["Montmartre", "Paris hill", "Sacre Coeur"],
            "大本钟": ["Big Ben", "London clock", "Westminster"],
            "伦敦眼": ["London Eye", "London wheel", "Thames wheel"],
            "白金汉宫": ["Buckingham Palace", "London palace", "British palace"],
            "大英博物馆": ["British Museum", "London museum", "UK museum"],
            "塔桥": ["Tower Bridge", "London bridge", "Thames bridge"],
            "西敏寺": ["Westminster Abbey", "London abbey", "British church"],
            "斗兽场": ["Colosseum", "Rome arena", "Roman amphitheater"],
            "万神殿": ["Pantheon", "Rome temple", "Roman architecture"],
            "罗马广场": ["Roman Forum", "Rome ruins", "Ancient Rome"],
            "特雷维喷泉": ["Trevi Fountain", "Rome fountain", "Italian fountain"],
            "西班牙阶梯": ["Spanish Steps", "Rome steps", "Italian stairs"]
        }
        
        logger.info("重试失败景点更新器初始化完成")
        logger.info(f"Unsplash API: {'✅' if self.unsplash_key else '❌'}")
        logger.info(f"Pexels API: {'✅' if self.pexels_key else '❌'}")
    
    async def search_pexels_images(self, query: str, count: int = 3) -> List[Dict]:
        """使用Pexels API搜索图片"""
        if not self.pexels_key:
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": min(count, 80),
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = []
                        
                        for photo in data.get("photos", []):
                            image_info = {
                                "id": photo["id"],
                                "url": photo["src"]["large"],
                                "medium_url": photo["src"]["medium"],
                                "thumbnail": photo["src"]["tiny"],
                                "description": photo.get("alt", query) or query,
                                "photographer": photo["photographer"],
                                "photographer_url": photo["photographer_url"],
                                "source": "Pexels",
                                "width": photo["width"],
                                "height": photo["height"],
                                "quality": "high"
                            }
                            images.append(image_info)
                        
                        logger.info(f"Pexels图片搜索成功: {query} -> {len(images)}张图片")
                        return images
                    else:
                        logger.error(f"Pexels图片搜索失败: {response.status}")
            
            return []
            
        except Exception as e:
            logger.error(f"Pexels图片搜索异常: {e}")
            return []
    
    async def search_pexels_videos(self, query: str, count: int = 2) -> List[Dict]:
        """使用Pexels API搜索视频"""
        if not self.pexels_key:
            return []
        
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": min(count, 80),
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        videos = []
                        
                        for video in data.get("videos", []):
                            video_files = video.get("video_files", [])
                            if video_files:
                                # 选择最佳质量视频
                                best_video = max(video_files, key=lambda x: x.get("width", 0) * x.get("height", 0))
                                
                                video_info = {
                                    "id": video["id"],
                                    "url": best_video["link"],
                                    "preview_url": video["image"],
                                    "description": f"{query} 视频",
                                    "photographer": video["user"]["name"],
                                    "photographer_url": video["user"]["url"],
                                    "source": "Pexels",
                                    "width": best_video.get("width", 0),
                                    "height": best_video.get("height", 0),
                                    "duration": video.get("duration", 0),
                                    "quality": best_video.get("quality", "hd")
                                }
                                videos.append(video_info)
                        
                        logger.info(f"Pexels视频搜索成功: {query} -> {len(videos)}个视频")
                        return videos
                    else:
                        logger.error(f"Pexels视频搜索失败: {response.status}")
            
            return []
            
        except Exception as e:
            logger.error(f"Pexels视频搜索异常: {e}")
            return []
    
    async def search_media_for_attraction(self, attraction: Dict) -> Dict:
        """为景点搜索媒体资源（使用英文关键词）"""
        attraction_name = attraction.get('name', '')
        
        # 获取英文搜索关键词
        english_queries = self.english_keywords.get(attraction_name, [attraction_name])
        
        all_images = []
        all_videos = []
        
        # 使用英文关键词搜索
        for query in english_queries:
            if len(all_images) >= 5:
                break
            
            # 搜索图片
            images = await self.search_pexels_images(query, 2)
            all_images.extend(images)
            await asyncio.sleep(0.5)  # API限制
            
            # 搜索视频
            if len(all_videos) < 2:
                videos = await self.search_pexels_videos(query, 1)
                all_videos.extend(videos)
                await asyncio.sleep(0.5)  # API限制
        
        return {
            "images": all_images[:5],  # 最多5张图片
            "videos": all_videos[:2]   # 最多2个视频
        }
    
    async def get_failed_attractions(self) -> List[Dict]:
        """获取之前失败的景点数据"""
        try:
            result = supabase_client.client.table('spot_attractions')\
                .select('*')\
                .in_('name', self.failed_attractions)\
                .execute()
            
            if result.data:
                logger.info(f"找到 {len(result.data)} 个需要重试的景点")
                return result.data
            else:
                logger.warning("没有找到需要重试的景点")
                return []
                
        except Exception as e:
            logger.error(f"获取失败景点数据失败: {e}")
            return []
    
    async def update_attraction_media(self, attraction: Dict) -> bool:
        """更新单个景点的媒体资源"""
        try:
            attraction_id = attraction['id']
            attraction_name = attraction.get('name', '')
            
            logger.info(f"开始重试更新景点媒体: {attraction_name}")
            
            # 搜索媒体资源
            media_resources = await self.search_media_for_attraction(attraction)
            images = media_resources.get("images", [])
            videos = media_resources.get("videos", [])
            
            if not images and not videos:
                logger.warning(f"景点 {attraction_name} 仍然没有找到合适的媒体资源")
                return False
            
            # 更新数据库
            update_data = {}
            
            # 更新主图片
            if images:
                best_image = images[0]
                update_data['main_image_url'] = best_image['url']
                logger.info(f"更新主图片: {best_image['url']}")
            
            # 更新视频
            if videos:
                best_video = videos[0]
                update_data['video_url'] = best_video['url']
                logger.info(f"更新视频: {best_video['url']}")
            
            # 执行数据库更新
            if update_data:
                result = supabase_client.client.table('spot_attractions')\
                    .update(update_data)\
                    .eq('id', attraction_id)\
                    .execute()
                
                if result.data:
                    logger.info(f"景点 {attraction_name} 媒体重试更新成功")
                    self.updated_count += 1
                    return True
                else:
                    logger.error(f"景点 {attraction_name} 数据库更新失败")
            
            return False
            
        except Exception as e:
            logger.error(f"重试更新景点媒体失败 {attraction.get('name', '')}: {e}")
            self.failed_count += 1
            return False
    
    async def retry_all_failed_attractions(self, delay: float = 2.0):
        """重试所有失败景点的媒体更新"""
        try:
            logger.info("开始重试失败景点的媒体更新")
            
            # 获取失败的景点
            attractions = await self.get_failed_attractions()
            if not attractions:
                logger.error("没有找到需要重试的景点")
                return
            
            total_count = len(attractions)
            logger.info(f"总共需要重试 {total_count} 个景点")
            
            # 逐个处理
            for i, attraction in enumerate(attractions):
                success = await self.update_attraction_media(attraction)
                if success:
                    logger.info(f"✅ {attraction.get('name', '')} 重试更新成功")
                else:
                    logger.warning(f"❌ {attraction.get('name', '')} 重试更新失败")
                
                # 进度报告
                progress = ((i + 1) / total_count) * 100
                logger.info(f"重试进度: {i + 1}/{total_count} ({progress:.1f}%)")
                
                # 延迟避免API限制
                if i < total_count - 1:
                    await asyncio.sleep(delay)
            
            logger.info(f"重试更新完成! 成功: {self.updated_count}, 失败: {self.failed_count}")
            
        except Exception as e:
            logger.error(f"重试更新失败: {e}")
    
    async def test_apis(self):
        """测试API连接"""
        try:
            logger.info("测试API连接...")
            
            # 测试Pexels图片
            if self.pexels_key:
                images = await self.search_pexels_images("Eiffel Tower", 1)
                if images:
                    logger.info(f"✅ Pexels图片API连接正常")
                else:
                    logger.error("❌ Pexels图片API连接失败")
                    return False
                
                # 测试Pexels视频
                videos = await self.search_pexels_videos("Paris", 1)
                if videos:
                    logger.info(f"✅ Pexels视频API连接正常")
                else:
                    logger.warning("⚠️ Pexels视频API连接失败")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ API连接测试失败: {e}")
            return False


async def main():
    """主函数"""
    try:
        # 创建更新器
        updater = RetryFailedAttractionsUpdater()
        
        # 测试API连接
        if not await updater.test_apis():
            logger.error("API连接测试失败，请检查API密钥")
            return
        
        # 询问用户是否继续
        print("\n" + "="*60)
        print("准备重试更新之前失败的景点媒体资源")
        print("- 使用有效的Pexels API密钥")
        print("- 针对国外景点使用英文关键词搜索")
        print("- 重点更新18个之前失败的景点")
        print("="*60)
        
        confirm = input("是否继续？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        # 开始重试更新
        start_time = datetime.now()
        await updater.retry_all_failed_attractions(delay=2.0)
        end_time = datetime.now()
        
        # 输出总结
        duration = (end_time - start_time).total_seconds()
        print("\n" + "="*60)
        print("重试更新完成!")
        print(f"总耗时: {duration:.1f} 秒")
        print(f"成功更新: {updater.updated_count} 个景点")
        print(f"更新失败: {updater.failed_count} 个景点")
        print("详细日志已保存到 retry_failed_attractions.log")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
