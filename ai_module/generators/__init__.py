"""
AI 生成器模块

支持多种 AI 服务商：
- OpenAI 兼容 API (包括公司内部 API)
- Google Gemini
- 自定义图片生成 API
"""

from .base import TextGenerator, ImageGenerator
from .factory import TextGeneratorFactory, ImageGeneratorFactory
from .openai_compatible import OpenAICompatibleTextGenerator, OpenAICompatibleImageGenerator
from .gemini import GeminiImageGenerator

__all__ = [
    'TextGenerator',
    'ImageGenerator', 
    'TextGeneratorFactory',
    'ImageGeneratorFactory',
    'OpenAICompatibleTextGenerator',
    'OpenAICompatibleImageGenerator',
    'GeminiImageGenerator'
]
