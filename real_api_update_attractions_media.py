#!/usr/bin/env python3
"""
使用真实API批量更新景点数据库中的图片和视频

支持的API:
- Unsplash API (图片)
- Pexels API (图片和视频)

使用说明：
1. 确保.env文件中配置了API密钥
2. 运行脚本：python real_api_update_attractions_media.py
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
        logging.FileHandler('real_api_media_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RealAPIMediaUpdater:
    """真实API媒体资源更新器"""
    
    def __init__(self):
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        self.updated_count = 0
        self.failed_count = 0
        
        logger.info("真实API媒体更新器初始化完成")
        logger.info(f"Unsplash API: {'✅' if self.unsplash_key else '❌'}")
        logger.info(f"Pexels API: {'✅' if self.pexels_key else '❌'}")
    
    async def search_unsplash_images(self, query: str, count: int = 3) -> List[Dict]:
        """使用Unsplash API搜索图片"""
        if not self.unsplash_key:
            return []
        
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_key}"
            }
            params = {
                "query": query,
                "per_page": min(count, 30),
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = []
                        
                        for photo in data.get("results", []):
                            image_info = {
                                "id": photo["id"],
                                "url": photo["urls"]["regular"],
                                "medium_url": photo["urls"]["small"],
                                "thumbnail": photo["urls"]["thumb"],
                                "description": photo.get("alt_description", query) or query,
                                "photographer": photo["user"]["name"],
                                "photographer_url": photo["user"]["links"]["html"],
                                "source": "Unsplash",
                                "width": photo["width"],
                                "height": photo["height"],
                                "quality": "high"
                            }
                            images.append(image_info)
                        
                        logger.info(f"Unsplash图片搜索成功: {query} -> {len(images)}张图片")
                        return images
                    else:
                        logger.error(f"Unsplash图片搜索失败: {response.status}")
            
            return []
            
        except Exception as e:
            logger.error(f"Unsplash图片搜索异常: {e}")
            return []
    
    async def search_pexels_images(self, query: str, count: int = 3) -> List[Dict]:
        """使用Pexels API搜索图片"""
        if not self.pexels_key:
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_key
            }
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
            headers = {
                "Authorization": self.pexels_key
            }
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
                            # 选择最高质量的视频文件
                            video_files = video.get("video_files", [])
                            if video_files:
                                # 按质量排序，选择最佳质量
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
        """为景点搜索媒体资源"""
        attraction_name = attraction.get('name', '')
        attraction_city = attraction.get('city', '')
        attraction_category = attraction.get('category', '')
        
        # 构建搜索查询词
        search_queries = [
            f"{attraction_name}",
            f"{attraction_name} {attraction_city}",
            f"{attraction_category} {attraction_city}",
            f"{attraction_city} landmark",
            attraction_category
        ]
        
        all_images = []
        all_videos = []
        
        # 搜索图片 - 优先使用Unsplash
        for query in search_queries[:3]:
            if len(all_images) >= 5:
                break
            
            # 先尝试Unsplash
            if self.unsplash_key:
                images = await self.search_unsplash_images(query, 2)
                all_images.extend(images)
                await asyncio.sleep(0.3)  # API限制
            
            # 如果图片不够，再尝试Pexels
            if len(all_images) < 3 and self.pexels_key:
                images = await self.search_pexels_images(query, 2)
                all_images.extend(images)
                await asyncio.sleep(0.3)  # API限制
        
        # 搜索视频 - 使用Pexels
        if self.pexels_key:
            for query in search_queries[:2]:
                if len(all_videos) >= 2:
                    break
                
                videos = await self.search_pexels_videos(query, 1)
                all_videos.extend(videos)
                await asyncio.sleep(0.3)  # API限制
        
        return {
            "images": all_images[:5],  # 最多5张图片
            "videos": all_videos[:2]   # 最多2个视频
        }
    
    async def get_all_attractions(self) -> List[Dict]:
        """获取所有景点数据"""
        try:
            result = supabase_client.client.table('spot_attractions')\
                .select('*')\
                .execute()
            
            if result.data:
                logger.info(f"获取到 {len(result.data)} 个景点")
                return result.data
            else:
                logger.warning("没有找到景点数据")
                return []
                
        except Exception as e:
            logger.error(f"获取景点数据失败: {e}")
            return []
    
    async def update_attraction_media(self, attraction: Dict) -> bool:
        """更新单个景点的媒体资源"""
        try:
            attraction_id = attraction['id']
            attraction_name = attraction.get('name', '')
            
            logger.info(f"开始更新景点媒体: {attraction_name}")
            
            # 搜索媒体资源
            media_resources = await self.search_media_for_attraction(attraction)
            images = media_resources.get("images", [])
            videos = media_resources.get("videos", [])
            
            if not images and not videos:
                logger.warning(f"景点 {attraction_name} 没有找到合适的媒体资源")
                return False
            
            # 更新数据库
            update_data = {}
            
            # 更新主图片
            if images:
                best_image = images[0]  # 选择第一张作为主图片
                update_data['main_image_url'] = best_image['url']
                logger.info(f"更新主图片: {best_image['url']}")
            
            # 更新视频
            if videos:
                best_video = videos[0]  # 选择第一个视频
                update_data['video_url'] = best_video['url']
                logger.info(f"更新视频: {best_video['url']}")
            
            # 执行数据库更新
            if update_data:
                result = supabase_client.client.table('spot_attractions')\
                    .update(update_data)\
                    .eq('id', attraction_id)\
                    .execute()
                
                if result.data:
                    logger.info(f"景点 {attraction_name} 媒体更新成功")
                    
                    # 保存详细的媒体信息到媒体表
                    await self.save_media_details(attraction_id, images, videos, attraction_name)
                    
                    self.updated_count += 1
                    return True
                else:
                    logger.error(f"景点 {attraction_name} 数据库更新失败")
            
            return False
            
        except Exception as e:
            logger.error(f"更新景点媒体失败 {attraction.get('name', '')}: {e}")
            self.failed_count += 1
            return False
    
    async def save_media_details(self, attraction_id: str, images: List[Dict], videos: List[Dict], attraction_name: str):
        """保存详细的媒体信息到媒体表"""
        try:
            # 删除旧的媒体记录
            supabase_client.client.table('spot_attraction_media')\
                .delete()\
                .eq('attraction_id', attraction_id)\
                .execute()
            
            # 插入图片记录
            for i, image in enumerate(images):
                media_data = {
                    'attraction_id': attraction_id,
                    'media_type': 'image',
                    'url': image['url'],
                    'thumbnail_url': image['thumbnail'],
                    'caption': f"{attraction_name} - {image['description']}",
                    'is_primary': i == 0,  # 第一张设为主图
                    'order_index': i
                }
                
                supabase_client.client.table('spot_attraction_media')\
                    .insert(media_data)\
                    .execute()
            
            # 插入视频记录
            for i, video in enumerate(videos):
                media_data = {
                    'attraction_id': attraction_id,
                    'media_type': 'video',
                    'url': video['url'],
                    'thumbnail_url': video['preview_url'],
                    'caption': f"{attraction_name} - {video['description']}",
                    'is_primary': False,
                    'order_index': i + 10  # 视频排在图片后面
                }
                
                supabase_client.client.table('spot_attraction_media')\
                    .insert(media_data)\
                    .execute()
            
            logger.info(f"保存了 {len(images)} 张图片和 {len(videos)} 个视频的详细信息")
            
        except Exception as e:
            logger.error(f"保存媒体详细信息失败: {e}")
    
    async def update_all_attractions(self, batch_size: int = 3, delay: float = 2.0):
        """批量更新所有景点的媒体资源"""
        try:
            logger.info("开始批量更新所有景点的媒体资源")
            
            # 获取所有景点
            attractions = await self.get_all_attractions()
            if not attractions:
                logger.error("没有找到景点数据")
                return
            
            total_count = len(attractions)
            logger.info(f"总共需要更新 {total_count} 个景点")
            
            # 分批处理
            for i in range(0, total_count, batch_size):
                batch = attractions[i:i + batch_size]
                logger.info(f"处理第 {i//batch_size + 1} 批，共 {len(batch)} 个景点")
                
                # 串行处理当前批次（避免API限制）
                for attraction in batch:
                    success = await self.update_attraction_media(attraction)
                    if success:
                        logger.info(f"✅ {attraction.get('name', '')} 更新成功")
                    else:
                        logger.warning(f"❌ {attraction.get('name', '')} 更新失败")
                    
                    # 每个景点之间的延迟
                    await asyncio.sleep(1.0)
                
                # 进度报告
                processed = min(i + batch_size, total_count)
                progress = (processed / total_count) * 100
                logger.info(f"总进度: {processed}/{total_count} ({progress:.1f}%)")
                
                # 批次间延迟
                if i + batch_size < total_count:
                    logger.info(f"等待 {delay} 秒后继续...")
                    await asyncio.sleep(delay)
            
            logger.info(f"批量更新完成! 成功: {self.updated_count}, 失败: {self.failed_count}")
            
        except Exception as e:
            logger.error(f"批量更新失败: {e}")
    
    async def test_apis(self):
        """测试API连接"""
        try:
            logger.info("测试API连接...")
            
            # 测试Unsplash
            if self.unsplash_key:
                images = await self.search_unsplash_images("landscape", 1)
                if images:
                    logger.info(f"✅ Unsplash API连接正常")
                else:
                    logger.error("❌ Unsplash API连接失败")
            
            # 测试Pexels图片
            if self.pexels_key:
                images = await self.search_pexels_images("nature", 1)
                if images:
                    logger.info(f"✅ Pexels图片API连接正常")
                else:
                    logger.error("❌ Pexels图片API连接失败")
                
                # 测试Pexels视频
                videos = await self.search_pexels_videos("city", 1)
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
        updater = RealAPIMediaUpdater()
        
        # 测试API连接
        if not await updater.test_apis():
            logger.error("API连接测试失败，请检查API密钥")
            return
        
        # 询问用户是否继续
        print("\n" + "="*60)
        print("准备使用真实API更新所有景点的图片和视频")
        print("- 使用Unsplash API获取高质量图片")
        print("- 使用Pexels API获取图片和视频")
        print("- 这将替换现有的媒体资源")
        print("="*60)
        
        confirm = input("是否继续？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        # 开始批量更新
        start_time = datetime.now()
        await updater.update_all_attractions(batch_size=2, delay=3.0)
        end_time = datetime.now()
        
        # 输出总结
        duration = (end_time - start_time).total_seconds()
        print("\n" + "="*60)
        print("更新完成!")
        print(f"总耗时: {duration:.1f} 秒")
        print(f"成功更新: {updater.updated_count} 个景点")
        print(f"更新失败: {updater.failed_count} 个景点")
        print("详细日志已保存到 real_api_media_update.log")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
