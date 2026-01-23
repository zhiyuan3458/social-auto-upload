# -*- coding: utf-8 -*-
"""
小红书图文笔记发布脚本
使用 xhs 库 API 方式发布图文内容
"""
import configparser
from pathlib import Path
from time import sleep

from xhs import XhsClient

from conf import BASE_DIR
from uploader.xhs_uploader.main import sign_local, beauty_print

# ============ 配置区域 ============
# Cookie 配置文件路径
CONFIG_FILE = Path(BASE_DIR / "uploader" / "xhs_uploader" / "accounts.ini")
# 图片目录
IMAGE_DIR = Path(BASE_DIR) / "images"
# =================================


def get_xhs_client():
    """获取已认证的小红书客户端"""
    config = configparser.RawConfigParser()
    config.read(CONFIG_FILE)
    
    try:
        cookies = config['account1']['cookies']
    except KeyError:
        print("[!] 请先配置 accounts.ini 文件中的 cookies")
        print(f"    文件路径: {CONFIG_FILE}")
        return None
    
    xhs_client = XhsClient(cookies, sign=sign_local, timeout=60)
    
    # 验证 cookie 是否有效
    try:
        xhs_client.get_video_first_frame_image_id("3214")
        print("[+] Cookie 有效")
        return xhs_client
    except Exception as e:
        print(f"[!] Cookie 失效或无效: {e}")
        print("[*] 请重新获取 Cookie 并更新 accounts.ini")
        return None


def publish_image_note(
    xhs_client: XhsClient,
    title: str,
    desc: str,
    image_paths: list,
    tags: list = None,
    post_time: str = None,
    is_private: bool = False
):
    """
    发布图文笔记
    
    :param xhs_client: 小红书客户端
    :param title: 标题（最多20字）
    :param desc: 正文描述（可以很长）
    :param image_paths: 图片路径列表（最多9张）
    :param tags: 话题标签列表
    :param post_time: 定时发布时间，格式 "2024-01-21 16:00:00"
    :param is_private: 是否私密发布
    :return: 发布结果
    """
    # 处理话题
    topics = []
    hash_tags_str = ''
    
    if tags:
        hash_tags = []
        for tag in tags[:5]:  # 最多5个话题
            try:
                topic_official = xhs_client.get_suggest_topic(tag)
                if topic_official:
                    topic_official[0]['type'] = 'topic'
                    topics.append(topic_official[0])
                    hash_tags.append(topic_official[0]['name'])
            except Exception as e:
                print(f"[!] 获取话题 '{tag}' 失败: {e}")
        
        if hash_tags:
            hash_tags_str = ' ' + ' '.join(['#' + tag + '[话题]#' for tag in hash_tags])
    
    # 构建完整描述
    full_desc = desc + hash_tags_str
    
    print(f"\n[*] 准备发布图文笔记:")
    print(f"    标题: {title[:20]}")
    print(f"    图片数量: {len(image_paths)}")
    print(f"    话题: {tags}")
    if post_time:
        print(f"    定时发布: {post_time}")
    
    try:
        note = xhs_client.create_image_note(
            title=title[:20],  # 标题限制20字
            desc=full_desc,
            files=image_paths,
            topics=topics if topics else None,
            post_time=post_time,
            is_private=is_private
        )
        print("[+] 图文笔记发布成功!")
        beauty_print(note)
        return note
    except Exception as e:
        print(f"[!] 发布失败: {e}")
        return None


def publish_video_note(
    xhs_client: XhsClient,
    title: str,
    desc: str,
    video_path: str,
    tags: list = None,
    post_time: str = None,
    is_private: bool = False
):
    """
    发布视频笔记
    
    :param xhs_client: 小红书客户端
    :param title: 标题（最多20字）
    :param desc: 正文描述
    :param video_path: 视频文件路径
    :param tags: 话题标签列表
    :param post_time: 定时发布时间
    :param is_private: 是否私密发布
    :return: 发布结果
    """
    # 处理话题（同图文）
    topics = []
    hash_tags_str = ''
    tags_str = ' '.join(['#' + tag for tag in (tags or [])])
    
    if tags:
        hash_tags = []
        for tag in tags[:3]:
            try:
                topic_official = xhs_client.get_suggest_topic(tag)
                if topic_official:
                    topic_official[0]['type'] = 'topic'
                    topics.append(topic_official[0])
                    hash_tags.append(topic_official[0]['name'])
            except:
                pass
        
        if hash_tags:
            hash_tags_str = ' ' + ' '.join(['#' + tag + '[话题]#' for tag in hash_tags])
    
    full_desc = desc + tags_str + hash_tags_str
    
    print(f"\n[*] 准备发布视频笔记:")
    print(f"    标题: {title[:20]}")
    print(f"    视频: {video_path}")
    
    try:
        note = xhs_client.create_video_note(
            title=title[:20],
            video_path=str(video_path),
            desc=full_desc,
            topics=topics if topics else None,
            post_time=post_time,
            is_private=is_private
        )
        print("[+] 视频笔记发布成功!")
        beauty_print(note)
        return note
    except Exception as e:
        print(f"[!] 发布失败: {e}")
        return None


# ============ 使用示例 ============

if __name__ == '__main__':
    # 1. 获取客户端
    client = get_xhs_client()
    if not client:
        exit(1)
    
    # 2. 发布图文笔记示例
    print("\n" + "=" * 50)
    print("📸 图文发布示例")
    print("=" * 50)
    
    # 准备图片（确保图片存在）
    sample_images = [
        str(Path(BASE_DIR) / "videos" / "demo.png"),  # 使用现有的 demo.png
    ]
    
    # 检查图片是否存在
    existing_images = [img for img in sample_images if Path(img).exists()]
    
    if existing_images:
        result = publish_image_note(
            xhs_client=client,
            title="测试图文笔记",
            desc="这是一条测试图文笔记的内容，可以写很长的文字描述。",
            image_paths=existing_images,
            tags=["测试", "学习"],
            # post_time="2024-01-22 16:00:00",  # 取消注释可定时发布
            is_private=True  # 先设为私密，测试用
        )
    else:
        print(f"[!] 未找到示例图片，请在 {IMAGE_DIR} 目录放入图片")
        print("[*] 支持的图片格式: jpg, png, webp")
    
    # 强制休眠避免风控
    sleep(5)
    
    print("\n" + "=" * 50)
    print("💡 使用提示")
    print("=" * 50)
    print("""
1. 首次使用需要配置 Cookie:
   - 文件: uploader/xhs_uploader/accounts.ini
   - 格式:
     [account1]
     cookies = 你的小红书cookie字符串

2. 获取 Cookie 方法:
   - 打开小红书网页版登录
   - F12 打开开发者工具 -> Network
   - 刷新页面，找到任意请求
   - 复制 Request Headers 中的 Cookie 值

3. 图文笔记限制:
   - 标题最多 20 字
   - 图片最多 9 张
   - 支持 jpg/png/webp 格式

4. 风控建议:
   - 每次发布间隔 30 秒以上
   - 避免短时间大量发布
""")
