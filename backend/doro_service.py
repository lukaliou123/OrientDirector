"""
Doro Service Module
处理Doro形象的管理、存储和检索
"""

import os
import json
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class DoroService:
    """Doro形象管理服务"""
    
    def __init__(self):
        """初始化Doro服务"""
        # 使用绝对路径或相对于当前文件的路径
        import os
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = current_dir / "doro"
        self.preset_dir = self.base_dir / "preset"
        self.custom_dir = self.base_dir / "custom"
        
        # 确保目录存在
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的图片格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
        
        # Doro元数据缓存
        self._doro_cache = {}
        
        # 初始化预设Doro元数据
        self._init_preset_metadata()
        
        logger.info(f"Doro服务初始化完成: 预设目录={self.preset_dir}, 自定义目录={self.custom_dir}")
    
    def _init_preset_metadata(self):
        """初始化预设Doro的元数据"""
        preset_metadata = {
            "doro1": {
                "name": "经典Doro",
                "description": "经典可爱的Doro形象",
                "style": "cute",
                "tags": ["经典", "可爱", "友好"]
            },
            "doro2": {
                "name": "冒险Doro",
                "description": "勇敢的冒险家Doro",
                "style": "adventurous",
                "tags": ["冒险", "勇敢", "探索"]
            },
            "doro3": {
                "name": "优雅Doro",
                "description": "优雅知性的Doro",
                "style": "elegant",
                "tags": ["优雅", "知性", "文艺"]
            },
            "doro4": {
                "name": "运动Doro",
                "description": "活力四射的运动Doro",
                "style": "sporty",
                "tags": ["运动", "活力", "健康"]
            },
            "doro5": {
                "name": "科技Doro",
                "description": "未来感十足的科技Doro",
                "style": "tech",
                "tags": ["科技", "未来", "智能"]
            }
        }
        
        # 保存元数据到文件
        metadata_file = self.preset_dir / "metadata.json"
        if not metadata_file.exists():
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(preset_metadata, f, ensure_ascii=False, indent=2)
    
    def get_all_doros(self) -> Dict[str, List[Dict]]:
        """
        获取所有可用的Doro形象
        
        Returns:
            包含预设和自定义Doro列表的字典
        """
        result = {
            "preset": [],
            "custom": []
        }
        
        # 获取预设Doro
        preset_metadata = self._load_preset_metadata()
        for image_path in self.preset_dir.glob("*"):
            if image_path.suffix.lower() in self.supported_formats:
                doro_id = image_path.stem
                metadata = preset_metadata.get(doro_id, {})
                
                result["preset"].append({
                    "id": doro_id,
                    "name": metadata.get("name", f"Doro {doro_id}"),
                    "description": metadata.get("description", ""),
                    "style": metadata.get("style", "default"),
                    "tags": metadata.get("tags", []),
                    "type": "preset",
                    "filename": image_path.name,
                    "url": f"http://localhost:8000/api/doro/image/{doro_id}",
                    "thumbnail": f"http://localhost:8000/api/doro/thumbnail/{doro_id}"
                })
        
        # 获取自定义Doro
        custom_metadata = self._load_custom_metadata()
        for image_path in self.custom_dir.glob("*"):
            if image_path.suffix.lower() in self.supported_formats:
                doro_id = image_path.stem
                metadata = custom_metadata.get(doro_id, {})
                
                result["custom"].append({
                    "id": doro_id,
                    "name": metadata.get("name", f"自定义 {doro_id[:8]}"),
                    "description": metadata.get("description", "用户上传的自定义Doro"),
                    "upload_time": metadata.get("upload_time", ""),
                    "type": "custom",
                    "filename": image_path.name,
                    "url": f"http://localhost:8000/api/doro/image/custom_{doro_id}",
                    "thumbnail": f"http://localhost:8000/api/doro/thumbnail/custom_{doro_id}"
                })
        
        logger.info(f"获取Doro列表: 预设={len(result['preset'])}个, 自定义={len(result['custom'])}个")
        return result
    
    def get_random_doro(self) -> Optional[Dict]:
        """
        随机获取一个Doro形象
        
        Returns:
            随机选择的Doro信息，如果没有可用Doro则返回None
        """
        all_doros = self.get_all_doros()
        
        # 合并预设和自定义Doro
        doro_list = all_doros["preset"] + all_doros["custom"]
        
        if not doro_list:
            logger.warning("没有可用的Doro形象")
            return None
        
        selected = random.choice(doro_list)
        logger.info(f"随机选择Doro: {selected['name']} (ID: {selected['id']})")
        return selected
    
    async def save_custom_doro(
        self, 
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        保存用户上传的自定义Doro
        
        Args:
            file: 上传的图片文件
            name: 自定义名称
            description: 自定义描述
            
        Returns:
            保存的Doro信息
        """
        # 验证文件格式
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(self.supported_formats)}"
            )
        
        # 验证文件大小（最大10MB）
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件太大。最大支持10MB"
            )
        
        # 生成唯一ID
        doro_id = str(uuid.uuid4())
        filename = f"{doro_id}{file_ext}"
        file_path = self.custom_dir / filename
        
        # 保存文件
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # 保存元数据
            metadata = {
                "id": doro_id,
                "name": name or f"自定义Doro {doro_id[:8]}",
                "description": description or "用户上传的自定义Doro形象",
                "upload_time": datetime.now().isoformat(),
                "original_filename": file.filename,
                "file_size": file_size
            }
            
            self._save_custom_metadata(doro_id, metadata)
            
            # 返回保存的信息
            result = {
                "id": doro_id,
                "name": metadata["name"],
                "description": metadata["description"],
                "type": "custom",
                "filename": filename,
                "url": f"http://localhost:8000/api/doro/image/custom_{doro_id}",
                "thumbnail": f"http://localhost:8000/api/doro/thumbnail/custom_{doro_id}",
                "upload_time": metadata["upload_time"]
            }
            
            logger.info(f"保存自定义Doro成功: {filename}")
            return result
            
        except Exception as e:
            # 如果保存失败，清理文件
            if file_path.exists():
                file_path.unlink()
            logger.error(f"保存自定义Doro失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    def get_doro_by_id(self, doro_id: str) -> Optional[Path]:
        """
        根据ID获取Doro图片路径
        
        Args:
            doro_id: Doro的ID
            
        Returns:
            图片文件路径，如果不存在则返回None
        """
        # 检查是否是自定义Doro
        if doro_id.startswith("custom_"):
            actual_id = doro_id[7:]  # 移除 "custom_" 前缀
            for file_path in self.custom_dir.glob(f"{actual_id}.*"):
                if file_path.suffix.lower() in self.supported_formats:
                    return file_path
        else:
            # 预设Doro
            for file_path in self.preset_dir.glob(f"{doro_id}.*"):
                if file_path.suffix.lower() in self.supported_formats:
                    return file_path
        
        return None
    
    def delete_custom_doro(self, doro_id: str) -> bool:
        """
        删除自定义Doro
        
        Args:
            doro_id: 要删除的Doro ID
            
        Returns:
            是否删除成功
        """
        if not doro_id.startswith("custom_"):
            logger.warning(f"尝试删除非自定义Doro: {doro_id}")
            return False
        
        actual_id = doro_id[7:]
        
        # 删除图片文件
        deleted = False
        for file_path in self.custom_dir.glob(f"{actual_id}.*"):
            if file_path.suffix.lower() in self.supported_formats:
                file_path.unlink()
                deleted = True
                logger.info(f"删除自定义Doro文件: {file_path}")
        
        # 删除元数据
        if deleted:
            self._delete_custom_metadata(actual_id)
        
        return deleted
    
    def _load_preset_metadata(self) -> Dict:
        """加载预设Doro元数据"""
        metadata_file = self.preset_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_custom_metadata(self) -> Dict:
        """加载自定义Doro元数据"""
        metadata_file = self.custom_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_custom_metadata(self, doro_id: str, metadata: Dict):
        """保存自定义Doro元数据"""
        metadata_file = self.custom_dir / "metadata.json"
        
        # 加载现有元数据
        all_metadata = self._load_custom_metadata()
        
        # 更新元数据
        all_metadata[doro_id] = metadata
        
        # 保存回文件
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    
    def _delete_custom_metadata(self, doro_id: str):
        """删除自定义Doro元数据"""
        metadata_file = self.custom_dir / "metadata.json"
        
        if metadata_file.exists():
            all_metadata = self._load_custom_metadata()
            
            if doro_id in all_metadata:
                del all_metadata[doro_id]
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(all_metadata, f, ensure_ascii=False, indent=2)

# 创建全局服务实例
doro_service = DoroService()