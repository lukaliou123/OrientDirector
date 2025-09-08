#!/usr/bin/env python3
"""
测试数据库连接和景点数据结构
"""

import os
import sys
import json
from dotenv import load_dotenv

# 添加backend目录到路径
sys.path.append('backend')

load_dotenv()

def test_supabase_connection():
    """测试Supabase连接"""
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            print("❌ 缺少Supabase配置")
            print("需要在.env文件中设置:")
            print("  SUPABASE_URL=your_supabase_url")
            print("  SUPABASE_ANON_KEY=your_anon_key")
            return False
        
        print(f"🔗 连接到Supabase: {url}")
        client = create_client(url, key)
        
        # 测试连接 - 查询景点表
        result = client.table('spot_attractions').select('count').execute()
        print(f"✅ Supabase连接成功")
        return client
        
    except Exception as e:
        print(f"❌ Supabase连接失败: {e}")
        return None

def test_attractions_table(client):
    """测试景点表结构"""
    try:
        print("\n📊 检查景点表结构...")
        
        # 获取少量数据查看结构
        result = client.table('spot_attractions').select('*').limit(3).execute()
        
        if result.data:
            print(f"✅ 找到 {len(result.data)} 个景点样本")
            
            # 显示第一个景点的结构
            if result.data:
                print("\n📋 景点数据结构:")
                sample = result.data[0]
                for key, value in sample.items():
                    value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"  {key}: {value_str}")
            
            return result.data
        else:
            print("⚠️  景点表为空")
            return []
            
    except Exception as e:
        print(f"❌ 查询景点表失败: {e}")
        return None

def test_media_table(client):
    """测试媒体表结构"""
    try:
        print("\n🎬 检查媒体表结构...")
        
        # 检查媒体表是否存在
        result = client.table('spot_attraction_media').select('*').limit(3).execute()
        
        if result.data:
            print(f"✅ 找到 {len(result.data)} 个媒体记录样本")
            
            # 显示媒体记录结构
            if result.data:
                print("\n📋 媒体数据结构:")
                sample = result.data[0]
                for key, value in sample.items():
                    value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"  {key}: {value_str}")
        else:
            print("⚠️  媒体表为空")
        
        return result.data
        
    except Exception as e:
        print(f"❌ 查询媒体表失败: {e}")
        print("   媒体表可能不存在，将在更新时自动创建")
        return []

def get_attractions_count(client):
    """获取景点总数"""
    try:
        result = client.table('spot_attractions').select('id').execute()
        count = len(result.data) if result.data else 0
        print(f"\n📈 数据库统计:")
        print(f"  总景点数: {count}")
        
        if count > 0:
            # 统计有图片的景点
            result_with_image = client.table('spot_attractions')\
                .select('id')\
                .not_.is_('main_image_url', 'null')\
                .execute()
            
            with_image = len(result_with_image.data) if result_with_image.data else 0
            
            # 统计有视频的景点
            result_with_video = client.table('spot_attractions')\
                .select('id')\
                .not_.is_('video_url', 'null')\
                .execute()
            
            with_video = len(result_with_video.data) if result_with_video.data else 0
            
            print(f"  有图片的景点: {with_image} ({with_image/count*100:.1f}%)")
            print(f"  有视频的景点: {with_video} ({with_video/count*100:.1f}%)")
        
        return count
        
    except Exception as e:
        print(f"❌ 统计景点数量失败: {e}")
        return 0

def main():
    """主函数"""
    print("="*60)
    print("数据库连接和结构测试")
    print("="*60)
    
    # 测试Supabase连接
    client = test_supabase_connection()
    if not client:
        return
    
    # 测试景点表
    attractions = test_attractions_table(client)
    if attractions is None:
        return
    
    # 测试媒体表
    test_media_table(client)
    
    # 获取统计信息
    count = get_attractions_count(client)
    
    print("\n" + "="*60)
    if count > 0:
        print("✅ 数据库连接正常，可以开始更新媒体资源")
        print("\n📝 接下来的步骤:")
        print("1. 运行: python setup_pexels_api.py  # 配置Pexels API密钥")
        print("2. 运行: python update_attractions_media.py  # 更新所有景点媒体")
    else:
        print("⚠️  数据库中没有景点数据")
        print("   请先添加景点数据再进行媒体更新")
    print("="*60)

if __name__ == "__main__":
    main()
