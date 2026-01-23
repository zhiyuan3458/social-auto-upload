"""
内容生成路由

POST /api/ai/content - 生成标题/文案/标签
"""

import logging
from flask import Blueprint, request, jsonify
from ai_module.services import get_content_service

logger = logging.getLogger(__name__)


def create_content_blueprint():
    """创建内容路由蓝图"""
    bp = Blueprint('ai_content', __name__)
    
    @bp.route('/content', methods=['POST'])
    def generate_content():
        """生成标题、文案、标签"""
        try:
            data = request.get_json() or {}
            
            topic = data.get('topic', '')
            outline = data.get('outline', '')
            
            if not topic:
                return jsonify({
                    "success": False,
                    "error": "Topic is required"
                }), 400
            
            logger.info(f"Generate content: topic={topic[:50]}...")
            
            service = get_content_service()
            result = service.generate_content(topic, outline)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bp
