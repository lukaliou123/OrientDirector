#!/usr/bin/env python3
"""
修复Supabase数据库中北京景点的图片问题

功能：
1. 使用Pexels API为北京景点重新搜索高质量图片
2. 更新Supabase数据库中的main_image_url和video_url字段
3. 确保所有景点都有高质量的图片和视频
"""

import os
import sys
import asyncio
import aiohttp
import logging
from typing import List, Dict
from dotenv import load_dotenv

# 添加backend目录到路径
sys.path.append('backend')

from supabase_client import supabase_client

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BeijingAttractionsUpdater:
    """北京景点更新器"""
    
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        if not self.pexels_key:
            raise ValueError("请确保PEXELS_API_KEY已配置")
        
        self.updated_count = 0
        self.failed_count = 0
        
        # 北京景点英文关键词
        self.beijing_keywords = {
            "天坛公园": ["Temple of Heaven Beijing", "Beijing temple", "Chinese temple architecture"],
            "圆明园": ["Old Summer Palace Beijing", "Beijing ruins", "Imperial garden ruins"],
            "北海公园": ["Beihai Park Beijing", "Beijing lake park", "Chinese imperial garden"],
            "八达岭长城": ["Badaling Great Wall", "Great Wall China", "Beijing Great Wall"],
            "明十三陵": ["Ming Tombs Beijing", "Beijing imperial tombs", "Chinese emperor tombs"],
            "三里屯太古里": ["Sanlitun Beijing", "Beijing shopping district", "modern Beijing"],
            "什刹海": ["Shichahai Beijing", "Beijing lake district", "Beijing hutong"],
            "南锣鼓巷": ["Nanluoguxiang Beijing", "Beijing hutong alley", "traditional Beijing"],
            "水立方（国家游泳中心）": ["Water Cube Beijing", "Beijing Olympic aquatics", "National Aquatics Center"],
            "恭王府": ["Prince Gong Palace Beijing", "Beijing mansion", "Qing dynasty palace"],
            "中山公园": ["Zhongshan Park Beijing", "Beijing city park", "Chinese urban park"],
            "前门大街": ["Qianmen Street Beijing", "Beijing shopping street", "traditional Beijing street"],
            "居庸关长城": ["Juyongguan Great Wall", "Great Wall pass Beijing", "Beijing Great Wall section"],
            "景山公园": ["Jingshan Park Beijing", "Beijing hill park", "Forbidden City view"],
            "雍和宫": ["Lama Temple Beijing", "Beijing Tibetan temple", "Yonghe Temple"],
            "王府井大街": ["Wangfujing Street Beijing", "Beijing shopping street", "famous Beijing street"],
            "鸟巢（国家体育场）": ["Birds Nest Beijing", "Beijing Olympic stadium", "National Stadium Beijing"],
            "798艺术区": ["798 Art Zone Beijing", "Beijing art district", "contemporary art Beijing"],
            "天安门广场": ["Tiananmen Square Beijing", "Beijing square", "China national square"],
            "颐和园": ["Summer Palace Beijing", "Beijing imperial garden", "Chinese royal garden"],
            "故宫博物院": ["Forbidden City Beijing", "Beijing palace museum", "Imperial Palace China"],
            "香山公园": ["Fragrant Hills Beijing", "Beijing mountain park", "autumn leaves Beijing"]
        }
    
    async def search_pexels_media(self, query: str) -> Dict:
        """搜索Pexels图片和视频"""
        try:
            # 搜索图片
            image_url = f"https://api.pexels.com/v1/search"
            video_url = f"https://api.pexels.com/videos/search"
            headers = {"Authorization": self.pexels_key}
            
            async with aiohttp.ClientSession() as session:
                # 搜索图片
                image_params = {
                    "query": query,
                    "per_page": 3,
                    "orientation": "landscape",
                    "size": "large"
                }
                
                async with session.get(image_url, headers=headers, params=image_params) as response:
                    if response.status == 200:
                        image_data = await response.json()
                        images = image_data.get("photos", [])
                    else:
                        images = []
                
                # 搜索视频
                video_params = {
                    "query": query,
                    "per_page": 2,
                    "orientation": "landscape",
                    "size": "medium"
                }
                
                async with session.get(video_url, headers=headers, params=video_params) as response:
                    if response.status == 200:
                        video_data = await response.json()
                        videos = video_data.get("videos", [])
                    else:
                        videos = []
                
                result = {
                    "image": images[0]["src"]["large"] if images else None,
                    "video": videos[0]["video_files"][0]["link"] if videos and videos[0].get("video_files") else None
                }
                
                logger.info(f"Pexels搜索成功: {query} -> 图片: {'✅' if result['image'] else '❌'}, 视频: {'✅' if result['video'] else '❌'}")
                return result
                
        except Exception as e:
            logger.error(f"Pexels搜索失败 {query}: {e}")
            return {"image": None, "video": None}
    
    async def get_beijing_attractions(self) -> List[Dict]:
        """获取北京景点数据"""
        try:
            result = supabase_client.client.table('spot_attractions')\
                .select('id, name, main_image_url, video_url, country')\
                .eq('country', '中国')\
                .execute()
            
            if result.data:
                logger.info(f"获取到 {len(result.data)} 个中国景点")
                return result.data
            
            return []
            
        except Exception as e:
            logger.error(f"获取北京景点失败: {e}")
            return []
    
    async def update_attraction_media(self, attraction: Dict) -> bool:
        """更新单个景点的媒体资源"""
        try:
            attraction_id = attraction['id']
            attraction_name = attraction['name']
            current_image = attraction.get('main_image_url', '')
            
            # 检查是否需要更新
            if current_image and 'pexels.com' in current_image:
                logger.info(f"⏭️ 景点 {attraction_name} 已有Pexels图片")
                return True
            
            logger.info(f"🔄 更新景点媒体: {attraction_name}")
            
            # 获取搜索关键词
            keywords = self.beijing_keywords.get(attraction_name, [attraction_name])
            
            best_media = {"image": None, "video": None}
            
            # 尝试多个关键词
            for keyword in keywords:
                if best_media["image"] and best_media["video"]:
                    break
                
                media = await self.search_pexels_media(keyword)
                
                if not best_media["image"] and media["image"]:
                    best_media["image"] = media["image"]
                
                if not best_media["video"] and media["video"]:
                    best_media["video"] = media["video"]
                
                await asyncio.sleep(0.5)  # API限制
            
            # 更新数据库
            if best_media["image"]:
                update_data = {"main_image_url": best_media["image"]}
                if best_media["video"]:
                    update_data["video_url"] = best_media["video"]
                
                result = supabase_client.client.table('spot_attractions')\
                    .update(update_data)\
                    .eq('id', attraction_id)\
                    .execute()
                
                if result.data:
                    logger.info(f"✅ 景点 {attraction_name} 更新成功")
                    self.updated_count += 1
                    return True
                else:
                    logger.error(f"❌ 景点 {attraction_name} 数据库更新失败")
            else:
                logger.warning(f"⚠️ 景点 {attraction_name} 未找到合适媒体")
            
            self.failed_count += 1
            return False
            
        except Exception as e:
            logger.error(f"更新景点媒体失败 {attraction.get('name', '')}: {e}")
            self.failed_count += 1
            return False
    
    async def update_all_beijing_attractions(self):
        """更新所有北京景点"""
        try:
            logger.info("开始更新北京景点媒体资源...")
            
            # 获取景点数据
            attractions = await self.get_beijing_attractions()
            if not attractions:
                logger.error("没有找到北京景点数据")
                return
            
            logger.info(f"找到 {len(attractions)} 个中国景点")
            
            # 更新每个景点
            for i, attraction in enumerate(attractions):
                await self.update_attraction_media(attraction)
                
                # 进度报告
                progress = ((i + 1) / len(attractions)) * 100
                logger.info(f"更新进度: {i + 1}/{len(attractions)} ({progress:.1f}%)")
                
                # 延迟避免API限制
                await asyncio.sleep(1.0)
            
            logger.info(f"更新完成! 成功: {self.updated_count}, 失败: {self.failed_count}")
            
        except Exception as e:
            logger.error(f"更新北京景点失败: {e}")
    
    def generate_report(self):
        """生成更新报告"""
        print("\n" + "="*60)
        print("北京景点媒体更新报告")
        print("="*60)
        print(f"✅ 成功更新: {self.updated_count} 个景点")
        print(f"❌ 更新失败: {self.failed_count} 个景点")
        print("="*60)


async def main():
    """主函数"""
    try:
        updater = BeijingAttractionsUpdater()
        
        print("\n" + "="*60)
        print("北京景点Supabase数据库媒体更新工具")
        print("- 使用Pexels API搜索高质量图片和视频")
        print("- 更新Supabase数据库中的媒体URL")
        print("- 确保前端显示高质量媒体资源")
        print("="*60)
        
        confirm = input("是否开始更新？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        await updater.update_all_beijing_attractions()
        updater.generate_report()
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
