"""
Google Gemini 图片生成器

专用于 Gemini 图片生成 API (gemini-2.0-flash-exp-image-generation)
"""

import logging
import base64
import requests
from typing import Optional
from .base import ImageGenerator

logger = logging.getLogger(__name__)


class GeminiImageGenerator(ImageGenerator):
    """Gemini 图片生成器"""
    
    def __init__(self, config: dict):
        """
        初始化
        
        Args:
            config: 配置字典，包含：
                - base_url: API 地址 (https://generativelanguage.googleapis.com)
                - api_key: API 密钥
                - model: 模型名称 (gemini-2.0-flash-exp-image-generation)
        """
        self.base_url = config.get('base_url', 'https://generativelanguage.googleapis.com').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.default_model = config.get('model', 'gemini-2.0-flash-exp-image-generation')
        self.timeout = config.get('timeout', 180)
        
        if not self.api_key:
            raise ValueError("api_key is required for Gemini API")
    
    def generate_image(
        self,
        prompt: str,
        model: str = None,
        size: str = "1024x1024",
        quality: str = "standard",
        **kwargs
    ) -> bytes:
        """生成图片"""
        model = model or self.default_model
        
        # Gemini API 格式
        url = f"{self.base_url}/v1beta/models/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 添加 API Key 到 URL
        url_with_key = f"{url}?key={self.api_key}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }
        
        try:
            logger.debug(f"Calling Gemini image API: model={model}")
            
            response = requests.post(
                url_with_key,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析 Gemini 响应
            # 响应格式: {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": "base64..."}}]}}]}
            candidates = result.get('candidates', [])
            if not candidates:
                raise Exception("No candidates in response")
            
            parts = candidates[0].get('content', {}).get('parts', [])
            
            for part in parts:
                if 'inlineData' in part:
                    inline_data = part['inlineData']
                    b64_data = inline_data.get('data', '')
                    if b64_data:
                        image_data = base64.b64decode(b64_data)
                        logger.debug(f"Image generated, size: {len(image_data)} bytes")
                        return image_data
            
            raise Exception("No image data in response")
            
        except requests.exceptions.Timeout:
            raise Exception("Gemini API request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error detail: {error_detail}")
                except:
                    pass
            raise Exception(f"Gemini API request failed: {str(e)}")
