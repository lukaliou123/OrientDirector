"""
AI服务模块 - 集成Langchain和OpenAI
负责生成场景锐评和个性化内容
支持Langchain和传统OpenAI两种模式
"""

import os
import asyncio
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# 尝试导入Langchain AI服务
try:
    from langchain_ai_service import get_langchain_ai_service, LangchainAIService
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logging.warning(f"⚠️ Langchain不可用，将使用传统OpenAI服务: {e}")

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """AI服务类，优先使用Langchain，回退到传统API调用"""
    
    def __init__(self):
        self.use_langchain = os.getenv('USE_LANGCHAIN', 'true').lower() == 'true'
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai')

        # 优先尝试使用Langchain
        self.langchain_service = None
        if LANGCHAIN_AVAILABLE and self.use_langchain:
            try:
                self.langchain_service = get_langchain_ai_service()
                if self.langchain_service:
                    logger.info(f"✅ AI服务初始化完成，使用Langchain + {self.ai_provider.capitalize()}")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Langchain服务初始化失败，回退到传统API: {e}")

        # 回退到传统API客户端
        if self.ai_provider == 'gemini':
            self.api_key = os.getenv('GEMINI_API_KEY')
            self.model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-latest')
            if not self.api_key:
                raise ValueError("❌ 未找到GEMINI_API_KEY环境变量")
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"✅ AI服务初始化完成，使用传统Gemini: {self.model}")
        
        elif self.ai_provider == 'openai':
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            if not self.api_key:
                raise ValueError("❌ 未找到OPENAI_API_KEY环境变量")
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info(f"✅ AI服务初始化完成，使用传统OpenAI: {self.model}")
        
        else:
            raise ValueError(f"❌ 不支持的AI_PROVIDER: {self.ai_provider}")
    
    async def generate_scene_review(
        self, 
        scene_name: str, 
        scene_description: str, 
        scene_type: str = "自然景观",
        user_context: Dict = None
    ) -> Dict[str, str]:
        """
        生成场景锐评（优先使用Langchain）
        
        Args:
            scene_name: 场景名称
            scene_description: 场景描述
            scene_type: 场景类型
            user_context: 用户上下文信息（可选）
        
        Returns:
            包含锐评内容的字典
        """
        # 优先使用Langchain服务
        if self.langchain_service:
            try:
                logger.info(f"🚀 使用Langchain为场景 '{scene_name}' 生成锐评...")
                review_data = await self.langchain_service.generate_scene_review(
                    scene_name=scene_name,
                    scene_description=scene_description,
                    scene_type=scene_type,
                    user_context=user_context
                )
                logger.info(f"✅ Langchain锐评生成成功")
                return review_data
            except Exception as e:
                logger.warning(f"⚠️ Langchain锐评生成失败，回退到传统API: {e}")
        
        # 回退到传统API方法
        logger.info(f"🔄 正在使用传统 {self.ai_provider.capitalize()} 方法...")
        try:
            prompt = self._build_review_prompt(scene_name, scene_description, scene_type, user_context)
            logger.info(f"🤖 使用传统 {self.ai_provider.capitalize()} 为场景 '{scene_name}' 生成锐评...")
            logger.info(f"🔍 提示词长度: {len(prompt)}字符")

            if self.ai_provider == 'gemini':
                response = await self.client.generate_content_async(prompt)
                content = response.text.strip()
            else: # openai
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位资深的旅游达人和文案专家，擅长为各种景点写出有趣、个性化的锐评。你的评价风格幽默风趣，既有专业知识又贴近用户体验。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=500  # 注意: gemini-1.5-flash-latest 的 max_output_tokens 在模型初始化时设置
                )
                content = response.choices[0].message.content.strip()

            # 调试：显示AI原始返回内容
            logger.info(f"🔍 ===== {self.ai_provider.upper()}原始输出 =====")
            logger.info(f"内容长度: {len(content)}字符")
            logger.info(f"原始内容: <<<{content}>>>")
            logger.info(f"================================")
            
            # 解析AI返回的结构化内容
            review_data = self._parse_ai_response(content)
            
            logger.info(f"✅ 传统 {self.ai_provider.capitalize()} 锐评生成成功: {len(content)}字符")
            return review_data
            
        except Exception as e:
            logger.error(f"❌ AI锐评生成失败: {str(e)}")
            # 返回备用内容
            return self._get_fallback_review(scene_name, scene_description, scene_type)
    
    def _build_review_prompt(self, scene_name: str, scene_description: str, scene_type: str, user_context: Dict = None) -> str:
        """构建锐评生成的提示词"""
        
        base_prompt = f"""
请为以下景点生成一个有趣的锐评：

**景点名称**: {scene_name}
**景点类型**: {scene_type}  
**景点描述**: {scene_description}

请按以下JSON格式返回锐评内容：
{{
    "title": "锐评标题（简短有趣）",
    "review": "主要锐评内容（100-200字，风趣幽默但不失专业）",
    "highlights": ["亮点1", "亮点2", "亮点3"],
    "tips": "实用小贴士（50字以内）",
    "rating_reason": "推荐理由（30字以内）",
    "mood": "推荐心情（如：放松、冒险、学习、拍照等）"
}}

要求：
1. 语言风格要轻松幽默，像朋友推荐一样
2. 突出这个地方的独特性和值得去的理由
3. 可以适当调侃或吐槽，但要正面积极
4. 包含实用的游玩建议
5. 体现背包客探索的精神
"""
        
        # 如果有用户上下文，添加个性化内容
        if user_context:
            visit_count = user_context.get('visit_count', 0)
            time_of_day = user_context.get('time_of_day', '')
            previous_places = user_context.get('previous_places', [])
            
            context_info = f"""

**用户上下文**:
- 这是您今天访问的第{visit_count + 1}个地点
- 当前时间: {time_of_day}
- 之前访问过: {', '.join(previous_places) if previous_places else '无'}

请结合用户的探索历程，让锐评更加个性化和贴合当前的旅程状态。
"""
            base_prompt += context_info
        
        return base_prompt
    
    def _parse_ai_response(self, content: str) -> Dict[str, str]:
        """解析AI返回的JSON内容"""
        try:
            import json
            
            # 尝试直接解析JSON
            if content.startswith('{') and content.endswith('}'):
                return json.loads(content)
            
            # 尝试提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            
            # 如果无法解析JSON，返回纯文本格式
            return {
                "title": "AI锐评",
                "review": content,
                "highlights": ["AI生成内容"],
                "tips": "探索愉快！",
                "rating_reason": "值得一去",
                "mood": "探索"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ AI响应解析失败: {e}")
            return self._get_fallback_review("", content, "")
    
    def _get_fallback_review(self, scene_name: str, scene_description: str, scene_type: str) -> Dict[str, str]:
        """生成备用锐评内容（当AI服务不可用时）"""
        return {
            "title": f"探索发现：{scene_name}",
            "review": f"这里是{scene_name}，{scene_description} 虽然AI服务暂时不可用，但这不影响您的探索热情！每个地方都有其独特的魅力等待您去发现。",
            "highlights": [
                "真实场景探索",
                "独特地理位置", 
                "值得记录的时刻"
            ],
            "tips": "用心感受每个地方的独特魅力",
            "rating_reason": "探索本身就是最好的理由",
            "mood": "冒险"
        }
    
    async def generate_journey_summary_ai(
        self, 
        visited_scenes: List[Dict], 
        total_distance: float, 
        journey_duration: str
    ) -> str:
        """
        生成AI旅程总结（优先使用Langchain）
        
        Args:
            visited_scenes: 访问的场景列表
            total_distance: 总距离
            journey_duration: 旅程时长
        
        Returns:
            AI生成的旅程总结文本
        """
        # 优先使用Langchain服务
        if self.langchain_service:
            try:
                logger.info(f"🚀 使用Langchain生成旅程总结...")
                summary_data = await self.langchain_service.generate_journey_summary(
                    visited_scenes=visited_scenes,
                    total_distance=total_distance,
                    journey_duration=journey_duration
                )
                # 返回总结文本
                result = summary_data.get('summary', '')
                if summary_data.get('recommendation'):
                    result += f"\n\n{summary_data['recommendation']}"
                logger.info(f"✅ Langchain旅程总结生成成功")
                return result
            except Exception as e:
                logger.warning(f"⚠️ Langchain旅程总结生成失败，回退到传统API: {e}")
        
        # 回退到传统API方法
        try:
            scene_names = [scene.get('name', '未知地点') for scene in visited_scenes]
            
            prompt = self._build_journey_summary_prompt(visited_scenes, total_distance, journey_duration)
            
            logger.info(f"🤖 使用传统 {self.ai_provider.capitalize()} 生成旅程总结...")

            if self.ai_provider == 'gemini':
                response = await self.client.generate_content_async(prompt)
                result = response.text.strip()
            else: # openai
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位温暖的旅程记录者，擅长为用户的探索旅程写出感人的总结。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000
                )
                result = response.choices[0].message.content.strip()

            logger.info(f"✅ 传统 {self.ai_provider.capitalize()} 旅程总结生成成功")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI旅程总结生成失败: {str(e)}")
            return f"🎉 恭喜完成这次精彩的探索之旅！您访问了{len(visited_scenes)}个地点，总共行进了{total_distance:.1f}公里。每一步都是独特的发现，每一处风景都值得珍藏。感谢您选择方向探索派对，期待您的下次冒险！🧭✨"

    def _build_journey_summary_prompt(self, visited_scenes: List[Dict], total_distance: float, journey_duration: str) -> str:
        """构建旅程总结的提示词"""
        scene_names = [scene.get('name', '未知地点') for scene in visited_scenes]
        return f"""
请为以下旅程生成一个温馨有趣的总结：

**旅程信息**:
- 访问地点: {', '.join(scene_names)}
- 总距离: {total_distance}公里
- 旅程时长: {journey_duration}
- 探索方式: 方向探索派对工具

请生成一段100-150字的温馨总结，要求：
1. 体现背包客探索的精神
2. 突出这次旅程的独特性
3. 鼓励用户继续探索
4. 语言风格温暖友好
5. 可以适当加入emoji表情
"""

# 全局AI服务实例
ai_service = None

def get_ai_service() -> AIService:
    """获取AI服务实例（单例模式）"""
    global ai_service
    if ai_service is None:
        try:
            ai_service = AIService()
        except Exception as e:
            logger.error(f"❌ AI服务初始化失败: {e}")
            ai_service = None
    return ai_service

