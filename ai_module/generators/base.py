"""
AI 生成器基类
"""

from abc import ABC, abstractmethod
from typing import Optional, List


class TextGenerator(ABC):
    """文本生成器基类"""
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        images: Optional[List[bytes]] = None
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            model: 模型名称
            temperature: 温度参数
            max_output_tokens: 最大输出 token 数
            images: 可选的图片列表 (用于多模态)
            
        Returns:
            生成的文本
        """
        pass


class ImageGenerator(ABC):
    """图片生成器基类"""
    
    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        model: str = None,
        size: str = "1024x1024",
        quality: str = "standard",
        **kwargs
    ) -> bytes:
        """
        生成图片
        
        Args:
            prompt: 提示词
            model: 模型名称
            size: 图片尺寸
            quality: 图片质量
            **kwargs: 其他参数
            
        Returns:
            图片二进制数据
        """
        pass
