#!/usr/bin/env python3
"""
修复本地景点数据库的图片问题

功能：
1. 从Supabase数据库获取北京景点的真实图片URL
2. 更新local_attractions_db.py中的base64占位图
3. 确保前端显示真实的高质量图片
"""

import os
import sys
import logging
from typing import Dict, List

# 添加backend目录到路径
sys.path.append('backend')

from supabase_client import supabase_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalAttractionsImageFixer:
    """本地景点图片修复器"""
    
    def __init__(self):
        self.updated_count = 0
        self.failed_count = 0
        
    def get_supabase_attractions(self) -> Dict[str, Dict]:
        """从Supabase获取所有景点数据"""
        try:
            result = supabase_client.client.table('spot_attractions')\
                .select('name, main_image_url, video_url')\
                .execute()
            
            if result.data:
                attractions_dict = {}
                for row in result.data:
                    name = row['name']
                    attractions_dict[name] = {
                        'image': row.get('main_image_url', ''),
                        'video': row.get('video_url', '')
                    }
                
                logger.info(f"从Supabase获取到 {len(attractions_dict)} 个景点数据")
                return attractions_dict
            
            return {}
            
        except Exception as e:
            logger.error(f"获取Supabase景点数据失败: {e}")
            return {}
    
    def read_local_attractions_file(self) -> str:
        """读取本地景点数据库文件"""
        try:
            with open('backend/local_attractions_db.py', 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"读取本地景点文件失败: {e}")
            return ""
    
    def update_local_attractions_file(self, content: str):
        """更新本地景点数据库文件"""
        try:
            with open('backend/local_attractions_db.py', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("本地景点文件更新成功")
        except Exception as e:
            logger.error(f"更新本地景点文件失败: {e}")
    
    def fix_attractions_images(self):
        """修复景点图片"""
        try:
            logger.info("开始修复本地景点数据库的图片...")
            
            # 获取Supabase数据
            supabase_attractions = self.get_supabase_attractions()
            if not supabase_attractions:
                logger.error("无法获取Supabase景点数据，修复失败")
                return
            
            # 读取本地文件
            content = self.read_local_attractions_file()
            if not content:
                logger.error("无法读取本地景点文件，修复失败")
                return
            
            # 替换图片URL
            updated_content = content
            
            for attraction_name, data in supabase_attractions.items():
                image_url = data.get('image', '')
                video_url = data.get('video', '')
                
                if image_url and image_url.startswith('http'):
                    # 查找并替换该景点的base64图片
                    # 查找景点定义的开始
                    name_pattern = f'"name": "{attraction_name}"'
                    name_index = updated_content.find(name_pattern)
                    
                    if name_index != -1:
                        # 找到景点定义，查找其图片字段
                        # 从景点名称开始，找到下一个景点或文件结束
                        next_name_index = updated_content.find('"name":', name_index + len(name_pattern))
                        if next_name_index == -1:
                            next_name_index = len(updated_content)
                        
                        # 在这个范围内查找image字段
                        attraction_section = updated_content[name_index:next_name_index]
                        image_start = attraction_section.find('"image":')
                        
                        if image_start != -1:
                            # 找到image字段，替换其值
                            image_start_global = name_index + image_start
                            
                            # 找到image值的开始和结束
                            value_start = updated_content.find('"', image_start_global + 8)  # 8 = len('"image":')
                            if value_start != -1:
                                value_end = updated_content.find('"', value_start + 1)
                                
                                # 处理可能的转义字符
                                while value_end != -1 and updated_content[value_end - 1] == '\\':
                                    value_end = updated_content.find('"', value_end + 1)
                                
                                if value_end != -1:
                                    # 替换图片URL
                                    old_value = updated_content[value_start + 1:value_end]
                                    if 'data:image/svg+xml;base64' in old_value:
                                        new_section = updated_content[:value_start + 1] + image_url + updated_content[value_end:]
                                        updated_content = new_section
                                        self.updated_count += 1
                                        logger.info(f"✅ 更新景点图片: {attraction_name}")
                                    else:
                                        logger.info(f"⏭️ 景点 {attraction_name} 已有真实图片URL")
                        
                        # 同样处理视频URL
                        if video_url and video_url.startswith('http'):
                            attraction_section = updated_content[name_index:next_name_index]
                            video_start = attraction_section.find('"video":')
                            
                            if video_start != -1:
                                video_start_global = name_index + video_start
                                value_start = updated_content.find(':', video_start_global + 7)  # 7 = len('"video"')
                                
                                if value_start != -1:
                                    # 跳过空格
                                    while value_start < len(updated_content) and updated_content[value_start] in ': \t':
                                        value_start += 1
                                    
                                    if updated_content[value_start:value_start + 4] == 'None':
                                        # 替换None为视频URL
                                        new_section = updated_content[:value_start] + f'"{video_url}"' + updated_content[value_start + 4:]
                                        updated_content = new_section
                                        logger.info(f"✅ 添加景点视频: {attraction_name}")
                    else:
                        logger.warning(f"⚠️ 未找到景点: {attraction_name}")
                        self.failed_count += 1
            
            # 保存更新后的文件
            if self.updated_count > 0:
                self.update_local_attractions_file(updated_content)
                logger.info(f"修复完成! 更新了 {self.updated_count} 个景点的图片")
            else:
                logger.info("所有景点图片都已是最新状态")
            
        except Exception as e:
            logger.error(f"修复景点图片失败: {e}")
    
    def generate_report(self):
        """生成修复报告"""
        print("\n" + "="*60)
        print("本地景点图片修复报告")
        print("="*60)
        print(f"✅ 成功更新: {self.updated_count} 个景点")
        print(f"❌ 更新失败: {self.failed_count} 个景点")
        print("="*60)


def main():
    """主函数"""
    try:
        fixer = LocalAttractionsImageFixer()
        
        print("\n" + "="*60)
        print("本地景点数据库图片修复工具")
        print("- 从Supabase获取真实图片URL")
        print("- 替换local_attractions_db.py中的base64占位图")
        print("- 确保前端显示高质量图片")
        print("="*60)
        
        confirm = input("是否开始修复？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        fixer.fix_attractions_images()
        fixer.generate_report()
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    main()
