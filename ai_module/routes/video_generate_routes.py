"""
视频生成路由

POST /api/ai/video/generate - 生成视频（调用第三方 API + 下载）
"""

import logging
from flask import Blueprint, request, jsonify
from pathlib import Path
from ai_module.services.video_generator import get_video_generator_service
from conf import DATA_DIR

logger = logging.getLogger(__name__)


def create_video_generate_blueprint():
    bp = Blueprint('ai_video_generate', __name__)

    @bp.route('/video/generate', methods=['POST'])
    def generate_video():
        """
        生成视频
        
        请求体:
        {
            "prompt": "视频提示词",
            "duration": 15,  # 可选，默认 15
            "aspect_ratio": "9:16",  # 可选，默认 9:16
            "download": true  # 可选，是否下载到本地，默认 true
        }
        
        响应:
        {
            "success": true,
            "video_url": "https://...",
            "local_path": "uploads/videos/video_xxx.mp4",  # 如果下载了
            "filename": "video_xxx.mp4"  # 如果下载了
        }
        """
        try:
            data = request.get_json() or {}
            
            prompt = (data.get('prompt') or '').strip()
            duration = int(data.get('duration') or 15)
            aspect_ratio = data.get('aspect_ratio') or '9:16'
            should_download = data.get('download', True)
            
            if not prompt:
                return jsonify({"success": False, "error": "Prompt is required"}), 400
            
            logger.info(f"Generate video: prompt={prompt[:50]}..., duration={duration}s, aspect_ratio={aspect_ratio}")
            
            # 确定下载目录
            download_dir = None
            if should_download:
                download_dir = Path(DATA_DIR) / 'uploads' / 'videos'
            
            # 调用视频生成服务
            service = get_video_generator_service()
            result = service.generate_video(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                download_dir=download_dir
            )
            
            if not result['success']:
                return jsonify(result), 500
            
            # 构造响应
            response = {
                "success": True,
                "video_url": result['video_url']
            }
            
            if result.get('local_path'):
                local_path = Path(result['local_path'])
                response['local_path'] = str(local_path.relative_to(DATA_DIR))
                response['filename'] = local_path.name
            
            if result.get('task_id'):
                response['task_id'] = result['task_id']
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Video generate route error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return bp

