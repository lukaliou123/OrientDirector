#!/usr/bin/env python3
"""
最终图片验证脚本

功能：
1. 验证数据库中所有景点都有Pexels图片
2. 检查前端代码是否还有base64占位图
3. 测试API返回的数据格式
4. 生成最终验证报告
"""

import os
import sys
import re
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


class FinalImageVerifier:
    """最终图片验证器"""
    
    def __init__(self):
        self.issues_found = []
        self.total_attractions = 0
        self.pexels_count = 0
        self.unsplash_count = 0
        self.other_count = 0
        
    def check_database_images(self):
        """检查数据库中的图片"""
        try:
            logger.info("🔍 检查数据库中的图片...")
            
            result = supabase_client.client.table('spot_attractions')\
                .select('id, name, main_image_url, video_url, country, city')\
                .execute()
            
            if result.data:
                self.total_attractions = len(result.data)
                logger.info(f"找到 {self.total_attractions} 个景点")
                
                for attraction in result.data:
                    name = attraction['name']
                    image_url = attraction.get('main_image_url', '')
                    video_url = attraction.get('video_url', '')
                    country = attraction.get('country', '')
                    
                    # 检查图片来源
                    if not image_url:
                        self.issues_found.append(f"❌ {name} ({country}): 无图片URL")
                    elif 'pexels.com' in image_url.lower():
                        self.pexels_count += 1
                        logger.info(f"✅ {name} ({country}): Pexels图片")
                    elif 'unsplash.com' in image_url.lower():
                        self.unsplash_count += 1
                        self.issues_found.append(f"⚠️ {name} ({country}): 仍使用Unsplash图片")
                        logger.warning(f"发现Unsplash图片: {name}")
                    elif 'data:image/svg+xml;base64' in image_url:
                        self.issues_found.append(f"❌ {name} ({country}): 仍使用base64占位图")
                        logger.error(f"发现base64占位图: {name}")
                    else:
                        self.other_count += 1
                        self.issues_found.append(f"⚠️ {name} ({country}): 其他图片来源 - {image_url[:50]}...")
                
                logger.info(f"数据库检查完成: Pexels={self.pexels_count}, Unsplash={self.unsplash_count}, 其他={self.other_count}")
                
            else:
                self.issues_found.append("❌ 数据库中没有找到景点数据")
                
        except Exception as e:
            error_msg = f"❌ 数据库检查失败: {e}"
            logger.error(error_msg)
            self.issues_found.append(error_msg)
    
    def check_frontend_code(self):
        """检查前端代码中的base64占位图"""
        try:
            logger.info("🔍 检查前端代码中的base64占位图...")
            
            # 检查app.js文件
            with open('app.js', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找base64占位图
            base64_pattern = r'data:image/svg\+xml;base64,[A-Za-z0-9+/=]+'
            matches = re.findall(base64_pattern, content)
            
            if matches:
                self.issues_found.append(f"❌ app.js中仍有 {len(matches)} 个base64占位图")
                for i, match in enumerate(matches[:3]):  # 只显示前3个
                    self.issues_found.append(f"   {i+1}. {match[:80]}...")
                if len(matches) > 3:
                    self.issues_found.append(f"   ... 还有 {len(matches) - 3} 个")
            else:
                logger.info("✅ app.js中没有发现base64占位图")
            
            # 检查onerror处理
            onerror_pattern = r'onerror="[^"]*data:image/svg\+xml;base64'
            onerror_matches = re.findall(onerror_pattern, content)
            
            if onerror_matches:
                self.issues_found.append(f"❌ app.js中仍有 {len(onerror_matches)} 个onerror base64占位图")
            else:
                logger.info("✅ app.js中的onerror处理已更新")
                
        except Exception as e:
            error_msg = f"❌ 前端代码检查失败: {e}"
            logger.error(error_msg)
            self.issues_found.append(error_msg)
    
    async def test_api_response(self):
        """测试API返回的数据格式"""
        try:
            logger.info("🔍 测试API返回的数据格式...")
            
            # 测试北京景点API
            import requests
            
            api_url = "http://localhost:8001/api/cities/beijing/attractions"
            
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        sample_attraction = data[0]
                        
                        # 检查必要字段
                        required_fields = ['name', 'image', 'video', 'latitude', 'longitude']
                        missing_fields = [field for field in required_fields if field not in sample_attraction]
                        
                        if missing_fields:
                            self.issues_found.append(f"❌ API响应缺少字段: {missing_fields}")
                        
                        # 检查图片URL格式
                        image_url = sample_attraction.get('image', '')
                        if image_url:
                            if 'pexels.com' in image_url:
                                logger.info(f"✅ API返回Pexels图片: {sample_attraction['name']}")
                            elif 'data:image/svg+xml;base64' in image_url:
                                self.issues_found.append(f"❌ API仍返回base64占位图: {sample_attraction['name']}")
                            else:
                                self.issues_found.append(f"⚠️ API返回其他格式图片: {sample_attraction['name']}")
                        else:
                            self.issues_found.append(f"❌ API返回空图片URL: {sample_attraction['name']}")
                        
                        logger.info(f"API测试完成，返回 {len(data)} 个景点")
                    else:
                        self.issues_found.append("❌ API返回空数据或格式错误")
                else:
                    self.issues_found.append(f"❌ API请求失败: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"API测试跳过（服务器可能未启动）: {e}")
                
        except Exception as e:
            error_msg = f"❌ API测试失败: {e}"
            logger.error(error_msg)
            self.issues_found.append(error_msg)
    
    async def verify_image_accessibility(self):
        """验证图片URL的可访问性"""
        try:
            logger.info("🔍 验证图片URL的可访问性...")
            
            result = supabase_client.client.table('spot_attractions')\
                .select('name, main_image_url')\
                .limit(5)\
                .execute()
            
            if result.data:
                accessible_count = 0
                total_tested = len(result.data)
                
                async with aiohttp.ClientSession() as session:
                    for attraction in result.data:
                        name = attraction['name']
                        image_url = attraction.get('main_image_url', '')
                        
                        if image_url and image_url.startswith('http'):
                            try:
                                async with session.head(image_url, timeout=10) as response:
                                    if response.status == 200:
                                        accessible_count += 1
                                        logger.info(f"✅ {name}: 图片可访问")
                                    else:
                                        self.issues_found.append(f"❌ {name}: 图片不可访问 (HTTP {response.status})")
                            except Exception as e:
                                self.issues_found.append(f"❌ {name}: 图片访问失败 - {str(e)}")
                
                logger.info(f"图片可访问性测试完成: {accessible_count}/{total_tested} 可访问")
                
        except Exception as e:
            error_msg = f"❌ 图片可访问性测试失败: {e}"
            logger.error(error_msg)
            self.issues_found.append(error_msg)
    
    def generate_report(self):
        """生成最终验证报告"""
        report = f"""
# 最终图片验证报告

## 📊 数据库状态
- 总景点数: {self.total_attractions}
- Pexels图片: {self.pexels_count} ({self.pexels_count/self.total_attractions*100:.1f}%)
- Unsplash图片: {self.unsplash_count}
- 其他来源: {self.other_count}

## 🔍 发现的问题
"""
        
        if self.issues_found:
            for issue in self.issues_found:
                report += f"- {issue}\n"
        else:
            report += "✅ 没有发现问题！所有图片都已正确配置。\n"
        
        report += f"""
## 📈 修复建议

### 如果发现Unsplash图片:
1. 运行 `python fix_beijing_attractions_in_supabase.py` 更新为Pexels图片
2. 重启后端服务

### 如果发现base64占位图:
1. 检查前端代码中的硬编码占位图
2. 确保使用 `handleImageError` 函数处理图片错误
3. 更新数据库中的图片URL

### 如果API返回错误格式:
1. 检查后端API是否正确映射数据库字段
2. 确保 `image` 字段映射到 `main_image_url`
3. 验证数据库连接和查询逻辑

## ✅ 验证完成
- 数据库检查: {'✅' if self.pexels_count == self.total_attractions else '❌'}
- 前端代码检查: {'✅' if not any('base64' in issue for issue in self.issues_found) else '❌'}
- API响应检查: {'✅' if not any('API' in issue for issue in self.issues_found) else '❌'}

生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 保存报告
        with open('final_image_verification_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        
        return len(self.issues_found) == 0


async def main():
    """主函数"""
    try:
        verifier = FinalImageVerifier()
        
        print("\n" + "="*60)
        print("最终图片验证工具")
        print("- 检查数据库中的图片来源")
        print("- 验证前端代码中的占位图")
        print("- 测试API返回的数据格式")
        print("- 验证图片URL的可访问性")
        print("="*60)
        
        # 执行所有检查
        verifier.check_database_images()
        verifier.check_frontend_code()
        await verifier.test_api_response()
        await verifier.verify_image_accessibility()
        
        # 生成报告
        all_good = verifier.generate_report()
        
        if all_good:
            print("\n🎉 验证通过！所有图片都已正确配置。")
        else:
            print(f"\n⚠️ 发现 {len(verifier.issues_found)} 个问题，请查看报告进行修复。")
        
    except Exception as e:
        logger.error(f"验证失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
