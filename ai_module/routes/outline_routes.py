"""
大纲生成路由

POST /api/ai/outline - 生成大纲
"""

import logging
from flask import Blueprint, request, jsonify
from ai_module.services import get_outline_service

logger = logging.getLogger(__name__)


def create_outline_blueprint():
    """创建大纲路由蓝图"""
    bp = Blueprint('ai_outline', __name__)
    
    @bp.route('/outline', methods=['POST'])
    def generate_outline():
        """生成大纲"""
        try:
            # 支持 JSON 和 FormData
            if request.content_type and 'multipart/form-data' in request.content_type:
                topic = request.form.get('topic', '')
                images = []
                if 'images' in request.files:
                    for file in request.files.getlist('images'):
                        images.append(file.read())
            else:
                data = request.get_json() or {}
                topic = data.get('topic', '')
                images = None
            
            if not topic:
                return jsonify({
                    "success": False,
                    "error": "Topic is required"
                }), 400
            
            logger.info(f"Generate outline: topic={topic[:50]}...")
            
            service = get_outline_service()
            result = service.generate_outline(topic, images)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Outline generation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bp
