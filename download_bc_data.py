#!/usr/bin/env python3
"""
批量下载historical-basemaps BC（公元前）历史数据
扩展时间覆盖范围到史前史和古代文明史
"""

import asyncio
import os
import sys
import aiohttp
import json
from datetime import datetime

# 添加backend到路径
sys.path.append('backend')
from historical_data_loader import HistoricalDataLoader

async def download_bc_historical_data():
    """下载BC（公元前）历史数据"""
    
    print("🏺 Historical-basemaps BC数据批量下载器")
    print("📅 时间范围：公元前123000年 - 公元前1年")
    print("=" * 60)
    
    # 初始化数据加载器
    loader = HistoricalDataLoader()
    
    # 提取BC数据集
    bc_datasets = {year: filename for year, filename in loader.available_datasets.items() if year < 0}
    
    print(f"📍 GitHub源: {loader.github_raw_base}")
    print(f"📁 缓存目录: {loader.cache_dir}")
    print(f"🕐 发现BC数据集: {len(bc_datasets)} 个")
    print()
    
    # 按时期分类显示BC数据
    print("📚 可用的BC历史数据集:")
    
    # 史前史 (>10000 BCE)
    prehistoric = [(year, filename) for year, filename in bc_datasets.items() if year <= -10000]
    print(f"🦕 史前史 ({len(prehistoric)}个):")
    for year, filename in sorted(prehistoric):
        period_name = get_period_name(year)
        print(f"   📆 {abs(year):,}年前 - {filename} ({period_name})")
    
    # 新石器时代 (10000-3000 BCE)
    neolithic = [(year, filename) for year, filename in bc_datasets.items() if -10000 < year <= -3000]
    print(f"🌾 新石器时代 ({len(neolithic)}个):")
    for year, filename in sorted(neolithic, reverse=True):
        period_name = get_period_name(year)
        print(f"   📆 公元前{abs(year)}年 - {filename} ({period_name})")
    
    # 青铜时代-古典时期 (3000-1 BCE)
    ancient = [(year, filename) for year, filename in bc_datasets.items() if -3000 < year < 0]
    print(f"🏛️ 青铜时代-古典时期 ({len(ancient)}个):")
    for year, filename in sorted(ancient, reverse=True):
        period_name = get_period_name(year)
        print(f"   📆 公元前{abs(year)}年 - {filename} ({period_name})")
    
    print()
    
    # 检查已缓存的BC数据
    cached_bc_files = []
    if os.path.exists(loader.cache_dir):
        all_files = [f for f in os.listdir(loader.cache_dir) if f.endswith('.geojson')]
        cached_bc_files = [f for f in all_files if f.startswith('world_bc')]
    
    print(f"📚 当前已缓存BC数据: {len(cached_bc_files)} 个")
    for file in sorted(cached_bc_files):
        size = os.path.getsize(os.path.join(loader.cache_dir, file)) / (1024*1024)
        print(f"   ✅ {file} ({size:.1f}MB)")
    
    # 找出缺失的BC数据
    cached_bc_years = []
    for file in cached_bc_files:
        try:
            if file.startswith('world_bc') and file.endswith('.geojson'):
                year_part = file[8:-8]  # 去掉 'world_bc' 前缀和 '.geojson' 后缀
                cached_bc_years.append(-int(year_part))
        except:
            pass
    
    missing_bc_years = []
    for year in bc_datasets.keys():
        if year not in cached_bc_years:
            missing_bc_years.append(year)
    
    missing_bc_years.sort(reverse=True)  # 按年份降序排列（越近的越靠前）
    
    print()
    print(f"📥 缺失的BC数据集: {len(missing_bc_years)} 个")
    
    if not missing_bc_years:
        print("🎉 所有BC历史数据已完整缓存！")
        return
    
    # 按重要性分组显示缺失数据
    important_periods = []  # 重要历史节点
    regular_periods = []    # 常规时期
    prehistoric_periods = [] # 史前时期
    
    for year in missing_bc_years:
        if year in [-323, -500, -1000, -2000, -3000]:  # 重要历史节点
            important_periods.append(year)
        elif year > -10000:  # 古代文明史
            regular_periods.append(year) 
        else:  # 史前史
            prehistoric_periods.append(year)
    
    if important_periods:
        print("🌟 重要历史节点:")
        for year in important_periods:
            filename = bc_datasets[year]
            period_name = get_period_name(year)
            print(f"   ⭐ 公元前{abs(year)}年 - {period_name}")
    
    if regular_periods:
        print("🏛️ 古代文明史:")
        for year in regular_periods:
            filename = bc_datasets[year]
            period_name = get_period_name(year)
            print(f"   📿 公元前{abs(year)}年 - {period_name}")
    
    if prehistoric_periods:
        print("🦕 史前史:")
        for year in prehistoric_periods:
            filename = bc_datasets[year]
            period_name = get_period_name(year)
            print(f"   🗿 {abs(year):,}年前 - {period_name}")
    
    print()
    print("🚀 开始自动下载所有BC数据...")
    print("-" * 50)
    
    # 批量下载
    download_stats = {
        'success': 0,
        'failed': 0,
        'total_size': 0
    }
    
    async with aiohttp.ClientSession() as session:
        for i, year in enumerate(missing_bc_years, 1):
            filename = bc_datasets[year]
            url = f"{loader.github_raw_base}/{filename}"
            period_name = get_period_name(year)
            
            print(f"📥 [{i}/{len(missing_bc_years)}] 下载公元前{abs(year)}年数据 ({period_name})...")
            print(f"   URL: {url}")
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        
                        # 验证JSON格式
                        try:
                            json_data = json.loads(data)
                            feature_count = len(json_data.get('features', []))
                        except:
                            raise Exception("无效的JSON格式")
                        
                        # 保存到缓存
                        cache_path = os.path.join(loader.cache_dir, filename)
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            f.write(data)
                        
                        file_size = len(data.encode('utf-8')) / (1024*1024)
                        download_stats['success'] += 1
                        download_stats['total_size'] += file_size
                        
                        print(f"   ✅ 下载成功: {feature_count} 个政治实体, {file_size:.1f}MB")
                        
                    else:
                        print(f"   ❌ 下载失败: HTTP {response.status}")
                        download_stats['failed'] += 1
                        
            except Exception as e:
                print(f"   ❌ 下载异常: {e}")
                download_stats['failed'] += 1
            
            print()
            
            # 添加延迟避免请求过频
            if i < len(missing_bc_years):
                await asyncio.sleep(1.5)
    
    print("-" * 50)
    print("📊 BC数据下载统计:")
    print(f"   ✅ 成功: {download_stats['success']} 个")
    print(f"   ❌ 失败: {download_stats['failed']} 个") 
    print(f"   📦 新增大小: {download_stats['total_size']:.1f}MB")
    
    # 显示最终统计
    final_cached = []
    final_bc_cached = []
    if os.path.exists(loader.cache_dir):
        final_cached = [f for f in os.listdir(loader.cache_dir) if f.endswith('.geojson')]
        final_bc_cached = [f for f in final_cached if f.startswith('world_bc')]
    
    total_cache_size = sum(os.path.getsize(os.path.join(loader.cache_dir, f)) for f in final_cached) / (1024*1024)
    
    print()
    print("🎊 BC数据下载完成！")
    print(f"📅 BC数据集: {len(final_bc_cached)}/{len(bc_datasets)} 个")
    print(f"📅 总数据集: {len(final_cached)}/{len(loader.available_datasets)} 个")
    print(f"💾 总缓存大小: {total_cache_size:.1f}MB")
    print(f"📁 存储位置: {os.path.abspath(loader.cache_dir)}")
    
    if len(final_cached) == len(loader.available_datasets):
        print("🌍 恭喜！所有历史数据（AD + BC）已完整下载！")
        time_span = 2000 - (-123000)  # 从公元前123000到公元2000年
        print(f"⏰ 时间覆盖: {time_span:,}年历史数据")

def get_period_name(year: int) -> str:
    """根据年份获取历史时期名称"""
    year = abs(year)
    
    if year >= 100000:
        return "旧石器时代晚期"
    elif year >= 50000:
        return "旧石器时代中期"
    elif year >= 10000:
        return "旧石器时代-中石器时代"
    elif year >= 8000:
        return "新石器时代早期"
    elif year >= 5000:
        return "新石器时代"
    elif year >= 3000:
        return "青铜时代早期"
    elif year >= 2000:
        return "青铜时代"
    elif year >= 1500:
        return "青铜时代晚期"
    elif year >= 1000:
        return "铁器时代早期"
    elif year >= 700:
        return "铁器时代"
    elif year >= 500:
        return "古典时代早期"
    elif year >= 323:
        return "希腊化时期"
    elif year >= 300:
        return "古典时代"
    elif year >= 200:
        return "罗马共和国时期"
    elif year >= 100:
        return "罗马共和国晚期"
    elif year >= 1:
        return "罗马帝国早期"
    else:
        return "未知时期"

async def main():
    """主函数"""
    try:
        await download_bc_historical_data()
    except KeyboardInterrupt:
        print("\n⏹️ 下载被用户中断")
    except Exception as e:
        print(f"\n❌ 下载过程出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())


