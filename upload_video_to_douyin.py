import asyncio
import os
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags
from playwright.async_api import async_playwright
from utils.base_social_media import set_init_script

# ============ 配置区域 ============
# 建议使用环境变量: export DOUYIN_PHONE="你的手机号" && export DOUYIN_PASSWORD="你的密码"
DOUYIN_PHONE = os.getenv("DOUYIN_PHONE", "13686524037")  # 手机号
DOUYIN_PASSWORD = os.getenv("DOUYIN_PASSWORD", "LZY83326040")  # 密码
# =================================


async def auto_login_douyin(account_file: str):
    """
    自动登录抖音（手机号+密码方式）
    注意：可能需要手动处理验证码
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        
        print("[*] 正在打开抖音创作者中心...")
        await page.goto("https://creator.douyin.com/")
        await asyncio.sleep(2)
        
        try:
            # 尝试点击"手机号登录"或"密码登录"
            print("[*] 尝试切换到密码登录...")
            
            # 方式1: 查找"手机号登录"按钮
            phone_login_btn = page.get_by_text("手机号登录")
            if await phone_login_btn.count() > 0:
                await phone_login_btn.click()
                await asyncio.sleep(1)
            
            # 方式2: 查找"密码登录"链接
            password_login_link = page.get_by_text("密码登录")
            if await password_login_link.count() > 0:
                await password_login_link.click()
                await asyncio.sleep(1)
            
            # 填充手机号
            if DOUYIN_PHONE:
                print(f"[*] 正在填充手机号: {DOUYIN_PHONE[:3]}****{DOUYIN_PHONE[-4:]}")
                phone_input = page.locator('input[placeholder*="手机号"]').first
                if await phone_input.count() > 0:
                    await phone_input.fill(DOUYIN_PHONE)
                    await asyncio.sleep(0.5)
            else:
                print("[!] 未设置手机号，请手动输入")
            
            # 填充密码
            if DOUYIN_PASSWORD:
                print("[*] 正在填充密码...")
                password_input = page.locator('input[type="password"]').first
                if await password_input.count() > 0:
                    await password_input.fill(DOUYIN_PASSWORD)
                    await asyncio.sleep(0.5)
                else:
                    # 尝试其他选择器
                    password_input = page.locator('input[placeholder*="密码"]').first
                    if await password_input.count() > 0:
                        await password_input.fill(DOUYIN_PASSWORD)
            
            print("[*] 密码已填充，请手动完成以下步骤：")
            print("    1. 检查手机号和密码是否正确")
            print("    2. 完成滑块验证（如果有）")
            print("    3. 输入短信验证码（如果有）")
            print("    4. 点击登录按钮")
            print("[*] 登录成功后会自动保存 Cookie...")
            
            # 等待用户手动完成验证和登录，监听URL变化
            print("[*] 等待登录成功（最多等待 300 秒）...")
            try:
                # 等待跳转到创作者中心主页
                await page.wait_for_url("**/creator-micro/**", timeout=300000)
                print("[+] 登录成功！")
            except:
                print("[!] 等待超时，请检查是否登录成功")
            
            # 保存 Cookie
            Path(account_file).parent.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=account_file)
            print(f"[+] Cookie 已保存到: {account_file}")
            
        except Exception as e:
            print(f"[!] 自动登录出错: {e}")
            print("[*] 请手动完成登录，然后关闭浏览器...")
            await page.pause()  # 回退到手动模式
            await context.storage_state(path=account_file)
        
        await asyncio.sleep(2)
        await context.close()
        await browser.close()
        
    return True


async def main():
    filepath = Path(BASE_DIR) / "videos"
    account_file = Path(BASE_DIR / "cookies" / "douyin_uploader" / "account.json")
    
    # 检查 Cookie 是否存在和有效
    cookie_valid = await douyin_setup(account_file, handle=False)
    
    if not cookie_valid:
        print("[*] Cookie 不存在或已失效，开始自动登录...")
        await auto_login_douyin(str(account_file))
        # 再次验证
        cookie_valid = await douyin_setup(account_file, handle=False)
        if not cookie_valid:
            print("[!] 登录失败，请重试")
            return
    
    # 获取视频目录
    folder_path = Path(filepath)
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    
    if file_num == 0:
        print(f"[!] 在 {filepath} 目录下没有找到 .mp4 视频文件")
        return
    
    print(f"[*] 找到 {file_num} 个视频文件")
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
    
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        thumbnail_path = file.with_suffix('.png')
        
        print(f"\n[{index+1}/{file_num}] 视频文件：{file.name}")
        print(f"    标题：{title}")
        print(f"    话题：{tags}")
        
        app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file)
        await app.main()
        print(f"[+] 视频 {file.name} 上传完成")


if __name__ == '__main__':
    asyncio.run(main())
