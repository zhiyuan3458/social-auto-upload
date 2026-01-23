"""
图片生成路由

POST /api/ai/generate - 生成图片 (SSE)
POST /api/ai/regenerate - 重新生成单张图片
GET /api/ai/images/<task_id>/<filename> - 获取图片
"""

import json
import logging
import base64
from flask import Blueprint, request, jsonify, Response, send_file
from ai_module.services import get_image_service

logger = logging.getLogger(__name__)


def create_image_blueprint():
    """创建图片路由蓝图"""
    bp = Blueprint('ai_image', __name__)
    
    @bp.route('/generate', methods=['POST'])
    def generate_images():
        """生成图片（SSE 流式返回）"""
        try:
            data = request.get_json() or {}
            
            pages = data.get('pages', [])
            task_id = data.get('task_id')
            full_outline = data.get('full_outline', '')
            user_topic = data.get('user_topic', '')
            user_images_base64 = data.get('user_images', [])
            
            if not pages:
                return jsonify({
                    "success": False,
                    "error": "Pages is required"
                }), 400
            
            # 解码用户图片
            user_images = None
            if user_images_base64:
                user_images = []
                for b64 in user_images_base64:
                    if ',' in b64:
                        b64 = b64.split(',')[1]
                    user_images.append(base64.b64decode(b64))
            
            logger.info(f"Generate images: pages={len(pages)}, task_id={task_id}")
            
            def generate():
                service = get_image_service()
                for event in service.generate_images(
                    pages=pages,
                    task_id=task_id,
                    full_outline=full_outline,
                    user_images=user_images,
                    user_topic=user_topic
                ):
                    event_type = event.get('event', 'message')
                    event_data = event.get('data', {})
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
            
            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive'
                }
            )
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/regenerate', methods=['POST'])
    def regenerate_image():
        """重新生成单张图片"""
        try:
            data = request.get_json() or {}
            
            task_id = data.get('task_id')
            page = data.get('page')
            use_reference = data.get('use_reference', True)
            full_outline = data.get('full_outline', '')
            user_topic = data.get('user_topic', '')
            
            if not task_id or not page:
                return jsonify({
                    "success": False,
                    "error": "task_id and page are required"
                }), 400
            
            service = get_image_service()
            result = service.retry_single_image(
                task_id=task_id,
                page=page,
                use_reference=use_reference,
                full_outline=full_outline,
                user_topic=user_topic
            )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Image regeneration error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/images/<task_id>/<filename>', methods=['GET'])
    def get_image(task_id, filename):
        """获取图片"""
        try:
            thumbnail = request.args.get('thumbnail', 'false').lower() == 'true'
            
            service = get_image_service()
            
            if thumbnail:
                filename = f"thumb_{filename}"
            
            image_path = service.get_image_path(task_id, filename)
            
            return send_file(image_path, mimetype='image/png')
            
        except Exception as e:
            logger.error(f"Get image error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 404
    
    return bp
