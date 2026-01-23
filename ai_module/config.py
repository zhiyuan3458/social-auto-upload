"""
AI 模块配置管理

支持用户自定义配置：
- Base URL (API 地址)
- API Key (密钥)
- Model (模型名称)
- 其他参数 (temperature, max_tokens 等)
"""

import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

# 获取数据目录
def get_data_dir():
    """获取数据目录"""
    from conf import DATA_DIR
    return DATA_DIR


class AIConfig:
    """AI 配置管理类"""
    
    _text_providers_config = None
    _image_providers_config = None
    
    # 默认配置
    DEFAULT_TEXT_CONFIG = {
        'active_provider': 'custom',
        'providers': {
            'custom': {
                'type': 'openai_compatible',
                'name': '自定义 API',
                'base_url': '',
                'api_key': '',
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_output_tokens': 4096
            }
        }
    }
    
    DEFAULT_IMAGE_CONFIG = {
        'active_provider': 'custom',
        'providers': {
            'custom': {
                'type': 'openai_compatible',
                'name': '自定义图片 API',
                'base_url': '',
                'api_key': '',
                'model': 'dall-e-3',
                'default_size': '1024x1024',
                'quality': 'standard'
            }
        }
    }
    
    @classmethod
    def get_config_dir(cls):
        """获取 AI 配置目录"""
        config_dir = Path(get_data_dir()) / 'ai_config'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @classmethod
    def get_history_dir(cls):
        """获取 AI 历史记录目录"""
        history_dir = Path(get_data_dir()) / 'ai_history'
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir
    
    @classmethod
    def load_text_providers_config(cls, force_reload=False):
        """加载文本生成服务商配置"""
        if cls._text_providers_config is not None and not force_reload:
            return cls._text_providers_config
        
        config_path = cls.get_config_dir() / 'text_providers.yaml'
        logger.debug(f"Loading text providers config: {config_path}")
        
        if not config_path.exists():
            logger.info("Text providers config not found, using default")
            cls._text_providers_config = cls.DEFAULT_TEXT_CONFIG.copy()
            cls.save_text_providers_config(cls._text_providers_config)
            return cls._text_providers_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._text_providers_config = yaml.safe_load(f) or {}
            logger.debug(f"Text providers config loaded: {list(cls._text_providers_config.get('providers', {}).keys())}")
        except yaml.YAMLError as e:
            logger.error(f"Text providers config YAML error: {e}")
            cls._text_providers_config = cls.DEFAULT_TEXT_CONFIG.copy()
        
        return cls._text_providers_config
    
    @classmethod
    def save_text_providers_config(cls, config):
        """保存文本生成服务商配置"""
        config_path = cls.get_config_dir() / 'text_providers.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        cls._text_providers_config = config
        logger.info(f"Text providers config saved to {config_path}")
    
    @classmethod
    def load_image_providers_config(cls, force_reload=False):
        """加载图片生成服务商配置"""
        if cls._image_providers_config is not None and not force_reload:
            return cls._image_providers_config
        
        config_path = cls.get_config_dir() / 'image_providers.yaml'
        logger.debug(f"Loading image providers config: {config_path}")
        
        if not config_path.exists():
            logger.info("Image providers config not found, using default")
            cls._image_providers_config = cls.DEFAULT_IMAGE_CONFIG.copy()
            cls.save_image_providers_config(cls._image_providers_config)
            return cls._image_providers_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._image_providers_config = yaml.safe_load(f) or {}
            logger.debug(f"Image providers config loaded: {list(cls._image_providers_config.get('providers', {}).keys())}")
        except yaml.YAMLError as e:
            logger.error(f"Image providers config YAML error: {e}")
            cls._image_providers_config = cls.DEFAULT_IMAGE_CONFIG.copy()
        
        return cls._image_providers_config
    
    @classmethod
    def save_image_providers_config(cls, config):
        """保存图片生成服务商配置"""
        config_path = cls.get_config_dir() / 'image_providers.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        cls._image_providers_config = config
        logger.info(f"Image providers config saved to {config_path}")
    
    @classmethod
    def get_active_text_provider(cls):
        """获取当前激活的文本服务商"""
        config = cls.load_text_providers_config()
        return config.get('active_provider', 'custom')
    
    @classmethod
    def get_active_image_provider(cls):
        """获取当前激活的图片服务商"""
        config = cls.load_image_providers_config()
        return config.get('active_provider', 'custom')
    
    @classmethod
    def get_text_provider_config(cls, provider_name=None):
        """获取指定文本服务商的配置"""
        config = cls.load_text_providers_config()
        
        if provider_name is None:
            provider_name = cls.get_active_text_provider()
        
        providers = config.get('providers', {})
        if provider_name not in providers:
            raise ValueError(f"Text provider not found: {provider_name}")
        
        return providers[provider_name]
    
    @classmethod
    def get_image_provider_config(cls, provider_name=None):
        """获取指定图片服务商的配置"""
        config = cls.load_image_providers_config()
        
        if provider_name is None:
            provider_name = cls.get_active_image_provider()
        
        providers = config.get('providers', {})
        if provider_name not in providers:
            raise ValueError(f"Image provider not found: {provider_name}")
        
        return providers[provider_name]
    
    @classmethod
    def reload_config(cls):
        """重新加载所有配置"""
        cls._text_providers_config = None
        cls._image_providers_config = None
        cls.load_text_providers_config()
        cls.load_image_providers_config()
        logger.info("AI config reloaded")
