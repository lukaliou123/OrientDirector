"""
🗄️ Prompt & Generation Database Management
管理prompt使用记录和图片生成历史的SQLite数据库
"""

import sqlite3
import json
import os
import time
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime

class PromptDatabase:
    """Prompt和生成历史数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的prompt_history.db
        """
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "data", "prompt_history.db")
        
        self.db_path = db_path
        
        # 确保data目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.init_database()
        
        print(f"📁 Prompt数据库已初始化: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        else:
            conn.commit()
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        schema_path = os.path.join(os.path.dirname(__file__), "database_schema.sql")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            print("✅ 数据库表结构初始化完成")
    
    def record_prompt_usage(
        self, 
        prompt: str, 
        prompt_type: str,
        historical_period: str = None,
        political_entity: str = None,
        cultural_region: str = None,
        notes: str = None
    ) -> int:
        """
        记录prompt使用
        
        Args:
            prompt: prompt内容
            prompt_type: 类型('scene' 或 'meme')
            historical_period: 历史时期
            political_entity: 政治实体
            cultural_region: 文化区域
            notes: 备注
            
        Returns:
            prompt记录的ID
        """
        with self.get_connection() as conn:
            # 检查是否已存在相同的prompt
            existing = conn.execute(
                "SELECT id, used_count FROM prompt_records WHERE prompt = ? AND type = ?",
                (prompt, prompt_type)
            ).fetchone()
            
            if existing:
                # 更新使用计数
                conn.execute(
                    """UPDATE prompt_records 
                       SET used_count = used_count + 1, 
                           updated_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (existing['id'],)
                )
                prompt_id = existing['id']
                print(f"📝 更新prompt使用记录 ID:{prompt_id}, 使用次数:{existing['used_count'] + 1}")
            else:
                # 创建新记录
                cursor = conn.execute(
                    """INSERT INTO prompt_records 
                       (prompt, type, historical_period, political_entity, cultural_region, notes)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (prompt, prompt_type, historical_period, political_entity, cultural_region, notes)
                )
                prompt_id = cursor.lastrowid
                print(f"📝 新建prompt记录 ID:{prompt_id}")
            
            return prompt_id
    
    def record_generation(
        self,
        prompt_id: int,
        image_path: str,
        image_url: str,
        success: bool = True,
        generation_time: float = None,
        error_message: str = None,
        scene_elements: List[str] = None,
        historical_context: Dict = None,
        api_parameters: Dict = None
    ) -> int:
        """
        记录生成历史
        
        Args:
            prompt_id: 关联的prompt记录ID
            image_path: 图片文件路径
            image_url: 图片访问URL
            success: 是否成功生成
            generation_time: 生成耗时（秒）
            error_message: 错误信息
            scene_elements: 场景元素列表
            historical_context: 历史背景信息
            api_parameters: API参数
            
        Returns:
            生成记录的ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO generation_history 
                   (prompt_id, image_path, image_url, success, generation_time, 
                    error_message, scene_elements, historical_context, api_parameters)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prompt_id, image_path, image_url, success, generation_time,
                    error_message,
                    json.dumps(scene_elements, ensure_ascii=False) if scene_elements else None,
                    json.dumps(historical_context, ensure_ascii=False) if historical_context else None,
                    json.dumps(api_parameters, ensure_ascii=False) if api_parameters else None
                )
            )
            generation_id = cursor.lastrowid
            
            # 如果生成成功，更新prompt的成功计数
            if success:
                conn.execute(
                    "UPDATE prompt_records SET success_count = success_count + 1 WHERE id = ?",
                    (prompt_id,)
                )
            
            print(f"🎨 记录生成历史 ID:{generation_id}, 成功:{success}")
            return generation_id
    
    def record_rating(
        self,
        generation_id: int,
        quality_score: int = None,
        creativity_score: int = None,
        historical_accuracy_score: int = None,
        feedback: str = None,
        is_recommended: bool = False
    ) -> int:
        """
        记录图片评分
        
        Args:
            generation_id: 关联的生成历史ID
            quality_score: 质量评分(1-5)
            creativity_score: 创意评分(1-5)
            historical_accuracy_score: 历史准确性评分(1-5)
            feedback: 文字反馈
            is_recommended: 是否推荐
            
        Returns:
            评分记录的ID
        """
        # 计算综合评分
        scores = [s for s in [quality_score, creativity_score, historical_accuracy_score] if s is not None]
        overall_rating = sum(scores) / len(scores) if scores else None
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO image_ratings 
                   (generation_id, quality_score, creativity_score, historical_accuracy_score,
                    overall_rating, feedback, is_recommended)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (generation_id, quality_score, creativity_score, historical_accuracy_score,
                 overall_rating, feedback, is_recommended)
            )
            rating_id = cursor.lastrowid
            print(f"⭐ 记录图片评分 ID:{rating_id}, 综合评分:{overall_rating:.1f}")
            return rating_id
    
    def get_unrated_images(self, image_type: str = None, limit: int = 20) -> List[Dict]:
        """
        获取未评分的图片列表（用于评分页面）
        
        Args:
            image_type: 图片类型过滤('scene' 或 'meme')
            limit: 返回数量限制
            
        Returns:
            未评分图片列表
        """
        sql = """
        SELECT gh.id, gh.image_path, gh.image_url, gh.created_at,
               pr.prompt, pr.type, pr.historical_period, pr.political_entity
        FROM generation_history gh
        JOIN prompt_records pr ON gh.prompt_id = pr.id
        LEFT JOIN image_ratings ir ON gh.id = ir.generation_id
        WHERE gh.success = 1 AND ir.id IS NULL
        """
        params = []
        
        if image_type:
            sql += " AND pr.type = ?"
            params.append(image_type)
        
        sql += " ORDER BY gh.created_at DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            results = conn.execute(sql, params).fetchall()
            return [dict(row) for row in results]
    
    def get_rated_images(self, image_type: str = None, min_rating: float = None, limit: int = 50) -> List[Dict]:
        """
        获取已评分的图片列表（用于查看和管理）
        
        Args:
            image_type: 图片类型过滤
            min_rating: 最低评分过滤
            limit: 返回数量限制
            
        Returns:
            已评分图片列表
        """
        sql = """
        SELECT * FROM generation_with_ratings 
        WHERE overall_rating IS NOT NULL
        """
        params = []
        
        if image_type:
            sql += " AND type = ?"
            params.append(image_type)
        
        if min_rating:
            sql += " AND overall_rating >= ?"
            params.append(min_rating)
        
        sql += " ORDER BY overall_rating DESC, generation_date DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            results = conn.execute(sql, params).fetchall()
            return [dict(row) for row in results]
    
    def get_prompt_statistics(self, prompt_type: str = None) -> List[Dict]:
        """
        获取prompt统计信息
        
        Args:
            prompt_type: 类型过滤
            
        Returns:
            prompt统计列表
        """
        sql = "SELECT * FROM prompt_statistics"
        params = []
        
        if prompt_type:
            sql += " WHERE type = ?"
            params.append(prompt_type)
        
        sql += " ORDER BY avg_rating DESC, used_count DESC"
        
        with self.get_connection() as conn:
            results = conn.execute(sql, params).fetchall()
            return [dict(row) for row in results]
    
    def get_best_prompts(self, prompt_type: str, min_rating: float = 4.0, min_uses: int = 2) -> List[Dict]:
        """
        获取高质量prompt（用于预设推荐）
        
        Args:
            prompt_type: prompt类型
            min_rating: 最低平均评分
            min_uses: 最少使用次数
            
        Returns:
            优质prompt列表
        """
        sql = """
        SELECT * FROM prompt_statistics 
        WHERE type = ? AND avg_rating >= ? AND used_count >= ?
        ORDER BY avg_rating DESC, recommended_count DESC
        """
        
        with self.get_connection() as conn:
            results = conn.execute(sql, (prompt_type, min_rating, min_uses)).fetchall()
            return [dict(row) for row in results]

# 全局实例
prompt_db = PromptDatabase()
