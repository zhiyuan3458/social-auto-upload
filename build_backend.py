#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python backend build script
Supports Windows and macOS
Auto-includes Playwright Chromium browser
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Fix Windows encoding issue
if platform.system() == 'Windows':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def get_separator():
    """Get path separator for PyInstaller --add-data"""
    return ';' if platform.system() == 'Windows' else ':'

def get_playwright_browsers_path():
    """Get Playwright browser install path"""
    if platform.system() == 'Windows':
        base = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright'
    else:  # macOS / Linux
        base = Path.home() / 'Library' / 'Caches' / 'ms-playwright'
    
    if not base.exists():
        base = Path.home() / '.cache' / 'ms-playwright'
    
    return base

def find_chromium_path():
    """Find the latest Chromium browser path"""
    browsers_path = get_playwright_browsers_path()
    
    if not browsers_path.exists():
        return None
    
    chromium_versions = []
    for item in browsers_path.iterdir():
        # 匹配 chromium-XXXX 格式（不包含 headless_shell）
        if item.is_dir() and item.name.startswith('chromium-') and 'headless' not in item.name.lower():
            try:
                # 提取版本号（chromium-1200 -> 1200）
                version = int(item.name.split('-')[1])
                chromium_versions.append((version, item))
            except (ValueError, IndexError):
                # 如果版本号解析失败，跳过
                continue
    
    if chromium_versions:
        # 按版本号排序，返回最新版本
        chromium_versions.sort(key=lambda x: x[0], reverse=True)
        return chromium_versions[0][1]
    
    return None

def build_backend():
    """Build backend"""
    print("=" * 60)
    print("Building Python backend...")
    print(f"System: {platform.system()}")
    print("=" * 60)
    
    # Project root directory
    root_dir = Path(__file__).parent.resolve()
    os.chdir(root_dir)
    
    # Output directory
    output_dir = root_dir / "build" / "backend"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sep = get_separator()
    
    # PyInstaller arguments
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "sau_backend",
        "--distpath", str(output_dir),
        "--workpath", str(root_dir / "build" / "temp"),
        "--specpath", str(root_dir / "build"),
        # Add data files
        f"--add-data={root_dir / 'utils'}{sep}utils",
        f"--add-data={root_dir / 'myUtils'}{sep}myUtils",
        f"--add-data={root_dir / 'uploader'}{sep}uploader",
        f"--add-data={root_dir / 'ai_module'}{sep}ai_module",  # AI module
        # Hidden imports
        "--hidden-import=playwright",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=playwright.async_api",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=sqlite3",
        "--hidden-import=PIL",
        "--hidden-import=yaml",
        # Clean
        "--clean",
        # Entry file
        str(root_dir / "sau_backend.py")
    ]
    
    print("Running command:")
    print(" ".join(pyinstaller_args))
    print()
    
    # Run PyInstaller
    result = subprocess.run(pyinstaller_args)
    
    if result.returncode != 0:
        print("[X] Build failed!")
        return False
    
    # Copy data directories
    print("\nCopying data directories...")
    
    data_dirs = ["cookiesFile", "db", "videoFile", "ai_config"]
    for dir_name in data_dirs:
        src = root_dir / dir_name
        dst = output_dir / dir_name
        
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  [OK] Copied {dir_name}/")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created {dir_name}/")
    
    # Copy latest Playwright Chromium browser
    print("\nCopying Playwright Chromium browser...")
    chromium_path = find_chromium_path()
    
    if chromium_path and chromium_path.exists():
        # 清理旧的 ms-playwright 目录
        dst_browsers_root = output_dir / "ms-playwright"
        if dst_browsers_root.exists():
            shutil.rmtree(dst_browsers_root)
        dst_browsers_root.mkdir(parents=True, exist_ok=True)
        
        dst_browsers = dst_browsers_root / chromium_path.name
        shutil.copytree(chromium_path, dst_browsers)
        size = get_dir_size(dst_browsers)
        print(f"  [OK] Copied: {chromium_path.name} ({size:.1f} MB)")
    else:
        print("  [WARN] Playwright Chromium not found, please run:")
        print("         python -m playwright install chromium")
        print("  [WARN] Users need to install browser manually!")
    
    print()
    print("=" * 60)
    print("[OK] Backend build completed!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    
    return True

def get_dir_size(path):
    """Calculate directory size (MB)"""
    total = 0
    for p in Path(path).rglob('*'):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024 * 1024)

def install_playwright_browsers():
    """Install Playwright browser"""
    print("Installing Playwright Chromium browser...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    print("[OK] Installation completed!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Python backend")
    parser.add_argument("--install-browsers", action="store_true", 
                       help="Install Playwright browser")
    
    args = parser.parse_args()
    
    if args.install_browsers:
        install_playwright_browsers()
    else:
        success = build_backend()
        sys.exit(0 if success else 1)
