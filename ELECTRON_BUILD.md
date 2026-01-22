# Electron 打包指南

## 项目结构

```
social-auto-upload/
├── electron/                # Electron 主进程
│   ├── main.js             # 主进程入口
│   └── preload.js          # 预加载脚本
├── sau_frontend/           # Vue 前端
├── sau_backend.py          # Flask 后端
├── package.json            # Electron 配置
├── build_backend.py        # Python 打包脚本
└── build/                  # 打包输出目录
    ├── backend/            # Python 后端 exe
    └── icon.png/ico/icns   # 应用图标
```

## 开发环境

### 1. 安装依赖

```bash
# 安装 Node.js 依赖
npm install

# 安装前端依赖
cd sau_frontend && npm install && cd ..

# 安装 Python 依赖
pip install -r requirements.txt
pip install pyinstaller
```

### 2. 开发模式运行

```bash
# 方式1：分别启动
# 终端1：启动 Python 后端
python sau_backend.py

# 终端2：启动前端
cd sau_frontend && npm run dev

# 终端3：启动 Electron
npm run dev:electron

# 方式2：一键启动（需要先启动 Python 后端）
python sau_backend.py &  # 后台运行后端
npm run dev              # 启动前端和 Electron
```

## 打包流程

### 步骤1：打包 Python 后端

```bash
# macOS
python build_backend.py

# Windows (在 Windows 机器上执行)
python build_backend.py
```

打包后的文件在 `build/backend/` 目录：
- macOS: `sau_backend` (无后缀)
- Windows: `sau_backend.exe`

### 步骤2：准备图标文件

将应用图标放到 `build/` 目录：
- `icon.png` - 通用图标 (512x512)
- `icon.ico` - Windows 图标
- `icon.icns` - macOS 图标

可以用在线工具将 PNG 转换为 ICO/ICNS。

### 步骤3：打包 Electron 应用

```bash
# 打包 macOS 版本 (在 Mac 上执行)
npm run build:mac

# 打包 Windows 版本 (在 Windows 上执行，或使用 wine)
npm run build:win

# 同时打包两个平台 (需要对应环境)
npm run build:all
```

打包后的安装包在 `release/` 目录：
- macOS: `Social Auto Upload-x.x.x.dmg`
- Windows: `Social Auto Upload Setup x.x.x.exe`

## 完整打包流程（Mac）

```bash
# 1. 安装所有依赖
npm install
cd sau_frontend && npm install && cd ..
pip install pyinstaller

# 2. 打包 Python 后端
python build_backend.py

# 3. 打包 Electron (Mac 版)
npm run build:mac
```

## 完整打包流程（Windows）

```bash
# 1. 安装所有依赖
npm install
cd sau_frontend && npm install && cd ..
pip install pyinstaller

# 2. 打包 Python 后端
python build_backend.py

# 3. 打包 Electron (Windows 版)
npm run build:win
```

## 注意事项

1. **跨平台打包**：Python 后端必须在目标平台上打包
   - macOS 版本需要在 Mac 上打包
   - Windows 版本需要在 Windows 上打包

2. **Playwright 浏览器**：
   ```bash
   # 打包前先安装 Chromium（会自动打包进 exe）
   python -m playwright install chromium
   
   # 或使用脚本安装
   python build_backend.py --install-browsers
   ```
   
   打包脚本会自动将 Chromium 浏览器复制到输出目录，**用户无需额外安装**！

3. **数据目录**：打包后，用户数据存储在可执行文件同级目录：
   - `cookiesFile/` - Cookie 文件
   - `db/` - 数据库
   - `videoFile/` - 视频文件
   - `ms-playwright/` - Chromium 浏览器（自动包含）

4. **签名（macOS）**：如果要分发给其他用户，需要 Apple 开发者证书签名

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Electron 应用                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐│
│  │   主进程        │    │        渲染进程              ││
│  │   (main.js)     │    │     (Vue 前端)              ││
│  │                 │    │                             ││
│  │  ┌───────────┐  │    │  ┌─────────────────────┐   ││
│  │  │启动后端   │  │    │  │  localhost:5173     │   ││
│  │  │子进程     │  │◄──►│  │  或 dist/index.html│   ││
│  │  └───────────┘  │    │  └─────────────────────┘   ││
│  │       │         │    │           │                 ││
│  └───────┼─────────┘    └───────────┼─────────────────┘│
│          │                          │                   │
│          ▼                          ▼                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Flask 后端 (sau_backend)            │   │
│  │                   :5409                          │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │  Playwright (Headless Chromium)         │    │   │
│  │  │  - 获取登录二维码                         │    │   │
│  │  │  - 验证 Cookie                           │    │   │
│  │  │  - 上传视频                              │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```
