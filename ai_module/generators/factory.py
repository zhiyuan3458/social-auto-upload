"""
AI 生成器工厂

根据配置创建对应的生成器实例
"""

import logging
from .base import TextGenerator, ImageGenerator
from .openai_compatible import OpenAICompatibleTextGenerator, OpenAICompatibleImageGenerator
from .gemini import GeminiImageGenerator

logger = logging.getLogger(__name__)


class TextGeneratorFactory:
    """文本生成器工厂"""
    
    @staticmethod
    def create(provider_type: str, config: dict) -> TextGenerator:
        """
        创建文本生成器
        
        Args:
            provider_type: 服务商类型 (openai_compatible, google_gemini, etc.)
            config: 服务商配置
            
        Returns:
            TextGenerator 实例
        """
        logger.info(f"Creating text generator: type={provider_type}")
        
        if provider_type in ['openai', 'openai_compatible', 'custom']:
            return OpenAICompatibleTextGenerator(config)
        elif provider_type == 'google_gemini':
            # Gemini 文本生成也可以用 OpenAI 兼容模式
            return OpenAICompatibleTextGenerator(config)
        else:
            # 默认使用 OpenAI 兼容模式
            logger.warning(f"Unknown provider type: {provider_type}, using OpenAI compatible")
            return OpenAICompatibleTextGenerator(config)


class ImageGeneratorFactory:
    """图片生成器工厂"""
    
    @staticmethod
    def create(provider_type: str, config: dict) -> ImageGenerator:
        """
        创建图片生成器
        
        Args:
            provider_type: 服务商类型
            config: 服务商配置
            
        Returns:
            ImageGenerator 实例
        """
        logger.info(f"Creating image generator: type={provider_type}")
        
        if provider_type in ['openai', 'openai_compatible', 'custom']:
            return OpenAICompatibleImageGenerator(config)
        elif provider_type in ['gemini', 'google_gemini']:
            return GeminiImageGenerator(config)
        else:
            # 默认使用 OpenAI 兼容模式
            logger.warning(f"Unknown provider type: {provider_type}, using OpenAI compatible")
            return OpenAICompatibleImageGenerator(config)
