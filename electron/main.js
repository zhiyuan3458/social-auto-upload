const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

// 后端进程
let backendProcess = null
let mainWindow = null

// 判断是否是开发环境
const isDev = !app.isPackaged

// 获取后端可执行文件路径
function getBackendPath() {
  if (isDev) {
    // 开发环境：直接运行 Python
    return null
  }
  
  // 生产环境：根据平台获取打包后的可执行文件
  const platform = process.platform
  const resourcesPath = process.resourcesPath
  
  if (platform === 'win32') {
    return path.join(resourcesPath, 'backend', 'sau_backend.exe')
  } else if (platform === 'darwin') {
    return path.join(resourcesPath, 'backend', 'sau_backend')
  }
  
  return null
}

// 启动后端服务
function startBackend() {
  return new Promise((resolve, reject) => {
    if (isDev) {
      // 开发环境：使用 Python 直接运行
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
      const backendScript = path.join(__dirname, '..', 'sau_backend.py')
      
      console.log('开发模式：启动 Python 后端...')
      backendProcess = spawn(pythonCmd, [backendScript], {
        cwd: path.join(__dirname, '..'),
        env: { ...process.env }
      })
    } else {
      // 生产环境：运行打包后的可执行文件
      const backendPath = getBackendPath()
      
      if (!backendPath || !fs.existsSync(backendPath)) {
        console.error('后端可执行文件不存在:', backendPath)
        reject(new Error('Backend executable not found'))
        return
      }
      
      console.log('生产模式：启动后端服务...', backendPath)
      const backendDir = path.dirname(backendPath)
      backendProcess = spawn(backendPath, [], {
        cwd: backendDir,
        env: { 
          ...process.env,
          // 设置 Playwright 浏览器路径
          PLAYWRIGHT_BROWSERS_PATH: path.join(backendDir, 'ms-playwright')
        }
      })
    }
    
    // 监听后端输出
    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend]: ${data}`)
      // 检测后端是否启动成功
      if (data.toString().includes('Running on')) {
        resolve()
      }
    })
    
    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error]: ${data}`)
    })
    
    backendProcess.on('error', (err) => {
      console.error('后端启动失败:', err)
      reject(err)
    })
    
    backendProcess.on('close', (code) => {
      console.log(`后端进程退出，代码: ${code}`)
    })
    
    // 设置超时，防止无限等待（增加到 15 秒，等待后端完全启动）
    setTimeout(() => {
      resolve() // 超时也继续，可能后端已经启动
    }, 15000)
  })
}

// 停止后端服务
function stopBackend() {
  if (backendProcess) {
    console.log('停止后端服务...')
    
    if (process.platform === 'win32') {
      // Windows: 使用 taskkill 强制结束进程树
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t'])
    } else {
      // Mac/Linux: 发送 SIGTERM
      backendProcess.kill('SIGTERM')
    }
    
    backendProcess = null
  }
}

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    title: 'Social Auto Upload',
    show: false // 先隐藏，等加载完成再显示
  })
  
  // 加载页面
  if (isDev) {
    // 开发环境：加载 Vite 开发服务器
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    // 生产环境：加载打包后的静态文件
    mainWindow.loadFile(path.join(__dirname, '..', 'sau_frontend', 'dist', 'index.html'))
  }
  
  // 页面加载完成后显示窗口
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })
  
  // 窗口关闭时清理
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// 应用准备就绪
app.whenReady().then(async () => {
  try {
    // 先启动后端
    await startBackend()
    console.log('后端服务已启动')
    
    // 再创建窗口
    createWindow()
  } catch (error) {
    console.error('启动失败:', error)
    // 即使后端启动失败也尝试创建窗口
    createWindow()
  }
  
  // macOS: 点击 dock 图标时重新创建窗口
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// 所有窗口关闭时
app.on('window-all-closed', () => {
  stopBackend()
  
  // macOS 上不退出应用
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 应用退出前
app.on('before-quit', () => {
  stopBackend()
})

// IPC 通信：获取应用信息
ipcMain.handle('get-app-info', () => {
  return {
    version: app.getVersion(),
    platform: process.platform,
    isDev: isDev
  }
})
