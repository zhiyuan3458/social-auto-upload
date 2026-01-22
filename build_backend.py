#!/usr/bin/env python3
"""
Python 后端打包脚本
支持 Windows 和 macOS
自动包含 Playwright Chromium 浏览器
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def get_separator():
    """获取路径分隔符（PyInstaller --add-data 用）"""
    return ';' if platform.system() == 'Windows' else ':'

def get_playwright_browsers_path():
    """获取 Playwright 浏览器安装路径"""
    # Playwright 默认安装路径
    if platform.system() == 'Windows':
        base = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright'
    else:  # macOS / Linux
        base = Path.home() / 'Library' / 'Caches' / 'ms-playwright'
    
    if not base.exists():
        # 尝试另一个常见路径
        base = Path.home() / '.cache' / 'ms-playwright'
    
    return base

def find_chromium_path():
    """查找已安装的 Chromium 路径"""
    browsers_path = get_playwright_browsers_path()
    
    if not browsers_path.exists():
        return None
    
    # 查找 chromium 目录
    for item in browsers_path.iterdir():
        if item.is_dir() and 'chromium' in item.name.lower():
            return item
    
    return None

def build_backend():
    """打包后端"""
    print("=" * 60)
    print("开始打包 Python 后端...")
    print(f"系统: {platform.system()}")
    print("=" * 60)
    
    # 项目根目录
    root_dir = Path(__file__).parent.resolve()
    os.chdir(root_dir)
    
    # 输出目录
    output_dir = root_dir / "build" / "backend"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sep = get_separator()
    
    # 查找 Playwright Chromium
    chromium_path = find_chromium_path()
    
    # PyInstaller 参数 - 使用绝对路径
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "sau_backend",
        "--distpath", str(output_dir),
        "--workpath", str(root_dir / "build" / "temp"),
        "--specpath", str(root_dir / "build"),
        # 添加数据文件（使用绝对路径）
        f"--add-data={root_dir / 'utils'}{sep}utils",
        f"--add-data={root_dir / 'myUtils'}{sep}myUtils",
        f"--add-data={root_dir / 'uploader'}{sep}uploader",
        # 隐式导入
        "--hidden-import=playwright",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=playwright.async_api",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=sqlite3",
        # 清理
        "--clean",
        # 入口文件（使用绝对路径）
        str(root_dir / "sau_backend.py")
    ]
    
    print("执行命令:")
    print(" ".join(pyinstaller_args))
    print()
    
    # 运行 PyInstaller
    result = subprocess.run(pyinstaller_args)
    
    if result.returncode != 0:
        print("❌ 打包失败!")
        return False
    
    # 复制必要的数据目录
    print("\n复制数据目录...")
    
    data_dirs = ["cookiesFile", "db", "videoFile"]
    for dir_name in data_dirs:
        src = root_dir / dir_name
        dst = output_dir / dir_name
        
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  ✓ 复制 {dir_name}/")
        else:
            # 创建空目录
            dst.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ 创建 {dir_name}/")
    
    # 复制 Playwright Chromium 浏览器
    print("\n复制 Playwright Chromium 浏览器...")
    if chromium_path and chromium_path.exists():
        dst_browsers = output_dir / "ms-playwright" / chromium_path.name
        if dst_browsers.exists():
            shutil.rmtree(dst_browsers)
        dst_browsers.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(chromium_path, dst_browsers)
        print(f"  ✓ 复制 Chromium: {chromium_path.name}")
        print(f"    大小: {get_dir_size(dst_browsers):.1f} MB")
    else:
        print("  ⚠️ 未找到 Playwright Chromium，请先运行:")
        print("     python -m playwright install chromium")
        print("  ⚠️ 用户需要自行安装浏览器!")
    
    print()
    print("=" * 60)
    print("✅ 后端打包完成!")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    return True

def get_dir_size(path):
    """计算目录大小(MB)"""
    total = 0
    for p in Path(path).rglob('*'):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024 * 1024)

def install_playwright_browsers():
    """安装 Playwright 浏览器"""
    print("安装 Playwright Chromium 浏览器...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    print("✅ 安装完成!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="打包 Python 后端")
    parser.add_argument("--install-browsers", action="store_true", 
                       help="安装 Playwright 浏览器")
    
    args = parser.parse_args()
    
    if args.install_browsers:
        install_playwright_browsers()
    else:
        success = build_backend()
        sys.exit(0 if success else 1)
