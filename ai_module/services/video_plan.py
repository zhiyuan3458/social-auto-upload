"""
视频提示词包生成服务

目标：生成通用生视频提示词（可灵/即梦等）+ 分镜结构化数据
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from ai_module.config import AIConfig
from ai_module.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class VideoPlanService:
    """生成视频提示词包（storyboard + prompt pack）"""

    def __init__(self):
        self.text_config = AIConfig.load_text_providers_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"VideoPlanService initialized, provider: {self.text_config.get('active_provider')}")

    def _get_client(self):
        active_provider = self.text_config.get('active_provider', 'custom')
        providers = self.text_config.get('providers', {})

        if not providers:
            raise ValueError("No text provider configured. Please configure in AI settings.")

        if active_provider not in providers:
            available = ', '.join(providers.keys())
            raise ValueError(f"Text provider [{active_provider}] not found. Available: {available}")

        provider_config = providers.get(active_provider, {})
        if not provider_config.get('api_key'):
            raise ValueError(f"API Key not configured for text provider [{active_provider}]")

        return get_text_chat_client(provider_config)

    def _load_prompt_template(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "video_plan_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")

        # fallback（理论不会走到）
        return "请输出严格JSON。"

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析 AI 返回的 JSON 响应（兼容 markdown code block / 前后噪声）"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response_text[start_idx:end_idx + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError("AI response format error (invalid JSON)")

    def generate_video_plan(
        self,
        topic: str,
        platform: str = "xiaohongshu",
        aspect_ratio: str = "9:16",
        duration_seconds: int = 15,
        product_info: str = "",
        target_audience: str = "",
        selling_points: str = "",
        style: str = "",
        must_include: str = "",
        forbidden: str = "",
        outline: str = ""
    ) -> Dict[str, Any]:
        """
        生成视频提示词包
        """
        try:
            if not topic:
                return {"success": False, "error": "Topic is required"}

            # 模型参数
            active_provider = self.text_config.get('active_provider', 'custom')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})
            model = provider_config.get('model', 'gpt-4')
            temperature = provider_config.get('temperature', 0.6)
            max_output_tokens = provider_config.get('max_output_tokens', 4096)

            # prompt
            prompt = self.prompt_template.format(
                platform=platform,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                topic=topic,
                product_info=product_info or "（无）",
                target_audience=target_audience or "（无）",
                selling_points=selling_points or "（无）",
                style=style or "（无）",
                must_include=must_include or "（无）",
                forbidden=forbidden or "（无）",
                outline=outline or "（无）"
            )

            logger.info(f"Generating video plan: topic={topic[:50]}..., model={model}")
            response_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )

            data = self._parse_json_response(response_text)

            # 轻度校验 + 默认补齐
            if "platform" not in data:
                data["platform"] = platform
            if "aspect_ratio" not in data:
                data["aspect_ratio"] = aspect_ratio
            if "duration_seconds" not in data:
                data["duration_seconds"] = duration_seconds

            return {"success": True, "video_plan": data}

        except Exception as e:
            logger.error(f"Video plan generation failed: {e}")
            return {"success": False, "error": f"Video plan generation failed: {str(e)}"}


_video_plan_service: Optional[VideoPlanService] = None


def get_video_plan_service() -> VideoPlanService:
    """获取单例服务实例（避免每次加载模板/配置）"""
    global _video_plan_service
    if _video_plan_service is None:
        _video_plan_service = VideoPlanService()
    return _video_plan_service


