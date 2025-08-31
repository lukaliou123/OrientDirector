#!/usr/bin/env python3
"""
测试Langchain集成
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

async def test_langchain_availability():
    """测试Langchain包是否可用"""
    print("🔍 测试Langchain包可用性...")
    
    try:
        # 测试导入Langchain核心包
        from langchain_core import __version__ as core_version
        print(f"✅ langchain-core: {core_version}")
    except ImportError as e:
        print(f"❌ langchain-core 不可用: {e}")
        return False
    
    try:
        # 测试导入Langchain OpenAI
        from langchain_openai import ChatOpenAI
        print("✅ langchain-openai 可用")
    except ImportError as e:
        print(f"❌ langchain-openai 不可用: {e}")
        return False
    
    try:
        # 测试导入提示模板
        from langchain_core.prompts import ChatPromptTemplate
        print("✅ langchain prompts 可用")
    except ImportError as e:
        print(f"❌ langchain prompts 不可用: {e}")
        return False
    
    try:
        # 测试导入输出解析器
        from langchain_core.output_parsers import PydanticOutputParser
        print("✅ langchain output parsers 可用")
    except ImportError as e:
        print(f"❌ langchain output parsers 不可用: {e}")
        return False
    
    return True

async def test_langchain_service():
    """测试Langchain AI服务"""
    print("\n🚀 测试Langchain AI服务...")
    
    # 检查API密钥
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ 未找到OPENAI_API_KEY环境变量")
        return False
    
    try:
        from langchain_ai_service import get_langchain_ai_service
        
        # 获取服务实例
        service = get_langchain_ai_service()
        if not service:
            print("❌ 无法创建Langchain AI服务实例")
            return False
        
        print("✅ Langchain AI服务实例创建成功")
        
        # 测试场景锐评生成
        print("🎯 测试场景锐评生成...")
        review_result = await service.generate_scene_review(
            scene_name="测试景点",
            scene_description="这是一个用于测试的景点",
            scene_type="测试类型",
            user_context={
                "visit_count": 1,
                "time_of_day": "下午",
                "previous_places": ["起始点"]
            }
        )
        
        if review_result and review_result.get('title'):
            print(f"✅ Langchain场景锐评测试成功")
            print(f"   标题: {review_result['title']}")
            print(f"   内容: {review_result['review'][:50]}...")
            return True
        else:
            print("❌ Langchain场景锐评测试失败")
            return False
    
    except Exception as e:
        print(f"❌ Langchain AI服务测试失败: {e}")
        return False

async def test_traditional_ai_service():
    """测试传统AI服务"""
    print("\n🤖 测试传统AI服务...")
    
    try:
        from ai_service import get_ai_service
        
        # 获取服务实例
        service = get_ai_service()
        if not service:
            print("❌ 无法创建AI服务实例")
            return False
        
        print("✅ AI服务实例创建成功")
        
        # 测试场景锐评生成
        print("🎯 测试场景锐评生成...")
        review_result = await service.generate_scene_review(
            scene_name="测试景点",
            scene_description="这是一个用于测试的景点",
            scene_type="测试类型"
        )
        
        if review_result and review_result.get('title'):
            print(f"✅ AI场景锐评测试成功")
            print(f"   标题: {review_result['title']}")
            print(f"   内容: {review_result['review'][:50]}...")
            return True
        else:
            print("❌ AI场景锐评测试失败")
            return False
    
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 OrientDiscover Langchain集成测试")
    print("=" * 50)
    
    # 测试Langchain包可用性
    langchain_available = await test_langchain_availability()
    
    if langchain_available:
        # 测试Langchain服务
        langchain_service_ok = await test_langchain_service()
    else:
        print("⚠️ Langchain不可用，跳过Langchain服务测试")
        langchain_service_ok = False
    
    # 测试传统AI服务
    traditional_service_ok = await test_traditional_ai_service()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"Langchain包可用: {'✅' if langchain_available else '❌'}")
    print(f"Langchain服务: {'✅' if langchain_service_ok else '❌'}")
    print(f"传统AI服务: {'✅' if traditional_service_ok else '❌'}")
    
    if langchain_service_ok:
        print("\n🎉 Langchain集成测试通过！")
        print("💡 建议：设置环境变量 USE_LANGCHAIN=true 来启用Langchain")
    elif traditional_service_ok:
        print("\n⚠️ Langchain集成不可用，但传统AI服务正常")
        print("💡 建议：安装Langchain依赖包或使用传统模式")
    else:
        print("\n❌ 所有AI服务均不可用，请检查配置")
    
    return langchain_service_ok or traditional_service_ok

if __name__ == "__main__":
    asyncio.run(main())
