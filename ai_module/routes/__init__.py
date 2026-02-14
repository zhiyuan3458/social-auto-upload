"""
AI API 路由模块

路由前缀：/api/ai
"""

from flask import Blueprint


def create_ai_blueprint():
    """创建 AI API 蓝图"""
    from .outline_routes import create_outline_blueprint
    from .image_routes import create_image_blueprint
    from .content_routes import create_content_blueprint
    from .video_routes import create_video_blueprint
    from .video_generate_routes import create_video_generate_blueprint
    from .config_routes import create_config_blueprint
    from .history_routes import create_history_blueprint

    
    # 创建主 AI 蓝图
    ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
    
    # 注册子蓝图
    ai_bp.register_blueprint(create_outline_blueprint())
    ai_bp.register_blueprint(create_image_blueprint())
    ai_bp.register_blueprint(create_content_blueprint())
    ai_bp.register_blueprint(create_video_blueprint())
    ai_bp.register_blueprint(create_video_generate_blueprint())
    ai_bp.register_blueprint(create_config_blueprint())
    ai_bp.register_blueprint(create_history_blueprint())
    
    return ai_bp


def register_ai_routes(app):
    """注册 AI 路由到 Flask 应用"""
    ai_bp = create_ai_blueprint()
    app.register_blueprint(ai_bp)


__all__ = ['register_ai_routes', 'create_ai_blueprint']
