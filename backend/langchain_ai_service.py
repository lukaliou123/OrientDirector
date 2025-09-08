"""
基于Langchain的AI服务模块
使用Langchain框架提供更强大和灵活的AI功能
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import logging
import json

# Langchain imports
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from pydantic import BaseModel, Field  # 使用pydantic v2
from langchain_core.runnables import RunnablePassthrough
from langchain_core.exceptions import LangChainException

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# Pydantic模型定义AI输出结构
class SceneReviewOutput(BaseModel):
    """场景锐评输出结构"""
    title: str = Field(description="锐评标题，简短有趣")
    review: str = Field(description="主要锐评内容，100-200字，风趣幽默但不失专业")
    highlights: List[str] = Field(description="亮点列表，3-5个亮点")
    tips: str = Field(description="实用小贴士，50字以内")
    rating_reason: str = Field(description="推荐理由，30字以内")
    mood: str = Field(description="推荐心情，如：放松、冒险、学习、拍照等")

class JourneySummaryOutput(BaseModel):
    """旅程总结输出结构"""
    summary: str = Field(description="旅程总结内容，100-150字")
    highlights: List[str] = Field(description="旅程亮点")
    recommendation: str = Field(description="后续探索建议")

class LangchainAIService:
    """基于Langchain的AI服务类"""
    
    def __init__(self):
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai')
        
        if self.ai_provider == 'gemini':
            self.api_key = os.getenv('GEMINI_API_KEY')
            self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-latest')
            if not self.api_key:
                raise ValueError("❌ AI_PROVIDER设置为gemini，但未找到GEMINI_API_KEY环境变量")
            
            # 初始化Langchain Gemini模型
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                max_output_tokens=2048,
                temperature=0.8,
                top_p=0.9,
            )
            logger.info(f"✅ Langchain AI服务初始化完成，使用Gemini模型: {self.model_name}")

        elif self.ai_provider == 'openai':
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            if not self.api_key:
                raise ValueError("❌ AI_PROVIDER设置为openai，但未找到OPENAI_API_KEY环境变量")
            
            # 初始化Langchain OpenAI模型
            self.llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                max_tokens=2000,
                max_retries=3
            )
            logger.info(f"✅ Langchain AI服务初始化完成，使用OpenAI模型: {self.model_name}")

        else:
            raise ValueError(f"❌ 不支持的AI_PROVIDER: {self.ai_provider}。请选择 'openai' 或 'gemini'")

        # 初始化输出解析器
        self.review_parser = PydanticOutputParser(pydantic_object=SceneReviewOutput)
        self.summary_parser = PydanticOutputParser(pydantic_object=JourneySummaryOutput)
        self.json_parser = JsonOutputParser()
        
        # 初始化提示模板
        self._init_prompt_templates()
        
        # 构建链
        self._build_chains()
    
    def _init_prompt_templates(self):
        """初始化Langchain提示模板"""
        
        # 场景锐评提示模板
        self.review_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深的旅游达人和文案专家，擅长为各种景点写出有趣、个性化的锐评。
你的评价风格幽默风趣，既有专业知识又贴近用户体验。
你需要按照指定的JSON格式返回结构化的锐评内容。"""),
            ("human", """请为以下景点生成一个有趣的锐评：

**景点名称**: {scene_name}
**景点类型**: {scene_type}  
**景点描述**: {scene_description}

{user_context_info}

要求：
1. 语言风格要轻松幽默，像朋友推荐一样
2. 突出这个地方的独特性和值得去的理由
3. 可以适当调侃或吐槽，但要正面积极
4. 包含实用的游玩建议
5. 体现背包客探索的精神

{format_instructions}""")
        ])
        
        # 旅程总结提示模板
        self.summary_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """你是一位温暖的旅程记录者，擅长为用户的探索旅程写出感人的总结。
你的文风温暖友好，善于发现旅程中的美好和意义。"""),
            ("human", """请为以下旅程生成一个温馨有趣的总结：

**旅程信息**:
- 访问地点: {scene_names}
- 总距离: {total_distance}公里
- 旅程时长: {journey_duration}
- 探索方式: 方向探索派对工具

要求：
1. 体现背包客探索的精神
2. 突出这次旅程的独特性
3. 鼓励用户继续探索
4. 语言风格温暖友好
5. 可以适当加入emoji表情

{format_instructions}""")
        ])
    
    def _build_chains(self):
        """构建Langchain执行链"""
        
        # 场景锐评生成链
        self.review_chain = (
            {
                "scene_name": RunnablePassthrough(),
                "scene_type": RunnablePassthrough(), 
                "scene_description": RunnablePassthrough(),
                "user_context_info": RunnablePassthrough(),
                "format_instructions": lambda _: self.review_parser.get_format_instructions()
            }
            | self.review_prompt_template
            | self.llm
        )
        
        # 旅程总结生成链
        self.summary_chain = (
            {
                "scene_names": RunnablePassthrough(),
                "total_distance": RunnablePassthrough(),
                "journey_duration": RunnablePassthrough(),
                "format_instructions": lambda _: self.summary_parser.get_format_instructions()
            }
            | self.summary_prompt_template
            | self.llm
            | self.summary_parser
        )
    
    async def generate_scene_review(
        self,
        scene_name: str,
        scene_description: str,
        scene_type: str = "自然景观",
        user_context: Dict = None
    ) -> Dict[str, Any]:
        """
        使用Langchain生成场景锐评
        
        Args:
            scene_name: 场景名称
            scene_description: 场景描述
            scene_type: 场景类型
            user_context: 用户上下文信息
        
        Returns:
            包含锐评内容的字典
        """
        try:
            # 构建用户上下文信息
            user_context_info = ""
            if user_context:
                visit_count = user_context.get('visit_count', 0)
                time_of_day = user_context.get('time_of_day', '')
                previous_places = user_context.get('previous_places', [])
                
                user_context_info = f"""
**用户上下文**:
- 这是您今天访问的第{visit_count + 1}个地点
- 当前时间: {time_of_day}
- 之前访问过: {', '.join(previous_places) if previous_places else '无'}

请结合用户的探索历程，让锐评更加个性化和贴合当前的旅程状态。
"""
            
            logger.info(f"🤖 使用Langchain为场景 '{scene_name}' 生成锐评...")
            
            # 准备输入数据
            input_data = {
                "scene_name": scene_name,
                "scene_type": scene_type,
                "scene_description": scene_description,
                "user_context_info": user_context_info
            }
            
            # 执行Langchain链
            raw_result = await self.review_chain.ainvoke(input_data)
            
            # 记录AI原始输出用于调试
            logger.info(f"🔍 AI原始输出内容:")
            logger.info(f"类型: {type(raw_result)}")
            logger.info(f"内容长度: {len(str(raw_result)) if raw_result else 0}字符")
            logger.info(f"原始内容: <<<{raw_result}>>>")
            if hasattr(raw_result, 'content'):
                logger.info(f"content属性: <<<{raw_result.content}>>>")
            
            # 手动解析AI返回的内容
            content_to_parse = raw_result.content if hasattr(raw_result, 'content') else str(raw_result)
            review_data = self._parse_ai_review_response(content_to_parse)
            
            logger.info(f"✅ Langchain场景锐评生成成功: {len(review_data.get('review', ''))}字符")
            return review_data
            
        except LangChainException as e:
            logger.error(f"❌ Langchain执行失败: {str(e)}")
            # 抛出异常让上层处理，而不是返回fallback
            raise Exception(f"Langchain JSON解析失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ 场景锐评生成失败: {str(e)}")
            # 抛出异常让上层处理，而不是返回fallback
            raise Exception(f"Langchain执行失败: {str(e)}")
    
    async def generate_journey_summary(
        self,
        visited_scenes: List[Dict],
        total_distance: float,
        journey_duration: str
    ) -> Dict[str, Any]:
        """
        使用Langchain生成旅程总结
        
        Args:
            visited_scenes: 访问的场景列表
            total_distance: 总距离
            journey_duration: 旅程时长
        
        Returns:
            包含旅程总结内容的字典
        """
        try:
            scene_names = [scene.get('name', '未知地点') for scene in visited_scenes]
            scene_names_str = ', '.join(scene_names)
            
            logger.info(f"🤖 使用Langchain生成旅程总结...")
            
            # 准备输入数据
            input_data = {
                "scene_names": scene_names_str,
                "total_distance": total_distance,
                "journey_duration": journey_duration
            }
            
                        # 执行Langchain链  
            raw_result = await self.summary_chain.ainvoke(input_data)
            
            # 记录AI原始输出用于调试
            logger.info(f"🔍 AI旅程总结原始输出:")
            logger.info(f"类型: {type(raw_result)}")  
            logger.info(f"内容长度: {len(str(raw_result)) if raw_result else 0}字符")
            logger.info(f"原始内容: <<<{raw_result}>>>")
            if hasattr(raw_result, 'content'):
                logger.info(f"content属性: <<<{raw_result.content}>>>")
            
            # 解析旅程总结内容
            content_to_parse = raw_result.content if hasattr(raw_result, 'content') else str(raw_result)
            summary_data = self._parse_ai_summary_response(content_to_parse)
            
            logger.info(f"✅ Langchain旅程总结生成成功")
            return summary_data
            
        except Exception as e:
            logger.error(f"❌ Langchain旅程总结生成失败: {str(e)}")
            return self._get_fallback_journey_summary(visited_scenes, total_distance, journey_duration)
    
    def _parse_ai_review_response(self, content: str) -> Dict[str, str]:
        """手动解析AI返回的锐评内容，支持更宽松的格式"""
        try:
            import json
            import re
            
            # 尝试直接解析JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                return json.loads(content.strip())
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # 如果无法解析，返回包含原始内容的默认格式
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
            return {
                "title": "AI锐评",
                "review": content,
                "highlights": ["AI生成内容"],
                "tips": "探索愉快！",
                "rating_reason": "值得一去", 
                "mood": "探索"
            }
    
    def _parse_ai_summary_response(self, content: str) -> Dict[str, str]:
        """手动解析AI返回的旅程总结内容，支持更宽松的格式"""
        try:
            import json
            import re
            
            # 尝试直接解析JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                return json.loads(content.strip())
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # 如果无法解析，返回包含原始内容的默认格式
            return {
                "summary": content,
                "highlights": ["AI生成总结"],
                "recommendation": "继续探索更多精彩地点"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ AI旅程总结响应解析失败: {e}")
            return {
                "summary": content,
                "highlights": ["AI生成总结"],
                "recommendation": "继续探索更多精彩地点"
            }
    
    def _get_fallback_review(self, scene_name: str, scene_description: str, scene_type: str) -> Dict[str, str]:
        """生成备用锐评内容（当Langchain服务不可用时）"""
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
    
    def _get_fallback_journey_summary(self, visited_scenes: List[Dict], total_distance: float, journey_duration: str) -> Dict[str, Any]:
        """生成备用旅程总结"""
        return {
            "summary": f"🎉 恭喜完成这次精彩的探索之旅！您访问了{len(visited_scenes)}个地点，总共行进了{total_distance:.1f}公里。每一步都是独特的发现，每一处风景都值得珍藏。感谢您选择方向探索派对，期待您的下次冒险！🧭✨",
            "highlights": ["勇敢探索", "发现未知", "收获回忆"],
            "recommendation": "继续保持探索的好奇心，世界还有更多精彩等待您发现！"
        }

# 全局Langchain AI服务实例
langchain_ai_service = None

def get_langchain_ai_service() -> LangchainAIService:
    """获取Langchain AI服务实例（单例模式）"""
    global langchain_ai_service
    if langchain_ai_service is None:
        try:
            langchain_ai_service = LangchainAIService()
        except Exception as e:
            logger.error(f"❌ Langchain AI服务初始化失败: {e}")
            langchain_ai_service = None
    return langchain_ai_service

async def test_langchain_service():
    """测试Langchain服务是否正常工作"""
    try:
        service = get_langchain_ai_service()
        if service is None:
            logger.error("❌ Langchain服务初始化失败")
            return False
        
        # 测试场景锐评生成
        test_result = await service.generate_scene_review(
            scene_name="测试景点",
            scene_description="这是一个用于测试的景点",
            scene_type="测试类型"
        )
        
        logger.info(f"✅ Langchain服务测试成功: {test_result['title']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Langchain服务测试失败: {e}")
        return False

if __name__ == "__main__":
    # 测试脚本
    asyncio.run(test_langchain_service())
