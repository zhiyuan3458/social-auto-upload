"""
视频提示词包路由

POST /api/ai/video/plan - 生成通用生视频提示词包（可灵/即梦等）
"""

import logging
from flask import Blueprint, request, jsonify

from ai_module.services.video_plan import get_video_plan_service

logger = logging.getLogger(__name__)


def create_video_blueprint():
    bp = Blueprint('ai_video', __name__)

    @bp.route('/video/plan', methods=['POST'])
    def generate_video_plan():
        try:
            data = request.get_json() or {}

            topic = (data.get('topic') or '').strip()
            outline = data.get('outline') or ''

            platform = data.get('platform') or 'xiaohongshu'
            aspect_ratio = data.get('aspect_ratio') or '9:16'
            duration_seconds = int(data.get('duration_seconds') or 15)

            product_info = data.get('product_info') or ''
            target_audience = data.get('target_audience') or ''
            selling_points = data.get('selling_points') or ''
            style = data.get('style') or ''
            must_include = data.get('must_include') or ''
            forbidden = data.get('forbidden') or ''

            if not topic:
                return jsonify({"success": False, "error": "Topic is required"}), 400

            logger.info(f"Generate video plan: topic={topic[:50]}..., duration={duration_seconds}s")

            service = get_video_plan_service()
            result = service.generate_video_plan(
                topic=topic,
                platform=platform,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                product_info=product_info,
                target_audience=target_audience,
                selling_points=selling_points,
                style=style,
                must_include=must_include,
                forbidden=forbidden,
                outline=outline
            )

            return jsonify(result)

        except Exception as e:
            logger.error(f"Video plan route error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return bp


