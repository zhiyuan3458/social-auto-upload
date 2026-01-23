"""
AI 图文生成模块

功能：
- 大纲生成 (outline)
- 图片生成 (image)
- 内容生成 (content) - 标题/文案/标签
- 历史记录管理 (history)
- AI 服务商配置 (config)
"""

from .routes import register_ai_routes

__all__ = ['register_ai_routes']
