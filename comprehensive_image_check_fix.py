#!/usr/bin/env python3
"""
全面的景点图片检查和修复脚本

功能：
1. 检查所有景点的图片状态
2. 验证图片URL的可访问性
3. 使用Pexels API重新获取无效图片
4. 确保海外和国内景点图片一致性
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
import requests
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
        logging.FileHandler('comprehensive_image_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveImageChecker:
    """全面的图片检查和修复器"""
    
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        if not self.pexels_key:
            raise ValueError("请确保PEXELS_API_KEY已配置")
        
        self.updated_count = 0
        self.failed_count = 0
        
        # 景点英文关键词映射（扩展版）
        self.english_keywords = {
            # 中国景点
            "故宫博物院": ["Forbidden City", "Beijing Palace", "Imperial Palace"],
            "天安门广场": ["Tiananmen Square", "Beijing square", "China square"],
            "天坛公园": ["Temple of Heaven", "Beijing temple", "Chinese temple"],
            "颐和园": ["Summer Palace", "Beijing garden", "Imperial garden"],
            "圆明园": ["Old Summer Palace", "Beijing ruins", "Imperial ruins"],
            "北海公园": ["Beihai Park", "Beijing park", "Chinese garden"],
            "景山公园": ["Jingshan Park", "Beijing hill", "Imperial hill"],
            "八达岭长城": ["Badaling Great Wall", "Great Wall", "China wall"],
            "慕田峪长城": ["Mutianyu Great Wall", "Great Wall China", "Beijing wall"],
            "居庸关长城": ["Juyongguan Great Wall", "Great Wall pass", "Beijing Great Wall"],
            "明十三陵": ["Ming Tombs", "Beijing tombs", "Imperial tombs"],
            "雍和宫": ["Lama Temple", "Beijing temple", "Tibetan temple"],
            "什刹海": ["Shichahai", "Beijing lake", "Chinese hutong"],
            "南锣鼓巷": ["Nanluoguxiang", "Beijing hutong", "Chinese alley"],
            "王府井大街": ["Wangfujing Street", "Beijing shopping", "Chinese street"],
            "前门大街": ["Qianmen Street", "Beijing street", "Chinese shopping"],
            "三里屯太古里": ["Sanlitun", "Beijing nightlife", "Chinese shopping"],
            "798艺术区": ["798 Art Zone", "Beijing art", "Chinese art district"],
            "鸟巢（国家体育场）": ["Birds Nest", "Beijing stadium", "Olympic stadium"],
            "水立方（国家游泳中心）": ["Water Cube", "Beijing aquatics", "Olympic pool"],
            "恭王府": ["Prince Gong Palace", "Beijing mansion", "Qing palace"],
            "香山公园": ["Fragrant Hills", "Beijing mountain", "Chinese park"],
            "中山公园": ["Zhongshan Park", "Beijing park", "Chinese garden"],
            
            # 法国景点
            "埃菲尔铁塔": ["Eiffel Tower", "Paris tower", "France landmark"],
            "卢浮宫": ["Louvre Museum", "Paris museum", "Mona Lisa museum"],
            "凯旋门": ["Arc de Triomphe", "Paris arch", "Champs Elysees"],
            "香榭丽舍大街": ["Champs Elysees", "Paris avenue", "French street"],
            "巴黎圣母院": ["Notre Dame", "Paris cathedral", "Gothic cathedral"],
            "蒙马特高地": ["Montmartre", "Paris hill", "Sacre Coeur"],
            
            # 英国景点
            "大本钟": ["Big Ben", "London clock", "Westminster"],
            "伦敦眼": ["London Eye", "London wheel", "Thames wheel"],
            "白金汉宫": ["Buckingham Palace", "London palace", "British palace"],
            "大英博物馆": ["British Museum", "London museum", "UK museum"],
            "塔桥": ["Tower Bridge", "London bridge", "Thames bridge"],
            "西敏寺": ["Westminster Abbey", "London abbey", "British church"],
            
            # 意大利景点
            "斗兽场": ["Colosseum", "Rome arena", "Roman amphitheater"],
            "万神殿": ["Pantheon", "Rome temple", "Roman architecture"],
            "罗马广场": ["Roman Forum", "Rome ruins", "Ancient Rome"],
            "特雷维喷泉": ["Trevi Fountain", "Rome fountain", "Italian fountain"],
            "西班牙阶梯": ["Spanish Steps", "Rome steps", "Italian stairs"],
            
            # 其他景点
            "大唐不夜城": ["Datang Everbright City", "Xian night market", "Chinese cultural district"],
            "凯旋门": ["Arc de Triomphe", "Paris arch", "French monument"],
            "卢浮宫": ["Louvre Palace", "Paris art museum", "French museum"]
        }
        
        logger.info("全面图片检查器初始化完成")
    
    async def check_image_accessibility(self, url: str) -> bool:
        """检查图片URL是否可访问"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"图片访问检查失败 {url}: {e}")
            return False
    
    async def search_pexels_images(self, query: str, count: int = 3) -> List[Dict]:
        """使用Pexels API搜索图片"""
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": min(count, 80),
                "orientation": "landscape",
                "size": "large"
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
    
    async def check_and_fix_attraction_image(self, attraction: Dict) -> bool:
        """检查并修复单个景点的图片"""
        try:
            attraction_id = attraction['id']
            attraction_name = attraction.get('name', '')
            current_image_url = attraction.get('main_image_url', '')
            
            logger.info(f"检查景点图片: {attraction_name}")
            
            # 检查当前图片是否有效
            needs_update = False
            
            if not current_image_url or current_image_url.strip() == '':
                logger.warning(f"景点 {attraction_name} 无图片URL")
                needs_update = True
            elif 'data:image/svg+xml' in current_image_url or 'base64' in current_image_url:
                logger.warning(f"景点 {attraction_name} 使用无效的base64图片")
                needs_update = True
            elif not current_image_url.startswith('http'):
                logger.warning(f"景点 {attraction_name} 图片URL格式无效")
                needs_update = True
            else:
                # 检查图片是否可访问
                is_accessible = await self.check_image_accessibility(current_image_url)
                if not is_accessible:
                    logger.warning(f"景点 {attraction_name} 图片无法访问")
                    needs_update = True
                else:
                    logger.info(f"景点 {attraction_name} 图片正常")
                    return True
            
            # 如果需要更新，搜索新图片
            if needs_update:
                logger.info(f"开始为景点 {attraction_name} 搜索新图片")
                
                # 获取搜索关键词
                search_queries = self.english_keywords.get(attraction_name, [attraction_name])
                
                all_images = []
                for query in search_queries:
                    if len(all_images) >= 3:
                        break
                    
                    images = await self.search_pexels_images(query, 2)
                    all_images.extend(images)
                    await asyncio.sleep(0.5)  # API限制
                
                if all_images:
                    # 选择最佳图片
                    best_image = all_images[0]
                    new_image_url = best_image['url']
                    
                    # 更新数据库
                    result = supabase_client.client.table('spot_attractions')\
                        .update({'main_image_url': new_image_url})\
                        .eq('id', attraction_id)\
                        .execute()
                    
                    if result.data:
                        logger.info(f"✅ 景点 {attraction_name} 图片更新成功: {new_image_url}")
                        self.updated_count += 1
                        return True
                    else:
                        logger.error(f"❌ 景点 {attraction_name} 数据库更新失败")
                else:
                    logger.warning(f"⚠️ 景点 {attraction_name} 未找到合适图片")
            
            return False
            
        except Exception as e:
            logger.error(f"检查修复景点图片失败 {attraction.get('name', '')}: {e}")
            self.failed_count += 1
            return False
    
    async def comprehensive_check_and_fix(self):
        """全面检查和修复所有景点图片"""
        try:
            logger.info("开始全面检查和修复景点图片")
            
            # 获取所有景点
            attractions = await self.get_all_attractions()
            if not attractions:
                logger.error("没有找到景点数据")
                return
            
            total_count = len(attractions)
            logger.info(f"总共需要检查 {total_count} 个景点")
            
            # 分类统计
            domestic_attractions = []
            foreign_attractions = []
            
            for attraction in attractions:
                country = attraction.get('country', '')
                if country == '中国':
                    domestic_attractions.append(attraction)
                else:
                    foreign_attractions.append(attraction)
            
            logger.info(f"国内景点: {len(domestic_attractions)} 个")
            logger.info(f"海外景点: {len(foreign_attractions)} 个")
            
            # 检查和修复所有景点
            for i, attraction in enumerate(attractions):
                success = await self.check_and_fix_attraction_image(attraction)
                
                # 进度报告
                progress = ((i + 1) / total_count) * 100
                logger.info(f"检查进度: {i + 1}/{total_count} ({progress:.1f}%)")
                
                # 延迟避免API限制
                await asyncio.sleep(1.0)
            
            logger.info(f"全面检查修复完成! 更新: {self.updated_count}, 失败: {self.failed_count}")
            
        except Exception as e:
            logger.error(f"全面检查修复失败: {e}")
    
    async def generate_report(self):
        """生成检查报告"""
        try:
            logger.info("生成检查报告...")
            
            attractions = await self.get_all_attractions()
            
            # 统计分析
            total_count = len(attractions)
            domestic_count = sum(1 for a in attractions if a.get('country') == '中国')
            foreign_count = total_count - domestic_count
            
            valid_images = 0
            invalid_images = 0
            no_images = 0
            
            domestic_valid = 0
            foreign_valid = 0
            
            for attraction in attractions:
                image_url = attraction.get('main_image_url', '')
                country = attraction.get('country', '')
                
                if not image_url or image_url.strip() == '':
                    no_images += 1
                elif 'data:image/svg+xml' in image_url or 'base64' in image_url:
                    invalid_images += 1
                elif image_url.startswith('http'):
                    valid_images += 1
                    if country == '中国':
                        domestic_valid += 1
                    else:
                        foreign_valid += 1
                else:
                    invalid_images += 1
            
            # 生成报告
            report = f"""
# 景点图片检查报告

## 📊 总体统计
- 总景点数: {total_count}
- 国内景点: {domestic_count}
- 海外景点: {foreign_count}

## 🖼️ 图片状态
- ✅ 有效图片: {valid_images} ({valid_images/total_count*100:.1f}%)
- ❌ 无图片: {no_images}
- ⚠️ 无效图片: {invalid_images}

## 🌍 地区分布
- 国内景点有效图片: {domestic_valid}/{domestic_count} ({domestic_valid/domestic_count*100:.1f}%)
- 海外景点有效图片: {foreign_valid}/{foreign_count} ({foreign_valid/foreign_count*100:.1f}%)

## 📈 修复结果
- 本次更新: {self.updated_count} 个景点
- 更新失败: {self.failed_count} 个景点

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # 保存报告
            with open('image_check_report.md', 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(report)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")


async def main():
    """主函数"""
    try:
        # 创建检查器
        checker = ComprehensiveImageChecker()
        
        # 询问用户是否继续
        print("\n" + "="*60)
        print("全面景点图片检查和修复")
        print("- 检查所有景点图片的有效性")
        print("- 使用Pexels API更新无效图片")
        print("- 确保海外和国内景点图片一致性")
        print("="*60)
        
        confirm = input("是否开始检查和修复？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        # 开始检查和修复
        start_time = datetime.now()
        await checker.comprehensive_check_and_fix()
        end_time = datetime.now()
        
        # 生成报告
        await checker.generate_report()
        
        # 输出总结
        duration = (end_time - start_time).total_seconds()
        print("\n" + "="*60)
        print("检查修复完成!")
        print(f"总耗时: {duration:.1f} 秒")
        print(f"更新景点: {checker.updated_count} 个")
        print(f"失败景点: {checker.failed_count} 个")
        print("详细日志: comprehensive_image_check.log")
        print("检查报告: image_check_report.md")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
