"""
AI 配置管理路由

GET /api/ai/config - 获取配置
POST /api/ai/config - 更新配置
POST /api/ai/config/test - 测试连接
"""

import logging
from flask import Blueprint, request, jsonify
from ai_module.config import AIConfig
from ai_module.services import reset_image_service

logger = logging.getLogger(__name__)


def create_config_blueprint():
    """创建配置路由蓝图"""
    bp = Blueprint('ai_config', __name__)
    
    @bp.route('/config', methods=['GET'])
    def get_config():
        """获取 AI 配置"""
        try:
            text_config = AIConfig.load_text_providers_config()
            image_config = AIConfig.load_image_providers_config()
            
            # 隐藏敏感信息
            def mask_api_key(config):
                result = {}
                for key, value in config.items():
                    if key == 'providers':
                        result['providers'] = {}
                        for name, provider in value.items():
                            result['providers'][name] = provider.copy()
                            if 'api_key' in result['providers'][name]:
                                api_key = result['providers'][name]['api_key']
                                if api_key:
                                    result['providers'][name]['api_key'] = api_key[:8] + '****'
                    else:
                        result[key] = value
                return result
            
            return jsonify({
                "success": True,
                "config": {
                    "text_generation": mask_api_key(text_config),
                    "image_generation": mask_api_key(image_config)
                }
            })
            
        except Exception as e:
            logger.error(f"Get config error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/config', methods=['POST'])
    def update_config():
        """更新 AI 配置"""
        try:
            data = request.get_json() or {}
            
            if 'text_generation' in data:
                text_config = data['text_generation']
                AIConfig.save_text_providers_config(text_config)
            
            if 'image_generation' in data:
                image_config = data['image_generation']
                AIConfig.save_image_providers_config(image_config)
                # 重置图片服务实例
                reset_image_service()
            
            return jsonify({
                "success": True,
                "message": "Configuration updated"
            })
            
        except Exception as e:
            logger.error(f"Update config error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/config/test', methods=['POST'])
    def test_connection():
        """测试 AI 服务商连接"""
        try:
            data = request.get_json() or {}
            
            provider_type = data.get('type', 'openai_compatible')
            api_key = data.get('api_key', '')
            base_url = data.get('base_url', '')
            model = data.get('model', 'gpt-4')
            
            if not api_key:
                return jsonify({
                    "success": False,
                    "error": "API Key is required"
                }), 400
            
            if not base_url:
                return jsonify({
                    "success": False,
                    "error": "Base URL is required"
                }), 400
            
            # 创建临时客户端测试
            from ai_module.generators import TextGeneratorFactory
            
            test_config = {
                'type': provider_type,
                'api_key': api_key,
                'base_url': base_url,
                'model': model,
                'timeout': 30
            }
            
            client = TextGeneratorFactory.create(provider_type, test_config)
            
            # 发送简单测试请求
            response = client.generate_text(
                prompt="Hello, this is a test. Reply with 'OK'.",
                model=model,
                max_output_tokens=50
            )
            
            if response:
                return jsonify({
                    "success": True,
                    "message": "Connection successful"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Empty response from API"
                })
            
        except Exception as e:
            logger.error(f"Test connection error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bp
