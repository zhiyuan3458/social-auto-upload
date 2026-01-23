# -*- coding: utf-8 -*-
"""
小红书图文上传模块

支持多图上传 + 文案发布
发布地址: https://creator.xiaohongshu.com/publish/publish?from=menu&target=image
"""

from datetime import datetime
from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio
from pathlib import Path
from typing import List, Optional

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import xiaohongshu_logger


class XiaoHongShuImage:
    """小红书图文上传类"""
    
    def __init__(
        self,
        title: str,
        image_paths: List[str],
        content: str,
        tags: List[str],
        publish_date: datetime,
        account_file: str
    ):
        """
        初始化
        
        Args:
            title: 笔记标题
            image_paths: 图片路径列表 (最多18张)
            content: 正文内容
            tags: 话题标签列表 (不带#号)
            publish_date: 发布时间，0表示立即发布
            account_file: cookie 文件路径
        """
        self.title = title[:20] if title else ""  # 标题最多20字
        self.image_paths = image_paths[:18]  # 最多18张图
        self.content = content[:1000] if content else ""  # 正文最多1000字
        self.tags = tags[:10] if tags else []  # 最多10个标签
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y-%m-%d %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
    
    async def set_schedule_time(self, page: Page, publish_date: datetime):
        """设置定时发布时间"""
        xiaohongshu_logger.info("  [-] 正在设置定时发布时间...")
        xiaohongshu_logger.info(f"publish_date: {publish_date}")
        
        # 点击定时发布选项
        label_element = page.locator("label:has-text('定时发布')")
        await label_element.click()
        await asyncio.sleep(1)
        
        publish_date_str = publish_date.strftime(self.date_format)
        xiaohongshu_logger.info(f"publish_date_str: {publish_date_str}")
        
        await asyncio.sleep(1)
        await page.locator('.el-input__inner[placeholder="选择日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_str))
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
    
    async def upload(self, playwright: Playwright) -> bool:
        """
        执行上传
        
        Returns:
            是否上传成功
        """
        # 启动浏览器
        if self.local_executable_path:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.local_executable_path
            )
        else:
            browser = await playwright.chromium.launch(headless=self.headless)
        
        # 创建浏览器上下文
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            storage_state=self.account_file
        )
        context = await set_init_script(context)
        
        # 创建页面
        page = await context.new_page()
        
        try:
            # 访问图文发布页面
            xiaohongshu_logger.info(f'[+] 正在上传图文: {self.title}')
            await page.goto("https://creator.xiaohongshu.com/publish/publish?from=menu&target=image")
            
            # 等待页面加载
            xiaohongshu_logger.info('[-] 正在打开图文发布页面...')
            await page.wait_for_url(
                "https://creator.xiaohongshu.com/publish/publish?from=menu&target=image",
                timeout=10000
            )
            await asyncio.sleep(2)
            
            # 上传图片
            xiaohongshu_logger.info(f'[-] 正在上传 {len(self.image_paths)} 张图片...')
            
            # 查找上传输入框
            upload_input = page.locator("input.upload-input")
            if await upload_input.count() == 0:
                # 尝试其他选择器
                upload_input = page.locator("div[class^='upload-content'] input[type='file']")
            
            # 上传所有图片
            await upload_input.set_input_files(self.image_paths)
            
            # 等待图片上传完成
            xiaohongshu_logger.info('[-] 等待图片上传完成...')
            await self._wait_for_upload_complete(page)
            
            # 填写标题
            xiaohongshu_logger.info(f'[-] 正在填写标题: {self.title}')
            await self._fill_title(page)
            
            # 填写正文和标签
            xiaohongshu_logger.info(f'[-] 正在填写正文和标签...')
            await self._fill_content_and_tags(page)
            
            # 设置定时发布
            if self.publish_date != 0:
                await self.set_schedule_time(page, self.publish_date)
            
            # 点击发布按钮
            xiaohongshu_logger.info('[-] 正在发布...')
            await self._click_publish(page)
            
            # 保存 cookie
            await context.storage_state(path=self.account_file)
            xiaohongshu_logger.success('[-] cookie 更新完毕！')
            
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            xiaohongshu_logger.error(f'[-] 上传失败: {str(e)}')
            # 截图保存错误信息
            try:
                await page.screenshot(path='xhs_image_upload_error.png', full_page=True)
            except:
                pass
            return False
            
        finally:
            await context.close()
            await browser.close()
    
    async def _wait_for_upload_complete(self, page: Page, timeout: int = 60):
        """等待图片上传完成"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError("图片上传超时")
            
            try:
                # 检查是否有上传中的状态
                uploading = await page.locator('div:has-text("上传中")').count()
                if uploading == 0:
                    # 检查是否有图片预览显示
                    preview_count = await page.locator('div[class*="preview"] img, div[class*="image-item"] img').count()
                    if preview_count >= len(self.image_paths):
                        xiaohongshu_logger.info(f'[+] 图片上传完成，共 {preview_count} 张')
                        break
                
                xiaohongshu_logger.info(f'[-] 正在上传图片中... ({int(elapsed)}s)')
                await asyncio.sleep(1)
                
            except Exception as e:
                xiaohongshu_logger.warning(f'[-] 检测上传状态出错: {e}')
                await asyncio.sleep(1)
        
        await asyncio.sleep(1)
    
    async def _fill_title(self, page: Page):
        """填写标题"""
        # 尝试多种标题输入框选择器
        title_selectors = [
            'div.plugin.title-container input.d-text',
            'input[placeholder*="标题"]',
            'div[class*="title"] input',
            '.notranslate'
        ]
        
        for selector in title_selectors:
            try:
                title_input = page.locator(selector).first
                if await title_input.count() > 0:
                    await title_input.click()
                    await page.keyboard.press("Control+KeyA")
                    await page.keyboard.type(self.title)
                    xiaohongshu_logger.info(f'[+] 标题填写成功')
                    return
            except:
                continue
        
        xiaohongshu_logger.warning('[-] 未找到标题输入框')
    
    async def _fill_content_and_tags(self, page: Page):
        """填写正文内容和标签"""
        # 定位正文编辑器
        content_selector = ".ql-editor"
        
        try:
            editor = page.locator(content_selector).first
            await editor.click()
            
            # 输入正文
            if self.content:
                await page.keyboard.type(self.content)
                await page.keyboard.press("Enter")
            
            # 输入标签
            for tag in self.tags:
                await page.keyboard.type("#" + tag)
                await page.keyboard.press("Space")
            
            xiaohongshu_logger.info(f'[+] 正文和 {len(self.tags)} 个标签填写完成')
            
        except Exception as e:
            xiaohongshu_logger.warning(f'[-] 填写正文失败: {e}')
    
    async def _click_publish(self, page: Page):
        """点击发布按钮"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                if self.publish_date != 0:
                    publish_btn = page.locator('button:has-text("定时发布")')
                else:
                    publish_btn = page.locator('button:has-text("发布")')
                
                await publish_btn.click()
                
                # 等待跳转到成功页面
                await page.wait_for_url(
                    "https://creator.xiaohongshu.com/publish/success**",
                    timeout=5000
                )
                xiaohongshu_logger.success('[+] 图文发布成功！')
                return
                
            except Exception as e:
                xiaohongshu_logger.info(f'[-] 等待发布完成... (尝试 {attempt + 1}/{max_attempts})')
                await asyncio.sleep(1)
        
        raise Exception("发布超时")
    
    async def main(self):
        """主入口"""
        async with async_playwright() as playwright:
            return await self.upload(playwright)


async def post_image_xhs(
    title: str,
    image_paths: List[str],
    content: str,
    tags: List[str],
    account_file: str,
    publish_date: datetime = 0
) -> bool:
    """
    发布小红书图文
    
    Args:
        title: 标题
        image_paths: 图片路径列表
        content: 正文内容
        tags: 标签列表
        account_file: cookie 文件路径
        publish_date: 发布时间，0 表示立即发布
        
    Returns:
        是否发布成功
    """
    uploader = XiaoHongShuImage(
        title=title,
        image_paths=image_paths,
        content=content,
        tags=tags,
        publish_date=publish_date,
        account_file=account_file
    )
    return await uploader.main()
