"""
内容生成服务

生成小红书风格的标题、文案和标签
"""

import json
import logging
import re
from typing import Dict, Any
from pathlib import Path

from ai_module.config import AIConfig
from ai_module.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class ContentService:
    """内容生成服务：生成标题、文案、标签"""
    
    def __init__(self):
        logger.debug("Initializing ContentService...")
        self.text_config = AIConfig.load_text_providers_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"ContentService initialized, provider: {self.text_config.get('active_provider')}")
    
    def _get_client(self):
        """获取文本生成客户端"""
        active_provider = self.text_config.get('active_provider', 'custom')
        providers = self.text_config.get('providers', {})
        
        if not providers:
            raise ValueError("No text provider configured.")
        
        if active_provider not in providers:
            available = ', '.join(providers.keys())
            raise ValueError(f"Text provider [{active_provider}] not found. Available: {available}")
        
        provider_config = providers.get(active_provider, {})
        
        if not provider_config.get('api_key'):
            raise ValueError(f"API Key not configured for [{active_provider}]")
        
        return get_text_chat_client(provider_config)
    
    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "content_prompt.txt"
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # 默认提示词模板
        return """你是一个小红书内容创作专家。请根据以下主题和大纲，生成小红书笔记的标题、文案和标签。

主题：{topic}

大纲：
{outline}

请生成以下内容并以 JSON 格式返回：
1. titles: 3个备选标题（数组）
2. copywriting: 正文文案（字符串，200-500字，包含emoji）
3. tags: 10个相关标签（数组，不带#号）

返回格式示例：
```json
{{
  "titles": ["标题1", "标题2", "标题3"],
  "copywriting": "文案内容...",
  "tags": ["标签1", "标签2", ...]
}}
```"""
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析 AI 返回的 JSON 响应"""
        # 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 markdown 代码块中提取
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试找到 JSON 对象
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response_text[start_idx:end_idx + 1])
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to parse JSON: {response_text[:200]}...")
        raise ValueError("AI response format error")
    
    def generate_content(
        self,
        topic: str,
        outline: str
    ) -> Dict[str, Any]:
        """
        生成标题、文案和标签
        
        Args:
            topic: 用户输入的主题
            outline: 大纲内容
            
        Returns:
            包含 titles, copywriting, tags 的字典
        """
        try:
            logger.info(f"Generating content: topic={topic[:50]}...")
            
            prompt = self.prompt_template.format(
                topic=topic,
                outline=outline
            )
            
            # 获取模型参数
            active_provider = self.text_config.get('active_provider', 'custom')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})
            
            model = provider_config.get('model', 'gpt-4')
            temperature = provider_config.get('temperature', 0.7)
            max_output_tokens = provider_config.get('max_output_tokens', 4096)
            
            logger.info(f"Calling text API: model={model}")
            response_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            
            # 解析 JSON 响应
            content_data = self._parse_json_response(response_text)
            
            titles = content_data.get('titles', [])
            copywriting = content_data.get('copywriting', '')
            tags = content_data.get('tags', [])
            
            # 确保 titles 是列表
            if isinstance(titles, str):
                titles = [titles]
            
            # 确保 tags 是列表
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            
            logger.info(f"Content generated: {len(titles)} titles, {len(tags)} tags")
            
            return {
                "success": True,
                "titles": titles,
                "copywriting": copywriting,
                "tags": tags
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Content generation failed: {error_msg}")
            
            return {
                "success": False,
                "error": f"Content generation failed: {error_msg}"
            }


def get_content_service() -> ContentService:
    """获取内容生成服务实例"""
    return ContentService()
