"""
图片压缩工具

用于压缩 AI 生成的图片，减少存储和传输开销
"""

import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def compress_image(image_data: bytes, max_size_kb: int = 200, quality: int = 85) -> bytes:
    """
    压缩图片到指定大小以内
    
    Args:
        image_data: 原始图片二进制数据
        max_size_kb: 目标最大大小 (KB)
        quality: 初始压缩质量 (1-100)
        
    Returns:
        压缩后的图片二进制数据
    """
    try:
        # 打开图片
        img = Image.open(io.BytesIO(image_data))
        
        # 如果是 RGBA 模式，转换为 RGB
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 逐步降低质量直到达到目标大小
        current_quality = quality
        while current_quality > 10:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=current_quality, optimize=True)
            
            if output.tell() <= max_size_kb * 1024:
                output.seek(0)
                return output.read()
            
            current_quality -= 10
        
        # 如果质量降到最低还是太大，则缩小尺寸
        width, height = img.size
        while True:
            width = int(width * 0.8)
            height = int(height * 0.8)
            
            if width < 100 or height < 100:
                break
            
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            resized.save(output, format='JPEG', quality=60, optimize=True)
            
            if output.tell() <= max_size_kb * 1024:
                output.seek(0)
                return output.read()
        
        # 最后尝试
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=50, optimize=True)
        output.seek(0)
        return output.read()
        
    except Exception as e:
        logger.error(f"Image compression failed: {e}")
        return image_data
