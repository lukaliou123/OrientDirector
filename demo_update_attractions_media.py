#!/usr/bin/env python3
"""
演示版本：使用Pexels API批量更新景点数据库中的图片和视频
使用预设的高质量图片和视频资源

使用说明：
1. 运行脚本：python demo_update_attractions_media.py
2. 这将使用精选的高质量媒体资源更新所有景点
"""

import os
import sys
import json
import asyncio
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
        logging.FileHandler('demo_media_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DemoMediaUpdater:
    """演示版媒体资源更新器"""
    
    def __init__(self):
        self.updated_count = 0
        self.failed_count = 0
        
        # 预设的高质量媒体资源库
        self.media_library = {
            "文化古迹": {
                "images": [
                    {
                        "url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop",
                        "description": "古代建筑文化遗产",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    },
                    {
                        "url": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400&h=300&fit=crop",
                        "description": "传统文化建筑",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    }
                ],
                "videos": [
                    {
                        "url": "https://player.vimeo.com/external/371433846.sd.mp4?s=236c2e6c2c0b1d1c8b5b5b5b5b5b5b5b5b5b5b5b",
                        "preview_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop",
                        "description": "文化古迹视频介绍"
                    }
                ]
            },
            "自然风光": {
                "images": [
                    {
                        "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop",
                        "description": "壮丽自然风光",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    },
                    {
                        "url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=300&fit=crop",
                        "description": "山水自然景观",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    }
                ],
                "videos": [
                    {
                        "url": "https://player.vimeo.com/external/371433847.sd.mp4?s=236c2e6c2c0b1d1c8b5b5b5b5b5b5b5b5b5b5b5b",
                        "preview_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                        "description": "自然风光视频"
                    }
                ]
            },
            "城市地标": {
                "images": [
                    {
                        "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400&h=300&fit=crop",
                        "description": "现代城市地标",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    },
                    {
                        "url": "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop",
                        "description": "城市建筑景观",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    }
                ],
                "videos": [
                    {
                        "url": "https://player.vimeo.com/external/371433848.sd.mp4?s=236c2e6c2c0b1d1c8b5b5b5b5b5b5b5b5b5b5b5b",
                        "preview_url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&h=600&fit=crop",
                        "description": "城市地标视频"
                    }
                ]
            },
            "default": {
                "images": [
                    {
                        "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                        "thumbnail": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop",
                        "description": "精美景点图片",
                        "photographer": "Unsplash",
                        "source": "Unsplash"
                    }
                ],
                "videos": [
                    {
                        "url": "https://player.vimeo.com/external/371433849.sd.mp4?s=236c2e6c2c0b1d1c8b5b5b5b5b5b5b5b5b5b5b5b",
                        "preview_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                        "description": "景点介绍视频"
                    }
                ]
            }
        }
        
        logger.info("演示版媒体更新器初始化完成")
    
    def get_media_for_category(self, category: str) -> Dict:
        """根据景点类别获取对应的媒体资源"""
        # 类别映射
        category_mapping = {
            "文化古迹": "文化古迹",
            "历史遗迹": "文化古迹",
            "博物馆": "文化古迹",
            "寺庙": "文化古迹",
            "宫殿": "文化古迹",
            "自然风光": "自然风光",
            "公园": "自然风光",
            "山水": "自然风光",
            "风景区": "自然风光",
            "城市地标": "城市地标",
            "建筑": "城市地标",
            "地标建筑": "城市地标",
            "现代建筑": "城市地标"
        }
        
        mapped_category = category_mapping.get(category, "default")
        return self.media_library.get(mapped_category, self.media_library["default"])
    
    async def get_all_attractions(self) -> List[Dict]:
        """获取所有景点数据"""
        try:
            # 直接查询景点表
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
            attraction_category = attraction.get('category', '')
            
            logger.info(f"开始更新景点媒体: {attraction_name} ({attraction_category})")
            
            # 根据类别获取媒体资源
            media_resources = self.get_media_for_category(attraction_category)
            
            # 选择图片和视频
            images = media_resources.get("images", [])
            videos = media_resources.get("videos", [])
            
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
            else:
                logger.warning(f"景点 {attraction_name} 没有找到合适的媒体资源")
            
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
            for i, image in enumerate(images[:3]):  # 最多保存3张图片
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
            for i, video in enumerate(videos[:1]):  # 最多保存1个视频
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
    
    async def update_all_attractions(self, batch_size: int = 5, delay: float = 1.0):
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
                
                # 并发处理当前批次
                tasks = [self.update_attraction_media(attraction) for attraction in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计结果
                batch_success = sum(1 for r in results if r is True)
                batch_failed = len(batch) - batch_success
                
                logger.info(f"第 {i//batch_size + 1} 批完成: 成功 {batch_success}, 失败 {batch_failed}")
                
                # 进度报告
                processed = min(i + batch_size, total_count)
                progress = (processed / total_count) * 100
                logger.info(f"总进度: {processed}/{total_count} ({progress:.1f}%)")
                
                # 延迟以避免过快处理
                if i + batch_size < total_count:
                    logger.info(f"等待 {delay} 秒后继续...")
                    await asyncio.sleep(delay)
            
            logger.info(f"批量更新完成! 成功: {self.updated_count}, 失败: {self.failed_count}")
            
        except Exception as e:
            logger.error(f"批量更新失败: {e}")


async def main():
    """主函数"""
    try:
        # 创建更新器
        updater = DemoMediaUpdater()
        
        # 询问用户是否继续
        print("\n" + "="*60)
        print("准备使用精选媒体资源更新所有景点的图片和视频")
        print("这将替换现有的媒体资源为高质量的Unsplash图片")
        print("="*60)
        
        confirm = input("是否继续？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        # 开始批量更新
        start_time = datetime.now()
        await updater.update_all_attractions(batch_size=5, delay=0.5)
        end_time = datetime.now()
        
        # 输出总结
        duration = (end_time - start_time).total_seconds()
        print("\n" + "="*60)
        print("更新完成!")
        print(f"总耗时: {duration:.1f} 秒")
        print(f"成功更新: {updater.updated_count} 个景点")
        print(f"更新失败: {updater.failed_count} 个景点")
        print("详细日志已保存到 demo_media_update.log")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
