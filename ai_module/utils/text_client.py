"""
文本生成客户端工具

根据配置创建对应的文本生成器
"""

import logging
from ai_module.generators import TextGeneratorFactory

logger = logging.getLogger(__name__)


def get_text_chat_client(config: dict):
    """
    获取文本生成客户端
    
    Args:
        config: 服务商配置字典
        
    Returns:
        TextGenerator 实例
    """
    provider_type = config.get('type', 'openai_compatible')
    return TextGeneratorFactory.create(provider_type, config)
