"""
大纲生成服务

根据用户输入的主题生成小红书图文大纲
"""

import logging
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from ai_module.config import AIConfig
from ai_module.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class OutlineService:
    """大纲生成服务"""
    
    def __init__(self):
        logger.debug("Initializing OutlineService...")
        self.text_config = AIConfig.load_text_providers_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"OutlineService initialized, provider: {self.text_config.get('active_provider')}")
    
    def _get_client(self):
        """获取文本生成客户端"""
        active_provider = self.text_config.get('active_provider', 'custom')
        providers = self.text_config.get('providers', {})
        
        if not providers:
            raise ValueError("No text provider configured. Please configure in AI settings.")
        
        if active_provider not in providers:
            available = ', '.join(providers.keys())
            raise ValueError(f"Text provider [{active_provider}] not found. Available: {available}")
        
        provider_config = providers.get(active_provider, {})
        
        if not provider_config.get('api_key'):
            raise ValueError(f"API Key not configured for text provider [{active_provider}]")
        
        return get_text_chat_client(provider_config)
    
    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "outline_prompt.txt"
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # 默认提示词模板
        return """你是一个小红书内容创作专家。请根据以下主题生成一份小红书图文笔记的大纲。

主题：{topic}

要求：
1. 生成 5-8 页内容
2. 第一页是封面，标注 [封面]
3. 中间是内容页，标注 [内容]
4. 最后一页是总结，标注 [总结]
5. 每页内容要生动有趣，符合小红书风格
6. 使用 <page> 标签分隔每一页

请直接输出大纲内容，不要包含其他说明。"""
    
    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        """解析大纲文本为页面列表"""
        # 按 <page> 分割页面
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 兼容 --- 分隔符
            pages_raw = outline_text.split("---")
        
        pages = []
        
        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue
            
            # 识别页面类型
            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "内容": "content",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")
            
            pages.append({
                "index": len(pages),
                "type": page_type,
                "content": page_text
            })
        
        return pages
    
    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        生成大纲
        
        Args:
            topic: 用户输入的主题
            images: 可选的参考图片列表
            
        Returns:
            包含 success, outline, pages 等字段的字典
        """
        try:
            logger.info(f"Generating outline: topic={topic[:50]}..., images={len(images) if images else 0}")
            prompt = self.prompt_template.format(topic=topic)
            
            if images and len(images) > 0:
                prompt += f"\n\n注意：用户提供了 {len(images)} 张参考图片，请在生成大纲时考虑这些图片的内容和风格。"
            
            # 获取模型参数
            active_provider = self.text_config.get('active_provider', 'custom')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})
            
            model = provider_config.get('model', 'gpt-4')
            temperature = provider_config.get('temperature', 0.7)
            max_output_tokens = provider_config.get('max_output_tokens', 4096)
            
            logger.info(f"Calling text API: model={model}, temperature={temperature}")
            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )
            
            logger.debug(f"API response length: {len(outline_text)} chars")
            pages = self._parse_outline(outline_text)
            logger.info(f"Outline parsed, {len(pages)} pages")
            
            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Outline generation failed: {error_msg}")
            
            return {
                "success": False,
                "error": f"Outline generation failed: {error_msg}"
            }


def get_outline_service() -> OutlineService:
    """获取大纲生成服务实例"""
    return OutlineService()
