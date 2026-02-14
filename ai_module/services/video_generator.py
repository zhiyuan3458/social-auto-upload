"""
视频生成服务
调用可灵/即梦等第三方 API 生成视频
"""

import logging
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from ai_module.config import AIConfig

logger = logging.getLogger(__name__)


class VideoGeneratorService:
    """视频生成服务类"""
    
    def __init__(self):
        self.config = AIConfig.load_video_generation_config()
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """从嵌套字典中获取值，支持 data.result.url 格式"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def _replace_template_vars(self, template: str, variables: Dict[str, Any]) -> str:
        """替换模板变量 {{var}}"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def generate_video(
        self,
        prompt: str,
        duration: int = 15,
        aspect_ratio: str = "9:16",
        download_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        生成视频
        
        Args:
            prompt: 视频提示词
            duration: 视频时长（秒）
            aspect_ratio: 画幅比例
            download_dir: 视频下载目录（如果为 None，则不下载）
        
        Returns:
            {
                "success": bool,
                "video_url": str,  # 视频 URL
                "local_path": str,  # 本地路径（如果下载了）
                "task_id": str,  # 任务 ID（如果有）
                "error": str  # 错误信息（如果失败）
            }
        """
        try:
            if not self.config.get('api_url'):
                return {"success": False, "error": "视频生成 API 未配置"}
            
            # 1) 准备请求参数
            api_url = self.config['api_url']
            method = self.config.get('method', 'POST').upper()
            headers = self.config.get('headers', {})
            
            # 替换请求体模板中的变量
            body_template = self.config.get('body_template', {})
            variables = {
                'prompt': prompt,
                'duration': duration,
                'aspect_ratio': aspect_ratio
            }
            
            # 递归替换 body_template 中的变量
            def replace_in_dict(obj):
                if isinstance(obj, dict):
                    return {k: replace_in_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_in_dict(item) for item in obj]
                elif isinstance(obj, str):
                    return self._replace_template_vars(obj, variables)
                else:
                    return obj
            
            body = replace_in_dict(body_template)
            
            logger.info(f"Calling video generation API: {api_url}")
            logger.debug(f"Request body: {body}")
            
            # 2) 发起请求
            if method == 'POST':
                response = requests.post(api_url, json=body, headers=headers, timeout=30)
            else:
                response = requests.get(api_url, params=body, headers=headers, timeout=30)
            
            response.raise_for_status()
            result_data = response.json()
            
            logger.debug(f"API response: {result_data}")
            
            # 3) 判断是否需要轮询
            need_polling = self.config.get('need_polling', False)
            
            if need_polling:
                # 提取任务 ID
                task_id_path = self.config.get('task_id_path', 'data.task_id')
                task_id = self._get_nested_value(result_data, task_id_path)
                
                if not task_id:
                    return {"success": False, "error": f"无法从响应中提取任务 ID（路径：{task_id_path}）"}
                
                logger.info(f"Task ID: {task_id}, starting polling...")
                
                # 轮询获取结果
                video_url = self._poll_task_result(task_id)
                if not video_url:
                    return {"success": False, "error": "轮询超时或任务失败"}
            else:
                # 直接从响应中提取视频 URL
                response_video_path = self.config.get('response_video_path', 'data.video_url')
                video_url = self._get_nested_value(result_data, response_video_path)
                
                if not video_url:
                    return {"success": False, "error": f"无法从响应中提取视频 URL（路径：{response_video_path}）"}
            
            logger.info(f"Video URL: {video_url}")
            
            # 4) 下载视频（如果指定了下载目录）
            local_path = None
            if download_dir:
                local_path = self._download_video(video_url, download_dir)
                if not local_path:
                    return {"success": False, "error": "视频下载失败"}
            
            return {
                "success": True,
                "video_url": video_url,
                "local_path": str(local_path) if local_path else None,
                "task_id": result_data.get('task_id') or result_data.get('id')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Video generation API request error: {e}")
            return {"success": False, "error": f"API 请求失败: {str(e)}"}
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _poll_task_result(self, task_id: str) -> Optional[str]:
        """轮询任务结果"""
        poll_url_template = self.config.get('poll_url', '')
        if not poll_url_template:
            logger.error("Poll URL not configured")
            return None
        
        poll_url = self._replace_template_vars(poll_url_template, {'task_id': task_id})
        poll_interval = self.config.get('poll_interval', 5)
        max_poll_count = self.config.get('max_poll_count', 30)
        success_status = self.config.get('success_status', 'completed')
        status_path = self.config.get('status_path', 'data.status')
        response_video_path = self.config.get('response_video_path', 'data.video_url')
        headers = self.config.get('headers', {})
        
        for i in range(max_poll_count):
            try:
                logger.debug(f"Polling attempt {i+1}/{max_poll_count}: {poll_url}")
                response = requests.get(poll_url, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # 检查状态
                status = self._get_nested_value(data, status_path)
                logger.debug(f"Task status: {status}")
                
                if status == success_status:
                    # 任务完成，提取视频 URL
                    video_url = self._get_nested_value(data, response_video_path)
                    if video_url:
                        logger.info(f"Task completed, video URL: {video_url}")
                        return video_url
                    else:
                        logger.error(f"Task completed but no video URL found (path: {response_video_path})")
                        return None
                elif status in ['failed', 'error', 'cancelled']:
                    logger.error(f"Task failed with status: {status}")
                    return None
                
                # 继续等待
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(poll_interval)
        
        logger.error("Polling timeout")
        return None
    
    def _download_video(self, video_url: str, download_dir: Path) -> Optional[Path]:
        """下载视频到本地"""
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = int(time.time())
            filename = f"video_{timestamp}.mp4"
            local_path = download_dir / filename
            
            logger.info(f"Downloading video from {video_url} to {local_path}")
            
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Video downloaded successfully: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Video download error: {e}")
            return None


# 单例服务
_video_generator_service = None

def get_video_generator_service() -> VideoGeneratorService:
    """获取视频生成服务单例"""
    global _video_generator_service
    if _video_generator_service is None:
        _video_generator_service = VideoGeneratorService()
    return _video_generator_service

