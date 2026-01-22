from pathlib import Path
import sys
import os

# 判断是否是打包后的环境
def is_packaged():
    return getattr(sys, 'frozen', False)

# 获取基础目录
if is_packaged():
    # PyInstaller 打包后的路径
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent.resolve()

# 获取数据目录（用于存储 cookie、数据库等可写文件）
def get_data_dir():
    if is_packaged():
        # 打包后使用可执行文件所在目录
        return Path(os.path.dirname(sys.executable))
    return BASE_DIR

DATA_DIR = get_data_dir()

# 设置 Playwright 浏览器路径（打包后使用自带的浏览器）
def setup_playwright_browsers():
    if is_packaged():
        browsers_path = DATA_DIR / "ms-playwright"
        if browsers_path.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
            print(f"✓ 使用自带浏览器: {browsers_path}")

# 初始化时设置浏览器路径
setup_playwright_browsers()

XHS_SERVER = "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # Mac Chrome 路径
LOCAL_CHROME_HEADLESS = True  # Electron 模式下使用无头浏览器
