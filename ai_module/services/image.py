"""
图片生成服务

根据大纲内容逐页生成图片，支持 SSE 流式返回进度
"""

import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Generator, List, Optional, Tuple
from pathlib import Path

from ai_module.config import AIConfig
from ai_module.generators import ImageGeneratorFactory
from ai_module.utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


class ImageService:
    """图片生成服务"""
    
    MAX_CONCURRENT = 5  # 最大并发数
    
    def __init__(self, provider_name: str = None):
        logger.debug("Initializing ImageService...")
        
        # 获取服务商配置
        if provider_name is None:
            provider_name = AIConfig.get_active_image_provider()
        
        logger.info(f"Using image provider: {provider_name}")
        provider_config = AIConfig.get_image_provider_config(provider_name)
        
        # 创建生成器实例
        provider_type = provider_config.get('type', 'openai_compatible')
        self.generator = ImageGeneratorFactory.create(provider_type, provider_config)
        
        self.provider_name = provider_name
        self.provider_config = provider_config
        
        # 加载提示词模板
        self.prompt_template = self._load_prompt_template()
        
        # 历史记录目录
        self.history_root_dir = str(AIConfig.get_history_dir())
        
        # 当前任务目录
        self.current_task_dir = None
        
        # 任务状态
        self._task_states: Dict[str, Dict] = {}
        
        logger.info(f"ImageService initialized: provider={provider_name}")
    
    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "image_prompt.txt"
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # 默认提示词模板
        return """Generate an image for a Xiaohongshu (Little Red Book) post.

Page type: {page_type}
Content: {page_content}

Requirements:
- Style: Modern, clean, aesthetic
- Aspect ratio: 3:4 (portrait)
- High quality, professional looking
- Suitable for social media"""
    
    def _save_image(self, image_data: bytes, filename: str, task_dir: str = None) -> str:
        """保存图片"""
        if task_dir is None:
            task_dir = self.current_task_dir
        
        if task_dir is None:
            raise ValueError("Task directory not set")
        
        # 保存原图
        filepath = os.path.join(task_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        # 生成缩略图
        thumbnail_data = compress_image(image_data, max_size_kb=50)
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = os.path.join(task_dir, thumbnail_filename)
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail_data)
        
        return filepath
    
    def _generate_single_image(
        self,
        page: Dict,
        task_id: str,
        reference_image: Optional[bytes] = None,
        full_outline: str = "",
        user_topic: str = ""
    ) -> Tuple[int, bool, Optional[str], Optional[str]]:
        """
        生成单张图片
        
        Returns:
            (index, success, filename, error_message)
        """
        index = page["index"]
        page_type = page["type"]
        page_content = page["content"]
        
        try:
            logger.debug(f"Generating image [{index}]: type={page_type}")
            
            # 构建提示词
            prompt = self.prompt_template.format(
                page_content=page_content,
                page_type=page_type,
                full_outline=full_outline,
                user_topic=user_topic or "Not provided"
            )
            
            # 调用生成器
            image_data = self.generator.generate_image(
                prompt=prompt,
                size=self.provider_config.get('default_size', '1024x1024'),
                model=self.provider_config.get('model'),
                quality=self.provider_config.get('quality', 'standard'),
            )
            
            # 保存图片
            filename = f"{index}.png"
            self._save_image(image_data, filename, self.current_task_dir)
            logger.info(f"[OK] Image [{index}] generated: {filename}")
            
            return (index, True, filename, None)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[X] Image [{index}] failed: {error_msg[:200]}")
            return (index, False, None, error_msg)
    
    def generate_images(
        self,
        pages: list,
        task_id: str = None,
        full_outline: str = "",
        user_images: Optional[List[bytes]] = None,
        user_topic: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        生成图片（生成器，支持 SSE 流式返回）
        
        Args:
            pages: 页面列表
            task_id: 任务 ID
            full_outline: 完整大纲
            user_images: 用户上传的参考图片
            user_topic: 用户原始输入
            
        Yields:
            进度事件字典
        """
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting image generation: task_id={task_id}, pages={len(pages)}")
        
        # 创建任务目录
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)
        
        total = len(pages)
        generated_images = []
        failed_pages = []
        cover_image_data = None
        
        # 压缩用户参考图
        compressed_user_images = None
        if user_images:
            compressed_user_images = [compress_image(img, max_size_kb=200) for img in user_images]
        
        # 初始化任务状态
        self._task_states[task_id] = {
            "pages": pages,
            "generated": {},
            "failed": {},
            "cover_image": None,
            "full_outline": full_outline,
            "user_topic": user_topic
        }
        
        # 第一阶段：生成封面
        cover_page = None
        other_pages = []
        
        for page in pages:
            if page["type"] == "cover":
                cover_page = page
            else:
                other_pages.append(page)
        
        if cover_page is None and len(pages) > 0:
            cover_page = pages[0]
            other_pages = pages[1:]
        
        if cover_page:
            yield {
                "event": "progress",
                "data": {
                    "index": cover_page["index"],
                    "status": "generating",
                    "message": "Generating cover...",
                    "current": 1,
                    "total": total,
                    "phase": "cover"
                }
            }
            
            index, success, filename, error = self._generate_single_image(
                cover_page, task_id, full_outline=full_outline, user_topic=user_topic
            )
            
            if success:
                generated_images.append(filename)
                self._task_states[task_id]["generated"][index] = filename
                
                # 读取封面作为后续参考
                cover_path = os.path.join(self.current_task_dir, filename)
                with open(cover_path, "rb") as f:
                    cover_image_data = compress_image(f.read(), max_size_kb=200)
                self._task_states[task_id]["cover_image"] = cover_image_data
                
                yield {
                    "event": "complete",
                    "data": {
                        "index": index,
                        "status": "done",
                        "image_url": f"/api/ai/images/{task_id}/{filename}",
                        "phase": "cover"
                    }
                }
            else:
                failed_pages.append(cover_page)
                self._task_states[task_id]["failed"][index] = error
                
                yield {
                    "event": "error",
                    "data": {
                        "index": index,
                        "status": "error",
                        "message": error,
                        "retryable": True,
                        "phase": "cover"
                    }
                }
        
        # 第二阶段：生成其他页面
        if other_pages:
            yield {
                "event": "progress",
                "data": {
                    "status": "batch_start",
                    "message": f"Generating {len(other_pages)} content pages...",
                    "current": len(generated_images),
                    "total": total,
                    "phase": "content"
                }
            }
            
            # 顺序生成（可改为并发）
            for page in other_pages:
                yield {
                    "event": "progress",
                    "data": {
                        "index": page["index"],
                        "status": "generating",
                        "current": len(generated_images) + 1,
                        "total": total,
                        "phase": "content"
                    }
                }
                
                index, success, filename, error = self._generate_single_image(
                    page, task_id, cover_image_data, full_outline, user_topic
                )
                
                if success:
                    generated_images.append(filename)
                    self._task_states[task_id]["generated"][index] = filename
                    
                    yield {
                        "event": "complete",
                        "data": {
                            "index": index,
                            "status": "done",
                            "image_url": f"/api/ai/images/{task_id}/{filename}",
                            "phase": "content"
                        }
                    }
                else:
                    failed_pages.append(page)
                    self._task_states[task_id]["failed"][index] = error
                    
                    yield {
                        "event": "error",
                        "data": {
                            "index": index,
                            "status": "error",
                            "message": error,
                            "retryable": True,
                            "phase": "content"
                        }
                    }
        
        # 完成
        yield {
            "event": "finish",
            "data": {
                "success": len(failed_pages) == 0,
                "task_id": task_id,
                "images": generated_images,
                "total": total,
                "completed": len(generated_images),
                "failed": len(failed_pages),
                "failed_indices": [p["index"] for p in failed_pages]
            }
        }
    
    def retry_single_image(
        self,
        task_id: str,
        page: Dict,
        use_reference: bool = True,
        full_outline: str = "",
        user_topic: str = ""
    ) -> Dict[str, Any]:
        """重试生成单张图片"""
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)
        
        reference_image = None
        
        # 从任务状态获取上下文
        if task_id in self._task_states:
            task_state = self._task_states[task_id]
            if use_reference:
                reference_image = task_state.get("cover_image")
            if not full_outline:
                full_outline = task_state.get("full_outline", "")
            if not user_topic:
                user_topic = task_state.get("user_topic", "")
        
        # 从文件加载封面
        if use_reference and reference_image is None:
            cover_path = os.path.join(self.current_task_dir, "0.png")
            if os.path.exists(cover_path):
                with open(cover_path, "rb") as f:
                    reference_image = compress_image(f.read(), max_size_kb=200)
        
        index, success, filename, error = self._generate_single_image(
            page, task_id, reference_image, full_outline, user_topic
        )
        
        if success:
            if task_id in self._task_states:
                self._task_states[task_id]["generated"][index] = filename
                if index in self._task_states[task_id]["failed"]:
                    del self._task_states[task_id]["failed"][index]
            
            return {
                "success": True,
                "index": index,
                "image_url": f"/api/ai/images/{task_id}/{filename}"
            }
        else:
            return {
                "success": False,
                "index": index,
                "error": error,
                "retryable": True
            }
    
    def get_image_path(self, task_id: str, filename: str) -> str:
        """获取图片路径"""
        task_dir = os.path.join(self.history_root_dir, task_id)
        return os.path.join(task_dir, filename)


# 全局服务实例
_service_instance = None


def get_image_service() -> ImageService:
    """获取图片生成服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ImageService()
    return _service_instance


def reset_image_service():
    """重置服务实例（配置更新后调用）"""
    global _service_instance
    _service_instance = None
