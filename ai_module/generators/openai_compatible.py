"""
OpenAI 兼容 API 生成器

支持所有兼容 OpenAI API 格式的服务商，包括：
- OpenAI 官方
- Azure OpenAI
- 公司内部 API
- 其他兼容服务
"""

import logging
import base64
import requests
from typing import Optional, List
from .base import TextGenerator, ImageGenerator

logger = logging.getLogger(__name__)


class OpenAICompatibleTextGenerator(TextGenerator):
    """OpenAI 兼容文本生成器"""
    
    def __init__(self, config: dict):
        """
        初始化
        
        Args:
            config: 配置字典，包含：
                - base_url: API 地址
                - api_key: API 密钥
                - model: 默认模型
        """
        self.base_url = config.get('base_url', '').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.default_model = config.get('model', 'gpt-4')
        self.timeout = config.get('timeout', 120)
        
        if not self.base_url:
            raise ValueError("base_url is required for OpenAI compatible API")
        if not self.api_key:
            raise ValueError("api_key is required for OpenAI compatible API")
    
    def generate_text(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        images: Optional[List[bytes]] = None
    ) -> str:
        """生成文本"""
        model = model or self.default_model
        
        # 构建消息
        content = []
        
        # 如果有图片，构建多模态消息
        if images:
            for img_data in images:
                base64_img = base64.b64encode(img_data).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
        
        content.append({
            "type": "text",
            "text": prompt
        })
        
        messages = [{"role": "user", "content": content}]
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens
        }
        
        try:
            url = f"{self.base_url}/chat/completions"
            logger.debug(f"Calling text API: {url}, model={model}")
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            text = result['choices'][0]['message']['content']
            logger.debug(f"Text generated, length: {len(text)}")
            return text
            
        except requests.exceptions.Timeout:
            raise Exception("API request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {str(e)}")


class OpenAICompatibleImageGenerator(ImageGenerator):
    """OpenAI 兼容图片生成器"""
    
    def __init__(self, config: dict):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.base_url = config.get('base_url', '').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.default_model = config.get('model', 'dall-e-3')
        self.timeout = config.get('timeout', 180)
        
        if not self.base_url:
            raise ValueError("base_url is required for OpenAI compatible API")
        if not self.api_key:
            raise ValueError("api_key is required for OpenAI compatible API")
    
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
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
            "n": 1
        }
        
        try:
            url = f"{self.base_url}/images/generations"
            logger.debug(f"Calling image API: {url}, model={model}")
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            b64_data = result['data'][0]['b64_json']
            image_data = base64.b64decode(b64_data)
            
            logger.debug(f"Image generated, size: {len(image_data)} bytes")
            return image_data
            
        except requests.exceptions.Timeout:
            raise Exception("API request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {str(e)}")
